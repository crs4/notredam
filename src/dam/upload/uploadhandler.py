"""
Base file upload handler classes, and the built-in concrete subclasses
"""

from django.core.files.uploadhandler import FileUploadHandler
from django.core.files.uploadedfile import UploadedFile

import shutil
import os

class StorageUploadedFile(UploadedFile):
    """
    A file uploaded to a temporary location (i.e. stream-to-disk).
    """
    def __init__(self, name, content_type, size, charset):
        from mediadart.storage import new_id
        from django.conf import settings
        res_id = new_id()
        fpath = os.path.join(settings.MEDIADART_STORAGE, res_id)
        file = open(fpath, 'wb')
        super(StorageUploadedFile, self).__init__(file, name, content_type, size, charset)

    def rename(self, ext):
        self.file.close()        
        new_name = self.file.name + ext
        print self.file.name, new_name
        shutil.move(self.file.name, new_name)
        self.file = open(new_name, 'r')
        
    def get_filename(self):
        return self.file.name

    def close(self):
        try:
            return self.file.close()
        except OSError, e:
            print e
            if e.errno != 2:
                raise

class StorageHandler(FileUploadHandler):
    """
    Upload handler that streams data into a storage file.
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

