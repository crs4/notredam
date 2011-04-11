#
# Interface definition for adapt_audio: used by the GUI
#

from dam.plugins.common.utils import get_variants

def inspect(workspace):
    variants = get_variants(workspace, 'audio')
    output_variants = get_variants(workspace, 'audio', auto_generated = True)
#    source_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = False)]
#    output_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = True, hidden = False)]
    
    
    width = 200
    audio_rate = {
                  'xtype': 'select',
                  'fieldLabel': 'Sample Rate (Hz)',
                  'name': 'audio_rate',                  
                  'width': 200,
                  'value':44100,
                  'values': [[44100],[48000],[59000] ]
    }
    
    
    bit_rate_b = {
                  'xtype': 'select',
                  'fieldLabel': 'Bit Rate (kbps)',
                  'name': 'audio_bitrate_b',
                  'width': 200,
                  'values': [[64, 64000], [80, 80000], [96, 96000], [112, 112000],[128, 128000], [160, 16000], [192, 192000], [224, 224000], [256, 256000], [590, 59000]],
                  'value': 128000,
                  'fields': ['kbps', 'bps'],                  
                  'valueField': 'bps',
                  'displayField': 'kbps',
                  'hiddenName': 'audio_bitrate_b'
    }
    
    bit_rate_kb = {
                  'xtype': 'select',
                  'fieldLabel': 'Bit Rate (kbps)',
                  'name': 'audio_bitrate_kb',
                  'width': 200,
                  'values': [[64], [80], [96], [112],[128], [160], [192], [224], [256], [590]],
                  'value': 128,
    }
    
    
    
    return {
        'name': __name__,
       
        
        'params':[
            {   
                'name': 'source_variant',
                'fieldLabel': 'Input Rendition',
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
                 'xtype':'selectfieldset',
                 'fieldLabel': 'Name',
                 'title': 'Preset',
                 'select_name': 'output_preset',
                 'select_value': 'MP3',
                 'values':{
                    'MP3':[
                       audio_rate,
                       bit_rate_kb
                    ],
                    
                    'AAC':[
                       audio_rate,
                       bit_rate_b
                    ],
                    
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

    
