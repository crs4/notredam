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

if __name__ == "__main__":
    help_message = "For help use -h, --help"
    parser = OptionParser(usage = __doc__)
    parser.add_option("-w", "--workspace", dest="workspace_id", help="workspace id on which items will be created")
    
    parser.add_option("-u", "--user", dest="username", help='user that will be used as items\' creator. He/She must be member of the workspace specified with option w and have "add items" permission.')
    parser.add_option("-r", help="recursively add files in subdirectories", default= False, dest='recursive', action = 'store_true')
    

    
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
        import_dir(dir_path, user, ws, make_copy = True, recursive = opts.recursive)
    else:
        print 'login failed'
        sys.exit(2)
