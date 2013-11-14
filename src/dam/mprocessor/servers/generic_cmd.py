# This servers launches a generic cmd line on the node 
# Parameters:
# cmd: the command to execute. The server may restrict this parameter
# argv: the list of the parameters
# env: the environment for the parameter execution. May be restricted
# 
# Among the arguments there are special arguments:
# files from the repository: are prefixed by 
#    file://<path relative to root of repository>
# they must exists before the command starts
# 
# output files to be stored in the repository: 
#    outfile://<path relative to root of repository>
# 
# All file names must be relative paths relative to che root of the repository
# of the server servicing the request (option [STORAGE]:cache_dir).  
# Any argument starting with "cache://" is tranformed
# in a valid path name in the repository.  For example, if the repository  
# "/opt/mediadart/repository", the an argument "cache://images/foo.png" is passed
# to convert as "/opt/mediadart/repository/images/foo.png". 
#
# Not using file:// for output files causes files to be left behind in case of
# failures.
# 
# If the option overwrite=False then an error is raised if an output file arguments
# points to an existing file in the repository
#
# Implementation schedule
# 1.0 basic class calling RunProc and _execute for copying output file in place
#     function to argparse to parse all arguments and make necessary substitutions
# 2.0 Implementing some adapter using the new class
# 3.0 Check on allowed commands and environments
# 4.0 Support for http feedback etc.

import os
import time
import types
from shutil import move
from uuid import uuid4
from ConfigParser import NoSectionError, NoOptionError

from dam.mprocessor import log
from dam.mprocessor.config import Configurator
from dam.mprocessor.storage import Storage, new_id
from dam.mprocessor.utils import RunProc

from dam.mprocessor.servers.progress import get_progress_cb

class MProcessorError(Exception):
    pass

UNIQUE_LEN = 8
def unique():
    "return and unique string"
    return '__' + uuid4().hex[:5] + '-'

class GenericCmdline(object):
    def __init__(self):
        c = Configurator()
        self.cfgsection = self.__class__.__name__.upper()
        self._fc = Storage()
        self._tmpdir = c.get('STORAGE', 'temp_dir')
        self.output = ""
        self.max_output = 256*1024
        self.lastlog = 0
        self.exe = None

        try:
            self._overwrite = c.getboolean(self.cfgsection, 'overwrite')
        except (NoOptionError, NoSectionError):
            self._overwrite = True

        try:
            self.progress_regex = c.get(self.cfgsection, 'progress_regex')
        except (NoOptionError, NoSectionError):
            self.progress_regex = None

    def __process_args(self, args):
        clean_args = []
        outfile_map = {}
        for arg in args:
            arg = str(arg).strip()
            cleaned = None
            if arg.startswith('..') or arg.startswith(os.sep):
                raise MProcessorError('invalid argument %s' % arg)
            elif arg.startswith('file://'):
                filename = arg[7:]
                if filename:
                    cleaned = str(self._fc.abspath(filename))   # strip file:// 
                else:
                    cleaned = ''
            elif arg.startswith('outfile://'):
                filename = arg[10:]
                if filename:
                    outfile = str(self._fc.abspath(filename))       # strip outfile:// 
                    if not self._overwrite and os.path.exists(outfile):
                        raise MProcessorError('ERROR: %s exists' % outfile)
                    cleaned = os.path.join(os.path.normpath(os.path.dirname(outfile)),
                                           unique() + os.path.basename(outfile))
                    outfile_map[cleaned] = outfile
                else:
                    cleaned = ''
            else:
                cleaned = arg
            clean_args.append(cleaned)
        return clean_args, outfile_map

    def filter_exe(self, cmd):
        """ Check if cmd is a valid/allowed executable in the local machine 
        
        Returns standardized path of executable and the boolean b_require_output.
        If b_require_output is True, the call fails if there are no output files.
        """
        return cmd, False     

    def filter_env(self, env):
        """ Check if env is a valid/allowed environment for the currnet command (self.exe) """
        return {}

    def _cb_done(self, result, tmpfile_map, stdout):
        for tmpfile, outfile in tmpfile_map.items():
            move(tmpfile, outfile)
        # if the script has no return value, return the name of the generated files

        # Try to access result['data'], and return a dictionary with a 'data'
        # field in case it does not work or it's empty
        # FIXME: just for retro-compatibility.  What the heck is going on here?
        try:
            _x = result['data']
            if not _x:
                raise Exception('FIXME: just to trigger "except" below')
        except:
            result = {}
            result['data'] = stdout[0] #"%s" % ':'.join(tmpfile_map.values())
        return result

    def _cb_err(self, result, tmpfile_map):
        for tmpfile in tmpfile_map:
            try:
                os.unlink(tmpfile)
            except:
                pass
        return result

    def accumulate_stdout(self, data, stdout):
        #log.debug('script output:\n%s\n' % data)
        data = data.decode('latin-1')
        stdout[0] = stdout[0][-self.max_output:] + data
        now = time.time()
        if now - self.lastlog > 2:
            log.debug('%s: still running: last output:\n%s' % (self.exe, data.strip()))
            self.lastlog = now

    def call(self, cmd, args, env={}, progress_url=None,):
        stdout = [""]
        self.exe, b_require_output = self.filter_exe(cmd)
        env = self.filter_env(env)
        args, tmpfile_map = self.__process_args(args)
        #log.debug('####### args: %s' % args)
        if b_require_output and not tmpfile_map:
            raise MProcessorError('No output files specified among the arguments')
        if progress_url and not self.progress_regex:
            raise MProcessorError('No configuration for progress report found (option %s/%s)' %
                (self.cfgsection, 'progress_regex'))
        elif progress_url:
            cb_func = get_progress_cb(progress_url, 'gstreamer-progressreport')
            cb_arg = []
        else:
            stdout = [u""]
            cb_arg = [stdout]
            cb_func = self.accumulate_stdout

        log.debug('Executing RunProc')
        try:
            result = RunProc.run(self.exe, args, env, cb=cb_func, cbargv=cb_arg, do_log=1)
            result = self._cb_done(result, tmpfile_map, stdout)
        except Exception as e:
            result = self._cb_err({'data' : ''}, tmpfile_map)
            raise
        return result

###############################################################################
# Celery task setup
from celery.task import task as celery_task
_SERVER_SINGLETON = GenericCmdline()
@celery_task
def call(cmd, args, env={}, progress_url=None):
    return _SERVER_SINGLETON.call(cmd=cmd, args=args, env=env,
                                  progress_url=progress_url)
