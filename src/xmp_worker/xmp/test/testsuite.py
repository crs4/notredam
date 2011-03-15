# This is a simple test, 

# Assume  that the server is already up

import time
import os
import subprocess
from mediadart.storage import Storage
from mediadart.mqueue.mqclient_async import Proxy


# launch server in another window FROM THIS DIRECTORY


p = Proxy('XMPEmbedder')
print p.ping()

def show_output(status_ok, result, userargs ):
    if status_ok:
        print '**** RESULT OK ****'
        print result
    else:
        print '*** ERROR ***'
        print result


p = Proxy('XMPEmbedded', show_output)
p.metadata_synch('BlueSquare',  {u'http://purl.org/dc/elements/1.1/': {u'title': {'xpath': [], 'is_array': u'alt', 'type': u'lang', 'qualifier': [u'it-IT', u'en-US'], 'value': [u'il mio titolo', u'my title']}}} )



