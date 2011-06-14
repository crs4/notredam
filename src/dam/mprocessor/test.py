from twisted.internet import reactor

from json import dumps
from dam.workspace.models import DAMWorkspace as Workspace
from mediadart.config import Configurator
from dam.mprocessor.models import Process, ProcessTarget,Pipeline, TriggerEvent
from dam.mprocessor.pipeline import DAG
from dam.mprocessor.processor import Batch


c=Configurator()
c.set('MPROCESSOR', 'plugins', 'dam.mprocessor.plogins')

pipeline = {
    'script1':{
        'script_name': 'a1', 
        'params':{
            'source_variant_name': 'original',
            'output_variant_name': 'output',
            'output_preset': 'script1',
            'uno': 'uno',
            'due': 'due',
            },
         'in': [],
         'out':['1']    
    },
    'script2':{
        'script_name': 'a1', 
        'params':{
            'source_variant_name': 'original',
            'output_variant_name': 'output',
            'output_preset': 'script2',
            'uno': 'uno',
            'due': 'due',
            },
         'in': [],
         'out':['2']    
    },
    'script3':{
        'script_name': 'a1', 
        'params':{
            'source_variant_name': 'original',
            'output_variant_name': 'output',
            'output_preset': 'script3',
            'uno': 'uno',
            'due': 'due',
            },
         'in': ['1', '2'],
         'out':[],
    },
}


def stop(result):
    reactor.stop()

def main():
    ws = Workspace.objects.get(id=1)  
    pipe = Pipeline.objects.filter(name='for-p-1')
    if pipe:
        pipe.delete()
    p = Process.objects.filter(id=-1)
    if p:
        p.delete()
    pipe = Pipeline.objects.create(name='for-p-1', description='', params=dumps(pipeline), workspace=ws)
    p = Process.objects.create(id=-1, pipeline=pipe, launched_by_id=1, workspace=ws)

# delete previous records 
    for pt in ProcessTarget.objects.filter(process=p):
        pt.delete()
    p.add_params(15, {'*':{'source_variant_name':'prima_istanza'}, 
                     'script1':{'source_variant_name':'valore_corretto'},
                    })
    p.add_params(16, {'*':{'source_variant_name':'prima_istanza'}, 
                     'script2':{'source_variant_name':'valore_corretto'},
                    })
    p.add_params(17, {'*':{'source_variant_name':'prima_istanza'}, 
                     'script1':{'source_variant_name':'valore_corretto'},
                    })
    b = Batch(p)
    b.run().addBoth(stop)

if __name__=='__main__':
    reactor.callWhenRunning(main)
    reactor.run()



