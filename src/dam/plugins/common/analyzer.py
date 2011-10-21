import os
from twisted.python.failure import Failure
from dam.core.dam_repository.models import Type
from dam.variants.models import Variant
from dam.repository.models import get_storage_file_name
from dam.plugins.common.utils import get_source_rendition
from dam.plugins.common.cmdline import splitstring, import_cmd
from mediadart import log
from mediadart.storage import Storage
from mediadart.mqueue.mqclient_twisted import Proxy


class Analyzer:
    """
    Base class for all the plugins that execute a command over a rendition
    and parse the standard output to extract interesting information.
    """
    md_server = 'GenericCmdline'  # default value
    get_cmdline = None  # override to provide specialized behaviour
    parse_stdout = None # override to provide specialized behaviour
    cmdline = None      # string with the commandine to execute
    env = {}            # environment for the executioni
    cb_args = []        # additional arguments passed to handle_result
    item = None         # the item object identifyed by item_id
    source = None       # the source Component
    media_type = None   # the dam_repository.Type of the output Component
    fake = False        # set to have just the command line printed

    def __init__(self, deferred, workspace, item_id, source_variant_name):    
        if self.get_cmdline is None:
            raise Exception('Analyzer is an abstract base class: instantiate a derived class')
        self.deferred = deferred
        self._fc = Storage()
        self.workspace = workspace
        self.item, self.source = get_source_rendition(item_id, source_variant_name, workspace)

    def handle_result(self, result, *args):
        #log.debug('= handle_result %s' % str(result)[:128])
        try:
            return_value = self.parse_stdout(result['data'], *args)
            self.deferred.callback(return_value)
        except Exception, e:
            log.error('Error in %s: %s %s' % (self.__class__.__name__, type(e), str(e)))
            self.deferred.errback(e)
        
    def handle_error(self, result):
        self.deferred.errback(Failure(Exception(result.getErrorMessage())))

    def execute(self, **params):     
        # get basic data (avoid creating stuff in DB)
        try:
            self.get_cmdline(**params)
            args = splitstring(self.cmdline)
        except Exception, e:
            log.error('Error in %s: %s %s' % (self.__class__.__name__, type(e), str(e)))
            self.deferred.errback(e)
        else:
            if self.fake:
                log.debug('######### Command line:\n%s' % str(args))
            else:
                proxy = Proxy(self.md_server)
                d = proxy.call(self.remote_exe, args, self.env)
                d.addCallbacks(self.handle_result, self.handle_error, callbackArgs=self.cb_args)
        return self.deferred    # if executed stand alone

