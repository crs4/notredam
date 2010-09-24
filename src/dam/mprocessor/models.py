import os
import time
from json import dumps, loads
from django.db import models
from dam.mprocessor import processors  # to be changed
from dam.repository.models import Component

from dam import logger

#
# example of use
# task = Task().add_component(component)\
#                .add_func('xmp_embed')\
#                .add_func('altro')\
#                .execute()
#
# or
# task = Task.object.get(id=task_id)
#

class Task(models.Model):
    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.decoded_params = loads(self.params)
        self.dirty = False
            
    task_id = models.CharField(max_length=32, primary_key=True, default=processors.new_id)
    component = models.ForeignKey(Component)
    params = models.TextField(default='["__dummy__"]')
    last_active = models.IntegerField(default=0)     # holds int(time.time())
    state = models.CharField(max_length=7, default='pending')

    def append_func(self, function_name, *function_params):
        print ("#-#-#-#-#- add_func %s" %function_name)
        self.decoded_params.append([function_name, function_params])
        self.dirty = True
        print ('self.decoded_params: %s, task_id %s' %(self.decoded_params, self.task_id))
        return self

    def leftappend_func(self, function_name, *function_params):
        index = 0
        if self.decoded_params and self.decoded_params[0] == '__dummy__':
            index = 1
        self.decoded_params.insert(index, [function_name, function_params])
        self.dirty = True
        print ('self.decoded_params: %s, task_id %s' %(self.decoded_params, self.task_id))
        return self

    def add_component(self, component):
        self.component = component
        self.dirty = True
        return self
    
    def str(self):
        return 'task_id %s, self.decoded_params %s' %(self.task_id,self.decoded_params)

    def execute(self, data):
        "This changes the state of the task and it is not undoable"
        if not self.component:
            raise('Error: executing action with no component')
        if not self.decoded_params:
            raise('Error: executing empty action')
        self.last_active = int(time.time())
        if not self.next_func():
            return
        fname, fparams = self.decoded_params[0]
        func = getattr(processors, fname)
        logger.debug('\n%s\nmprocessor: executing %s\n' % ('-'*80, fname))
        try:
            func(self, data, *fparams)
        except Exception, ex:
            self.failed()
            logger.error('Task: error executing %s: %s' % (fname, ex))
        logger.debug('\n%s\nmprocessor: %s returned' % ('-'*80, fname))
        if self.dirty:
            self.serialize()

    def next_func(self):
        if not self.decoded_params:
            return 0
        self.decoded_params.remove(self.decoded_params[0])
        if self.decoded_params:
            self.serialize()
            return 1
        else:
            self.delete()
            return 0

    def serialize(self):
        self.params = dumps(self.decoded_params)
        self.save()
        self.dirty = False

    def failed(self):
        self.state = 'failed'
        self.dirty = 1

