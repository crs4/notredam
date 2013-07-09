import os
from uuid import uuid4
from config import Configurator
from utils import normpath
from . import log

class StorageError(Exception): pass

def new_id(filename=''):
    'returns a unique hex id, with the extension of filename attached if there is any'
    res_id = uuid4().get_hex()
    _, ext = os.path.splitext(filename)
    if ext:
        res_id = '%s%s' % (res_id, ext)
    return res_id
        

class Storage:
    def __init__(self):
        self.c = Configurator()
        self._root = os.path.normpath(self.c.get('STORAGE', 'cache_dir'))

    def exists(self, filename):
        if filename != None:
            return os.path.exists(self.abspath(filename))
        else:
            log.debug('inside MProcessor storage, method exists, filename is %s' % filename)
            return False

    def abspath(self, path, in_cache=False):
        """absolute path of path, relative to the cache_dir defined in mprocessor.cfg

        If the argument path is already an absolute path, returns it unchanged, unless
        in_cache = True. In this case raise an exception unless path points inside 
        cache_dir
        """
        if os.path.isabs(path):
            abs = path
        else:
            abs = os.path.abspath(os.path.join(self._root, path))
        abs = normpath(abs)
        if in_cache:
            if not abs.startswith(self._root):
                raise StorageError('%s is not under %s' % (abs, self._root))
        return abs

    def relpath(self, path, in_cache=False):
        """ This is the inverse of abspath
        """
        path = os.path.abspath(path)
        path = normpath(path)
        rel = os.path.relpath(path, self._root)
        if in_cache:
            if rel.startswith('..'):
                raise StorageError('%s is not under %s' % (path, self._root))
        else:
            return rel

if __name__=='__main__':
    if not os.path.isdir('/tmp/prova'):
        os.mkdir('/tmp/prova')
    fc=Storage()
    print fc.abspath('est/prova')
