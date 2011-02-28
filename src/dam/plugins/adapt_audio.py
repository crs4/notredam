from dam.plugins.common.utils import get_variants
def inspect(workspace):
    variants = get_variants(workspace, 'audio')
#    source_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = False)]
#    output_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = True, hidden = False)]
     
    width = 200
    audio_rate = {
                  'xtype': 'numberfield',
                  'fieldLabel': 'Sample Rate (Hz)',
                  'name': 'audio_rate',                  
                  'width': 200,
                  'value':44100
    }
    
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
                 'xtype':'selectfieldset',
                 'fieldLabel': 'Name',
                 'title': 'Preset',
                 'select_name': 'preset',
                 'values':{
                    'MP3':[
                           audio_rate,
                           {
                        'xtype': 'numberfield',
                        'name': 'audio_bitrate_kb',    
                        'fieldLabel': 'Bit Rate  (Kbps)',
                        'width': width,
                        'value': 128
                    }],
                    
                    'AAC':[
                           audio_rate,
                           {
                        'xtype': 'numberfield',
                        'name': 'audio_bitrate_b',    
                        'fieldLabel': 'Bit Rate (bps)',
                        'width': width,
                        'value': 320000
                    }],
                    
                    'OGG':[
                           audio_rate,
                           {
                        'xtype': 'numberfield',
                        'name': 'audio_quality',    
                        'fieldLabel': 'Audio Quality',
                        'minValue': 0,
                        'maxValue': 1,
                        'allowDecimals': True,                    
                        'width': width,
                        'value': 0.9
                    }],
                    'WAV': [audio_rate]
                    
                      
                }
                 
             }
                      
            
        ]
                    
    } 
