import os
import sys
import subprocess
from distutils.core import setup, Command, DistutilsOptionError
from distutils.command.install import install as _install

# The python packages that this setup is going to install
package_list = [
'dam',
'dam/admin',
'dam/api',
'dam/api/django_restapi',
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

# Names of required debian packages. Each entry specifies:
# <package_name>  <list of args of apt-get install (version numbers etc.)>
debian_packages = [
'python-django=1.1',
'python-egenix-mxdatetime',
]

# list of <tarfile>, <unpacked directory, None if unpacks in curdir>, <install_command>
tarfiles = [
# ('python-txamqp_0.3.tgz', 'python-txamqp-0.3', ['sudo', 'python', 'setup.py', 'install']),
]



class InstallDep(Command):
    description = "install required debian and tarball packages"
    user_options = []
    def initialize_options(self): pass
    def finalize_options(self): pass

    def install_tar(self, failures):
        curdir = os.getcwd()
        for tarfile, topdir, exe in tarfiles:
            print ('\n Installing %s' % tarfile)
            clean_up = topdir and not os.path.exists(topdir)  # delete new directories
            ret = subprocess.call(['tar', 'xvzf', tarfile])
            if ret != 0:
                failures.append('Installation error for %s: unable to untar' % tarfile)
                return
            if topdir:
                os.chdir(topdir)
            ret = subprocess.call(exe)
            if ret != 0:
                failures.append('Installation error for %s: unable to install' % tarfile)
                return
            os.chdir(curdir)
            if clean_up:
                print 'Removing %s' % topdir
                subprocess.call(['sudo', 'rm', '-rf', topdir])

    def run(self):
        failures = []
        response = raw_input('\nDependencies:%s%s\nInstall? (y/N): ' % (
              '\n - '.join([''] + debian_packages), '\n - '.join([''] + [x[0] for x in tarfiles])))
        if not response or response.lower().startswith('n'):
            print('Aborting installation of dependencies')
            return
        for pkg in debian_packages:
            print ('\n Installing %s' % pkg)
            ret = subprocess.call(['sudo', 'apt-get', 'install', pkg])
            if ret != 0:
                failures.append('Installation error for %s' % pkg)
        self.install_tar(failures)
        if failures:
            print >>sys.stderr, '\nSome packages failed to install:'
            print >>sys.stderr, '\n'.join(failures)

class Config(Command):
    description = "create configuration directory and copies cfg files"
    user_options = [('cfgroot=', None, 'directory for .cfg files')]

    def initialize_options(self):
        self.cfgroot = None

    def finalize_options(self):
        if not self.cfgroot:
            if 'HOME' in os.environ:
                self.cfgroot = os.path.join(os.environ['HOME'], '.mediadart')
            else:
                raise DistutilsOptionError('Missing value for configuration directory')

    def check_exe(self):
        from mediadart.config import Configurator
        c=Configurator()
        for section in c.sections():
            for item in c.items(section):
                if item[0].endswith('_exe'):
                    if not os.path.exists(item[1]):
                        print('##### WARNING: executable %s not found' % item[1])

    def run(self):
        if not os.path.exists(self.cfgroot):
            self.mkpath(self.cfgroot)
        if not os.path.exists(os.path.join(self.cfgroot, 'bin')):
            self.mkpath(os.path.join(self.cfgroot, 'bin'))
        self.copy_file('mediadart/config/mediadart.cfg', self.cfgroot)
        self.copy_file('mediadart/adapter/gst-discover', os.path.join(self.cfgroot, 'bin'))
        self.check_exe()

class install(_install):
    def run(self):
        self.run_command('install_dep')
        _install.run(self)
        self.run_command('config')

setup(name='notredam', 
      version='1.0.1', 
      description='A collaborative, web based Digital Asset Management platform',
      long_description="""NotreDAM is a collaborative, web based Digital Asset Management platform that allows to classify, organize, archive and adapt digital objects. The target users are people involved in content production, archiving and publishing, that collaborate remotely sharing content and methodologies. NotreDAM can manage several types of objects, such as images, audio, video and textual documents, and supports the most common encoding formats. It adopts XMP for content description and supports other metadata standards (EXIF, IPTC, etc.) as well. Custom metadata schemes can be easily added as XMP extensions.""",
      author='CRS4',
      author_email='agelli@crs4.it',
      license='LGPL',
      platforms=['Unix'],
      url='http://code.google.com/p/mediadart', 
      packages= package_list,
      scripts=[],
      cmdclass={'install_dep':  InstallDep,  'install': install, 'config': Config, },
     )

