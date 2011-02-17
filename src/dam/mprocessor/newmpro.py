####################################################################################
#
# Functionalities
# 
# 0.1
# Read the list of items id and the pipeline to operate upon them.
# Create the DAG of the pipeline and request a schedule of single actions.
# Loop over all items and for each item loop over pipeline.
#     On success, execute next actions.
#     On error, log the error, delete all dependent actions from pipeline and 
#     execute next actions.
# 
# 0.2
# Keep the total number of outstanding requests under a predefined limit.
# (Congestion control)
# 
# 0.3
# Invert loop order, looping over pipeline and for each stage on all items.
# This avoids issuing consecutive requests for the same item, avoid stalling
# on NFS locking.
# 
# 0.4
# Paginate the items lookup, to decrease the memory footprint of the mprocessor
# and allow scaling to very large jobs.
# 
# 0.5
# Randomize schedules, associating a schedule to each item. This can help improve
# servers load. Not useful is schedules are natively totally ordered.
# 
#####################################################################################


import os
import datetime
from twisted.internet import reactor, defer
from mediadart.utils import default_start_mqueue


from json import loads
from mediadart.mqueue.mqserver import MQServer
from mediadart.config import Configurator
from mediadart import log
from dam.mprocessor.models import Process, ProcessTarget
from dam.mprocessor.pipeline import DAG

class BatchError(Exception):
    pass

class MProcessor(MQServer):
    def mq_run(self, process_id, call_mode='non-blocking'):
        log.debug('launching process %s'%process_id)
        process = Process.objects.get(pk=process_id)
        log.debug('--------- process %s'%process)
        batch = Batch(process)
        d = batch.run()
        if call_mode != 'non-blocking':
            return d
        else:
            return 'request in progress'

class Batch:
    def __init__(self, process):
        self.cfg = Configurator()
        self.max_outstanding = self.cfg.getint('MPROCESSOR', 'max_outstanding')
        self.update_interval = self.cfg.getint('MPROCESSOR', 'update_interval')
        self.batch_size = self.cfg.getint('MPROCESSOR', 'batch_size') # how many items to load
        self.pipeline = loads(process.pipeline.params)
        self.dag = DAG(self.pipeline)
        self.schedule_length = len(self.pipeline)
        self.process = process
        self.scripts = self._get_scripts(self.pipeline)
        self.deferred = None               # used to signal end of batch job
        self.outstanding = 0               # number of not yet answered requests
        self.cur_batch = 0                 # index in batch
        self.totals = {'update':0, 'passed':0, 'failed':0, 'targets': 0, None: 0} 
        self.results = {}

    def run(self):
        "Start the iteration initializing state so that the iteration starts correctly"
        log.debug('running process %s' % str(self.process.pk))
        self.deferred = defer.Deferred()
        self.process.targets = ProcessTarget.objects.filter(process=self.process).count()
        self.tasks = []
        reactor.callLater(0, self._iterate)
        return self.deferred

    def _update_item_stats(self, item, action, result, success, failure, cancelled):
        log.debug('_update_item_stats: item=%s action=%s success=%s, failure=%s, cancelled=%s' % (item.target_id, action, success, failure, cancelled))
        item.actions_passed += success
        item.actions_failed += failure
        item.actions_cancelled += cancelled
        item.actions_todo -= (success + failure + cancelled)
        if item.target_id not in self.results:
            self.results[item.target_id] = {}
        self.results[item.target_id][action] = (success, result)
        if item.actions_todo <= 0:
            log.debug('_update_item_stats: finalizing item %s' % item.target_id)
            item.result = dumps(self.results[item.target_id])
            del self.results[item.target_id]
        
    def _get_scripts(self, pipeline):
        """Load scripts from plugin directory. 
        
           Returns the dictionary
           {'script_name': (callable, params)}
           Throws an exception if not all scripts can be loaded.
        """
        plugins_module = self.cfg.get("MPROCESSOR", "plugins")
        scripts = {}
        for script_key, script_dict in pipeline.items():
            script_name = script_dict['script_name']
            full_name = plugins_module + '.' + script_name + '.run'
            p = full_name.split('.')
            log.info('<$> loading script: %s' % '.'.join(p))
            m = __import__('.'.join(p[:-1]), fromlist = p[:-1])
            f = getattr(m, p[-1], None)
            if not f or not callable(f):
                raise BatchError('Plugin %s has no callable run method' % script_name)
            else:
                scripts[script_key] = (f, script_dict.get('params', {}))
        return scripts

    def _new_batch(self):
        "Loads from db the next batch of items and associate a schedule to each item"
        targetset = ProcessTarget.objects.filter(process=self.process.pk)[self.cur_batch:self.cur_batch + self.batch_size]
        if targetset:
            self.cur_batch += self.batch_size
            ret = [{'item':x, 'schedule':self.dag.sort(True)} for x in targetset]   # item, index of current action, schedule
        else:
            self.deferred.callback('done')
            self.process.end_date = datetime.datetime.now()
            self.process.save()
            ret = None
        return ret

    def _get_action(self):
        """returns the first action found or None. Retire tasks with no actions left"""
        schedule = None
        while not schedule and self.tasks:
            task = self.tasks.pop(0)
            schedule = task['schedule']
        if schedule:
            action = schedule.pop(0)
            if schedule:
                self.tasks.append(task)   # still work to do
            else:
                log.debug('%s: DONE' % task['item'].target_id)
            method, params = self.scripts[action]
            log.debug('_get_action: %s' % action)
            return action, task['item'], schedule, method, params
        else:
            log.debug('_get_action: None')
            return None, None, None, None, None

    def _iterate(self):
        """ Run the actions listed in schedule on the items returned by _new_batch """
        #log.debug('_iterate')
        if self.tasks is None:
            #log.debug('ALREADY DONE')
            return
        if not self.tasks:
            self.tasks = self._new_batch()
        action, item, schedule, method, params = self._get_action()
        if action:
            log.debug('target %s: executing action %s: remaining %s' % (item.target_id, action, schedule))
            try:
                log.debug('calling run with params %s'%params)
                self.outstanding += 1
                d = method(item.target_id, self.process.workspace, **params)
            except Exception, e:
                self._handle_err(str(e), item, schedule, action, params)
            else:
                d.addCallbacks(self._handle_ok, self._handle_err, 
                    callbackArgs=[item, schedule, action, params], errbackArgs=[item, schedule, action, params])
            if self.outstanding < self.max_outstanding:
                reactor.callLater(0.1, self._iterate)
        else:
            log.debug('EMPTY ACTION')
            reactor.callLater(0, self._iterate)

    def _handle_ok(self, result, item, schedule, action, params):
        log.info("_handle_ok: target %s: action %s: %s" % (item.target_id, action, result))
        self.outstanding -= 1
        if self.outstanding < self.max_outstanding:
            reactor.callLater(0, self._iterate)
        self._update_item_stats(item, action, result, 1, 0, 0)
        item.save()

    def _handle_err(self, result, item, schedule, action, params):
        log.error('_handle_err %s %s %s' % (str(result), item.target_id, action))
        self.outstanding -= 1
        dependencies = self.dag.dependencies(action)
        cancelled = 0
        for a in dependencies:
            if a in schedule:
                log.info('target %s: removing action %s, dependent on failed %s' % (item.target_id, a, action))
                cancelled += 1
                schedule.remove(a)
        if self.outstanding < self.max_outstanding:
            reactor.callLater(0, self._iterate)
        self._update_item_stats(item, action, str(result), 0, 1, cancelled)
        item.save()


def start_server():
    default_start_mqueue(MProcessor, [])

##############################################################################################
# 
# Test

import sys
from django.contrib.auth.models import User
from dam.mprocessor.make_plugins import pipeline as test_pipe
from dam.mprocessor.models import Pipeline
from dam.workspace.models import DAMWorkspace
from json import dumps

class fake_config:
    dictionary = {
        'MPROCESSOR': {
            'plugins': 'dam.mprocessor.plugins',
            'max_outstanding': '17',
            'update_interval': '1',
            'batch_size': '5',
        },
    }
    def get(self, section, option):
        return self.dictionary[section][option]

    def getint(self, section, option):
        return int(self.dictionary[section][option])

def end_test(result, process):
    print_stats(process, [], False)
    print 'end of test %s' % result
    reactor.callLater(3, reactor.stop)

def print_stats(process, items, redo=True):
    if process.targets == 0:
        print >>sys.stderr, 'Process stats: not initialized'
    else:
        print >>sys.stderr, 'Process stats: completed=%d/%d failed=%d/%d' % (process.get_num_target_completed(), process.targets,
                                   process.get_num_target_failed(), process.targets)

    pt = ProcessTarget.objects.filter(process=process, target_id__in=items, actions_todo=0, actions_failed=0)
    print >>sys.stderr, 'Process stats: completed successfully: %s' % ' '.join([x.target_id for x in pt])
    if redo:
        reactor.callLater(1, print_stats, process, items)

def test():
    global Configurator
    Configurator = fake_config
    ws = DAMWorkspace.objects.get(pk=1)
    user = User.objects.get(username='admin')
    try: 
        pipeline = Pipeline.objects.get(name='test', workspace=ws)
    except:
        pipeline = Pipeline.objects.create(name="test", type="test", description='', params=dumps(test_pipe), workspace=ws)
    process = Process.objects.create(pipeline=pipeline, workspace=ws, launched_by=user)
    for n in xrange(250):
        print 'adding target %d' % n
        process.add_params('item%d' % n)
    try:
        batch = Batch(process)
        d = batch.run()
        d.addBoth(end_test, process)
    except Exception, e:
        log.error("Fatal initialization error: %s" % str(e))
        reactor.stop()
    print_stats(process, [
        'item0', 'item9', 'item18', 'item27', 'item36', 'item45', 'item54', 'item63', 'item72', 'item81', 'item90', 'item99', 'item108', 'item117', 'item126', 'item135', 'item144', 'item153', 'item162', 'item171', 'item180', 'item189', 'item198', 'item207', 'item216', 'item225', 'item234', 'item243',
    ])

if __name__=='__main__':
    reactor.callWhenRunning(test)
    reactor.run()
