""" 

This script allows to import a directory and its subdirectories into NotreDAM.
An item will be created for each media files contained in the given directory.\
 If an item already exists for a given file, it will be skipped .\
 If the file has been modified since the item has been created, it is possibile to update the item (see option -U)
 
Typical usage:

python import_dir.py /home/user/import_dir/ -u admin -w 1 -r
"""
from django.core.management import setup_environ
import settings
setup_environ(settings)
from django.db.models.loading import get_models
get_models()
from django.contrib.auth import authenticate

import os
import getpass
import sys

from django.contrib.auth.models import User
from dam.workspace.models import DAMWorkspace as Workspace
from dam.upload.views import import_dir
from optparse import OptionParser
import time
import logging
from dam.logger import logger

class NoItemToProcess(Exception):
    pass

class LoginFailed(Exception):
    pass

class NotMember(Exception):
    pass
    
class InsufficientPermissions(Exception):
    pass


## {{{ http://code.activestate.com/recipes/168639/ (r1)
class progressBar:
	def __init__(self, minValue = 0, maxValue = 10, totalWidth=12):
		self.progBar = "[]"   # This holds the progress bar string
		self.min = minValue
		self.max = maxValue
		self.span = maxValue - minValue
		self.width = totalWidth
		self.amount = 0       # When amount == max, we are 100% done 
		self.updateAmount(0)  # Build progress bar string

	def updateAmount(self, newAmount = 0):
		if newAmount < self.min: newAmount = self.min
		if newAmount > self.max: newAmount = self.max
		self.amount = newAmount

		# Figure out the new percent done, round to an integer
		diffFromMin = float(self.amount - self.min)
		percentDone = (diffFromMin / float(self.span)) * 100.0
		percentDone = round(percentDone)
		percentDone = int(percentDone)

		# Figure out how many hash bars the percentage should be
		allFull = self.width - 2
		numHashes = (percentDone / 100.0) * allFull
		numHashes = int(round(numHashes))

		# build a progress bar with hashes and spaces
		self.progBar = "[" + '#'*numHashes + ' '*(allFull-numHashes) + "]"

		# figure out where to put the percentage, roughly centered
		percentPlace = (len(self.progBar) / 2) - len(str(percentDone)) 
		percentString = str(percentDone) + "%"

		# slice the percentage into the bar
		self.progBar = self.progBar[0:percentPlace] + percentString + self.progBar[percentPlace+len(percentString):]

	def __str__(self):
		return str(self.progBar)
## end of http://code.activestate.com/recipes/168639/ }}}

def check_user(username, password, workspace_id):    
    user = authenticate(username=username, password=password)
    if user is None:        
        raise LoginFailed
    ws = Workspace.objects.get(pk = opts.workspace_id)
    if not ws.has_member(user):
        raise NotMember
    if not ws.has_permission(user, 'add_item'):
        raise InsufficientPermissions
    return user, ws

def _import_dir(user, ws, dir_path, recursive, force_generation, link, remove_orphans):

    items_deleted ,processes = import_dir(dir_path, user, ws, make_copy = True, recursive = recursive, force_generation = force_generation, link = link, remove_orphans=remove_orphans)
    return items_deleted, processes
    

def print_progress(items_deleted, processes):
    if items_deleted:
        print 'Orphan items deleted:', items_deleted

    if not processes:
        raise NoItemToProcess

    total_items = 0
    for process in processes:        
        total_items += process.processtarget_set.all().count()
    
    print '\nProcessing %s item(s)... \nNote that closing the shell will not interrupt the processing.\n'%total_items
    total_progress = 0
    
    prog = progressBar(0, 100, 100)
    #print '\nProcessing %s item(s)...\n'%items.count()
    while total_progress <=100:
        total_progress = 0
        
        for process in processes:   
            items_completed, items_failed, total_items, progress = process.get_progress()
            total_progress += progress
            
        if processes:
            total_progress = float(total_progress)/len(processes)
        else: 
            total_progress = 100
        prog.updateAmount(total_progress)
        #print total_progress
        print prog, "\r",
        time.sleep(.05)
        if total_progress >=100:
            break
    print ''
      

if __name__ == "__main__":
    logger.setLevel(logging.ERROR)
    help_message = "For help use -h, --help"
    parser = OptionParser(usage = __doc__)
    parser.add_option("-w", "--workspace", dest="workspace_id", help="workspace id on which items will be created")
    
    parser.add_option("-u", "--user", dest="username", help='user that will be used as items\' creator. He/She must be member of the workspace specified with option w and have "add items" permission.')
    parser.add_option("-r", help="recursively add files in subdirectories", default= False, dest='recursive', action = 'store_true')
    #parser.add_option("-f", help="force creation of items, even if there is already an item associated to a file", default= False, dest='force_generation', action = 'store_true')
    parser.add_option("-l", help="create links inside NotreDAM storage, instead of copying the files", default= False, dest='link', action = 'store_true')
    parser.add_option("-U", help="update modified files. The original rendition will be replaced and new renditions will be generated", default= False, dest='force_generation', action = 'store_true')
    parser.add_option("-R", help="remove orphan items, ie items whose relative file has been deleted", default= False, dest='remove_orphans', action = 'store_true')

    (opts, args) = parser.parse_args()
   
    if len(args) < 1:
        print 'no directory passed. ' + help_message
        sys.exit(2)
    dir_path = args[0]
    
    if not opts.workspace_id:
        print 'No workspace passed. ' + help_message
        sys.exit(2)
    
    if not opts.username:
        print 'No user passed. ' + help_message
        sys.exit(2)
    
    if not os.path.isabs(dir_path):
        dir_path = os.path.join(os.getcwd(), dir_path)
        
    if not os.path.exists(dir_path):
        print 'dir %s does not exist'%dir_path
        sys.exit(2)
    
    password = getpass.getpass()
    try:
        user, ws = check_user(opts.username, password, opts.workspace_id)
        items_deleted, processes = _import_dir(user, ws, dir_path, opts.recursive, opts.force_generation, opts.link, opts.remove_orphans)
        print_progress(items_deleted, processes)

    except LoginFailed:
        print 'Login failed'
        sys.exit(2)
    
    except Workspace.DoesNotExist:
        print 'workspace %s does not exist'%opts.workspace_id
        sys.exit(2)

    except NotMember:
        print 'You are not member of workspace %s'%ws
        sys.exit(2)
    
    except InsufficientPermissions:
        print 'You have insufficient permissions on workspace %s'%ws
    
    except NoItemToProcess:
        print """\nNo item to process. It happens when:
        - the directory is empty or does not contain media files supported by NotreDAM.
        - all files are already inside NotreDAM workspace and up to date.
        """
        sys.exit(2)
    
    except Exception, ex:
        print 'Internal Error.'
        logger.exception(ex)
        sys.exit(2)
