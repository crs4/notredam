from libxmp import XMPFiles
from twisted.internet import reactor
from mediadart import log
from mediadart.config import Configurator
from mediadart.storage import Storage
from mediadart.mqueue.mqserver import MQServer, RPCError
from mediadart.utils import default_start_mqueue


class XMPExtractor(MQServer):
    _id = 'urn:uuid:a7da26e7-f37b-4c88-a80a-3f46b58f1fa9'   # required by jsonrpc

    def __init__(self):
        MQServer.__init__(self)
        self._fc = Storage()

    def mq_extract(self, infile):
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
        
def start_server():
    default_start_mqueue(XMPExtractor, [])

if __name__=='__main__':
    import sys
    start_server(
        '127.0.0.1',
        5672,
        'guest',
        'guest',
        )
    reactor.run()
