#!/usr/bin/env python

###############################################################################
# NotreDAM hooks and kludges start here (the original manage.py file
# is pasted at the end of the file)
# FIXME: remove these kludges somehow, or at least move them somewhere else
###############################################################################
from django.core import management
from django.core.management.commands.syncdb import Command

from kb import init_kb

orig_handle_noargs = Command.handle_noargs

# This may win the prize for the ugliest hack of the century.  We
# monkey-patch Django's syncdb command class in order to perform KB
# initialization *before* and *after* a syncdb is actually executed.
def handle_noargs(instance, *args, **kwargs):
    init_kb.preinit_notredam_kb()
    ret = orig_handle_noargs(instance, *args, **kwargs)
    init_kb.init_notredam_kb()
    return ret

# Here's the dirty work
Command.handle_noargs = handle_noargs
###############################################################################
# NotreDAM hooks and kludges end here (original Django's manage.py
# contents are reported below)
###############################################################################

from django.core.management import execute_manager
try:

    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
