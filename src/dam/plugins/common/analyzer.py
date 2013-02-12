import os
from dam.core.dam_repository.models import Type
from dam.variants.models import Variant
from dam.repository.models import get_storage_file_name
from dam.plugins.common.utils import get_source_rendition
from dam.plugins.common.cmdline import splitstring, import_cmd
from mprocessor import log
from mprocessor.storage import Storage
from dam.mprocessor.servers import generic_cmd


class Analyzer:
    """
    Base class for all the plugins that execute a command over a rendition
    and parse the standard output to extract interesting information.
    """
    get_cmdline = None  # override to provide specialized behaviour
    parse_stdout = None # override to provide specialized behaviour
    cmdline = None      # string with the commandine to execute
    env = {}            # environment for the executioni
    item = None         # the item object identifyed by item_id
    source = None       # the source Component
    media_type = None   # the dam_repository.Type of the output Component
    fake = False        # set to have just the command line printed

    def __init__(self, workspace, item_id, source_variant_name):    
        if self.get_cmdline is None:
            raise Exception('Analyzer is an abstract base class: instantiate a derived class')
        self._fc = Storage()
        self.workspace = workspace
        self.item, self.source = get_source_rendition(item_id, source_variant_name, workspace)

    def handle_result(self, result, *args):
        #log.debug('= handle_result %s' % str(result)[:128])
        try:
            return self.parse_stdout(result['data'], *args)
        except Exception, e:
            log.error('Error in %s: %s %s' % (self.__class__.__name__, type(e), str(e)))
            raise

    def execute(self, **params):     
        # get basic data (avoid creating stuff in DB)
        try:
            self.get_cmdline(**params)
            args = splitstring(self.cmdline)
        except Exception, e:
            log.error('Error in %s: %s %s' % (self.__class__.__name__, type(e), str(e)))
            raise
        else:
            if self.fake:
                log.debug('######### Command line:\n%s' % str(args))
            else:
                result = generic_cmd.call.delay(self.remote_exe,
                                                args, self.env).get()
                return self.handle_result(result)

