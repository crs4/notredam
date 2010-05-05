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

from django.db import models, connection
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.utils import simplejson

from dam.workspace.models import DAMWorkspace as Workspace
from dam.repository.models import Component
from dam.metadata.models import RightsValue

from dam.framework.dam_repository.models import Type

import logger
import time

class Variant(models.Model):    
    name = models.CharField(max_length=50)
    caption = models.CharField(max_length=64)
    is_global = models.BooleanField(default=False) #common for all ws
    editable = models.BooleanField(default=True)    
    media_type = models.ForeignKey(Type,  null = True, blank = True)
    auto_generated = models.BooleanField(default=True)
    shared = models.BooleanField(default= False) #the same component will be shared through ws
    default_url = models.CharField(max_length=100, null = True, blank = True) #for static variant, i.e. thumbnail for audio ;)
    default_rank = models.IntegerField(null = True, blank = True) #not null for imported variants. variant with rank 1 will be used for generating  the others
    resizable = models.BooleanField(default=True)
    
    def is_original(self):
        return self.name == 'original' and self.is_global
    
    def get_source(self,  workspace,  item):
#        if not self.auto_generated:
#            return None
            
        sources = SourceVariant.objects.filter(destination = self,  workspace = workspace)
        for source_variant in sources:
            v = source_variant.source
            logger.debug('source_variant.source %s'%v)
            if Component.objects.filter(item = item, variant = v).count( ) > 0:
                return v
            
           
  
    def get_component(self, workspace,  item):
      
        return self.component_set.get(item = item,  workspace = workspace)
        
    def get_preferences(self, workspace):
        return VariantAssociation.objects.get(variant = self,  workspace = workspace).preferences
    
    def __str__(self):
        return self.name

    def save(self,  *args,  **kwargs):
        if self.is_global and Variant.objects.filter(name = self.name,  is_global = True,  media_type= self.media_type).count() > 0:
            raise Exception('A global variant with name %s already exists'%self.name)
        super(Variant, self).save(*args,  **kwargs)

class VariantDefault(models.Model):
    variant = models.ForeignKey(Variant)
#    media_type = models.ForeignKey(Type)
    
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    preferences = generic.GenericForeignKey()
    
class VariantAssociation(models.Model):
    variant = models.ForeignKey(Variant)
    workspace = models.ForeignKey(Workspace)
#    media_type = models.ForeignKey(Type)
    
    content_type = models.ForeignKey(ContentType,  null = True, blank = True)
    object_id = models.PositiveIntegerField(null = True, blank = True)
    preferences = generic.GenericForeignKey()
    
    class Meta:
        unique_together = (("variant", "workspace"),)
        
        
class Preferences(models.Model):
    variant_association = generic.GenericRelation(VariantAssociation)
    variant_default = generic.GenericRelation(Variant)
    component = generic.GenericRelation(Component)
    rights_type = models.ForeignKey(RightsValue, default=None, null=True, blank=True)
    
    
    def get_prefs(self):
        prefs = dict(self.__dict__)
        prefs.pop('id')
        prefs.pop('rights_type_id')
        if self.rights_type:
            prefs['rights_type'] = self.rights_type.value
        return prefs
    
    def save_rights(self, value):
        if value:
            if value == 'original license':
                self.rights_type = None
            else:
                logger.debug('value.__class__ %s'%value.__class__)
                self.rights_type = RightsValue.objects.get(value=value)

    def save_func(self,  value_dict):
        
        logger.debug('value_dict %s'%value_dict)
        prefs_dict = dict(self.__dict__)
    #    prefs_dict .pop('id')
        logger.debug('before changes, prefs_dict %s' %prefs_dict)
        prefs_dict.pop('id')
        
        
        for param in prefs_dict.keys():        
            value = value_dict.get(param,  False)

            if param == 'rights_type_id':
                self.save_rights(value)
            else: 
                if value and value.isdigit():
                    logger.debug('param %s'%param)
                    logger.debug('value %s'%value)
                    logger.debug('value.__class__ %s'%value.__class__)
                    value = int(value)
                    
                try:
                    logger.debug('param %s'%param)
                    logger.debug('value %s'%value)
                    
                    
                    self.__dict__ [param] = value
                except Exception,  ex:
                    logger.exception('param %s'%param)
                    logger.exception(ex)
            
        logger.debug('prefs_dict %s'%prefs_dict)        
        self.save()
        
        
    def __eq__(self, other):
        if isinstance(other, Preferences):
            for field in self._meta.get_all_field_names():
                if field in ['id',  'component',  'variant_association',  'variant_default',  'rights_type']:
                    continue 
                if self.__dict__[field] != other.__dict__[field]:
                    return False
            return True
            
        return False

        
    def copy(self):
        copy = self.__class__()
        for field in self._meta.get_all_field_names():
            if field == 'id':
                continue           
            try:
                copy.__dict__[field] = self.__dict__[field]
            except Exception,  ex:
#                logger.exception(ex)
                pass
            
        copy.save()
        return copy
    
    class Meta:
        abstract = True

class WatermarkingPreferences(models.Model):
    watermarking = models.BooleanField(default=False)
    watermark_uri = models.CharField(max_length=41, null=True, blank=True,  default = None)

    watermarking_position = models.IntegerField(null=True, blank=True,  default = None)
  
    class Meta:
        abstract = True

    def get_watermarking_params(self):
        if self.watermarking:
            params = {}
            if self.watermarking_position <= 3:
                params['watermark_top_percent'] = 15                
                
            if self.watermarking_position >=4  and self.watermarking_position <=6:
                params['watermark_top_percent'] = 50
                
            if self.watermarking_position >=7  and self.watermarking_position <=9:
                params['watermark_top_percent'] = 83
                
            if self.watermarking_position == 1 or self.watermarking_position == 4 or  self.watermarking_position == 7:
                params['watermark_left_percent'] = 15                
                
            if self.watermarking_position == 2 or self.watermarking_position == 5 or  self.watermarking_position == 8:
                params['watermark_left_percent'] = 50                    
            
            if self.watermarking_position == 3 or self.watermarking_position == 6 or  self.watermarking_position == 9:
                params['watermark_left_percent'] = 83  
            
            logger.debug('params %s'%params)
            return params
        else:
            return None
            
            
        

class PresetPreferences(Preferences):
    
    def get_prefs(self):
        prefs = dict(self.__dict__)
        prefs.pop('id')
        prefs.pop('preset_id')
        prefs.pop('rights_type_id')
        if self.rights_type:
            prefs['rights_type'] = self.rights_type.value
        

        preset = {'name': self.preset.name,  'parameters': {}}
        prefs['preset'] =preset
        
        for value in self.values.all():
            preset['parameters'][value.parameter.name] = value.value
            
        return prefs
        
    
    class Meta:
        abstract = True
        
    def save_func(self,  value_dict):   
        from django.contrib.contenttypes.models import ContentType
 
        super(PresetPreferences,  self).save_func(value_dict)
        
        try:
            prefs_dict = dict(self.__dict__)      
            prefs_dict.pop('id')
            v = self.variant_association.all()[0].variant

            preset_id = value_dict['preset']
            preset = Preset.objects.get(pk = preset_id)
            logger.debug('preset %s'%preset)
            self.preset = preset 
            self.save()
            
            for param in preset.parameters.all():
                logger.debug('param %s'%param)
                value = value_dict.get(param.name)
                logger.debug('value %s'%value)
                if value:                    
                    
                    try:                        
                        logger.debug('param.pk %s'%param.pk)
                        logger.debug('self.pk %s'%self.pk)
                        param_value = PresetParameterValue.objects.get(parameter = param, videopreferences = self,  content_type = ContentType.objects.get_for_model(self))
                        
                    except PresetParameterValue.DoesNotExist,  ex:                      
                        
                        param_value = PresetParameterValue.objects.create(parameter = param, preferences = self)                     
                        
                    param_value.value = value
     
                    param_value.save()
             
            logger.debug(self.values.all())
        except Exception,  ex:
            logger.exception(ex)
            raise ex
            
            
    def __eq__(self, other):
       
        if isinstance(other, self.__class__):
            if self.preset != other.preset:      
                return False
                
            if self.values.all().count() != other.values.all().count():       
                return False                
            for value in self.values.all():
                
                other_value = other.values.get(parameter =  value.parameter)
                if other_value.value != value.value:
                    return False
                    
            
            for field in self._meta.get_all_field_names():
                if field in ['id',  'component',  'variant_association',  'variant_default',  'rights_type',   'preset',  'values']:
                    continue 
                
                logger.debug('self.pk %s'%self.pk)
                logger.debug('self.__class__ %s'%self.__class__)
                logger.debug('other.pk %s'%other.pk)
                logger.debug('self.watermark_uri %s'%self.watermark_uri)
                logger.debug('other.watermark_uri %s'%other.watermark_uri)
                
                logger.debug('self.__dict__["watermark_uri"] %s'%self.__dict__["watermark_uri"])
                logger.debug('other.__dict__["watermark_uri"] %s'%other.__dict__["watermark_uri"])
                
                
                if str(self.__dict__[field]) != str(other.__dict__[field]):
                    logger.debug('field %s'%field)
                    logger.debug('self.__dict__[field].__class__ %s'%self.__dict__[field].__class__)
                    logger.debug('dir(self.__dict__[field]) %s'%dir(self.__dict__[field]))
                    logger.debug('self.__dict__[field] %s'%self.__dict__[field])
                    logger.debug('other.__dict__[field] %s'%other.__dict__[field])
                    return False
           
            
            return True
        
        return False


    def copy(self):      
        copy = self.__class__()
        copy.preset = self.preset
        copy.save()
        for value in self.values.all():
            PresetParameterValue.objects.create(preferences = copy,  parameter = value.parameter,  value = value.value)
 
        
        return copy


    

class AudioPreferences(PresetPreferences):    
    preset = models.ForeignKey('Preset')
    values = generic.GenericRelation('PresetParameterValue')
    
    def _get_media_type(self):
        return Type.objects.get(name = 'audio')
    
    
    media_type = property(fget=_get_media_type)
    mime_type = property(fget=_get_media_type)

        
class VideoPreferences(PresetPreferences,  WatermarkingPreferences):    
    preset = models.ForeignKey('Preset')
    values = generic.GenericRelation('PresetParameterValue')    
    
    def _get_media_type(self):
        return Type.objects.get(name = 'movie')
   
    media_type = property(fget=_get_media_type)
    mime_type = property(fget=_get_media_type)
    
    def copy(self):    
        copy = super(VideoPreferences,  self).copy()
        for field in self._meta.get_all_field_names():
            if field in ['id',  'component',  'variant_association',  'variant_default',  'rights_type',   'preset',  'values']:
                continue 
            
            copy.__dict__[field] = self.__dict__[field]
        
        copy.save()        
        return copy

    
    
class ImagePreferences(Preferences):
    container = models.CharField(max_length=10, default = 'jpg',  null= True,  blank = True)
#    TODO: delete contaniner and update fixture
    codec = models.CharField(max_length=10,  default = 'jpg')
    max_dim = models.IntegerField(default = -1,  null = True,  blank = True)
    cropping = models.BooleanField('maintain aspect ratio',  default=False)
    watermarking = models.BooleanField(default=False)
    watermark_uri = models.CharField(max_length=41, null=True, blank=True,  default = None)
    watermarking_position = models.IntegerField(null=True, blank=True,  default = None)
    video_position = models.IntegerField(null=True, blank=True,  default = None)
    
    def save_func(self,  value_dict):    
        prefs_dict = dict(self.__dict__)
        logger.debug('ID PREFSSSSS %s'%self.pk)
    #    prefs_dict .pop('id')
        logger.debug('before changes, prefs_dict %s' %prefs_dict)
        prefs_dict.pop('id')
        v = self.variant_association.all()[0].variant
        logger.debug('v.resizable %s'%v.resizable)
        if not v.resizable:
            prefs_dict.pop('max_dim')
        
        for param in prefs_dict.keys():
        
            value = value_dict.get(param, False)
            
            if param == 'rights_type_id':
                self.save_rights(value)
                continue
#            elif param == 'cropping': #the value passed is keep maintain ratio, ie not cropping
#                
#                if value_dict.__contains__(param):                    
#                    value = False
#                   
#                else:
#                    value = True
            
            else:
                value = value_dict.get(param,  self._meta.get_field_by_name(param)[0].default)
                        

                if value and isinstance(value, str)  and value.isdigit():
                   
                    value = int(value)
                
            try:
              
                self.__dict__ [param] = value
            except Exception,  ex:
                logger.exception('param %s'%param)
                logger.exception(ex)
                raise ex
            
        logger.debug('prefs_dict %s'%prefs_dict)        
        self.save()    
    
    def _get_media_type(self):
        return Type.objects.get(name = 'image')
    
    media_type = property(fget=_get_media_type)
    mime_type = property(fget=_get_media_type)


class DocPreferences(Preferences):
    codec = models.CharField(max_length=10,  default = 'jpg')
    max_dim = models.IntegerField(default = 100)
    
    def _get_media_type(self):
        return Type.objects.get(name = 'doc')
  
    def _get_mime_type(self):
        return Type.objects.get(name = 'image')
    
    media_type = property(fget=_get_media_type)
    mime_type = property(fget=_get_mime_type)

class SourceVariant(models.Model):
    source = models.ForeignKey(Variant,  related_name = 'sources' )
    destination = models.ForeignKey(Variant,  related_name = 'destinations')
    workspace= models.ForeignKey(Workspace)
    rank = models.PositiveIntegerField()
    
    class Meta:
#        unique_together = (('workspace',  'rank'), )
        ordering = ["rank"]

#audio_container = {'ogg':{'bitrate':[], }}
    
    
class PreferencesForm:    
    def __init__(self,  prefs = None):
        if prefs:
            logger.debug('prefs %s'%prefs)
            logger.debug('prefs.__dict__ %s'%prefs.__dict__)
            checked_value = prefs.rights_type
        else:
            checked_value = None
            
        rights_list = [{
                        'fieldLabel': 'License',
                        'boxLabel': 'Original License',
                        'name': 'rights_type_id',
                        'inputValue': 'original license', 
                        'checked': checked_value is None
                    }]    
            
        rights = RightsValue.objects.all()
        
        for r in rights:
            new_rightvalue = {
                        'boxLabel': r.value,
                        'name': 'rights_type_id',
                        'inputValue': r.value, 
                        'checked': checked_value ==  r
                    }
            rights_list.append(new_rightvalue)
        
        self.rights = {
                'xtype':'fieldset', 
                'collapsed': True,
            'collapsible': True,
            'defaultType': 'radio',
            'items':rights_list,
        'title': 'Rights',
        'autoHeight': True
                
                }
                
    def _create_source(self,  media_type,  variant):
        self.sources = {
            'xtype':'fieldset',  
#            'collapsible': True, 
#            'collapsed': False, 
            'title':'Source', 
            'autoHeight': 'auto',       
            'autoWidth':True, 
            'width':'auto', 
            'items':[{
                      'xtype': 'variantrankpanel', 
                      'media_type': media_type                      
                      }
            ]
            }
                   
        if variant:
            self.sources['items'][0]['variant_id'] = variant.pk
    
    def _create_transcoding(self,  store_codec,  codec):
        self.transcoding ={
                'xtype':'fieldset',  
                'title':'Transcoding', 
                'autoHeight': 'auto', 
                'items':{'xtype':'combo', 
                'store':  store_codec,
                'editable': False,
                'value': codec, 
                'name': 'codec',
                'displayField':'format',
                'hiddenName': 'codec',
                'mode': 'local',
                'fieldLabel': 'format',
                'triggerAction': 'all',
                'allowBlank':False,
                'forceSelection': True
                    }
                }
        
    

    def _get_wm(self):
        if self.prefs:
            cb_checked  = self.prefs.watermarking
            position = self.prefs.watermarking_position
            
            if self.prefs.watermark_uri:
                src_wm = '/redirect_to_resource/'+self.prefs.watermark_uri+'/?t=%s'%time.time()
                uri = self.prefs.watermark_uri
            else:
                src_wm = ''
                uri = ''
        else:
            cb_checked  = False
            position = 1
            src_wm = ''
            uri = ''
            
            
        self.watermarking =  {
                'xtype':'watermarkingfieldset',  
                'title':'Watermarking', 
                'autoHeight': 'auto', 
                'name':'watermarking',
               'cb_name': 'watermarking',  
                'cb_checked':cb_checked,
                'media_type':'image',   
                'src_watermark_uri': src_wm, 
                'watermark_uri': uri, 
                'media_type':'image',   
                'watermarking_position': position,  
                

        }



    def get_form(self):
        pass
class ImagePreferencesForm(PreferencesForm):
    def __init__(self, prefs = None):
        PreferencesForm.__init__(self,  prefs)
        self.store_codec = ['jpg','bmp', 'gif', 'png']
        max_dim_value = 300
        if not prefs:
            self.prefs = ImagePreferences(cropping = False,  max_dim = max_dim_value, codec= self.store_codec[0], )   
            variant = None
            variant_resizable = True
        else:
            self.prefs = prefs
            variant = prefs.variant_association.all()[0].variant
            variant_resizable = variant.resizable
#        v = self.variant_association.all()[0].variant
        
        
        
        self._create_source('image',  variant)
        
        not_cropping = {
            'xtype':'checkbox', 
            'name': 'cropping', 
            'fieldLabel':'keep aspect ratio', 
            
                            
        }
        try:
            if not self.prefs.cropping:
                not_cropping['checked'] = True
        
        except Exception,  ex:
            logger.debug(ex)
            
        if variant_resizable:

            logger.debug('self.prefs.max_dim %s'%self.prefs.max_dim)
            cb_checked = self.prefs.max_dim > 0
            if self.prefs.max_dim > 0:
                max_dim = self.prefs.max_dim
            else:
                max_dim = max_dim_value
            
            
      
            
            self.resize_fieldset = {
                'xtype':'fieldsetcheckbox',  
                'title':'Resize', 
                'autoHeight': 'auto', 
                'name':'resize',
               'cb_name': 'resize',  
                'cb_checked':cb_checked, 
                'items':[
                         {'xtype': 'intfield',                             
                            'value': max_dim, 
                            'name': 'max_dim',
                            'displayField':'max dimension',                          
                            'fieldLabel': 'max dimension',
                                 
                                 }, 
#                            not_cropping
                         ], 
                }
        
        else:
            self.resize_fieldset = None
        self._get_wm()
        self._create_transcoding(self.store_codec,  self.prefs.codec)
        
        
    
    def get_form(self):
        if self.resize_fieldset:
            resp =  [                
                self.sources, 
                self.resize_fieldset, 
                self.transcoding,
               self.watermarking,  
                self.rights, 
            ]
        else:
            resp =  [                
                self.sources, 
                self.resize_fieldset, 
                self.transcoding,
               self.watermarking,  
                self.rights, 
            ]
        return resp
        

def _create_parameters_json(params, prefs,  variant_resizable):
    try:
        parameter_json = []
        max_dims = [256, 300, 512, 640, 800, 1024, 1280, 1600, 2048]
        
        fieldsets = {}
        
        for param in params:
            
            
            if not variant_resizable and param._class == 'size' :
                continue
            else:
                
                if param.type == 'int':
                    item = {
                        'xtype': 'intfield', 
                        'name': param.name,
                        'displayField':param.caption,
                        
                        'fieldLabel': param.caption,
                        'value': param.default, 
                    }

                    
                else:
                    item = {
                    'xtype': 'combo', 
                    'editable': False,
                    'name': param.name,
                    'displayField':param.caption,
                    'hiddenName': param.name,
                    'mode': 'local',
                    'fieldLabel': param.caption,
                    'triggerAction': 'all',
                    'allowBlank':False, 
                    'forceSelection': True, 
                    'labelStyle': 'width:135px'
                    }
                
                    if param.values:

                        logger.debug('param.values %s'%param.values)
                        logger.debug('param %s'%param)
                        values = simplejson.loads(param.values)
                        logger.debug('values %s'%values)
                        item['store'] = values
                        logger.debug('---------------' )
                        logger.debug(item['store'] )
                    
                if prefs:
                    try:
                        item['value'] = prefs.values.get(parameter = param).value
                    
                    except:
                        item['value'] = param.default
            
                else:
                    item['value'] = param.default
                
                
                
                if param._class == 'watermarking':
                    pass
                else:
                    if fieldsets.has_key(param._class):
                        
                        fieldsets[param._class]['items'].append(item)
                    else:
                        fieldsets[param._class] = {'xtype': 'fieldset', 
                                                                'title':param._class, 
                                                                'autoHeight': 'auto',
                                                                'items':[item] , 
                                                                'id': 'preset_' + param._class,                                      
                                                   }
                    
        
        for fieldset in fieldsets.values():
            parameter_json.append(fieldset)
            
        logger.debug('parameter_json %s'%parameter_json)

    
    except Exception,  ex:
        logger.debug('exxxxxxxx %s'%ex)
        raise ex

    return parameter_json

class VideoPreferencesForm(PreferencesForm):
    def __init__(self, prefs = None):
        PreferencesForm.__init__(self,  prefs)
        self.prefs = prefs
        presets = Preset.objects.filter(media_type__name = 'movie')
        if prefs:
            logger.debug('prefs %s'%prefs)
            
            preset_selected = self.prefs.preset
            logger.debug('preset_selected %s' %preset_selected)
            variant = self.prefs.variant_association.all()[0].variant
            variant_resizable = variant.resizable
        else:
            preset_selected = presets[0]
            variant = None
            variant_resizable = True
            
        self._create_source('movie',  variant)
    
        params = preset_selected.parameters.all()
        

        self.presets= {
            'xtype': 'presetfieldset', 
            'preset_store': [(preset.pk,  preset.caption) for preset in presets],
            'preset_selected' :preset_selected.pk
        }
        
        self.presets['parameters'] = _create_parameters_json(params,  prefs,  variant_resizable)
        
        self._get_wm()

    def get_form(self):
      
            return [                
                self.sources,                 
                self.presets,
                self.watermarking,                 
                self.rights
                ]
    
    
class AudioPreferencesForm(PreferencesForm):
    def __init__(self, prefs = None):
        PreferencesForm.__init__(self,  prefs)
        self.prefs = prefs
        presets = Preset.objects.filter(media_type__name = 'audio')
        if prefs:
            logger.debug('prefs %s'%prefs)
            
            preset_selected = self.prefs.preset
            logger.debug('preset_selected %s' %preset_selected)
            variant = self.prefs.variant_association.all()[0].variant
            variant_resizable = variant.resizable
        else:
            preset_selected = presets[0]
            variant = None
            variant_resizable = True
            
        self._create_source('audio',  variant)
    
        params = preset_selected.parameters.all()
        

        self.presets= {
            'xtype': 'presetfieldset', 
            'preset_store': [(preset.pk,  preset.caption) for preset in presets],
            'preset_selected' :preset_selected.pk
        }
        
        self.presets['parameters'] = _create_parameters_json(params,  prefs,  variant_resizable)
        
        

    def get_form(self):
      
            return [                
                self.sources,                 
                self.presets,
                self.rights
                ]
    




class DocPreferencesForm(PreferencesForm):
    def __init__(self, prefs = None):
        PreferencesForm.__init__(self,  prefs)
        self.store_codec = ['jpg','bmp', 'gif', 'png']
        max_dim_value = 300
        if not prefs:
            self.prefs = DocPreferences(max_dim = max_dim_value, codec= self.store_codec[0], )   
            variant = None
            variant_resizable = True
        else:
            self.prefs = prefs
            variant = prefs.variant_association.all()[0].variant
            variant_resizable = variant.resizable
#        v = self.variant_association.all()[0].variant
        
        
        
        self._create_source('image',  variant)
        self._create_transcoding(self.store_codec,  self.prefs.codec)
        
        
        
        if not variant_resizable:
            self.resize_fieldset = None
                
        else:
            cb_checked = self.prefs.max_dim > 0
            if self.prefs.max_dim: 
                max_dim = self.prefs.max_dim
            else:
                max_dim = max_dim_value
        
            
            
            self.resize_fieldset = {
                'xtype':'fieldsetcheckbox',  
                'title':'Resize', 
                'autoHeight': 'auto', 
                'name':'resize',
               'cb_name': 'resize',  
                'cb_checked':cb_checked, 
                'items':[
                         {'xtype': 'intfield',                             
                            'value': max_dim, 
                            'name': 'max_dim',
                            'displayField':'max dimension',                          
                            'fieldLabel': 'max dimension',
                                 
                                 }, 
#                            not_cropping
                         ], 
                }
            
    
    def get_form(self):
        if self.resize_fieldset:
            return [
#                self.sources, 
                self.resize_fieldset, 
                self.transcoding,
                self.rights]
        else:
            return [
#                self.sources, 
                self.transcoding,
                self.rights]
        
        
    
class Preset(models.Model):
    name = models.CharField(max_length=40)
    caption = models.CharField(max_length=64)
    extension = models.CharField(max_length=5)
    parameters = models.ManyToManyField('PresetParameter')
    media_type = models.ForeignKey(Type)
    
    
#    container = models.CharField(max_length=10, default='flv')
#    video_codec = models.CharField(max_length=10, default='flv')
#    audio_codec = models.CharField(max_length=10, default='mp3')
#    video_bitrate = models.IntegerField(default = 900000)
#    frame_rate = models.IntegerField(default = 25)
#    audio_sample_rate = models.IntegerField(default = 22050)
#    audio_bitrate = models.IntegerField(default = 64)
#    max_dim = models.IntegerField(default = 300)
#    cropping = models.BooleanField(default=False)
#    watermarking = models.BooleanField(default=False)
#    watermark_uri = models.CharField(max_length=41, null=True, blank=True)
#    watermarking_position = models.IntegerField(null=True, blank=True) 


    def __unicode__(self):
        return self.name
    
class PresetParameter(models.Model):
    name = models.CharField(max_length=20)
    caption = models.CharField(max_length=64)
    _class = models.CharField(max_length=10)
    type = models.CharField(max_length=10)
    default = models.CharField(max_length=20,  null = True, blank = True)
    values = models.CommaSeparatedIntegerField(max_length = 255,  null = True, blank = True)
    
    def __unicode__(self):
        return self.name
    
class PresetParameterValue(models.Model):
    content_type = models.ForeignKey(ContentType,  null = True, blank = True)
    object_id = models.PositiveIntegerField(null = True, blank = True)
    preferences = generic.GenericForeignKey()
    
    parameter = models.ForeignKey('PresetParameter')
    value = models.CharField(max_length=20)
    
    def __unicode__(self):
        return self.value

