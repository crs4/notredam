from actions import BaseAction, new_id
from mediadart.mqueue.mqclient_twisted import Proxy
from mediadart import log

class Crop(BaseAction):
    def execute(self, save_as = None, codec = None):
        input = self.get_input()
        if isinstance(input, Component):            
            argv = []
            input_width = input.width
            input_height = input.height
        else:
            tmp = self.input.get_ouput()
            argv = tmp['argv']
            input_width = tmp['input_width']
            input_height = tmp['input_height']
        
            if self.params.get('ratio'):
                x_ratio, y_ratio = self.params['ratio'].split(':')
                y_ratio = int(y_ratio)
                x_ratio = int(x_ratio)
                final_width = min(input_width, input_height*x_ratio/y_ratio)
                final_height = final_width*y_ratio/x_ratio
                log.debug('ratio=(%s,%s), final(h,w)=(%s, %s), original(h,w)=(%s, %s)'%(
                       x_ratio, y_ratio, final_height, final_width, input_height, input_width))
                ul_y = (input_height - final_height)/2
                ul_x = 0
                lr_y = ul_y + final_height
                lr_x = final_width 
            else:
                lr_x = int(int(self.params['lowerright_x'])*component.source.width/100)
                ul_x = int(int(self.params['upperleft_x'])*component.source.width/100)
                lr_y = int(int(self.params['lowerright_y'])*component.source.height/100)
                ul_y = int(int(self.params['upperleft_y'])*component.source.height/100)
            
            input_width = lr_x -ul_x 
            input_height = lr_y - ul_y
            log.debug('orig(h,w)=(%s, %s)' % (input_height, input_width))
            argv +=  ['-crop', '%dx%d+%d+%d' % (input_width, input_height,  ul_x, ul_y)]
            log.debug('argv %s'%argv)
            
            if not save_as: 
                self._output = {
                    'argv': argv,
                    'input_width': input_width,
                    'input_height': input_height
                }
                return self
            
            else:
                transcoding_format = codec or input.format  #change to original format
                dest_res_id = new_id()
                dest_res_id = dest_res_id + '.' + transcoding_format
                adapter_proxy = Proxy('Adapter')
                d = adapter_proxy.adapt_image_magick('%s[0]' % input.ID, dest_res_id, argv)
                
class Resize(BaseAction):
    def execute(self, save_as = None, codec = None):
        input = self.get_input()
        if isinstance(input, Component):            
            argv = []
            input_width = input.width
            input_height = input.height
            
        else:
            tmp = self.input.get_ouput()
            argv = tmp['argv']
            input_width = tmp['input_width']
            input_height = tmp['input_height']            
        
        if item.type.name == 'image':
            max_width = min(self.params['max_width'],  input_width)
            max_height = min(self.params['max_height'],  input_height)
            argv +=  ['-resize', '%dx%d' % (max_width, max_height)]
                
        if not save_as: 
            #computing some data for other actions like crop
            aspect_ratio = input_height/input_width 
            alfa = min(self.params['max_width']/input_width, self.params['max_height']/input_height)
            input_width = alfa*input_width
            input_height = alfa*input_height
            self._output = {
                'argv': argv,
                'input_width': input_width,
                'input_height': input_height
            }
            return self
        else:
            transcoding_format = codec or input.format  #change to original format
            dest_res_id = new_id()
            dest_res_id = dest_res_id + '.' + transcoding_format
            adapter_proxy = Proxy('Adapter')
            d = adapter_proxy.adapt_image_magick('%s[0]' % input.ID, dest_res_id, argv)
            
                
Crop(Resize(orig, **params).execute(), **params).execute(save_as = '', format = '')
Pipeline(input = orig, output = ooo, actions = [Resize(**params),]   )