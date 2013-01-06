from libxmp import XMPFiles
from mprocessor import log
from mprocessor.config import Configurator
from mprocessor.storage import Storage


class XMPExtractor(object):
    def __init__(self):
        self._fc = Storage()

    def extract(self, infile):
        """ extract the requested feature and returns a dictionary of extracted features """
        infile = self._fc.abspath(infile)
        d = {}
        try:
            xmpfile = XMPFiles(file_path=infile)
            xmp = xmpfile.get_xmp()
            for x in xmp:            
                if x[-1]['IS_SCHEMA']:
                    d[x[0]] = []
                else:
                    d[x[0]].append(x[1:])
            xmpfile.close_file()
            XMPFiles.terminate()
        except:
            pass
        return d

###############################################################################
# Celery task setup
from celery.task import task as celery_task
_SERVER_SINGLETON = XMPExtractor()
@celery_task
def extract(infile):
    return _SERVER_SINGLETON.extract(infile)
