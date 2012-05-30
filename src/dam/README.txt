Version 1.0.9rc1


========================
INSTALLATION AND UPGRADE
========================

Please note: since version 1.08rc2, NotreDAM requires South 0.7.3
(http://south.aeracode.org/).

    -----------------------------
    Setting up a new installation
    -----------------------------

    When creating a new NotreDAM installation from scratch, you will
    need to setup the DB by executing BOTH the following commands:

        python manage.py syncdb --noinput
        python manage.py migrate

    -------------------------------------------
    Upgrading a previous installation (1.08rc1)
    -------------------------------------------

    If you want to upgrade a NotreDAM 1.08rc1 installation, you will
    need to:

        0. perform a backup of your DB (just in case)

        1. add 'south' to the INSTALLED_APPS of your settings.py

        2. execute the following three commands:

               python manage.py syncdb --noinput
               python manage.py migrate --fake treeview 0001
               python manage.py migrate --no-initial-data

    That's it!  Your old installation is now upgraded.

===================
NEWS AND OTHER INFO
===================

Please add notes about new features, bug fixing, and other things at
the end of the list.

===============================================================================
NEW FEATURES
===============================================================================

1.
IE compliant (tested with versions greater than IE7), although there is the
IE limitation to upload one file at a time.

2.
Optimization and bug fixing in vocabulary and real-world objects

3.
Added file wsgi.py to make easy apache server set up

4.
More supported file format for uploading (.mov, .mod, .mts, .mxf)

===============================================================================
BUG FIXING
===============================================================================

1.
Fixed bug in item sharing with another workspace

2.
Fixed bug in moving items to a different workspace

3.
Fixed bug in metadata saving

4.
Other minor bug fixing
 
===============================================================================
OTHER THINGS
===============================================================================



