========================
INSTALLATION AND UPGRADE
========================

Requirements:

 - Django 1.3 (http://www.djangoproject.com)
 - South 0.7.3 (http://south.aeracode.org)
 - alembic 0.4.1 (http://pypi.python.org/pypi/alembic)
 - SQLAlchemy 0.7.9 (http://www.sqlalchemy.org)
 - Celery 2.4.6 (http://www.celeryproject.org/)
 - MediaInfo 0.7.61 (http://mediainfo.sf.net/)

========================
INSTALLATION AND UPGRADE
========================

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

               # Rename initial data files, thus avoiding reload by 'syncdb'
	       find . -type f -name initial_data.json -exec mv {} {}.excl \;
               python manage.py syncdb --noinput

               python manage.py migrate --fake treeview 0001
               python manage.py migrate --no-initial-data

	3. add SAFE_MODE=False to your settings.py

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



