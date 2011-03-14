from django.db import models
from mediadart.storage import new_id
from django.contrib.auth.models import User
from mediadart.mqueue.mqclient_async import Proxy
from django.utils import simplejson
from dam.core.dam_repository.models import Type
import logger
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
    start_date = models.DateTimeField(null = True, blank = True)
    end_date = models.DateTimeField(null = True, blank = True)
    launched_by = models.ForeignKey(User)
    last_show_date = models.DateTimeField(null = True, blank = True)

    def add_params(self, target_id):
        ProcessTarget.objects.create(process = self, target_id = target_id, actions_todo=self.pipeline.num_actions())

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
    target_id = models.CharField(max_length=512, null=False)           # foreign key to Item
    actions_passed = models.IntegerField(default=0)
    actions_cancelled = models.IntegerField(default=0)
    actions_failed = models.IntegerField(default=0)
    actions_todo = models.IntegerField(default=0)   # passed+cancelled+failed+todo = pipeline.num_actions()
    result = models.TextField()                     # anything sensible
    

