from variants.models import Variant
def inspect(workspace):
    from django.db.models import Q
    variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True),  hidden = False, media_type__name = 'doc')]
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
                'description': 'input-variant',
                
                'help': ''
            },
            
            {   
                'name': 'output_variant',
                'fieldLabel': 'Output Rendition',
                'xtype': 'select',
                'values': variants,
                'description': 'output-variant',
                'default': 0,
                'help': ''
            },
            {
             'xtype': 'numberfield',
             'name': 'xsize',
             'fieldLabel': 'width',
             'value': 300,
             'width':200
             },
             {
             'xtype': 'numberfield',
             'name': 'ysize',
             'fieldLabel': 'height',
             'value': 300,
             'width':200
             
             }
            
            ]
             
                                    
    } 
