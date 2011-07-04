""" 
This script allows to import a directory into NotreDAM. An item will be created for each media files contained in the given directory. 
Typical usage:

python import_dir.py -d /home/user/import_dir/ -u admin -w 1 

Options:
    -d: the directory to import
    -u: user that will be used as items' creator. He/She must be member of the workspace specified with option w and have "add items" permission.
    -w: workspace id on which items will be created

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
import getopt
from django.contrib.auth.models import User
from dam.workspace.models import DAMWorkspace as Workspace
from dam.upload.views import import_dir

def usage():
    print __doc__

if __name__ == "__main__":
    help_message = "for help use -h, --help"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hrw:d:u:",["help"])
        #print 'opts', opts
        #print 'args', args
    except getopt.error, msg:
        print msg
        print help_message
        sys.exit(2)
     
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        
    if len(opts) < 1: 
        print 'no args passed'
        print help_message
        sys.exit(2)
        
    opts = dict(opts)
    
    if not opts.has_key('-d'):
        print 'no dir specified'
        print help_message
        sys.exit(2)
    
    if not opts.has_key('-u'):
        print 'no user specified'
        print help_message
        sys.exit(2)

    if not opts.has_key('-w'):
        print 'no workspace specified'
        print help_message
        sys.exit(2)
    
    dir_path = opts['-d']
    if not os.path.exists(dir_path):
        print 'dir %s does not exist'%dir_path
        sys.exit(2)
    
    if opts.has_key('-r'):
        recursive = True
    else:
        recursive = False
    
    try:
        user = User.objects.get(username = opts['-u'])
    except User.DoesNotExist:
        print 'user %s does not exist'%opts['-u']
        sys.exit(2)

    try:
        ws = Workspace.objects.get(pk = opts['-w'])
    except Workspace.DoesNotExist:
        print 'workspace %s does not exist'%opts['-w']
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
        
        import_dir(dir_path, user, ws, make_copy = True, recursive = recursive)
        
            
    else:
        print 'login failed'
        sys.exit(2)

    
    
