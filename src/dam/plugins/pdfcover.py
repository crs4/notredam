from dam.plugins.common.utils import save_type, get_variants
def inspect(workspace):    
    variants = get_variants(workspace, 'doc')
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
