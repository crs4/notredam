from dam.plugins.common.utils import get_variants
def inspect(workspace):
    variants = get_variants(workspace, 'video')
    image_variants = get_variants(workspace, 'image') 
    output_variants = get_variants(workspace, 'video', auto_generated = True)
#    source_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = False)]
#    output_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = True, hidden = False)]
     
    width = 200
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
                 'xtype':'selectfieldset',
                 'fieldLabel': 'Name',
                 'title': 'Preset',
                 'select_name': 'preset',
                 'select_value': 'FLV',
                 'values':{
                    'FLV':[       
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_b',    
                            'fieldLabel': 'Video Bit Rate  (bps)',
                            'width': width,
                            'value': 640000
                        },
                         
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_kb',    
                            'fieldLabel': 'Audio Bit Rate  (Kbps)',
                            'width': width,
                            'value': 128
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
                    
                    ],
                    'FLV_H264_AAC':[                            
                       
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_b',    
                            'fieldLabel': 'Video Bit Rate  (kbps)',
                            'width': width,
                            'value': 2048
                        },
                        
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_b',    
                            'fieldLabel': 'Audio Bit Rate  (bps)',
                            'width': width,
                            'value': 128000
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
                    
                    ],
                    'MPGETS':[
                       
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_b',    
                            'fieldLabel': 'Video Bit Rate  (bps)',
                            'width': width,
                            'value': 12000000
                        },
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_kb',    
                            'fieldLabel': 'Audio Bit Rate  (Kbps)',
                            'width': width,
                            'value': 256
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
                    
                    ],
                    'MATROSKA_MPEG4_AAC':[
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_b',    
                            'fieldLabel': 'Video Bit Rate  (bps)',
                            'width': width,
                            'value': 264000
                        },                        
                       
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_b',    
                            'fieldLabel': 'Audio Bit Rate  (bps)',
                            'width': width,
                            'value': 128000
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
                    
                    ],
                    'MP4_H264_AACLOW':[
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_kb',    
                            'fieldLabel': 'Video Bit Rate  (Kbps)',
                            'width': width,
                            'value': 192
                        },
                        
                        
                        
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_b',    
                            'fieldLabel': 'Audio Bit Rate  (bps)',
                            'width': width,
                            'value': 128000
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
                    
                    ],
                    'AVI':[                      
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_b',    
                            'fieldLabel': 'Video Bit Rate  (bps)',
                            'width': width,
                            'value': 180000
                        },                      
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_kb',    
                            'fieldLabel': 'Audio Bit Rate  (Kbps)',
                            'width': width,
                            'value': 128
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
                    
                    ],
                     
                    
                    'THEORA':[
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_kb',    
                            'fieldLabel': 'Video Bit Rate  (kbps)',
                            'width': width,
                            'value': 192
                        },
                        
                        
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_quality',    
                            'fieldLabel': 'Audio Quality',
                            'width': width,
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
