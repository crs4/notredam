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
from dam.mprocessor.schedule import Schedule

class BatchError(Exception):
    pass

#
# This class can be only a singleton (option only_one_server=True) to ensure that
# only one process is active in mediadart at the same time.
#
class MProcessor(MQServer):
    def wake_process(self):
        waiting_processes = Process.objects.filter(start_date=None)
        if waiting_processes:
            return waiting_processes[0]
        else:
            return None

    def mq_run(self, process_id=None):
        """Run a waiting process.
        
           This method tries to run a waiting process and schedules itself to run again
           when the process ends so that the queue of waiting processes can be emptied
           """

        process = self.wake_process()
        if not process:
            msg = ""
        elif str(process.pk) != str(process_id):
            msg = "request put on execution queue"
        else:
            msg = "request running"
        if process:
            d = Batch(process).run()
            d.addCallback(self.mq_run)
        return msg

class Batch:
    def __init__(self, process):
        self.cfg = Configurator()
        self.max_outstanding = self.cfg.getint('MPROCESSOR', 'max_outstanding')
        self.batch_size = self.cfg.getint('MPROCESSOR', 'batch_size') # how many items to load
        self.pipeline = loads(process.pipeline.params)
        self.dag = DAG(self.pipeline)
        self.schedule_length = len(self.pipeline)
        self.process = process
        self.scripts = self._get_scripts(self.pipeline)
        self.all_targets_read = False      # True when all targets have been read
        self.gameover = False              # True when all targets are done
        self.deferred = None               # used to signal end of batch job
        self.outstanding = 0               # number of not yet answered requests
        self.cur_batch = 0                 # index in batch
        self.cur_task = 0                  # index in tasks
        self.totals = {'update':0, 'passed':0, 'failed':0, 'targets': 0, None: 0} 
        self.results = {}

    def run(self):
        "Start the iteration initializing state so that the iteration starts correctly"
        log.debug('### Running process %s' % str(self.process.pk))
        self.deferred = defer.Deferred()
        self.process.start_date = datetime.datetime.now()
        self.process.save()
        self.process.targets = ProcessTarget.objects.filter(process=self.process).count()
        self.tasks = []
        reactor.callLater(0, self._iterate)
        return self.deferred

    def _update_item_stats(self, item, action, result, success, failure, cancelled):
        #log.debug('_update_item_stats: item=%s action=%s success=%s, failure=%s, cancelled=%s' % (item.target_id, action, success, failure, cancelled)) #d
        item.actions_passed += success
        item.actions_failed += failure
        item.actions_cancelled += cancelled
        item.actions_todo -= (success + failure + cancelled)
        if item.pk not in self.results:
            self.results[item.pk] = {}
        self.results[item.pk][action] = (success, result)
        if item.actions_todo <= 0 or failure > 0:
            item.result = dumps(self.results[item.pk])
        if item.actions_todo <= 0:
            #log.debug('_update_item_stats: finalizing item %s' % item.target_id) #d
            del self.results[item.pk]
        
    def _get_scripts(self, pipeline):
        """Load scripts from plugin directory. 
        
           Returns the dictionary
           {'script_name': (callable, params)}
           Throws an exception if not all scripts can be loaded.
        """
        plugins_module = self.cfg.get("MPROCESSOR", "plugins")
        print plugins_module
        scripts = {}
        for script_key, script_dict in pipeline.items():
            script_name = script_dict['script_name']
            full_name = plugins_module + '.' + script_name + '.run'
            p = full_name.split('.')
            log.info('<$> loading script: %s' % '.'.join(p[:-1]))
            m = __import__('.'.join(p[:-1]), fromlist = p[:-1])
            f = getattr(m, p[-1], None)
            if not f or not callable(f):
                raise BatchError('Plugin %s has no callable run method' % script_name)
            else:
                scripts[script_key] = (f, script_dict.get('params', {}))
        return scripts

    def _new_batch(self):
        "Loads from db the next batch of items and associate a schedule to each item"
        if self.all_targets_read:
            return []

        targetset = ProcessTarget.objects.filter(process=self.process.pk)[self.cur_batch:self.cur_batch + self.batch_size]
        if targetset:
            self.cur_batch += self.batch_size
            ret = [{'item':x, 'schedule':Schedule(self.dag, x.target_id)} for x in targetset]   # item, index of current action, schedule
        else:
            self.all_targets_read = True
            ret = []
        return ret

    def _get_action(self):
        """returns the first action found or None. Delete tasks with no actions left"""
        #log.debug("_get_action on num_tasks=%s" % len(self.tasks)) #d
        to_delete = []
        action = ''
        for n in xrange(len(self.tasks)):
            idx = (self.cur_task + n) % len(self.tasks)
            task = self.tasks[idx]
            action = task['schedule'].action_to_run()
            if action is None:
                #log.debug('111111113 - deleting task %s' % task) #d
                to_delete.append(task)
            elif action:
                #log.debug('111111112 -%s- %s' % (action, len(action))) #d
                break

        #log.debug('to_delete %s' % to_delete) #d

        for t in to_delete:                   
            #log.debug('deleting done target %s' % t['item'].target_id) #d
            self.tasks.remove(t)

        #log.debug('111111111') #d
        # update cur_task so that we do not always start querying the same task for new actions
        if action:
            idx = self.tasks.index(task)
            self.cur_task = (idx + 1) % len(self.tasks)
        else:
            self.cur_task = 0

        #log.debug('2222222') #d
        # if action is None or empy there is no action ready to run
        # if there are new targets available try to read some and find some new action
        if action:
            return action, task
        else:
            #log.debug('33333') #d
            if not self.all_targets_read and self.outstanding < self.max_outstanding:
                new_tasks = self._new_batch()
                #log.debug('4444 %s' % self.tasks) #d
                if new_tasks:
                    #log.debug('5555') #d
                    self.cur_task = len(self.tasks)
                    self.tasks.extend(new_tasks)
            if self.all_targets_read and not self.tasks:
                log.debug("_get_action: gameover")
                self.gameover = True
                self.process.end_date = datetime.datetime.now()
                self.process.save()
                self.deferred.callback('done')
            return  None, None


    def _iterate(self):
        """ Run the actions listed in schedule on the items returned by _new_batch """
        #log.debug('_iterate: oustanding=%s' % self.outstanding) #d
        if self.gameover:
            log.debug('_iterate: gameover')
            return
        action, task = self._get_action()
        if action:
            item, schedule = task['item'], task['schedule']
            method, params = self.scripts[action]
            #log.debug('target %s: executing action %s' % (item.target_id, action))
            try:
                item_params = loads(item.params)
                #log.debug('item_params %s'%item_params)
                #log.debug('params %s'%params)
                params.update(item_params.get('*', {}))
                params.update(item_params.get(action, {}))
                self.outstanding += 1
                log.debug('calling method with params ws=%s, id=%s, params=%s' % (self.process.workspace.pk, item.target_id, params))
                d = method(self.process.workspace, item.target_id, **params)
            except Exception, e:
                self._handle_err(str(e), item, schedule, action, params)
            else:
                d.addCallbacks(self._handle_ok, self._handle_err, 
                    callbackArgs=[item, schedule, action, params], errbackArgs=[item, schedule, action, params])
        # If _get_action did not find anything and there are no more targets, no action
        # will be available until an action completes and allows more actions to go ready.
        if self.outstanding < self.max_outstanding and (action or not self.all_targets_read):
            #log.debug('_iterate: rescheduling') #d
            reactor.callLater(0, self._iterate)

    def _handle_ok(self, result, item, schedule, action, params):
        #log.info("_handle_ok: target %s: action %s: %s" % (item.target_id, action, result)) #d
        self.outstanding -= 1
        schedule.done(action)
        if self.outstanding < self.max_outstanding:
            ##log.debug('_handle_ok: rescheduling') #d
            reactor.callLater(0, self._iterate)
        self._update_item_stats(item, action, result, 1, 0, 0)
        item.save()


    def _handle_err(self, result, item, schedule, action, params):
        log.error('_handle_err action %s on target_id=%s: %s' % (action, item.target_id, str(result)))
        self.outstanding -= 1
        cancelled = schedule.fail(action)
        self._update_item_stats(item, action, str(result), 0, 1, 0)
        for a in cancelled:
            self._update_item_stats(item, a, "cancelled on failed %s" % action, 0, 0, 1)
        if self.outstanding < self.max_outstanding:
            ##log.debug('_handle_err: rescheduling') #d
            reactor.callLater(0, self._iterate)
        item.save()


def start_server():
    default_start_mqueue(MProcessor, [])

##############################################################################################
# 
# Test

import sys
from django.contrib.auth.models import User
from dam.mprocessor.make_plugins import pipeline as test_pipe
from dam.mprocessor.make_plugins import simple_pipe as test_pipe2
from dam.mprocessor.models import Pipeline, TriggerEvent
from dam.workspace.models import DAMWorkspace
from json import dumps

class fake_config:
    dictionary = {
        'MPROCESSOR': {
            'plugins': 'dam.mprocessor.plugins',
            'max_outstanding': '17',
            'batch_size': '5',
        },
    }
    def get(self, section, option):
        return self.dictionary[section][option]

    def getint(self, section, option):
        return int(self.dictionary[section][option])

gameover = False

def end_test(result, process):
    global gameover
    gameover = True
    print_stats(process, False)
    log.debug('end of test %s' % result)
    reactor.callLater(3, reactor.stop)

def print_stats(process, redo=True):
    if process.targets == 0:
        print >>sys.stderr, 'Process stats: not initialized'
    else:
        print >>sys.stderr, 'Process stats: completed=%d/%d failed=%d/%d' % (process.get_num_target_completed(), process.targets,
                                   process.get_num_target_failed(), process.targets)

    pt = ProcessTarget.objects.filter(process=process, actions_todo=0, actions_failed=0)
    print >>sys.stderr, 'Process stats: completed successfully: %s' % ' '.join([x.target_id for x in pt])
    if not gameover and redo:
        reactor.callLater(1, print_stats, process)

def test():
    global Configurator
    Configurator = fake_config
    ws = DAMWorkspace.objects.get(pk=1)
    user = User.objects.get(username='admin')
    t = TriggerEvent.objects.get_or_create(name="test")[0]
    print 't.pk=', t.pk
    try: 
        print 'attempting to reuse pipeline'
        pipeline = Pipeline.objects.get(name='test4', workspace=ws)
    except:
        print 'creating new pipeline'
        pipeline = Pipeline.objects.create(name="test4", description='', params=dumps(test_pipe2), workspace=ws)
        print 'ok'
        pipeline.triggers.add(t)
        print 'ok2'
        pipeline.save()
        print 'done'
    process = Process.objects.create(pipeline=pipeline, workspace=ws, launched_by=user)
    for n in xrange(15):
        print 'adding target %d' % n
        process.add_params(item = 'item%d' % n)
    try:
        batch = Batch(process)
        d = batch.run()
        d.addBoth(end_test, process)
    except Exception, e:
        log.error("Fatal initialization error: %s" % str(e))
        reactor.stop()
    print_stats(process)

if __name__=='__main__':
    reactor.callWhenRunning(test)
    reactor.run()
