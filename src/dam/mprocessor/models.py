from django.db import models
from mediadart.storage import new_id
from django.contrib.auth.models import User
from mediadart.mqueue.mqclient_async import Proxy
    
class Pipeline(models.Model):
    name = models.CharField(max_length= 50)
    description = models.TextField(blank=True)
    # upload etc, used to group pipelines that must be run in succession at certain points
    type = models.CharField(max_length=32, blank=True, default="") 
    params = models.TextField()
    workspace = models.ForeignKey('workspace.DAMWorkspace')
    
    def num_actions(self):
        if not hasattr(self.length):
            self.length = len(simplejson.loads(self.params))
        return self.length
    
#    def create_process(self, user):
#        return Process.objects.create(pipeline = self, workspace =  self.workspace, launched_by = user)
    
class Process(models.Model):    
    pipeline = models.ForeignKey(Pipeline)
    session = models.CharField(max_length=128,null = True, blank = True, unique = True)
    workspace = models.ForeignKey('workspace.DAMWorkspace')
    passed = models.IntegerField(default=0)     # number of actions passed
    failures = models.IntegerField(default=0)   # number of actions failed
    total = models.IntegerField(default=0)      # total number of actions to be performed
    start_date = models.DateTimeField(auto_now_add = True)
    end_date = models.DateTimeField(null = True, blank = True)
    launched_by = models.ForeignKey(User)

    def create_process(self, user, pipeline):
        pipeline = Pipeline.objects.get(name=pipeline)
        return Process.objects.create(pipeline = pipeline, workspace =  self.workspace, launched_by = user)

    def add_params(self, target_id):
        ProcessTarget.objects.create(process = self, target_id = target_id)
        
    def get_num_target_completed(self):
        return ProcessTarget.objects.filter(process = self, passed = self.pipeline.num_actions()).count()
    
    def get_num_target_failed(self):
        return ProcessTarget.objects.filter(process = self, failed__gt = 0).count()

    def run(self):
        Proxy('MProcessor').run(self.pk)        

def new_processor(pipeline_name, user, workspace):
    "utility function to create a process associated to a given pipeline"
    pipeline = Pipeline.objects.get(name=pipeline)
    return Process.objects.create(pipeline = pipeline_name, workspace =  self.workspace, launched_by = user)
    

class ProcessTarget(models.Model):
    process = models.ForeignKey(Process)
    target_id = models.CharField(max_length=512, null=False)           # foreign key to Item
    passed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)

    def completed(self):
        return self.passed == self.process.pipeline.num_actions()
