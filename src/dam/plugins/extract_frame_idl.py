
#
# Interface definition: used by the GUI
#

from dam.variants.models import Variant    

def inspect(workspace):
    from django.db.models import Q
    source_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = False)]
    output_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = True, hidden = False)]
    return {
        'name': __name__,
        'params':[
            {   
                'name': 'source_variant',
                'fieldLabel': 'Source Variant',
                'xtype': 'select',
                'values': source_variants,
                'description': 'input-variant',
                'help': ''
            },
            
            {   
                'name': 'output_variant',
                'fieldLabel': 'Output Variant',
                'xtype': 'select',
                'values': output_variants,
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
                'xtype':'????????',
                'name': 'output_format',
                'fieldLabel': 'format',                    
                'description': 'format of output variant',
                'minValue':10,
#                    'value': 100,
                'help': 'mime type of the format of the output_variant'
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
        ],
    } 



