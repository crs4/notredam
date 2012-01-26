#########################################################################
#
# NotreDAM, Copyright (C) 2011, Sardegna Ricerche.
# Email: labcontdigit@sardegnaricerche.it
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
# Various utility methods.
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

def notredam_connstring():
    '''
    Return a SQLAlchemy-compatible connection string representing the
    NotreDAM DB settings
    '''
    # FIXME: this function, of course, is quite a kludge
    from dam.settings import DATABASES

    # We may need to modify the settings
    db = DATABASES['default']

    django_db_host = db['HOST']
    if ('' == django_db_host):
        django_db_host = 'localhost'

    # Username/password separator in SQLAlchemy connection string (may
    # be modified depending on the engine)
    user_pass_separator = ':'

    # FIXME: kludgy way to convert Django database settings into a connstring
    django_db_engine = db['ENGINE']
    if ('django.db.backends.postgresql_psycopg2' == django_db_engine):
        connstr = '%s://%s:%s@%s/%s' % ('postgresql',
                                         db['USER'],
                                         db['PASSWORD'],
                                         django_db_host, db['NAME'])
    elif ('django.db.backends.mysql' == django_db_engine):
        connstr = '%s://%s:%s@%s/%s?charset=utf8' % ('mysql',
                                                     db['USER'],
                                                     db['PASSWORD'],
                                                     django_db_host,
                                                     db['NAME'])
    elif ('django.db.backends.sqlite3' == django_db_engine):
        connstr = '%s:///%s' % ('sqlite', db['NAME'])
    else:
        raise ValueError('Unsupported DB for knowledge base: '
                         + django_db_engine)

    return connstr
