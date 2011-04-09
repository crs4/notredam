#from scripts.actions import BaseAction, new_id, Resource
#from mediadart.mqueue.mqclient_twisted import Proxy
#from mediadart import log
#
#from repository.models import Component
#
#class AdaptImageResource(Resource):
#    pass
#    
#class Crop(AdaptImage):    
#    
#    def _execute(self):
#        log.debug('executing crop')
#        
#        log.debug('input %s' %self.resource)
#        input = self.resource.component
#        argv = input.params.get('argv', [])
#        input_width = input.width
#        input_height = input.height
#            
#        
#        if self.params.get('ratio'):
#            x_ratio, y_ratio = self.params['ratio'].split(':')
#            y_ratio = int(y_ratio)
#            x_ratio = int(x_ratio)
#            final_width = min(input_width, input_height*x_ratio/y_ratio)
#            final_height = final_width*y_ratio/x_ratio
#            log.debug('ratio=(%s,%s), final(h,w)=(%s, %s), original(h,w)=(%s, %s)'%(
#                   x_ratio, y_ratio, final_height, final_width, input_height, input_width))
#            ul_y = (input_height - final_height)/2
#            ul_x = 0
#            lr_y = ul_y + final_height
#            lr_x = final_width 
#        else:
#            lr_x = int(int(self.params['lowerright_x'])*input_width/100)
#            ul_x = int(int(self.params['upperleft_x'])*input_width/100)
#            lr_y = int(int(self.params['lowerright_y'])*input_height/100)
#            ul_y = int(int(self.params['upperleft_y'])*input_height/100)
#        
#        input_width = lr_x -ul_x 
#        input_height = lr_y - ul_y
#        log.debug('orig(h,w)=(%s, %s)' % (input_height, input_width))
#        argv +=  ['-crop', '%dx%d+%d+%d' % (input_width, input_height,  ul_x, ul_y)]
#        log.debug('argv %s'%argv)
#        
#        if not save_as: 
#            self._output = {
#                'argv': argv,
#                'input_width': input_width,
#                'input_height': input_height
#            }
#            return self
#        
#        else:
#            transcoding_format = codec or input.format  #change to original format
#            dest_res_id = new_id()
#            dest_res_id = dest_res_id + '.' + transcoding_format
#            adapter_proxy = Proxy('Adapter')
#            d = adapter_proxy.adapt_image_magick('%s[0]' % input.ID, dest_res_id, argv)
#            log.debug('crop started')
##            d.addCallbacks()
#                
#class Resize(AdaptImage):
#    def _execute(self, input_id, argv, codec = None):
#        transcoding_format = codec   #change to original format
#        dest_res_id = new_id()
#        dest_res_id = dest_res_id + '.' + transcoding_format
#        adapter_proxy = Proxy('Adapter')
#        input_id = self.resource.component.ID        
#        d = adapter_proxy.adapt_image_magick('%s[0]' % input_id, dest_res_id, argv)       
#        self
#     
#    
#    def execute(self):
#                
#        input = self.resource.component
#        codec = input.format
#        input_id = self.resource.component.ID
#        argv = self.resource.get('argv', [])
#        input_width = self.resource.get('width')
#        input_height = self.resource.get('height')
#        if input.item.type.name == 'image':
#            max_width = min(self.params['max_width'],  input_width)
#            max_height = min(self.params['max_height'],  input_height)
#            argv +=  ['-resize', '%dx%d' % (max_width, max_height)]
#        
#        
#        
#            aspect_ratio = input_height/input_width 
#            alfa = min(self.params['max_width']/input_width, self.params['max_height']/input_height)
#            
#            self.resource.params['width'] = alfa*input_width
#            self.resource.params['height'] = alfa*input_height
#            self.resource.params['argv'] = argv
#                    
#            self.resource.do_action(self._execute, input_id, argv)
#      
#   
#        
#        
#       
#        return AdaptImageResource(self.resource.component)
#            
#       
#            
#    
#   
#
#    
#            
#         
#
#resource = Crop(Resize(Resource(orig), **params).execute(), **params).execute()
#resource.save(variant=  '')
##Pipeline(input = orig, output = ooo, actions = [Resize(**params),]   )
