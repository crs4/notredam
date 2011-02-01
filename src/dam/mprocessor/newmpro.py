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
from twisted.internet import reactor, defer
from mediadart.utils import default_start_mqueue


from json import loads
from pipeline import DAG
from mediadart.mqueue.mqserver import MQServer
from mediadart.config import Configurator
from mediadart import log
from mprocessor.models import Process, ProcessTarget

class BatchError(Exception):
    pass

class MProcessor(MQServer):
    def mq_run(self, process_id):
        log.debug('launching process %s'%process_id)
        process = Process.objects.get(pk=process_id)
        batch = Batch(process)
        return batch.run()

class Batch:
    def __init__(self, process):
        self.cfg = Configurator()
        self.pipeline = loads(process.pipeline.params)
        self.dag = DAG(self.pipeline)
        self.schedule_length = len(self.pipeline)
        self.process = process
        self.scripts = self._get_scripts(self.pipeline)
        self.deferred = None               # used to signal end of batch job
        self.outstanding = 0               # number of not yet answered requests
        self.max_outstanding = self.cfg.getint('MPROCESSOR', 'max_outstanding')
        self.update_interval = self.cfg.getint('MPROCESSOR', 'update_interval')
        self.batch_size = self.cfg.getint('MPROCESSOR', 'batch_size') # how many items to load
        self.cur_batch = 0                 # index in batch
        self.totals = {}
        self._init_totals()

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

    def _init_totals(self):
        self.totals = {'update':0, 'passed':0, 'failed':0}
        self.totals['all'] = ProcessTarget.objects.filter(process=self.process.pk).count() * self.schedule_length
        self.process.total = self.totals['all']
        self.process.save()

    def _new_batch(self):
        "Loads from db the next batch of items and associate a schedule to each item"
        log.debug('_new_batch: entering')
        targetset = ProcessTarget.objects.filter(process=self.process.pk)[self.cur_batch:self.cur_batch + self.batch_size]
        log.debug('_new_batch: after filter loaded %s items' % len(targetset))
        if targetset:
            log.debug('_new_batch: inside if')
            self.cur_batch += self.batch_size
            ret = [{'item':x, 'schedule':self.dag.sort(True)} for x in targetset]   # item, index of current action, schedule
            for d in ret:
                log.error('1')
                if len(d['schedule']) != self.schedule_length:
                    log.error('### item %s: WRONG LENGTH: %s' % (d['item'].target_id, len(d['schedule'])))
                log.error('3')
            log.debug('_new_batch: end of if')
        else:
            log.debug('_new_batch: None')
            self.deferred.callback('done')
            ret = None
        if ret is not None:
            log.debug('_new_batch: returning %d items' % len(ret))
        else:
            log.debug('_new_batch: returning None')
        return ret

    def update_totals(self, success):
        "update total number of successes/failures"
        self.totals['update'] += 1.
        if success:
            self.totals['passed'] += 1
        else:
            self.totals['failed'] += 1
        if (self.totals['update'] % self.update_interval) == 0:
            self.process.passed = self.totals['passed']
            self.process.failures = self.totals['failed']
            self.process.save()

    def run(self):
        "Start the iteration initializing state so that the iteration starts correctly"
        log.debug('running process %s' % str(self.process.pk))
        self.deferred = defer.Deferred()
        self.tasks = []
        reactor.callLater(0, self.iterate)
        return self.deferred

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
            log.debug('_get_action: return %s' % action)
            return action, task['item'], schedule, method, params
        else:
            log.debug('_get_action: return None')
            return None, None, None, None, None

    def iterate(self):
        """ Run the actions listed in schedule on the items returned by _new_batch """
        log.debug('iterate')
        if self.tasks is None:
            return
        if not self.tasks:
            self.tasks = self._new_batch()
            log.debug('iterate: loaded task')
        action, item, schedule, method, params = self._get_action()
        if action:
            log.debug('target %s: executing action=%s (%d: %s)' % (item.target_id, action, id(schedule), schedule))
            try:
                log.debug('calling run with params %s'%params)
                self.outstanding += 1
                d = method(item.target_id, self.process.workspace, **params)
            except Exception, e:
                self.handle_err('Error %s: launching action %s on item %s' % (str(e), action , item.target_id), item, schedule, action, params)
            else:
                d.addCallbacks(self.handle_ok, self.handle_err, 
                    callbackArgs=[item, schedule, action, params], errbackArgs=[item, schedule, action, params])
            if self.outstanding < self.max_outstanding:
                reactor.callLater(0.1, self.iterate)
        else:
            log.debug('EMPTY ACTION')
            reactor.callLater(0, self.iterate)

    def handle_ok(self, result, item, schedule, action, params):
        log.info("target %s: action %s: %s" % (item.target_id, action, result))
        self.outstanding -= 1
        self.update_totals(success=True)
        if self.outstanding < self.max_outstanding:
            reactor.callLater(0, self.iterate)
        item.passed += 1
        item.save()


    def handle_err(self, result, item, schedule, action, params):
        log.error('handler_err %s %s %s' % (result, item.target_id, action))
        self.outstanding -= 1
        self.update_totals(success=False)
        dependencies = self.dag.dependencies(action)
        for a in dependencies:
            if a in schedule:
                log.info('target %s: removing action %s, dependent from failed %s' % (item.target_id, a, action))
                schedule.remove(a)
        if self.outstanding < self.max_outstanding:
            reactor.callLater(0, self.iterate)
        item.failed += 1
        item.save()


def start_server():
    default_start_mqueue(MProcessor, [])


def end_test(result):
    print 'end of test %s' % result
    reactor.stop()

def test():
    process = Process.objects.all()[0]
    try:
        batch = Batch(process)
        d = batch.run()
    except Exception, e:
        log.error("Fatal initialization error: %s" % str(e))
        reactor.stop()
    d.addBoth(end_test)

if __name__=='__main__':
    reactor.callWhenRunning(test)
    reactor.run()
