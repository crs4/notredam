#from repository.models import Component
from uuid import uuid4
from twisted.internet import defer

def new_id():
    return uuid4().hex

class BaseAction(object):    
   
    def __init__(self, input, **params):   
        self.resource = input         
        self.params = params
        self._output = None
        
    def get_output(self):
        return self._output
   
    def _execute(self):
        pass
        
    def execute(self): 
        self.resource.do_action(self._execute)
        
    
    @staticmethod
    def get_parameters():
       return {}

class Resource(object):
    def __init__(self,component):
        self.deferred = defer.Deferred()
        self.component = component                
        self.action = None
        
    def get(self, param, default = None):
        if not self.params.has_key(param):
            return self.component.__dict__.get(param, default)
        
        return self.params[param] 
    
    
    def do_action(self, action, *args):
        self.action = action
        self.deferred.addCallback(action._execute, *args)
        
        
    
    def save(self, variant, **params):
       pass
   
        
    