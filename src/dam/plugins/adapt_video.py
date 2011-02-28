from variants.models import Variant
def inspect(workspace):
    from django.db.models import Q
    variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True),  hidden = False, media_type__name = 'video')]
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
    wm = {
            'xtype': 'cbfieldset',
            'title': 'Watermark',
            'items':[{
                'xtype': 'numberfield',
                'name': 'watermark_top',    
                'fieldLabel': 'Watermark Top',
                'width': width,
                
            },
            {
                    'xtype': 'numberfield',
                    'name': 'watermark_left',    
                    'fieldLabel': 'Watermark Left',
                    'width': width,
                    
                },
                {
                   'xtype': 'textfield',
                   'name': 'watermark_filename', 
                   'fieldLabel': 'Image'                           
                }]
            
            }
    
    frame_rate = {
        'xtype': 'textfield',
        'name': 'video_framerate',
        'fieldLabel': 'Frame Rate',
        'value': '30/1',
        'width': width,
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
                    'FLV':[
                            
                        frame_rate,
                              
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_b',    
                            'fieldLabel': 'Video Bit Rate  (bps)',
                            'width': width,
                            'value': 640000
                        },
                        
                        
                         audio_rate,
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_kb',    
                            'fieldLabel': 'Audio Bit Rate  (Kbps)',
                            'width': width,
                            'value': 128
                        },
                        
                       
                        
                        resize,
                        wm
                    
                    ],
                    'FLV_H264_AAC':[
                            
                        frame_rate,      
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_b',    
                            'fieldLabel': 'Video Bit Rate  (kbps)',
                            'width': width,
                            'value': 2048
                        },
                        
                        
                         audio_rate,
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_b',    
                            'fieldLabel': 'Audio Bit Rate  (bps)',
                            'width': width,
                            'value': 128000
                        },
                        
                        resize,
                        wm
                    
                    ],
                    'MPGETS':[
                            
                        frame_rate,      
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_b',    
                            'fieldLabel': 'Video Bit Rate  (bps)',
                            'width': width,
                            'value': 12000000
                        },
                        
                        
                         audio_rate,
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_kb',    
                            'fieldLabel': 'Audio Bit Rate  (Kbps)',
                            'width': width,
                            'value': 256
                        },
                        
                        resize,
                        wm
                    
                    ],
                    'MATROSKA_MPEG4_AAC':[
                            
                        frame_rate,      
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_b',    
                            'fieldLabel': 'Video Bit Rate  (bps)',
                            'width': width,
                            'value': 264000
                        },
                        
                        
                         audio_rate,
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_b',    
                            'fieldLabel': 'Audio Bit Rate  (bps)',
                            'width': width,
                            'value': 128000
                        },
                        
                        resize,
                        wm
                    
                    ],
                    'MP4_H264_AACLOW':[
                            
                        frame_rate,      
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_kb',    
                            'fieldLabel': 'Video Bit Rate  (Kbps)',
                            'width': width,
                            'value': 192
                        },
                        
                        
                         audio_rate,
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_b',    
                            'fieldLabel': 'Audio Bit Rate  (bps)',
                            'width': width,
                            'value': 128000
                        },
                        
                        resize,
                        wm
                    
                    ],
                    'AVI':[
                            
                        frame_rate,      
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_b',    
                            'fieldLabel': 'Video Bit Rate  (bps)',
                            'width': width,
                            'value': 180000
                        },
                        
                        
                         audio_rate,
                        {
                            'xtype': 'numberfield',
                            'name': 'audio_bitrate_kb',    
                            'fieldLabel': 'Audio Bit Rate  (Kbps)',
                            'width': width,
                            'value': 128
                        },
                        
                        resize,
                        wm
                    
                    ],
                     
                    
                    'THEORA':[
                        frame_rate,
                        {
                            'xtype': 'numberfield',
                            'name': 'video_bitrate_kb',    
                            'fieldLabel': 'Video Bit Rate  (kbps)',
                            'width': width,
                            'value': 192
                        },
                        
                        
                         audio_rate,
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
                        
                        resize,
                        wm
                               
                    
                    ]
                    
                      
                }
                 
             }
                      
            
        ]
                    
    } 
