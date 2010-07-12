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

from httplib import HTTPSConnection
from urllib2 import HTTPSHandler

import os
import md5
import hashlib,random
import urllib2
import urllib
import httplib
import socket
 
class fake_logger():
	def debug(*args):
		pass
		
def get_logger(path,log= None):
	return fake_logger()
#from configuration import conf
import threading

logger = get_logger("upload")



#class KeyCertHTTPSConnection(httplib.HTTPSConnection):
#    
#    def connect(self):
#        self.key_file = conf["client_key"] 
#        self.cert_file = conf["client_certificate"]
##        logger.debug("CHIAMATO connect() di KeyCertHTTPSConnection:")
##        logger.debug("Key File:%s" % self.key_file)
##        logger.debug("Cert File:%s" % self.cert_file)
#        httplib.HTTPSConnection.connect(self)
#         
#        
#    
#class ConnectHTTPSHandler(urllib2.HTTPSHandler):
#    
##    def https_open(self, req):
##            return self.do_open(KeyCertHTTPConnection, req)
#
#    def do_open(self, http_class, req):
#         
#        return urllib2.HTTPSHandler.do_open(self,KeyCertHTTPSConnection, req)
#



class AsyncFileSplitter:

   def __init__(self, filename, res_id, chunks, chunk_size, url,logger=None):

       self.chunks = chunks
       self.filename = filename.encode()
       self.chunk_size = chunk_size
       self.res_id = res_id.encode()
       self.url = url
       self.logger = logger
       if self.logger!=None:
           self.logger.debug("Istanziato AsyncFileSplitter su risorsa %s" % res_id)
       
       
   def create_chunks(self):
       #print "in create chunks di file splitter"
       self.logger.debug("called create chunks")
       self.logger.debug("In __create_chunk: filename:%s" % self.filename)
       self.logger.debug("Chunk size:%s" % self.chunk_size)
       self.logger.debug("Chunks:%s" % self.chunks)
       fsize = os.path.getsize(self.filename)
       self.logger.debug("file size:%s" % fsize)
       f = open(self.filename, 'rb')
       #self.logger.debug("File:%s" % f)
       chunk_params = []
       start_len = []

       cur_start = 0
       for i in range(self.chunks):
           #print "Creating chunk:%s " % i

           if fsize - (i*self.chunk_size) > self.chunk_size:
               remaining_data = self.chunk_size
           else:
               remaining_data = fsize - (i*self.chunk_size)

           start_len.append((cur_start,remaining_data))
           cur_start+=remaining_data

           data = f.read(remaining_data)
           
           md5_chunk = md5.new(data).hexdigest()

           #print md5_chunk, i

           chunk_params.append({ "md5_chunk" : md5_chunk, "chunk" : str(i), "filename" : self.filename  })
       #self.logger.debug("Prima di chiudere il file")
       f.close()
       #self.logger.debug("Dopo il file") 
       #print "CHUNK_PARAMS:%s START_LEN=%s" % (chunk_params,start_len)
       #self.logger.debug("Alla uscita di __create_chunks")
       return (chunk_params,start_len)


class ChunkStatus:
    (SENDING_FAILED,NOTHING_TO_SEND,READY_TO_SEND,SENDING_REQUEST,SENDING_OK) = (-1,0,1,2,3)



class StandardUploader:
    
    
   def __init__(self,filename, upload_dict, log_path="./"):
        
       self.job_id = upload_dict['job_id']      
       
       #self.uploader_url = "https://%s:%s/" % (self.storage.get_node_ip(),self.storage.get_node_port())
       #self.uploader_url = node_url
       self.filename= filename
       self.id = upload_dict['res_id']
        
       self.fsize = os.path.getsize(self.filename)
       self.extension = os.path.splitext(self.filename)[-1]
        
       self.file_url = None
       self.chunks_info = None
       self.num_chunks = upload_dict['chunks']
       self.chunk_size = upload_dict['chunk_size']
       self.file_url = "http://%s:%s/upload/%s/" % (upload_dict['ip'], upload_dict['port'], upload_dict["unique_key"])

       self.cur_chunk = 0
       
       self.__setup_made = False
       self.chunk_states = []
       self.num_fails = 0
       self.MAX_FAILURES = 5
       self._current_uploadings = 0
       self.logger = get_logger(log_path,"uploader")
       self.internal=False
       self.client_coords= '' 
       self.replicability = 0
       self.logger.debug("Registering uploader Job:%s" %self.job_id)
    
       #self.__setup_chunks()
       
       
   def get_resource_id(self):
       return self.id
   
 
   def __setup_chunks(self):
       self.logger.debug("in __setup_chunks")
       try:    
           
          """
          {'chunk_size': 131072,
             'chunks': 1,
             'id': '928ce7ae214edabfb5443496aad60adae0d84983',
             'ip': '127.0.0.1',
             'job_id': '4d1ac6a7ffe64e49ff3ef0e63e82bc4e9d94c4aa',
             'port': '13000',
             'service_load': 0,
             'unique_key': 'f8e1e45666294767be1a7f27cc50fe3e430b134e'}

          """
          #self.file_url =  "http://%s:%s/upload/%s/"  %   (upload_dict["ip"],upload_dict["port"],upload_dict["unique_key"])
          #self.file_url = 
          #self.logger.debug("URL PER UPLOAD:%s" % self.file_url)
          check_md5 = False
          self.logger.debug("Richiamo storage.get_upload_url con replicability:%s" % self.replicability)
          #print "Richiamo storage.get_upload_url da uploader..."
          #upload_dict = self.storage.get_upload_url(self.id, check_md5, self.fsize,self.extension,self.internal,self.client_coords,self.replicability)
          #print "get_upload_url richiamato."
          #print "UPLOAD_DICT:%s" % upload_dict
          #self.num_chunks = upload_dict["chunks"]
          #chunk_size = upload_dict["chunk_size"]
          #self.file_url = os.path.join(self.uploader_url,"upload/%s/" % upload_dict["unique_key"])
          #self.file_url = "http://%s:%s/upload/%s/" % (upload_dict['ip'], upload_dict['port'], upload_dict["unique_key"])
          
          #print "FILE URL:%s" %  self.file_url
          self.logger.debug("FILE_URL:%s" % self.file_url)
          async_splitter = AsyncFileSplitter(self.filename, self.id,self.num_chunks, self.chunk_size,self.file_url, self.logger)
          self.logger.debug("FILE_Splitter instanziato")
          #print "File splitter instanziato"
          # creazione dei chunk
         
          self.chunks_info = async_splitter.create_chunks();
          #print "File splitter instanziato"
          self.logger.debug("Info sui chunk creati\n")
          #self.logger.debug("Informazioni sui chunks", self.chunks_info)
          #print "Chunks:" ,self.chunks_info
          self.chunk_states = self.num_chunks*[ChunkStatus.READY_TO_SEND]
          #print "esco da setup chunks"
          #defer.returnValue(chunks_info)
       except Exception,ex:
           #self.logger.error("Error connecting to the server (%s). Retry..." % ex)
           self.logger.error("errore di connessione al server:%s" % ex)
        
           
        

  
   def upload_next_chunk(self):
       """
       @return: ChunkStatus 
       """
       self.logger.debug("EFFETTUATA CHIAMATA A upload_next_chunk")
       #print "EFFETTUATA CHIAMATA A upload_next_chunk"
       
       if not self.__setup_made:
           self.__setup_made = True
           self.logger.debug("Richiamato setup chunks da upload_next_chunk")
           self.__setup_chunks()
       else:
           self.logger.debug("self.__setup_made=True")
                
            
           
       #self.logger.debug("In upload next chunk... self.chunks_info=%s" % self.chunks_info)
       if self.chunks_info==None:
           return ChunkStatus.SENDING_FAILED
                 
       if self.is_file_uploaded() or self.cur_chunk<0 or self.num_fails>=self.MAX_FAILURES:
           self.logger.debug("Nulla da spedire: cur_chunk:%s" % self.cur_chunk)
           return ChunkStatus.NOTHING_TO_SEND
       
       chunk_to_upload = self.cur_chunk
        
       upChunk = AsyncChunkUploader(self.file_url,self.filename,self.chunks_info,self.file_url, chunk_to_upload,self.logger)
       self.chunk_states[chunk_to_upload]= ChunkStatus.SENDING_REQUEST
       
       #self.logger.debug("uploading chunk %s of %s" % ( chunk_to_upload, self.num_chunks))
       #self.logger.debug("upChunk:%s" % upChunk)
       self._current_uploadings+=1
       result = upChunk.upload_chunk()
       self.logger.debug("Risultato upload chunk %s:%s" % (chunk_to_upload,result))
       if result:
           self.chunk_send_ok(chunk_to_upload)
       else:
           self.chunk_send_failed(chunk_to_upload)
    
       # considero il prossimo chunk da spedire (sicuramente almeno uno e' ancora da spedire)
       next_chunk = (chunk_to_upload +1) % self.num_chunks 
       # il prossimo chunk potrebbe essere gia in fase di spedizione
       self.cur_chunk =  self.get_next_chunk_index(next_chunk) 
       #self.logger.debug("Prossimo chunk da uploadare:%s" % self.cur_chunk)
       if result:
           return ChunkStatus.SENDING_OK
       else:
           return ChunkStatus.SENDING_FAILED 
       
       
   def restart_sending(self):
       self.logger.warning("Failed %s sending. Restarting sending on a new node."  % self.num_fails)
       self.num_fails = 0
       self._current_uploadings = 0
       self.__setup_made = False
       self.chunks_to_send = True
       
   
   def get_next_chunk_index(self,cur_chunk):
       return self.__get_next_chunk_index(cur_chunk)
        
  
   def __get_next_chunk_index(self,cur_chunk):
       # si e' spedito tutto
       c = cur_chunk
       while self.chunk_states[cur_chunk]==ChunkStatus.SENDING_OK or self.chunk_states[cur_chunk]==ChunkStatus.SENDING_REQUEST:
           cur_chunk = (cur_chunk +1) % self.num_chunks 
           if cur_chunk==c:
               # sono stati tutti spediti
               return -1
       return cur_chunk
            
       
       
           
   def is_file_uploaded(self):
       somma = sum(self.chunk_states)
       exp = self.num_chunks*ChunkStatus.SENDING_OK 
       self.logger.debug("SOMMA:%s PER FINIRE:%s"  % (somma,exp) )
       return somma==exp
   
   
   def is_upload_failed(self):
       somma = sum(self.chunk_states)
       return somma== ChunkStatus.SENDING_FAILED*self.num_chunks
           
    
   def chunk_send_ok(self,cur_chunk):
        
       self._current_uploadings-=1
       self.logger.debug( "Ok sending chunk: %s (current up: %s) " % (cur_chunk, self._current_uploadings))
       self.logger.debug( "SUCCESS")
       self.chunk_states[cur_chunk]=ChunkStatus.SENDING_OK
       
   
   def chunk_send_failed(self,cur_chunk):
       #print "send failed???", failed
       self._current_uploadings-=1
        
       self.logger.error( "FAILED sending chunk: %s " % cur_chunk)
       self.chunk_states[cur_chunk]=ChunkStatus.SENDING_FAILED
       self.num_fails+=1
       if self.logger!=None:
           self.logger.warning("Failing n.%d" % self.num_fails)
       if self.num_fails>=self.MAX_FAILURES:
           self.restart_sending()
           
   def get_current_uploadings(self):
       return self._current_uploadings

   def asyncUpload(self):
       #print "Starting upload thread"
       threading.Thread(target=self.__uploadFileThread).start()

   def __uploadFileThread(self):
         
       result = self.upload_next_chunk()
       
       while (result!=ChunkStatus.NOTHING_TO_SEND):
           result = self.upload_next_chunk()
           #print "Uload chunk:%s" % str(result)
           self.logger.debug("Uploading Chunk:%s totFails:%s" % (result, self.num_fails))
    
       #print "Fine operazione upload"
       if self.is_file_uploaded():
           self.file_uploaded()
       else:
           self.file_not_uploaded("FAILED uploading:%s" % str(self.chunk_states))
           
       self.logger.debug("Exiting from uploadFileThread")
       #threads.deferToThread(self.uploadFile)
       

   def uploadFile(self):
       #uploader_url = 'http://127.0.0.1:13003/uploader/'
       # invio dei chunk
       if self.chunks_info==None:
           self.logger.debug("IN UPLOAD FILE: chunk_info nullo... %s" % self.chunks_info)
            
           self.__setup_chunks()
           
       self.logger.debug("NUM CHUNKS:%s" % self.num_chunks)
      
       for i in range(self.num_chunks):
           upChunk = AsyncChunkUploader(self.file_url,self.filename,self.chunks_info,self.file_url,i,self.logger)
           self.logger.debug("uploading chunk %s of %s: %s" % (i, self.num_chunks, self.file_url))
           result = upChunk.upload_chunk()
        
           self.logger.debug("Spedizione Chunk:%s:%s" % (i,result))
           
       if self.is_file_uploaded():
           self.file_uploaded()
       else:
           self.file_not_uploaded("FAILED uploading:%s" % str(self.chunk_states))
           
       self.logger.debug("Exiting from uploadFile")
        

   def file_uploaded(self):
       #print "File uploadato con successo"
       self.logger.debug("FILE UPLOADING END.")
       
   
   def file_not_uploaded(self,failure):
       self.logger.debug("FILE UPLOADING FAILED:%s" % failure)
       #print "Upload ok!"
       #reactor.stop()
           

    

class AsyncChunkUploader:

   def __init__(self, uploader_chunk_url,filename, info, url, num_chunk,logger):
       #print "INFO IN CHUNK UP:%s :::: %s " % info
       self.chunk_params = info[0][num_chunk]
       self.start_len = info[1]
       self.url = "%s%s/" % (uploader_chunk_url, num_chunk)
       #print "UPLOADER CHUNK URL=%s" % self.url
       self.filename =  filename
       self.start = self.start_len[num_chunk][0]
       self.len =  self.start_len[num_chunk][1]
       self.logger = logger
       #print "Chunk:%s from: %s len: %s " % (num_chunk,self.start,self.len)



   def __encodeForm(self, inputs):

       lines = []
       file_handle = open(inputs["filename"], "rb")
       file_handle.seek(self.start)
       lines.append(file_handle.read(self.len))
       file_handle.close()

       return '\r\n'.join(lines)
   

   def chunkSend(self,success):
       self.logger.debug("Chunk uploadato")
    
   def handleError(self,failure):
       #print "Errore..."
       self.logger.debug("Error:%s" % failure.getErrorMessage())
       #reactor.stop()


   def upload_chunk(self):
       try:
    #       self.chunk_params['upload_file'] = fileToCheck
           self.logger.debug("UPLOADING CHUNK TO URL::%s" % self.url)
           #self.logger.debug("In upload chunk prima di __encodeForm")
           form = self.__encodeForm(self.chunk_params)
           self.logger.debug("In upload chunk dopo di __encodeForm")
           
           
           #clientCtxFactory = ssl.DefaultOpenSSLContextFactory(client_key, client_certificate)
    
    #       postRequest=client.getPage(self.url, 
    #                                  contextFactory=clientCtxFactory,
    #                                  method='POST',
    #                                  headers={'Content-Type': 'application/octet-stream',
    #                                           'Content-Length':str(len(form))},
    #                                           postdata=form)
    #
           post_headers = {'Content-Type': 'application/octet-stream',
                           'Content-Length':str(len(form))
                           }
          
           self.logger.debug("opening urllib2 handlers..")
           self.logger.debug("URL DI DESTINAZIONE:%s" % self.url)
           #ConnectHTTPSHandler
           opener = urllib2.build_opener()
           #opener = urllib2.build_opener(HTTPSHandler)
           urllib2.install_opener(opener)
            
           postRequest=urllib2.Request(self.url, data=form, headers=post_headers)
           response = urllib2.urlopen(postRequest)
           self.logger.debug("Uploaded chunk...post Request:%s" % postRequest)
           self.logger.debug("response:%s" % response)
           return True
       except Exception, ex:
           self.logger.error(ex)
           return False

class SimpleUploader:
    def __init__(self, workspace_id, item_id, variant_id, filename):
        self.item_id = item_id
        self.variant_id = variant_id
        self.filename = filename
        self.workspace_id = workpace_id
		
    def uploadFile(self):
        pass
    