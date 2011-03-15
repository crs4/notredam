import os
import time
from json import dumps, loads
from django.db import models
from mediadart.storage import new_id
from mediadart.mqueue.mqclient_async import Proxy
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

class MAction:
    """
    This class can be initialized in three wasy:
    1. with no data for initialization
    2. with json data and a query_func

    In case (1) the class is used to build a list of actions for the mprocessor.
    In case (2) the json_data contains the list of actions and the parameter get_component.
    is a function used to retreive a Component object from the db
    """
    def __init__(self, component=None, action_id=None, params=None, state='pending', last_active=0):
        self.task = None
        self.component = component
        self.action_id = action_id or new_id()
        self.params = params or [['__dummy__', []]]
        self.state = state
        self.last_active = last_active

    def append_func(self, function_name, *function_params):
        self.params.append([function_name, function_params])
        return self

    def add_component(self, component):
        self.component = component
        return self
    
    def to_json(self):
        return dumps({'action_id':self.action_id, 'component_id':self.component.pk, 'params':self.params})

    def activate(self, callback):
        data = self.to_json()
        logger.debug('MProcessor.activate %s' % data)
        Proxy('MProcessor', callback=callback).activate(data)

    def pop(self):
        "This changes the state of the task and it is not undoable"
        if not self.component:
            raise('Error: executing action with no component')
        if not self.params:
            raise('Error: executing empty action')
        self.last_active = int(time.time())
        fname, fparams = self._next_func()
        return fname, fparams

    def _next_func(self):
        if not self.params:
            return None, None
        self.params.remove(self.params[0])
        if not self.params:
            logger.debug('###################### CLOSING TASK')
            if self.state == 'pending':
                logger.debug('###################### SETTING TASK TO DONE')
                #self.state = 'done'
                #self.serialize()
                self.task.delete()
            return None, None
        else:
            self.serialize()
            return self.params[0]

    def serialize(self):
        if not self.task:
            logger.debug('############# CREATING TASK(%s)' % self.state)
            self.task = Task.objects.create(component=self.component, 
                                            params=dumps(self.params), 
                                            last_active=int(time.time()),
                                            state=self.state)
        else:
            logger.debug('############ SAVING TASK(%s)' % self.state)
            self.task.state = self.state
            self.task.save()

    def failed(self):
        logger.debug('################ ACTION FAILURE')
        self.state = 'failed'

class Task(models.Model):
    task_id = models.CharField(max_length=32, primary_key=True, default=new_id)
    component = models.ForeignKey(Component)
    params = models.TextField(default='[["__dummy__", []]]')
    last_active = models.IntegerField(default=0)     # holds int(time.time())
    state = models.CharField(max_length=7, default='pending')
