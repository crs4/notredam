
from dam.plugins.common.utils import get_variants

def inspect(workspace):
    variants = get_variants(workspace, 'image')
    return {
        'name': __name__,
        'params':[
            {   
                'name': 'source_variant',
                'fieldLabel': 'Source Rendition',
                'xtype': 'select',
                'values': variants,
                'value': variants[0],
                'description': 'input-variant',
               
                'help': ''
            }]
         
        } 

