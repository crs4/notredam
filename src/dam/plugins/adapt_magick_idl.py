

#
# Interface definition for adapt_image: used by the GUI
#
from dam.plugins.common.utils import get_variants, get_ext_by_type
def inspect(workspace):
   
    media_types = get_ext_by_type('image')
    variants = get_variants(workspace, 'image')
    output_variants = get_variants(workspace, 'image', auto_generated = True)
#    source_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = False)]
#    output_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = True, hidden = False)]
     
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
            },
            
            {   
                'name': 'output_variant',
                'fieldLabel': 'Output Rendition',
                'xtype': 'select',
                'values': output_variants,
                'value': output_variants[0],
                'description': 'output-variant',
                'default': 0,
                'help': ''
            },
              
            {   
                'name': 'output_extension',
                'fieldLabel': 'format',
                'xtype': 'select',
                'values': media_types,
                'description': 'output_extension',
                'value': '.jpg',
                'help': ''
            },
            {   
                'name': 'cmdline',
                'fieldLabel': 'Command line',
                'value': '',                            
                'description': 'command line',
                'help': '''Command line, minus the input file (first arg) and the output file (last arg) that are 
 provided implicitly by the action''',
            }
              
        ]
        
    } 


