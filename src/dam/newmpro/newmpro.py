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
from mprocessor.models import Process, ItemSet

class BatchError(Exception):
    pass

class MProcessor(MQServer):
    def mq_run(self, process_id):
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
        for script_name in pipeline:
            full_name = plugins_module + '.' + script_name + '.run'
            p = full_name.split('.')
            log.info('<$> loading script: %s' % '.'.join(p))
            m = __import__('.'.join(p[:-1]), fromlist = p[:-1])
            f = getattr(m, p[-1], None)
            if not f or not callable(f):
                raise BatchError('Plugin %s has no callable run method' % script_name)
            else:
                scripts[script_name] = (f, pipeline[script_name].get('params', {}))
        return scripts

    def _init_totals(self):
        self.totals = {'update':0, 'passed':0, 'failed':0}
        self.totals['all'] = ItemSet.objects.filter(process=self.process.process_id).count() * self.schedule_length
        self.process.total = self.totals['all']
        self.process.save()

    def _new_batch(self):
        "Loads from db the next batch of items and associate a schedule to each item"
        itemset = ItemSet.objects.filter(process=self.process.process_id)[self.cur_batch:self.cur_batch + self.batch_size]
        self.cur_batch += self.batch_size
        self.i_index = 0                  # index of the current item in item_list
        self.a_index = 0                  # index of the current action in schedule
        ret = [(x, self.dag.sort(True)) for x in itemset]
        log.debug('_new_batch: loaded %d items' % len(ret))
        return ret

    def update_totals(self, success):
        "update total number of successes/failures"
        self.totals['update'] += 1.
        if success:
            self.totals['passed'] += 1
        else:
            self.totals['failed'] += 1
        if (self.totals['update'] % self.update_interval) == 0:
            log.debug('Writing update data')
            self.process.passed = self.totals['passed']
            self.process.failures = self.totals['failed']
            self.process.save()


    def run(self):
        "Start the iteration initializing state so that the iteration starts correctly"
        log.debug('running process %s' % str(self.process.process_id))
        self.deferred = defer.Deferred()
        self.tasks = []
        self.i_index = len(self.tasks)
        self.a_index = self.schedule_length
        self.iterate()
        return self.deferred


    def iterate(self):
        """ Run the actions listed in schedule on the items returned by _new_batch """
        if self.tasks is None:
            return
            #log.debug('iterating over empy task list')
        log.debug('entering iterate: i_index = %d, a_index=%d, outs=%s' % (self.i_index, self.a_index, self.outstanding))
        self.i_index += 1
        if self.i_index >= len(self.tasks):
            self.i_index = 0
            self.a_index += 1
            if self.a_index >= self.schedule_length or not self.tasks:
                log.debug('loading new items')
                self.tasks = self._new_batch()  # sets i_index and a_index = 0
                log.debug('WWWWWW loaded %d items' % len(self.tasks))
                if not self.tasks:
                    self.deferred.callback('done')
                    self.tasks = None
                    return    # we are done
        item, schedule = self.tasks[self.i_index]
        action = schedule[self.a_index]
        log.debug('iterating over %s, action=%s, schedule=%s' % (item.item_id, action, schedule))
        if action is not None:
            method, params = self.scripts[schedule[self.a_index]]
            delay = 0.1
            try:
                d = method(item.item_id, **params)
            except Exception, e:
                log.error('Error %s: launching action %s on item %s' % (str(e), action , item.item_id))
            else:
                self.outstanding += 1
                d.addCallbacks(self.handle_ok, self.handle_err, 
                    callbackArgs=[item, schedule, action, params], errbackArgs=[item, schedule, action, params])
        else:
            log.debug("item %s: cancelled action %s" % (item.item_id, action))
            delay = 0
        if self.outstanding < self.max_outstanding:
            reactor.callLater(delay, self.iterate)


    def handle_ok(self, result, item, schedule, action, params):
        log.info(result)
        self.outstanding -= 1
        self.update_totals(success=True)
        if self.outstanding < self.max_outstanding:
            reactor.callLater(0, self.iterate)
        item.passed += 1
        item.save()


    def handle_err(self, result, item, schedule, action, params):
        log.error('handler_err %s %s %s %s' % (result, item, schedule, action))
        self.outstanding -= 1
        self.update_totals(success=False)
        self.dag.delete(action, schedule)
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


from mprocessor.models import ItemSet, Process
if __name__=='__main__':
    reactor.callWhenRunning(test)
    reactor.run()
