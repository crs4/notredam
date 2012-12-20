import os
from ConfigParser import SafeConfigParser

class ConfiguratorError(Exception): pass

# this is the singleton
_theConfigurator = None

class Configurator(SafeConfigParser, object):
    def __new__(cls):
        "make the configurator a singleton"
        global _theConfigurator
        if _theConfigurator is None:
            _theConfigurator = super(Configurator, cls).__new__(cls)
            _theConfigurator.__initialized = False
        return _theConfigurator

    def __init__(self):
        if not self.__initialized:
            global _theConfigurator
            super(Configurator, self).__init__()
            self.__read = self.read(self.build_cfg_list())
            if len(self.__read) == 0:
                _theConfigurator = None
                raise ConfiguratorError('no configuration found')
            self.__initialized = True
            if self.getboolean('CONFIG', 'search_cur_dir'):
                self.__read.extend(self.read('./mprocessor.cfg'))

    def cfg_from_dir(self, dirname):
        """Returns the list of configuration files, first those called mprocessor.cfg,
           then other *.cfg files"""
        files = []
        mainfile = os.path.join(dirname, 'mprocessor.cfg')
        if os.path.exists(mainfile):
            files.append(mainfile)
        others = [os.path.join(dirname, x) for x in os.listdir(dirname) 
                        if x.endswith('.cfg') and x != 'mprocessor.cfg']
        others.sort()
        files.extend(others)
        return files

    def get_cfg_dirs(self):
        """Return the list of directories where to look for configuration files"""
        ret = ['/etc/notredam']
        if 'HOME' in os.environ:
            ret.append(os.path.join(os.environ['HOME'], '.notredam'))
        return ret

    def build_cfg_list(self):
        cfgfiles = []
        for d in self.get_cfg_dirs():
            if os.path.exists(d):
                cfgfiles.extend(self.cfg_from_dir(d))
        return cfgfiles

    def get_files(self):
        return self.__read

    def reload(self):
        self.__read = self.read(self.build_cfg_list())


