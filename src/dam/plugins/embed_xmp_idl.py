# All parameters to this action are provided dynacally
# There is no default.

from dam.plugins.common.utils import get_variants

def inspect(workspace):
    variants = get_variants(workspace, 'image')
    return {
        'name': __name__,
        'params':[
            {   
                'name': 'variant',
                'fieldLabel': 'Source Rendition',
                'xtype': 'select',
                'values': variants,
                'value': variants[0],          # The pipeline accepts a single variant
                'description': 'input-variant',
                'help': ''
            },
         ],
    } 

