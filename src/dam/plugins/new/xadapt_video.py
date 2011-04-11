TBD='___undefined___'   # this is the value of parameters for which there is no default

encoder = ' ! progressreport name=report ! filesink location="outfile://%(out_filename)s"'
encoder_defaults = { 'out_filename': TBD, }

video_decoder = """
  filesrc location="file://%(in_filename)s" ! decodebin name=decode ! queue 
  ! ffmpegcolorspace ! video/x-raw-rgb, bpp=24 
  ! watermark filename="file://%(watermark_filename)s" top=%(watermark_top)s left=%(watermark_left)s 
  ! ffmpegcolorspace ! videoscale 
  ! video/x-raw-rgb, width=%(video_width)s, height=%(video_height)s 
  ! videorate ! video/x-raw-rgb, bpp=24, framerate=%(video_framerate)s ! ffmpegcolorspace 
"""
video_decoder_defaults = {
    'in_filename': TBD,
    'watermark_filename':'' ,
    'watermark_top':'0' ,
    'watermark_left':'0' ,
    'video_width':'320' ,
    'video_height':'240' ,
    'video_framerate':'30/1' ,
}

audio_decoder = ' decode. ! queue ! audioconvert ! audioresample ! audio/x-raw-int, rate=%(audio_rate)s '
audio_decoder_defaults = { 'audio_rate':'44100', }

silent_audio = """
  audiotestsrc num-buffers=%(video_duration)s samplesperbuffer=200 wave=4 
  ! audio/x-raw-int, rate=200 ! audioresample ! audioconvert 
  ! audio/x-raw-int, rate=%(audio_rate)s
"""
# num_buffers is 
silent_audio_defaults = { 'video_duration': TBD, 'audio_rate': '44100', }


pipelines = {
'MATROSKA_MPEG4_AAC' : {
    'cmdline': 
        video_decoder + 
        ' ! queue ! ffenc_mpeg4 bitrate=%(video_bitrate_b)s ! matroskamux name=mux ' + 
        encoder + audio_decoder +
        ' ! queue ! faac bitrate=%(audio_bitrate_b)s ! mux.',

    'defaults': {
        'video_bitrate_b':'264000' ,
        'audio_bitrate_b':'128000' ,
    },
    'mime': 'video/x-m4v',
    'server': 'GenericCmdline',
},

'MP4_H264_AACLOW' : {
    'cmdline':
        video_decoder + 
        ' ! x264enc bitrate=%(video_bitrate_kb)s ! mp4mux name=mux ' +
        encoder + audio_decoder +
        ' ! faac bitrate=%(audio_bitrate_b)s profile=2 ! mux.',

    'defaults': {
        'video_bitrate_kb':'192' ,
        'audio_bitrate_b':'128000' ,
    },
    'mime': 'video/mp4',
    'server': 'GenericCmdline',
},

'FLV' : {
    'cmdline':
        video_decoder + 
        ' ! ffenc_flv bitrate=%(video_bitrate_b)s ! queue ! flvmux name=mux ' +
        encoder + audio_decoder +
        ' ! lame bitrate=%(audio_bitrate_kb)s ! mp3parse ! mux.',

    'defaults': {
      'audio_bitrate_kb': '128',
      'video_bitrate_b': '640000',
    },
    'mime': 'video/flv',
    'server': 'GenericCmdline',
},

'AVI' : {
    'cmdline':
        video_decoder + 
        ' ! xvidenc bitrate=%(video_bitrate_b)s ! queue ! avimux name=mux ' +
        encoder + audio_decoder +
        ' ! lame bitrate=%(audio_bitrate_kb)s ! mp3parse ! mux. ',

    'defaults' : {
      'audio_bitrate_kb': '128',
      'video_bitrate_b': '180000',
    },
    'mime': 'video/x-msvideo',
    'server': 'GenericCmdline',
},

'MPEGTS' : {
    'cmdline':
        video_decoder + 
       ' ! ffenc_mpeg2video bitrate=%(video_bitrate_b)s ! mpegvideoparse ! flutsmux name=mux ' +
        encoder + audio_decoder +
       ' ! lame bitrate=%(audio_bitrate_kb)s ! mp3parse ! mux.' ,

    'defaults' : {
      'audio_bitrate_kb': '256',
      'video_bitrate_b': '12000000',
    },
    'mime': 'video/ts',
    'server': 'GenericCmdline',
},

'FLV_H264_AAC' : {
    'cmdline':
        video_decoder + 
       ' ! x264enc bitrate=%(video_bitrate_kb)s ! queue ! flvmux name=mux ' +
        encoder + audio_decoder +
       ' ! faac bitrate=%(audio_bitrate_b)s ! mux.',  

    'defaults' : {
      'audio_bitrate_b': '128000',
      'video_bitrate_kb': '2048',
    },
    'mime': 'video/flv',
    'server': 'GenericCmdline',
},


'THEORA' : {
    'cmdline':
        video_decoder + 
       ' ! theoraenc bitrate=%(video_bitrate_kb)s ! queue ! oggmux name=mux  ' +
        encoder + audio_decoder +
       ' ! audioconvert ! audio/x-raw-float ! vorbisenc quality=%(audio_quality)s ! mux. ',

    'defaults' : {
      'audio_quality': '0.9',
      'video_bitrate_kb': '192',
    },
    'mime': 'video/ogg',
    'server': 'GenericCmdline',
},}



def __get_standard_params():
    "returns all defaults that do not depend on the preset"
    params = {}
    params.update(video_decoder_defaults)
    params.update(encoder_defaults)
    params.update(silent_audio_defaults)
    params.update(silent_audio_defaults)
    return params

def get_preset_params(preset, defaults=__get_standard_params()):
    "return the default values for the preset"
    ret = {}
    ret.update(defaults)
    ret.update(pipelines[preset]['defaults'])
    return ret

#
#
# TEST STUFF
#
#
import sys
import time
from dam.plugins.common.utils import splitstring
def show(key, has_audio, list_output):
    params = {}
    params.update(video_decoder_defaults)
    params.update(encoder_defaults)
    if not has_audio:
        params.update(silent_audio_defaults)
    else:
        params.update(audio_decoder_defaults)
    params.update(pipelines[key]['defaults'])

    t = pipelines[key]['cmdline']
    if not has_audio:
        t = t.replace(audio_decoder, silent_audio)
    ret = t % params
    if list_output:
        ret = splitstring(ret)
    print ret

if __name__=='__main__':
    if sys.argv[1] == '-l':
        list_output = True
        sys.argv.pop(1)
    else:
        list_output = False
    has_audio = True
    key = sys.argv[1].upper()
    if len(sys.argv) > 2:
        has_audio = False
    show(key, has_audio, list_output)
