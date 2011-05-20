from json import dumps
from django.db import models
from mediadart.storage import new_id
from django.contrib.auth.models import User
from mediadart.mqueue.mqclient_async import Proxy
from django.utils import simplejson
from dam.core.dam_repository.models import Type
from dam.logger import logger
import datetime


# this class is used to group together pipelines that must executed at specific
# trigger points, like after an upload, before an export. 
class TriggerEvent(models.Model):
    name = models.CharField(max_length = 40, null = False, blank=False)

    def __str__(self):
        return self.name
    
class Pipeline(models.Model):
    name = models.CharField(max_length= 50)
    description = models.TextField(blank=True)
    triggers = models.ManyToManyField(TriggerEvent)
    media_type  = models.ManyToManyField(Type)  # mime types of objects that can be in params
    params = models.TextField()
    workspace = models.ForeignKey('workspace.DAMWorkspace')
    
    def num_actions(self):
        if not hasattr(self, 'length'):
            self.length = len(simplejson.loads(self.params))
        return self.length

    def is_compatible(self, media_type):
        "return True if no type is registered or if media_type is registered"
        types = self.media_type.all()
        return (not types)  or (media_type in types)

    
class Process(models.Model):    
    pipeline = models.ForeignKey(Pipeline)
#    session = models.CharField(max_length=128,null = True, blank = True, unique = True)
    workspace = models.ForeignKey('workspace.DAMWorkspace')
    targets = models.IntegerField(default=0)    # total number of items in ProcessTarget
    start_date = models.DateTimeField(null = True, blank = True)  # None if waiting. Set on running
    end_date = models.DateTimeField(null = True, blank = True)    # Set on completion
    launched_by = models.ForeignKey(User)
    last_show_date = models.DateTimeField(null = True, blank = True)

    def add_params(self, target_id, params={}):
        """create a record in ProcessTarget for an item

        @param target_id: a string that identifies a target for the actions in the pipeline.
                          usually the id of an item.
        @param params: a dictionary of the form 
                   {'*':{<dictionary of parameters for all actions>},
                    '<action_name>': {dictionary of key:value for the action <action_name>},
                   }
        For example if the pipeline has an action "adapt_preview", then calling
        add_params(34, {'*':{'width':324, 'height':256}, 'adapt_preview':{'width':100}})
        will invoke the pipeline on item 34, passing to all actions the parameters
        width=324 and height=256, and will invoke the action adapt_preview with parameters
        width=100 and height=256.
        """
        for x in params.values():
            if type(x) != type({}):
                raise ValueError('parameters params must be a dictionary of dictionaries')
        s = dumps(params)
        ProcessTarget.objects.create(process = self, target_id = target_id, params=s, actions_todo=self.pipeline.num_actions())

    def get_num_target_completed(self):
        return ProcessTarget.objects.filter(process = self, actions_todo__lte=0).count()
    
    def get_num_target_failed(self):
        return ProcessTarget.objects.filter(process = self, actions_failed__gt = 0).count()
    
    def is_completed(self):
        return self.end_date is not None

    def run(self):
        Proxy('MProcessor').run(self.pk)        

def new_processor(pipeline_name, user, workspace):
    "utility function to create a process associated to a given pipeline"
    pipeline = Pipeline.objects.get(name=pipeline_name, workspace = workspace)
    return Process.objects.create(pipeline = pipeline, workspace = workspace, launched_by = user)
    

class ProcessTarget(models.Model):
    process = models.ForeignKey(Process)
    target_id = models.CharField(max_length=64, null=False)           # foreign key to Item
    params = models.TextField(null=True, blank=True)                  # json encoded dictonary of parameters
    actions_passed = models.IntegerField(default=0)
    actions_cancelled = models.IntegerField(default=0)
    actions_failed = models.IntegerField(default=0)
    actions_todo = models.IntegerField(default=0)   # passed+cancelled+failed+todo = pipeline.num_actions()
    result = models.TextField()                     # anything sensible
    

