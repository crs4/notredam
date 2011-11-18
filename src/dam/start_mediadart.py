#########################################################################
#
# NotreDAM, Copyright (C) 2010
# Web: www.notre-dam.org
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#########################################################################

#
# This starts mediadart. It is needed when one of the servers need 
# to access the settings of a django installation, as is the case
# of the mprocessor for notredam
#
import os
import sys
#os.environ['DJANGO_SETTINGS_MODULE'] = 'dam.settings'

from django.core.management import setup_environ
import settings
setup_environ(settings)
from django.db.models.loading import get_models
from mediadart import log
from mediadart.config import Configurator
from mediadart.launch import main
#try:
#    import settings # Assumed to be in the same directory.
#except ImportError:
#    import sys
#    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
#    sys.exit(1)


def check_notredam_config():
    c = Configurator()
    if not c.has_option('MQUEUE', 'server_mprocessor'):
        print 'ERROR: no option for starting mprocessor'
        sys.exit(1)

msg = '\n## Notredam settings:\n * settings module: %s\n * database: %s' % (settings.__file__, settings.DATABASES['default']['ENGINE'])

# XXX: (Temporary) workaround for ticket #1796: force early loading of all
# models from installed apps.
loaded_models = get_models()
check_notredam_config()
main(msg)
