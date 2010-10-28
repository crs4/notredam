import os
import sys
import subprocess
from uuid import uuid4
from distutils.core import setup, Command, DistutilsOptionError
from distutils.command.install import install as _install
from distutils.file_util import move_file
from distutils.dir_util import mkpath
from shutil import copyfile

# The python packages that this setup is going to install
package_list = [
'dam',
'dam/admin',
'dam/api',
'dam/api/django_restapi',
'dam/appearance',
'dam/application',
'dam/basket',
'dam/core',
'dam/core/dam_metadata',
'dam/core/dam_repository',
'dam/core/dam_tree',
'dam/core/dam_workspace',
'dam/eventmanager',
'dam/geo_features',
'dam/metadata',
'dam/mprocessor',
'dam/preferences',
'dam/repository',
'dam/scripts',
'dam/treeview',
'dam/upload',
'dam/variants',
'dam/workflow',
'dam/workspace',
]

package_data = {
'dam/workspace': ['fixtures/initial_data.json'],
'dam/appearance': ['fixtures/initial_data.json'],
'dam/metadata': ['fixtures/initial_data.json'],
'dam/scripts': ['fixtures/initial_data.json'],
'dam/eventmanager': ['fixtures/initial_data.json'],
'dam/variants': ['fixtures/initial_data.json'],
'dam/core/dam_repository': ['fixtures/initial_data.json'],
'dam/core/dam_metadata': ['fixtures/initial_data.json'],
'dam': ['fixtures/initial_data.json', 'LICENSE.TXT', ],
'dam/treeview': ['fixtures/initial_data.json'],
'dam/preferences': ['fixtures/initial_data.json'], 
}

# Names of required debian packages. Each entry specifies:
# <package_name>  <list of args of apt-get install (version numbers etc.)>
debian_packages = [
'python-django=1.1*',
'python-egenix-mxdatetime',
]

# list of <tarfile>, <unpacked directory, None if unpacks in curdir>, <install_command>
tarfiles = [
# ('python-txamqp_0.3.tgz', 'python-txamqp-0.3', ['sudo', 'python', 'setup.py', 'install']),
]

#############################################################################################3


#
# Utility functions
#
def _run(cmdline, as_root, failures):
    if as_root:
        cmdline.insert(0, 'sudo')
    ret = subprocess.call(cmdline)
    if ret > 0:
        failures.append('Error executing %s' % ' '.join(cmdline))
    return ret

def _install_tar(failures):
    "install the tarballs"
    curdir = os.getcwd()
    for tarfile, topdir, exe in tarfiles:
        print ('\n######## Installing %s' % tarfile)
        clean_up = topdir and not os.path.exists(topdir)  # delete new directories
        _run(['tar', 'xvzf', tarfile], 1, failures)
        if topdir and os.path.exists(topdir):
            os.chdir(topdir)
            _run(exe, 1, failures)
        os.chdir(curdir)
        if clean_up:
            print 'Removing %s' % topdir
            _run(['rm', '-rf', topdir], 1, failures)


def _install_debian(failures):
    "install the debian packages"
    response = raw_input('\nDependencies:%s%s\nInstall? (y/N): ' % (
          '\n - '.join([''] + debian_packages), '\n - '.join([''] + [x[0] for x in tarfiles])))
    if not response or response.lower().startswith('n'):
        print('Aborting installation of dependencies')
        return
    for pkg in debian_packages:
        print ('\n Installing %s' % pkg)
        _run(['apt-get', 'install', pkg], 1, failures)
    _install_tar(failures)

def _install_scripts(destination, scripts, failures):
    for script in scripts:
        filename = os.path.basename(os.path.normpath(script))
        target = os.path.join(destination, filename)
        ret = _run(['cp', '-f', script, target], 1, failures)
        if ret == 0:
            _run(['chmod', '555', target], 1, failures)

def _adapt_cfg(cfgroot, as_root, source_cfg, target_cfg, failures):
    """rewrite cache_dir in the file that configures mediadart for notredam.
    
    target_cfg must be writable
    """
    if not os.path.exists(cfgroot):
        raise DistutilsModuleError('Missing mediadart configuration directory: %s' % self.cfgroot)
    tmpfilename = os.path.join(os.sep, 'tmp', uuid4().get_hex())
    tmpfile = open(tmpfilename, 'w')
    with open(source_cfg, 'r') as f:
        for line in f:
            parsed = [x.strip() for x in line.split('=')]
            if len(parsed) == 2 and parsed[0] == 'cache_dir':
                if as_root:
                    value = '/var/spool/notredam'
                else:
                    value = '/tmp/notredam'
                _run(['mkdir', '-p', value], as_root, failures)
                tmpfile.write('%s=%s\n' % (parsed[0], value))
            else:
                tmpfile.write(line)
    tmpfile.close()
    print('writing %s' % target_cfg)
    _run(['mv', '-f', tmpfilename, target_cfg], 1, failures)

def _print_errors(failures):
    if failures:
        print >>sys.stderr, '\n### Errors during installation:'
        print >>sys.stderr, '\n'.join(failures)

#
# Custom commands
#
class install(_install):
    user_options = _install.user_options + [ 
              ('settings=', None, 'can specify default-dev, default, or mqsql'),
              ('cachedir=', None, 'path of the shared filesystem'),]
    
    def initialize_options(self):
        _install.initialize_options(self)
        self.cachedir = None
        self.settings = None
        self.as_root = 1
        self.cfgroot = os.path.join(os.sep, 'etc', 'mediadart')

    def finalize_options(self):
        _install.finalize_options(self)
        if not self.settings or self.settings == 'default.dev':
            self.settings_module = os.path.join('dam', 'settings.py.default.dev')
        elif self.settings == 'default':
            self.settings_module = os.path.join('dam', 'settings.py.default')
        elif self.settings == 'mysql':
            self.settings_module = os.path.join('dam', 'settings.py.mysql')
        else:
            raise DistutilsOptionError('Invalid value for --settings: %s' % self.settings)

    def _adapt_cfg(self, source_cfg, target_cfg, failures):
        """rewrite cache_dir in the file that configures mediadart for notredam.
        
        target_cfg must be writable
        """
        if not os.path.exists(self.cfgroot):
            raise DistutilsModuleError('Missing mediadart configuration directory: %s' % self.cfgroot)
        tmpfilename = os.path.join(os.sep, 'tmp', uuid4().get_hex())
        tmpfile = open(tmpfilename, 'w')
        with open(source_cfg, 'r') as f:
            for line in f:
                parsed = [x.strip() for x in line.split('=')]
                if len(parsed) == 2 and parsed[0] == 'cache_dir':
                    value = self.cachedir
                    _run(['mkdir', '-p', value], self.as_root, failures)
                    tmpfile.write('%s=%s\n' % (parsed[0], value))
                else:
                    tmpfile.write(line)
        tmpfile.close()
        print('writing %s' % target_cfg)
        _run(['mv', '-f', tmpfilename, target_cfg], 1, failures)

    def run(self):
        failures = []
        _install_debian(failures)
        if self.as_root:
            _install.run(self)
        if os.path.exists(os.path.join('dam', 'settings.py')):
            os.unlink(os.path.join('dam', 'settings.py'))
        self.copy_file(self.settings_module, os.path.join(self.install_purelib, 'dam', 'settings.py'))
        self.copy_file(self.settings_module, os.path.join('dam', 'settings.py'))
        if self.install_purelib != os.path.dirname(os.path.abspath(__file__)):
            self.copy_tree(os.path.join('dam', 'files'), os.path.join(self.install_purelib, 'dam', 'files'))
            self.copy_tree(os.path.join('dam', 'templates'), os.path.join(self.install_purelib, 'dam', 'templates'))
        self._adapt_cfg(os.path.join('dam', '001-notredam.cfg'), 
                        os.path.join(self.cfgroot, '001-notredam.cfg'),
                        failures)
        from dam.settings import dir_log
        if not os.path.exists(dir_log):
            self.mkpath(dir_log)
        _print_errors(failures)

class local_install(install):
    description = "install leaving the source tree in-place: need to set PYTHONPATH"

    def finalize_options(self):
        install.finalize_options(self)
        self.install_purelib = os.path.dirname(os.path.abspath(__file__))
        if not self.cachedir:
            self.cachedir = '/tmp/mediadart'
        self.as_root = 0


setup(name='notredam', 
      version='1.0.1', 
      description='A collaborative, web based Digital Asset Management platform',
      long_description="""NotreDAM is a collaborative, web based Digital Asset Management platform that allows to classify, organize, archive and adapt digital objects. The target users are people involved in content production, archiving and publishing, that collaborate remotely sharing content and methodologies. NotreDAM can manage several types of objects, such as images, audio, video and textual documents, and supports the most common encoding formats. It adopts XMP for content description and supports other metadata standards (EXIF, IPTC, etc.) as well. Custom metadata schemes can be easily added as XMP extensions.""",
      author='CRS4',
      author_email='agelli@crs4.it',
      license='LGPL',
      platforms=['Unix'],
      url='http://www.notredam.org', 
      packages= package_list,
      package_data = package_data,
      scripts=[],
      cmdclass={'install':  install,  'local_install': local_install,},
     )

