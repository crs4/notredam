import time
from dam.plugins.common.utils import splitstring

commands = {
'MATROSKA_MPEG4_AAC' : {
'cmdline': """
  filesrc location="file://%(in_filename)s" 
! decodebin name=decode 
! queue 
! ffmpegcolorspace 
! video/x-raw-rgb, bpp=24 
! watermark filename="file://%(watermark_filename)s" top="%(watermark_top)s" left="%(watermark_left)s" 
! ffmpegcolorspace 
! videoscale 
! video/x-raw-rgb, width="%(video_width)s", height="%(video_height)s" 
! videorate 
! video/x-raw-rgb, bpp=24, framerate="%(video_framerate)s" 
! ffmpegcolorspace 
! queue 
! ffenc_mpeg4 bitrate="%(video_bitrate_b)s" 
! matroskamux name=mux 
! progressreport name=report 
! filesink location="outfile://%(out_filename)s" 
  decode. 
! queue 
! audioconvert 
! audioresample 
! audio/x-raw-int, rate="%(audio_rate)s"
! queue 
! faac bitrate="%(audio_bitrate_b)s" 
! mux.
""",

'defaults': {
'watermark_filename':'' ,
'watermark_top':'' ,
'watermark_left':'' ,
'video_width':'320' ,
'video_height':'240' ,
'video_framerate':'30/1' ,
'video_bitrate_b':'264000' ,
'audio_bitrate_b':'128000' ,
'audio_rate':'44100',
},},

'MP4_H264_AACLOW' : {
'cmdline': """
  filesrc location="file://%(in_filename)s" 
! decodebin name=decode 
! queue 
! ffmpegcolorspace 
! video/x-raw-rgb, bpp=24 
! watermark filename="file://%(watermark_filename)s" top="%(watermark_top)s" left="%(watermark_left)s" 
! ffmpegcolorspace 
! videoscale 
! video/x-raw-rgb, width="%(video_width)s", height="%(video_height)s" 
! videorate 
! video/x-raw-rgb, bpp=24, framerate="%(video_framerate)s" 
! ffmpegcolorspace


! x264enc bitrate=%(video_bitrate_kb)s 
! mp4mux name=mux 
! progressreport name=report ! filesink location="outfile://%(out_filename)s"

decode. ! queue ! audioconvert ! audioresample ! audio/x-raw-int, rate="%(audio_rate)s"

! faac bitrate=%(audio_bitrate_b)s profile=2 
! mux.
""",
},

}



#encoder
progressreport name=report ! filesink location="outfile://%(out_filename)s"

#video_decoder
  filesrc location="file://%(in_filename)s" 
! decodebin name=decode 
! queue 
! ffmpegcolorspace 
! video/x-raw-rgb, bpp=24 
! watermark filename="file://%(watermark_filename)s" top="%(watermark_top)s" left="%(watermark_left)s" 
! ffmpegcolorspace 
! videoscale 
! video/x-raw-rgb, width="%(video_width)s", height="%(video_height)s" 
! videorate 
! video/x-raw-rgb, bpp=24, framerate="%(video_framerate)s" 
! ffmpegcolorspace

#audio_decoder audio_pipe
decode. ! queue ! audioconvert ! audioresample ! audio/x-raw-int, rate="%(audio_rate)s"

#audio_decoder no_audio_pipe
audiotestsrc num-buffers="%(num_buffers)s" samplesperbuffer=1000 wave=4 
! audio/x-raw-int, rate=48000 ! audioresample ! audioconvert 
! audio/x-raw-int, rate="%(audio_rate)s"





t0 = time.time()
s = splitstring(pipe % defaults)
#s = pipe % defaults
t1 = time.time()
print s
print 'time: %f' % (t1-t0)

#
#def adapt_video(in_filename, out_filename, progress_url, preset, preset_params):
#    c = Configurator()
#    max_attempts = c.getint('ADAPTER', 'max_discover_errors')
#
#    def __retry(error, attempt):
#        log.error("discover error: %s" % str(error))
#        if attempt < max_attempts:
#            log.debug('discovering %s'  % in_filename)
#            d = discover(in_filename)
#            d.addCallbacks(__adapt, __retry, callbackArgs=[preset], errbackArgs=[attempt+1])
#            return d
#        else:
#            return error
#
#    def __adapt(features, preset):
#        global encoder, decoder, transcoder
#        log.debug('starting video_adapt: %s' % str(features))
#        userargs = {'in_filename':in_filename, 
#                    'out_filename':out_filename, 
#                    'num_buffers':int(features['video_length']/1000*48),}
#        userargs.update(preset_params)
#
#        max_width = int(userargs.get('max_width', 0))
#        max_height = int(userargs.get('max_height', 0))
#        w_orig, h_orig = int(features['video_width']), int(features['video_height'])
#        log.debug('dim before %sx%s %sx%s' % (w_orig, h_orig, max_width, max_height))
#        w, h = resize_image(w_orig, h_orig, max_width, max_height)
#        log.debug('dim after %sx%s' % (w, h))
#
#        userargs['video_width'] = w
#        userargs['video_height'] = h
#        if 'watermark_top_percent' in userargs and 'watermark_left_percent' in userargs:
#            userargs['watermark_top'] = int(w_orig * (userargs['watermark_top_percent']/100.0))
#            userargs['watermark_left'] = int(h_orig * (userargs['watermark_left_percent']/100.0))
#
#        decoder_args = {}
#        decoder_args.update(decoder['defaults'])
#        decoder_args.update(userargs)
#        video_pipe = decoder['video_pipe'] % decoder_args
#
#        if features['has_audio']:
#            audio_pipe = decoder['audio_pipe'] % decoder_args
#        else:
#            audio_pipe = decoder['no_audio_pipe'] % decoder_args
#
#        encoder_args = {}
#        encoder_args.update(encoder['defaults'])
#        encoder_args.update(userargs)
#        encoder_pipe = encoder['pipe'] % encoder_args
#
#        transcoder_args = {'video_decoder': video_pipe, 'audio_decoder': audio_pipe, 
#                           'encoder': encoder_pipe }
#        transcoder_args.update(transcoder[preset]['defaults'])
#        transcoder_args.update(userargs)
#        transcoder_pipe = transcoder[preset]['pipe'] % transcoder_args
#
#        exe = c.get('ADAPTER', 'gstreamer_exe')
#        argv = transcoder_pipe.split('\x00')
#        env = {'SDL_VIDEODRIVER': 'dummy',
#                    'GST_PLUGIN_PATH': c.get('ADAPTER', 'gst_plugin_path')}
#        log.debug('\n\n######VIDEO PIPELINE:\ngst-launch %s\n' % ' '.join(argv))
#        cb_func = get_progress_cb(progress_url, 'gstreamer-progressreport')
#        r = RunProc.run(exe, argv, env, cb=cb_func, do_log=False)
#        return r.getResult()
#    
#    preset = preset.upper()
#    if preset not in transcoder.keys():
#        raise AdapterError('Error adapting video: unknown preset %s' % preset)
#    # checks for obsolete key
#    assert('watermark_id' not in preset_params)
#    if 'watermark_filename' in preset_params:
#        storage = Storage()
#        preset_params['watermark_filename'] = storage.abspath(preset_params['watermark_filename'])
#    log.debug('discovering %s'  % in_filename)
#    d = discover(in_filename)
#    d.addCallbacks(__adapt, __retry, callbackArgs=[preset], errbackArgs=[1])
#    return d
