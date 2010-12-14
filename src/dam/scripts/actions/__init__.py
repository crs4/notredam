from repository.models import Component
from uuid import uuid4

def new_id():
    return uuid4().hex

class BaseAction(object):
    
    media_type_supported = ['image', 'video', 'audio', 'doc']
    verbose_name = ''
    def __init__(self, input, **params):   
        self.input = input #could be a variant or an Action
        self.params = params
        self._output = None
        
        
    def get_output(self):
        return self._output
   
    def execute(self, save_as = None, format = None):
        pass
    
    @staticmethod
    def get_parameters():
       return {}
