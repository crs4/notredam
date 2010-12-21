#########################################################################
#
# NotreDAM, Copyright (C) 2009, Sardegna Ricerche.
# Email: labcontdigit@sardegnaricerche.it
# Web: www.notre-dam.org
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#########################################################################

from django.db import models
from django.utils import simplejson
from django.contrib.contenttypes import generic
from dam.upload.views import generate_tasks
from dam.variants.models import Variant
from dam.repository.models import Component
from dam.core.dam_repository.models import Type
from django.db.models import Q
from dam import logger

#PRESETS = {'video':{
#            'flv': {'preset':'flv', 'extension': 'flv'},
#             'mkv aac':{'preset': 'matroska_mpeg4_aac', 'extension':'mkv'},
#             'mp4':{'preset': 'mp4_h264_aaclow', 'extension':'mp4'},
#             'avi':{'preset': 'avi', 'extension':'avi'},
#             'mpegts':{'preset': 'mpegts', 'extension':'mpeg'},
#             'flv h264 aac':{'preset': 'flv_h264_aac', 'extension':'flv'},
#             'theora': {'preset': 'theora', 'extension':'ogv'}
#        },
#        'audio':{
#            'wav': {'preset':'wav', 'extension': 'wav'},
#            'ogg': {'preset':'ogg', 'extension': 'ogg'},
#            'mp3': {'preset':'mp3', 'extension': 'mp3'},
#            'aac': {'preset':'aac', 'extension': 'aac'}                 
#        }
#}
#
#
#class ScriptException(Exception):
#    pass
#  
#class MissingActionParameters(ScriptException):
#    pass
#
#class WrongInput(ScriptException):
#    pass
#
#class ActionError(ScriptException):
#    pass
#
#class MediaTypeNotSupported(ScriptException):
#    pass
#
#class PresetUnknown(ScriptException):
#    pass
#
#class ScriptDefault(models.Model):
#    name = models.CharField(max_length= 50)
#    description = models.CharField(max_length= 200)
#    pipeline = models.TextField()
#
#def get_all_actions():
#    classes = []
#    classes.extend(BaseAction.__subclasses__())
#    classes.extend(SaveAction.__subclasses__())
#    classes.append(SendByMail)
#    
#    return classes
#    
#
#def _get_orig():
#    return Variant.objects.get(name = 'original')
#
#class ActionList(models.Model):
#    actions = models.TextField()
#    script = models.ForeignKey('Script')
#    media_type = models.ForeignKey(Type)
#    source_variant = models.ForeignKey(Variant, default = _get_orig)
#
#class Script(models.Model):
#    name = models.CharField(max_length= 50)
#    description = models.CharField(max_length= 200)
#    workspace = models.ForeignKey('workspace.DAMWorkspace')
#    event = generic.GenericRelation('eventmanager.EventRegistration')
#    state = models.ForeignKey('workflow.State',  null = True,  blank = True)
#
#    is_global = models.BooleanField(default = False)
#    
#    def get_actions(self, for_json = False):
#        actions_available = {}       
#        logger.debug('--------- script %s' %self)
#        classes = get_all_actions()
#        
#        for subclass in classes:
#            if subclass != SaveAction:
#                actions_available[subclass.__name__.lower()] = subclass
#                actions_available[subclass.verbose_name.lower()] = subclass
#            
#            
#        actions_available[SendByMail.__name__.lower()] = SendByMail
#        actions_available[SendByMail.verbose_name.lower()] = SendByMail
#        
#        if for_json:
#             actions = {
#                'image':{'actions':[]},
#                'video':{'actions':[]},
#                'audio':{'actions':[]},
#                'doc':{'actions':[]}
#                }
#        
#        else:
#            actions = {
#                'image':[],
#                'video':[],
#                'audio':[],
#                'doc':[]
#                }
#            
#    
##        logger.debug('media_types %s'%media_types)
#        
##        for media_type, info in pipeline.items():
#        logger.debug('self.pk %s'%self.pk)
#        logger.debug('self.actionlist_set.all() %s'%self.actionlist_set.all())
#        for action in self.actionlist_set.all():
#            logger.debug("action.actions %s"%action.actions)
#            info = simplejson.loads(str(action.actions))
#            media_type = action.media_type.name
#            logger.debug('info %s '%info)            
#            logger.debug('media_type %s'%media_type)
#            
#            if for_json:
#                actions[media_type]['source_variant'] = action.source_variant.name
##            source_variant = info['source_variant']
#            for action_dict in info['actions']:
#                
#                type = action_dict['type'].lower()
#                params = action_dict['parameters']
#                params['workspace'] = self.workspace
#                params['media_type'] = media_type
#                params['source_variant'] = action.source_variant
#                params['script'] = self
#                logger.debug('----action_dict %s'%action_dict)
#                logger.debug('params %s'%params)
#                try:                    
#                    action_tmp = actions_available[type](**params)                
#                except Exception, ex:              
#                    logger.exception(ex)                
#                    raise ActionError('action_tmp %s does not exist'%type)
#                if for_json:
#                    actions[media_type]['actions'].append(action_tmp._get_params())
#                else:
#                    actions[media_type].append(action_tmp)
#        return actions
#    
#    def save(self, *args,**kwargs):
#        #avoiding empty string saving
#        if self.name == '':
#            self.name = None
#        super(Script, self).save(*args,**kwargs)
#
#
#    def __unicode__(self):
#        return unicode(self.name)
#    
#    
#    def execute(self, items):
#        logger.debug('execute')
#        actions = self.get_actions()
#
#        logger.debug('actions %s'%actions)
#        for item in items:
#            adapt_parameters = {}   
#          
#            media_type = item.type.name
#                
#            for action in actions[media_type]:
##                if isinstance(action, SaveAs) or isinstance(action, SendByMail) or isinstance:
#                if action.__class__.__base__ == SaveAction or action.__class__ == SendByMail:
#                    action.execute(item,adapt_parameters)
#                else:
#                    tmp_adapt_parameters = action.get_adapt_params()
#                    logger.debug('tmp_adapt_parameters %s'%tmp_adapt_parameters)
#                    if tmp_adapt_parameters:
#                        adapt_parameters.update(tmp_adapt_parameters)
#            
#    class Meta:
#        unique_together = ('name', 'workspace')
# 
#    
#class BaseAction(object):
#    
#    media_type_supported = ['image', 'video', 'audio', 'doc']
#    verbose_name = ''
#    def __init__(self, media_type, source_variant, workspace, script, **params):   
#        
##        if media_type not in self.media_type_supported:
##            raise MediaTypeNotSupported('media_type %s not supported by action %s'%(media_type, self.__class__.__name__))
#        
#        
#        self.media_type = media_type
#        logger.debug('self.media_type %s'%self.media_type)
#        self.source_variant = source_variant
#        self.script = script
#        self.workspace = workspace
#        if params:
#            self.parameters = params
#        else:
#            self.parameters = {}
#            
#    def get_adapt_params(self):
#        return self.parameters
#    
#    def _get_params(self):
#        return {
#            'type': self.verbose_name,
#            'parameters':self.get_adapt_params()                       
#        }
#    
#    @staticmethod
#    def required_parameters(workspace):
#        return []
#    
#    
#    @staticmethod
#    def get_values(workspace = None):
#        pass
#
#class SetRights(BaseAction):
#    media_type_supported = ['image', 'video',  'doc', 'audio']
#    verbose_name = 'set rights'
#    @staticmethod
#    def required_parameters(workspace):
#        from metadata.models import RightsValue
#        tmp = [str(right) for right in RightsValue.objects.all().values_list('value', flat = True)]
#        values = {}
#        for media_type in Type.objects.all():
#            values[str(media_type)] = tmp
#        return  [{'name':'rights',  'type': 'string', 'values': values}]
#   
#    def __init__(self, media_type, source_variant, workspace, script, rights):  
#        super(SetRights, self).__init__(media_type, source_variant, workspace, script,  **{'rights':rights})
#        
#
#class SaveAction(BaseAction):
#    media_type_supported = ['image', 'video',  'doc', 'audio']
#       
#       
#    @staticmethod
#    def required_parameters(workspace):
#        
#        return [
#                {'name':'embed_xmp',  'type': 'boolean'},
#                 {'name':'output_format',  'type': 'string',  'values':{'image':['jpeg',  'gif','png', 'bmp'], 
#                                    'video': PRESETS['video'].keys(), 
#                                    'audio':  PRESETS['audio'].keys(), 
#                                    'doc': ['jpeg']
#            }
#        },
#
#        
#        ]
#    def __init__(self, media_type, source_variant, workspace, script, output_format, embed_xmp):  
#        super(SaveAction, self).__init__(media_type, source_variant, workspace, script)
#        self.output_format = output_format
#        self.embed_xmp = embed_xmp
#        
#    
#    def _get_output_media_type(self, adapt_parameters):
#                
#        if self.media_type == 'doc':
#            output_media_type = 'image'
#        elif  adapt_parameters.has_key('output_media_type'):
#            output_media_type= adapt_parameters.pop('output_media_type')
#        else:
#            output_media_type = self.media_type
#        
#        return output_media_type
#    
#    def _same_adapted_resource(self, component):
#        c = Component.objects.filter(source = component.source, parameters = component.parameters).exclude(pk = component.pk)
#        if c.count() > 0:
#            c = c[0]
#            if c._id:
#                return c
#        return None
#    
#    def _generate_resource(self, component, adapt_parameters): 
#        if adapt_parameters.has_key('rights'):
#            rights = adapt_parameters.pop('rights')
#        else:
#            rights = None
#        
#        if adapt_parameters.has_key('embed_xmp'):
#            embed_xmp = adapt_parameters.pop('embed_xmp')
#        else:    
#            embed_xmp = None
#            
#        logger.debug('rights %s'%rights)
#        logger.debug('embed_xmp %s'%embed_xmp)
#            
#        logger.debug('self.output %s'%self.output_variant)
#        logger.debug('self.media_type %s'%self.media_type)
#         
#        if self.media_type == 'video' or self.media_type == 'audio':
#            adapt_parameters['preset_name'] = self.output_format
#        else:
#            adapt_parameters['codec'] = self.output_format
#
#        logger.debug('adapt_parameters %s'%adapt_parameters)    
#         
##        component.save_rights_value(rights, self.workspace)
#        logger.debug('self.source %s'%self.source_variant)
#        try:
##            source_variant = Variant.objects.get(name = self.source_variant)         
#            source = self.source_variant.component_set.get(item = component.item, workspace = self.workspace)
#        except Exception, ex:
##            in case edited does not exist
#            logger.error(ex)
#            source_variant = Variant.objects.get(name = 'original')
#            source = source_variant.get_component(self.workspace, component.item)                 
#        
#        logger.debug('source.variant %s'%source.variant.name)
#        
##        if component.imported or( component.source and component._previous_source_id == source._id and  component.get_parameters() == adapt_parameters):
##            logger.debug('component.source._id %s'%component.source._id)
##            logger.debug('source._id %s'%source._id)
##            logger.debug('component will not be regenerated, is imported or no mods in source or adapt_params')
##            return
#        
#        component.set_parameters(adapt_parameters)
#        component.set_source(source)
#        
#        component.script = self.script
#        component.save()
#        component.save_rights_value(rights, self.workspace)
#        
#        same_resource = self._same_adapted_resource(component)
#        if same_resource:
#            component._id = same_resource._id
#            component.format = same_resource.format
#            component.save()
#            component.copy_metadata(same_resource) 
#        else:
#            logger.debug('generate task')        
#            generate_tasks(component, self.workspace, embed_xmp = embed_xmp)
#        
#    def execute(self, item, adapt_parameters):
#        output_media_type = self._get_output_media_type(adapt_parameters)
#        logger.debug('---------- self.output_variant %s'%self.output_variant)
#        logger.debug('---------- self.media_type %s'%self.media_type)
#        variant = Variant.objects.get(pk = self.output_variant) 
#                         
#        component = variant.get_component(self.workspace,  item,  Type.objects.get(name = output_media_type))
#        self._generate_resource(component, adapt_parameters)
#    
#    
#class SaveAs(SaveAction):
#    media_type_supported = ['image', 'video',  'doc', 'audio']
#    verbose_name = 'save'
#    
#    def _get_params(self):
#        return {
#                'type': self.verbose_name,
#                'parameters':
#                    {
#                    'output': self.output_variant,
##                    'output_name': Variant.objects.get(pk = self.output_variant).name,
#                    'output_format': self.output_format,
#                    'embed_xmp': self.embed_xmp,
#                
#                }}
#    
#    @staticmethod
#    def required_parameters(workspace):
#        params = SaveAction.required_parameters(workspace)
#        tmp = {}
#        for media_type in Type.objects.all():
#            tmp_dict ={}
#            for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), hidden = False, media_type = media_type,  auto_generated = True):
#                tmp_dict[variant.pk] = variant.name
#            tmp[media_type.name] = tmp_dict
#       
#        params.append({'name':'output',  'type': 'string',  'values':tmp})
#        
#        
#        return params
#    def __init__(self, media_type, source_variant, workspace, script, output,  output_format,   embed_xmp = False):  
#        super(SaveAs, self).__init__(media_type, source_variant, workspace, script,output_format,   embed_xmp)
#        logger.debug('........... output%s'%output)
#        self.output_variant = output
#    
#    
#        
#        
#class SendByMail(SaveAs):
#    verbose_name = 'send by mail'
#    
#    def __init__(self, media_type, source_variant, workspace, script, mail,  output_format,   embed_xmp= False):
#        output = Variant.objects.get(name = 'mail').pk
#        super(SendByMail, self).__init__(media_type, source_variant, workspace, script, output, output_format,   embed_xmp)
#        self.mail = mail
#         
#         
#    def _get_params(self):
#        return {
#                'type': self.verbose_name,
#                'parameters':
#                    {
#                    'mail': self.mail,
##                    'output_name': Variant.objects.get(pk = self.output_variant).name,
#                    'output_format': self.output_format,
#                    'embed_xmp': self.embed_xmp,
#                
#                }}
#        
#    @staticmethod
#    def required_parameters(workspace = None):
#        params = SaveAction.required_parameters(workspace)               
#        params.append({'name':'mail',  'type': 'string'})
#        return params
#    
#    def execute(self, item, adapt_parameters):  
#        adapt_parameters['mail'] = self.mail
#        super(SendByMail, self).execute(item, adapt_parameters)
#
#class Resize(BaseAction): 
#    verbose_name = 'resize'
#    media_type_supported = ['image', 'video',  'doc']
#    @staticmethod
#    def required_parameters(workspace):
#        return [{'name':'max_height',  'type':'number'},{'name':'max_width','type':'number'}]
#   
#    def __init__(self, media_type, source_variant, workspace, script,  max_height, max_width):
#        super(Resize, self).__init__(media_type, source_variant, workspace, script)
#        
#        self.parameters['max_height'] = max_height
#        self.parameters['max_width'] = max_width
#                
#
#class Crop(BaseAction): 
#    verbose_name = 'crop'
#    media_type_supported = ['image',]
#    @staticmethod
#    def required_parameters(workspace):
#        return [
#                { 'name': 'ratio',  'type': 'string'}, 
#                ]
#    
#    def __init__(self, media_type, source_variant, workspace, script,  ratio ):
#       
#        params = { 'ratio': ratio }
#            
#        super(Crop, self).__init__(media_type, source_variant, workspace, script, **params)
#     
#class Watermark(BaseAction): 
#    verbose_name = 'watermark'
#    media_type_supported = ['image', 'video']
#   
#    @staticmethod
#    def required_parameters(workspace):
#        return [{ 'name': 'watermark_filename',  'type': 'string'}, { 'name': 'pos_x_percent','type': 'number'}, { 'name': 'pos_y_percent',  'type': 'number'}, { 'name': 'alpha',  'type': 'number'}]
#    
#    def __init__(self, media_type, source_variant, workspace, script,  watermark_filename, pos_x = None, pos_y = None, pos_x_percent = None, pos_y_percent = None, alpha = None):
#        
#        super(Watermark,  self).__init__(media_type, source_variant, workspace, script)
#        self.parameters['watermark_filename'] = watermark_filename
#        
#         
#        
#        if self.media_type == 'image':
##            if not (pos_x and pos_y):
###                TMP waiting for mediadart
##                pos_x = pos_x_percent
##                pos_y = pos_y_percent
###                raise MissingActionParameters('pos_x or pos_y parameter is missing: they are required')
#            
#            self.parameters['alpha'] = alpha
#            self.parameters['pos_x_percent'] = pos_x_percent
#            self.parameters['pos_y_percent'] = pos_y_percent
#            
#        else:
#            if not ((pos_x and pos_y) or (pos_x_percent and pos_y_percent)):
#                raise MissingActionParameters('no coordinates for watermark are passed (pos_x, pos_y or pos_x_percent, pos_y_percent): they are required')
#            
#            if (pos_x and pos_y):
#                self.parameters['watermark_top'] = pos_y
#                self.parameters['watermark_left'] = pos_x
#            else:
#                self.parameters['watermark_top_percent'] = pos_y_percent
#                self.parameters['watermark_left_percent'] = pos_x_percent
#                
#       
#       
#    def _get_params(self):
#        if self.media_type == 'video': 
#            return {
#                    'type': self.verbose_name,
#                    'parameters':
#                        {
#                        'watermark_filename': self.parameters['watermark_filename'],
#                        'pos_y_percent': self.parameters['watermark_top_percent'],
#                        'pos_x_percent': self.parameters['watermark_left_percent'],
#                    
#            }}
#        else:
#            return super(Watermark, self)._get_params() 
#            
##    def get_adapt_params(self):
##        if self.media_type == 'image':
##            return self.parameters
##        else:
##            tmp = dict(self.parameters)
##            tmp['pos_y_percent'] = tmp.pop('watermark_top_percent')
##            tmp['pos_x_percent'] = tmp.pop('watermark_left_percent')
##            
##            return tmp
#
#        
#
#preset = {'video':
#                   {'matroska_mpeg4_aac': 'mpeg4',
#                   'mp4_h264_aaclow': 'mpeg4',
#                   'flv': 'flv',
#                   'avi': 'avi',
#                   'flv_h264_aac': 'flv',
#                   'theora': 'ogg'}
#     
#}
#
#        
#class VideoEncode(BaseAction):
#    verbose_name = 'video encode'
#    """default bitrate in kb""" 
#    media_type_supported = ['video']
#    @staticmethod
#    def required_parameters(workspace):
#        return [{ 'name': 'bitrate','type': 'number', 
#                 'values': {'video': [64,128, 192, 256, 590, 640 ,1024 , 1536, 2048, 4096, 8192, 12288, 20040],
#                  'audio': [], 'image':[], 'doc': []}
#                },
#                { 'name': 'framerate', 'type': 'number',
##                 'values': [[\"25/2\", 12.5], [\"24/1\", 24], [\"25/1\", 25], [\"57000/1001\", 29.97],[\"57/1\", 57]]
#                'values': {'video':['25/2','24/1', '25/1', '57000/1001', '57/1'], 'audio': [], 'image':[], 'doc': []}
#                 }                
#                ]
#    
#    def __init__(self, media_type, source_variant, workspace, script, bitrate, framerate):
#        params = {'bitrate':bitrate,  'framerate': framerate}
#        super(VideoEncode, self).__init__(media_type, source_variant, workspace, script, **params)
#        
#       
#        if self.parameters.has_key('bitrate'):
##            if self.parameters['output_format'] in ['flv', 'avi', 'mpegts']:
##                self.parameters['video_bitrate'] = int(self.parameters.pop('bitrate')*1000)
##            else:
##                 self.parameters['video_bitrate'] = int(self.parameters.pop('bitrate'))
#            self.parameters['video_bitrate'] = int(self.parameters.pop('bitrate'))       
#        
#        if self.parameters.has_key('framerate'): 
#            self.parameters['video_framerate'] = self.parameters.pop('framerate')
#            
#            
#    def get_adapt_params(self):
#        tmp = dict(self.parameters)
#        tmp['bitrate'] = tmp.pop('video_bitrate')
#        tmp['framerate'] = tmp.pop('video_framerate')
#        
#        return tmp
#                
#class AudioEncode(BaseAction):
#    verbose_name = 'audio encode'
#    """default bitrate in kb"""
#    media_type_supported = ['video', 'audio']
#    
#    @staticmethod
#    def required_parameters(workspace):
#        return [{ 'name': 'bitrate','type': 'number', 'values': {
#                                                                 'video': [64, 80, 96, 112,128, 160, 192, 224, 256,590],
#                                                                 'audio': [64, 80, 96, 112,128, 160, 192, 224, 256,590], 
#                                                                 'image':[], 'doc': []
#                                                                 
#                                                                 }},  
#                { 'name': 'rate', 'type': 'number', 'values': { 'video': [59000, 44100, 48000],
#                                                               'audio': [59000, 44100, 48000],
#                                                               'image':[], 'doc': []
#                                                               
#                                                               
#                                                               }}]
#    def __init__(self, media_type, source_variant, workspace, script, rate, bitrate):
#        super(AudioEncode, self).__init__(media_type, source_variant, workspace, script)
#        
#
#        self.parameters['audio_bitrate'] = int(bitrate)            
#        self.parameters['audio_rate'] = int(rate)
#        
#    
#    def get_adapt_params(self):
#        tmp = dict(self.parameters)
#        tmp['bitrate'] = tmp.pop('audio_bitrate')
#        tmp['rate'] = tmp.pop('audio_rate')
#        
#        return tmp
#            
#class ExtractVideoThumbnail(SaveAction):
#    verbose_name = 'extract video thumbnail'
#    media_type_supported = ['video']
#    @staticmethod
#    def required_parameters(workspace):
#        
#        tmp_output = {}
#        for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), hidden = False, media_type__name = 'video',  auto_generated = True):
#            tmp_output[variant.pk] = variant.name
#        
#        params = [{ 'name': 'max_height','type': 'number'},
#                { 'name': 'max_width', 'type': 'number'},
#                {'name':'output_format',  'type': 'string',  'values':{'video':['jpeg',  'gif','png', 'bmp'],
#                                                                       'image': [],
#                                                                       'audio': [],
#                                                                       'doc':[]
#                                                                       }},
#                                                                    
#                { 'name': 'mail','type': 'string'},
#                
#                
#                {'name':'output',  'type': 'string',  'values':{'audio': [],
#                   'image': [],
#                   'doc':[],
#                  
#                  'video': tmp_output
#            }}
#                
#                ]
#        
#        return params
#    
#    
#    
#         
#    def __init__(self, media_type, source_variant, workspace, script, max_height,  max_width, output_format, output= None, mail = None):  
#        media_type = 'image'
#        params = {'max_height': max_height,  'max_width':max_width,   'output': output, 'mail': mail}
#        super(ExtractVideoThumbnail, self).__init__(media_type, source_variant, workspace, script,output_format,   False)
#        logger.debug('---------------------------------------------media_type %s'%media_type)
#        
#        self.parameters = {}
#        if mail:
#            self.mail = mail
##            self.output_variant = 'mail'
#            self.output_variant = Variant.objects.get(name = 'mail').pk
#            self.parameters['mail'] =  mail
#            self.parameters['output'] =  Variant.objects.get(name = 'mail').pk
#        else:
#            self.output_variant = output
#            self.parameters['output'] =  output
#            
#            self.mail = ''
#            self.parameters['mail'] =  ''
#            
#        self.output_media_type= 'image'
#        self.max_height = max_height
#        self.max_width = max_width 
#        self.parameters['output_format'] = output_format 
#        self.parameters['max_width'] =  max_width
#        
#        self.parameters['max_height'] =  max_height
#    
##    def __init__(self, media_type, source_variant, workspace , script, max_height,  max_width):
##        params = {'max_height': max_height,  'max_width':max_width,  'output_media_type': 'image'}
##        super(ExtractVideoThumbnail, self).__init__(media_type, source_variant, workspace, script, **params)
#    
#    def execute(self, item, adapt_parameters):  
#        if self.mail:
#            adapt_parameters['mail'] = self.mail        
#     
#        adapt_parameters['max_height'] = self.max_height
#        adapt_parameters['max_width'] = self.max_width
#        return super(ExtractVideoThumbnail, self).execute(item, adapt_parameters)
        
class Script(models.Model):
    name = models.CharField(max_length= 50)
    description = models.CharField(max_length= 200)
    workspace = models.ForeignKey('workspace.DAMWorkspace')
    actions = models.TextField()
    
    
        

def inspect_actions():
    from settings import INSTALLED_ACTIONS
    import sys
    
    actions = []
    
    for action in INSTALLED_ACTIONS:
        __import__(action)   
        m = sys.modules[action]
        name = m.__name__.split('.')[-1]
        actions.append({'name': name, 'parameters': m.inspect()})

    
    return actions
        

    
    
    
