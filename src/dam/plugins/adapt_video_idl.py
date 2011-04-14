from dam.plugins.common.utils import get_variants

def inspect(workspace):
    variants = get_variants(workspace, 'video', exclude=['thumbnail'])
    image_variants = get_variants(workspace, 'image') 
    output_variants = get_variants(workspace, 'video', auto_generated = True)
     
    audio_rate = {
                  'xtype': 'numberfield',
                  'fieldLabel': 'Sample Rate (Hz)',
                  'name': 'audio_rate',                  
#                  'width': 200,
#                  'value':44100
    }
    
    resize = {
                 'xtype': 'cbfieldset',
                 'title': 'Resize',
                 'items':[{
                     'xtype': 'numberfield',
                    'name': 'video_height',    
                    'fieldLabel': 'Height',
                    'width': 150,
                    
                    },                            
                    
                    {
                     'xtype': 'numberfield',
                    'name': 'video_width',    
                    'fieldLabel': 'Width',
                    'width': 150,
                    
                     
                    }
                ]
                     
             }
    
    wm = {'xtype': 'watermarkfieldset',
              'title': 'Watermark',
              'name': 'watermark',                            
              'movable': False,
              'renditions': variants,
              'wm_x_name': 'watermark_top_percent',
              'wm_y_name':'watermark_left_percent',
              'wm_id_name': 'watermark_filename',
              'wm_id_width': 120
          }
    
    frame_rate = {
        'xtype': 'select',
        'name': 'video_framerate',
        'fieldLabel': 'Frame Rate',
#        'value': '30/1',
        'values':[['24/1'], ['25/1'],['30/1'],['25/2'],['57000/1001'],['57/1']],
        'width': 150,
     }
    
    
    bit_rate_b = {
                  'xtype': 'select',
                  'fieldLabel': 'Audio Bit Rate (kbps)',
                  'name': 'audio_bitrate_b',
                  'width': 200,
                  'values': [[64, 64000], [80, 80000], [96, 96000], [112, 112000],[128, 128000], [160, 16000], [192, 192000], [224, 224000], [256, 256000], [590, 59000]],
                  'value': 128000,
                  'fields': ['kbps', 'bps'],                  
                  'valueField': 'bps',
                  'displayField': 'kbps',
                  'hiddenName': 'audio_bitrate_b',
                  
    }
    
    bit_rate_kb = {
                  'xtype': 'select',
                  'fieldLabel': 'Audio Bit Rate (kbps)',
                  'name': 'audio_bitrate_kb',
                  'width': 200,
                  'values': [[64], [80], [96], [112],[128], [160], [192], [224], [256], [590]],
                  'value': 128
    }
    
    
    video_bit_rate_b = {
                  'xtype': 'select',
                  'fieldLabel': 'Video Bit Rate (kbps)',
                  'name': 'video_bitrate_b',
                  'width': 200,
                  'values': [[64, 64000], [128, 128000], [192, 192000], [256, 256000], [590, 59000], [640, 640000], [1024, 1024000], [1536, 1536000], [2048, 2048000], [4096, 4096000], [8192, 8192000], [12288, 12288000], [20040, 20040000]],
                  'value': 640000,
                  'fields': ['kbps', 'bps'],                  
                  'valueField': 'bps',
                  'displayField': 'kbps',
                  'hiddenName': 'video_bitrate_b',
                  
    }
    
    video_bit_rate_kb = {
          'xtype': 'select',
          'fieldLabel': 'Video Bit Rate (kbps)',
          'name': 'video_bitrate_kb',
          'width': 200,
          'values': [[64], [128], [192], [256], [590], [640], [1024], [1536], [2048], [4096], [8192], [12288], [20040]],
          'value': 640
    }

                         
    
    return {
        'name': __name__,
       
        
        'params':[
            {   
                'name': 'source_variant_name',
                'fieldLabel': 'Input Rendition',
                'xtype': 'select',
                'values': variants,
                'value': variants[0],
                'description': 'input-variant',
                
                'help': ''
            },
            
            {   
                'name': 'output_variant_name',
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
                 'select_value': 'FLV',
                 'values':{
                    'FLV':[       
                        video_bit_rate_b,                         
                        bit_rate_kb,
                       {
                        'xtype': 'cbfieldset',
                        'title': 'Sampling',
                        'items': [
                          frame_rate,
                          audio_rate
                        ]
                        
                        }, 
                       
                        
                        resize,
                        wm
                    
                    ],
                    'FLV_H264_AAC':[                            
                       
                        video_bit_rate_b,
                        bit_rate_b,
                        
                        {
                        'xtype': 'cbfieldset',
                        'title': 'Sampling',
                        'items': [
                          frame_rate,
                          audio_rate
                        ]
                        
                        },
                        resize,
                        wm
                    
                    ],
                    'MPGETS':[
                       
                        video_bit_rate_b,
                        bit_rate_kb,
                        {
                        'xtype': 'cbfieldset',
                        'title': 'Sampling',
                        'items': [
                          frame_rate,
                          audio_rate
                        ]
                        
                        },
                        resize,
                        wm
                    
                    ],
                    'MATROSKA_MPEG4_AAC':[
                        video_bit_rate_b,
                        bit_rate_b,
                        {
                        'xtype': 'cbfieldset',
                        'title': 'Sampling',
                        'items': [
                          frame_rate,
                          audio_rate
                        ]
                        
                        },
                        resize,
                        wm
                    
                    ],
                    'MP4_H264_AACLOW':[
                       video_bit_rate_kb,
                       bit_rate_b,
                        {
                        'xtype': 'cbfieldset',
                        'title': 'Sampling',
                        'items': [
                          frame_rate,
                          audio_rate
                        ]
                        
                        },
                        
                        resize,
                        wm
                    
                    ],
                    'AVI':[                      
                        video_bit_rate_b,                      
                        bit_rate_kb,
                        {
                        'xtype': 'cbfieldset',
                        'title': 'Sampling',
                        'items': [
                          frame_rate,
                          audio_rate
                        ]
                        
                        },
                        resize,
                        wm
                    
                    ],
                     
                    
                    'THEORA':[
                        video_bit_rate_kb,
                        
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_quality',    
                            'fieldLabel': 'Audio Quality',
                            'width': 150,
                            'value': 0.9,
                            'minValue': 0,
                            'maxValue':1,
                            'allowDecimals':True
                        },
                        {
                        'xtype': 'cbfieldset',
                        'title': 'Sampling',
                        'items': [
                          frame_rate,
                          audio_rate
                        ]
                        
                        },
                        resize,
                        wm
                               
                    
                    ]
                    
                      
                }
                 
             }
                      
            
        ]
                    
    } 
