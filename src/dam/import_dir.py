""" 
This script allows to import a directory into NotreDAM. An item will be created for each media files contained in the given directory. 
Typical usage:

python import_dir.py /home/user/import_dir/ -u admin -w 1 

"""
from django.core.management import setup_environ
import dam.settings as settings
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




if __name__ == "__main__":
    #logger.setLevel(logging.ERROR)
    help_message = "For help use -h, --help"
    parser = OptionParser(usage = __doc__)
    parser.add_option("-w", "--workspace", dest="workspace_id", help="workspace id on which items will be created")
    
    parser.add_option("-u", "--user", dest="username", help='user that will be used as items\' creator. He/She must be member of the workspace specified with option w and have "add items" permission.')
    parser.add_option("-r", help="recursively add files in subdirectories", default= False, dest='recursive', action = 'store_true')
    parser.add_option("-f", help="force creation of items, even if there is already an item associated to a file", default= False, dest='force_generation', action = 'store_true')
    parser.add_option("-s", help="create symbolic link inside notredam storage, instead of copy the file", default= False, dest='symlink', action = 'store_true')
    

    
    (opts, args) = parser.parse_args()
    #print 'opts', opts
    #print 'args', args
    
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
    try:
        user = User.objects.get(username = opts.username)
    except User.DoesNotExist:
        print 'user %s does not exist'%opts.username
        sys.exit(2)

    try:
        ws = Workspace.objects.get(pk = opts.workspace_id)
    except Workspace.DoesNotExist:
        print 'workspace %s does not exist'%opts.workspace_id
        sys.exit(2)
    
    
    if not ws.has_member(user):
        print 'You are not a member of workspace "%s"'%ws.name
        sys.exit(2)
        
    if not ws.has_permission(user, 'add_item'):
        print 'You have insufficient permissions'
        sys.exit(2)
    
    
    password = getpass.getpass()
    user = authenticate(username=user.username, password=password)
    
    if user is not None:        
        processes = import_dir(dir_path, user, ws, make_copy = True, recursive = opts.recursive, force_generation = opts.force_generation, symlink = opts.symlink)
        
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
      
            
    else:
        print 'login failed'
        sys.exit(2)
