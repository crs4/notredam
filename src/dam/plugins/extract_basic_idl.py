#
# Interface definition for extract_basic: used by the GUI
#

from dam.plugins.common.utils import get_variants

def inspect(workspace):
    #variants = get_variants(workspace)
    return {
        'name': __name__,
        'params':[
            {   
                'name': 'source_variant_name',
                'fieldLabel': 'Input Rendition',
                'xtype': 'multiselect',
                'value': ['edited', 'original'],                
                'description': 'input-variant',
               
                'help': ''
            }]
         
        } 

