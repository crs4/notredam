
#
# Interface definition: used by the GUI
#

from dam.variants.models import Variant    
from dam.plugins.common.utils import get_ext_by_type, get_variants

def inspect(workspace):
    from django.db.models import Q
    media_types = get_ext_by_type('image')
    #source_variants = get_variants(workspace, 'video', exclude= ['thumbnail'])
    #output_variants = get_variants(workspace, 'image', auto_generated=True)
    return {
        'name': __name__,
        'params':[
            {   
                'name': 'source_variant_name',
                'fieldLabel': 'Input Rendition',
                'xtype': 'multiselect',
                'value': ['edited', 'original'],
                #'values': source_variants,
                #'value': [source_variants[1], source_variants[0]],
                'description': 'input-variant',
                'help': ''
            },
            
            {   
                'name': 'output_variant_name',
                'fieldLabel': 'Output Rendition',
                'xtype': 'select',
                #'values': output_variants,
                
                'description': 'output-variant',
                'default': 0,
                'help': ''
            },             
            {
                'xtype':'numberfield',
                'name': 'frame_w',
                'fieldLabel': 'frame width',                    
                'description': 'width of the extracted frame',
                'minValue':10,
#                    'value': 100,
                'help': 'width of the extracted image in pixels (aspect ratio is preserved)'
            },
            {
                'xtype':'numberfield',
                'name': 'frame_h',
                'fieldLabel': 'frame height',                    
                'description': 'height of the extracted frame',
                'minValue':10,
#                    'value': 100,
                'help': 'height of the extracted image in pixels (aspect ratio is preserved)'
            },
            {
                'xtype':'numberfield',
                'name': 'position',
                'fieldLabel': 'position',                    
                'description': 'position of frame',
                'minValue':10,
#                    'value': 100,
                'help': 'position of frame to extract as percentage of total time'
            },
            {   
                'name': 'output_extension',
                'fieldLabel': 'Output format',
                'xtype': 'select',
                'values': media_types,
                'description': 'output_extension',
                'value': '.jpg',
                'help': ''
            },
        ],
    } 



