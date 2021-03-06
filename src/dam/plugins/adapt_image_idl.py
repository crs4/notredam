
#
# Interface definition for adapt_image: used by the GUI
#
from dam.plugins.common.utils import get_variants, get_ext_by_type
def inspect(workspace):
   
    media_types = get_ext_by_type('image')
    variants = get_variants(workspace, 'image')
    
    #output_variants = get_variants(workspace, 'image', auto_generated = True)
#    source_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = False)]
#    output_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = True, hidden = False)]
     
    return {
        'name': __name__,
        
        'params':[
            {   
                'name': 'source_variant_name',
                'fieldLabel': 'Input Rendition',
                'xtype': 'multiselect',
                'media_type': 'image',
                'value': ['edited', 'original'],
                'description': 'input-variant',
                
                'help': ''
            },
            
            {   
                'name': 'output_variant_name',
                'fieldLabel': 'Output Rendition',
                'xtype': 'rendition_select',
                #'values': output_variants,
                #'value': output_variants[0],
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
              'xtype': 'movablecbfieldset',
              'title': 'Rotate',
              'name': 'rotate',              
              'order_field_name': 'actions',
              'order_field_value': 'rotate', 
              'items':[{
                    'xtype':'combo',
                    'name': 'rotation', # this name must be the same as the name of the parameter passed to run method !
                    'allowBlank': 'false',
                    'autoSelect': 'true',
                    'width': 50,
                    'editable':'false',
                    'triggerAction':'all',
                    'lazyRender':'true',
                    'forceSelection':'true',
                    'fieldLabel': 'rotation',                    
                    'store':['0', '+90','-90'],
                    'mode':'local',
                    'description': '90 degree clockwise/counterclockwise rotation',
                    'help': 'performs a 90 degree clockwise/counterclockwise rotation'
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
                'name': 'output_extension',
                'fieldLabel': 'Output Format',
                'xtype': 'select',
                'values': media_types,
                'description': 'output_extension',
                'value': '.jpg',
                'help': ''
            }
              
        ]
        
    } 


