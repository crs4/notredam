import time
from json import dumps, loads
from django.db import models
from dam.mprocessor import processors  # to be changed
from dam.repository.models import Component


#
# example of use
# job = Job().add_component(component)\
#                .add_func('xmp_embed')\
#                .add_func('altro')\
#                .execute()
#
# or
# job = Job.object.get(id=job_id)
#
class Job(models.Model):
    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.decoded_params = loads(self.params)
            
    job_id = models.CharField(max_length=32, primary_key=True, default=processors.new_id)
    #workspace = models.ForeignKey('workspace.DAMWorkspace')   
    component = models.ForeignKey(Component)
    params = models.TextField(default='["__dummy__"]')
    last_active = models.IntegerField(default=0)     # holds int(time.time())

    def add_func(self, function_name, *function_params):
        self.decoded_params.append([function_name, function_params])
        return self

    def add_component(self, component):
        self.component = component
        return self
    
#    def add_workspace(self, workspace):
#        self.workspace = workspace
#        return self

    def execute(self, data):
        "This changes the state of the job and it is not undoable"
        if not self.component:
            raise('Error: executing action with no component')
        if not self.decoded_params:
            raise('Error: executing empty action')
        if self.decoded_params[0] == '__dummy__':
            self.next()
        self.last_active = int(time.time())
        fname, fparams = self.decoded_params[0]
        func = getattr(processors, fname)
        print('------------------------------------------------------------Action.executing: %s' % fname)
        return func(self, data, *fparams)

    def next(self):
        if not self.decoded_params:
            raise('Error: next on empty action')
        self.decoded_params.remove(self.decoded_params[0])
        if self.decoded_params:
            self.params = dumps(self.decoded_params)
            self.save()
            return 1
        else:
            self.delete()
            return 0
