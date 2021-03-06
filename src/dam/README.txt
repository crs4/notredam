Trunk Version
========================
INSTALLATION AND UPGRADE
========================

Please note: since 2012-10-22, NotreDAM requires:
 - alembic 0.4 (http://pypi.python.org/pypi/alembic);
 - SQLAlchemy-0.7.9 (http://www.sqlalchemy.org).
 

Version 1.0.9
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

        2. execute the following four commands:

	       find . -type f -name "initial_data.json" -exec rm {} \;
               python manage.py syncdb --noinput
               python manage.py migrate --fake treeview 0001
               python manage.py migrate --no-initial-data

	3. add SAFE_MODE=False to the your settings.py

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
Added file wsgi.py to make easy apache server set up

2.
More supported file formats for uploading (.mov, .mod, .mxf)

3.
Added DateLikeString attribute to real-world objects, which is a specific field required for storing BC dates (negative dates are not supported by most of Databases)

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
IE compliant (tested with versions greater than IE7), although there is the
IE limitation to upload one file at a time.

5.
Optimization and bug fixing in vocabulary and real-world objects

6.
Other minor bug fixing
 
===============================================================================
OTHER THINGS
===============================================================================



