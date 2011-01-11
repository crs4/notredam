"""
File upload handler classes
"""

from django.core.files.uploadhandler import FileUploadHandler, MemoryFileUploadHandler
from django.core.files.uploadedfile import UploadedFile
import logger
import shutil
import os

class StorageUploadedFile(UploadedFile):
    """
    An uploaded file will be saved to the mediaDART storage location
    """
    def __init__(self, name, content_type, size, charset):
        from mediadart.storage import new_id
        from django.conf import settings
        res_id = new_id()
        fpath = os.path.join(settings.MEDIADART_STORAGE, res_id)
        file = open(fpath, 'wb')
        super(StorageUploadedFile, self).__init__(file, name, content_type, size, charset)

    def rename(self):

        fname, ext = os.path.splitext(self.name)

        self.file.close()
        new_name = self.file.name + ext
        shutil.move(self.file.name, new_name)
        self.file = open(new_name, 'r')
        
    def get_filename(self):
        return self.file.name
        
    def get_res_id(self):
        uploaded_fname = self.get_filename()
        path, res_id = os.path.split(uploaded_fname)    
        
        return res_id

    def close(self):
        try:
            return self.file.close()
        except OSError, e:
            print e
            if e.errno != 2:
                raise

class StorageHandler(FileUploadHandler):
    """
    Upload handler that streams data into a file.
    """
    def __init__(self, *args, **kwargs):
        super(StorageHandler, self).__init__(*args, **kwargs)

    def new_file(self, file_name, *args, **kwargs):
        """
        Create the file object to append to as data is coming in.
        """
        super(StorageHandler, self).new_file(file_name, *args, **kwargs)
        self.file = StorageUploadedFile(self.file_name, self.content_type, 0, self.charset)

    def receive_data_chunk(self, raw_data, start):
        self.file.write(raw_data)

    def file_complete(self, file_size):
        self.file.seek(0)
        self.file.size = file_size
        return self.file



from django.core.files.uploadhandler import FileUploadHandler
from django.core.cache import cache
"from http://code.google.com/p/django-multi-file-uploader/"
class UploadProgressCachedHandler(FileUploadHandler):
    """
    Tracks progress for file uploads.
    The http post request must contain a header or query parameter, 'X-Progress-ID'
    which should contain a unique string to identify the upload to be tracked.
    """

    def __init__(self, request=None):
        super(UploadProgressCachedHandler, self).__init__(request)
        self.progress_id = None
        self.field_name = None
        self.cache_key = None
        self.received = 0
        self.length = 0

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        if 'X-Progress-ID' in self.request.GET and content_length > 0:
            self.progress_id = self.request.GET['X-Progress-ID']
            self.length = content_length

    def new_file(self, field_name, file_name, content_type, content_length, charset=None):
        if self.progress_id:
            self.cache_key = "%s_%s_%s" % (self.request.META['REMOTE_ADDR'], self.progress_id, field_name)
            cache.set(self.cache_key, 0)

    def receive_data_chunk(self, raw_data, start):
        self.received += self.chunk_size
        if self.cache_key:
            p = min(100, int(100 * self.received / self.length))
            cache.set(self.cache_key, p)
        return raw_data
   
    def file_complete(self, file_size):
        if self.cache_key:
            cache.set(self.cache_key, 100)

    def upload_complete(self):
        pass


