
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
             'xtype':'fieldsetcontainer',
             'order_field_name': 'actions',
             'items':[{
              'xtype': 'movablecbfieldset',
              'title': 'Resize',
              'name': 'resize',
              'order_field_name': 'actions',
              'order_field_value': 'resize',
            
             
              'items':[{
                    'xtype':'numberfield',
                    'name': 'resize_h',
                    'fieldLabel': 'height',                    
                    'description': 'height',
                    'minValue':0,
#                    'value': 100,
                    'help': 'height of resized image in pixels'
                },
                {
                    'xtype':'numberfield',
                    'name': 'resize_w',
                    'fieldLabel': 'width',                    
                    'description': 'width',
#                    'value': 100,
                    'minValue':0,
                    'help': 'width of resized image in pixels'
                },
                
              ]
              },
               {
              'xtype': 'movablecbfieldset',
              'title': 'Crop',
              'name': 'crop',
             
              'order_field_name': 'actions',
              'order_field_value': 'crop',
              'items':[{
                    'xtype':'numberfield',
                    'name': 'crop_h',
                    'fieldLabel': 'height',                    
                    'description': 'height',
                    'minValue':0,
#                    'value': 100,
                    'help': 'heigth of crop area, default till bottom edge of image'
                },
                {
                    'xtype':'numberfield',
                    'name': 'crop_w',
                    'fieldLabel': 'width',                    
                    'description': 'width',
#                    'value': 100,
                    'minValue':0,
                    'help': 'width of crop area, default till right edge of image'
                },
                
                
              ]
              },
              {
              'xtype': 'watermarkfieldset',
              'title': 'Watermark',
              'name': 'watermark',
              'order_field_name': 'actions',
              'order_field_value': 'watermark',                            
               'renditions': variants
              },
              ]
             
             },
                         

              
              {   
                'name': 'output_format',
                'fieldLabel': 'format',
                'xtype': 'select',
                'values': media_types,
                'description': 'output_format',
                'value': '.jpg',
                'help': ''
            }
              
        ]
        
    } 


