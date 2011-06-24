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
    pass

if __name__ == "__main__":
    help_message = "for help use -h, --help"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hw:d:u:",["help"])
        print 'opts', opts
        print 'args', args
    except getopt.error, msg:
        print msg
        print help_message
        sys.exit(2)
     
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
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
    
    password = getpass.getpass()
    user = authenticate(username=user.username, password=password)
    if user is not None:
        import_dir(dir_path, user, ws, make_copy = True)
    else:
        print 'login failed'
        sys.exit(2)

    
    
