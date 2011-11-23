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
# A few tentative testing functions, which are most likely going to be
# turned into well-defined unit tests.
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

import errors as kb_exc
import access
import schema
import session

import pdb

CONNSTRING = 'postgresql://tinykb:tinykb@localhost/tinykb'

def reset_db():
    s = schema.Schema()
    s.reset_db(CONNSTRING)

def init_db():
    s = schema.Schema()
    s.init_db(CONNSTRING)

def test_create_object_classes(connstring=CONNSTRING):
    ses = session.Session(connstring)
    classes = ses.orm
    attrs = ses.orm.attributes

    ## Retrieve user 1, if it exists
    try:
        u1 = ses.user(1)
    except kb_exc.NotFound:
        u1 = classes.User('user')
        ses.add(u1)

    ## Retrieve workspace 1, if it exists
    try:
        w1 = ses.workspace(1)
    except kb_exc.NotFound:
        w1 = classes.Workspace('ws', u1)
        ses.add(w1)

    ## Retrieve the 'Keyword' class, which must exists
    # KeywordClass = ses.class_('keyword')
    # Keyword = KeywordClass.python_class

    class1 = classes.KBRootClass('Building', explicit_id='building',
                                 notes='Generic building',
                                 attributes=[attrs.Boolean('Visitable',
                                                           default=True),
                                             attrs.Integer('Height',
                                                           min_=0),
                                             attrs.String('Location'),
                                             attrs.Date('Date of completion')])
    class2 = classes.KBRootClass('Apple')
    class3 = classes.KBRootClass('Orange')

    class1.realize() # FIXME: automatically build parent tables?
    class2.realize()
    class3.realize()

    ## Ensure that the Keyword class is visible in all workspaces
    ## FIXME: it should be done automatically
    # KeywordClass.setup_workspace(w1, access.OWNER)

    class1.setup_workspace(w1, access=access.OWNER)
    class2.setup_workspace(w1, access=access.OWNER)
    class3.setup_workspace(w1, access=access.OWNER)

    # it1 = classes.Item()
    # it2 = classes.Item()
    # it3 = classes.Item()

    # it1.add_to_workspace(w1)
    # it2.add_to_workspace(w1)
    # it3.add_to_workspace(w2)

    # kw1 = Keyword('key1', 'Just a keyword', explicit_id='key1')
    # kw2 = Keyword('key2', explicit_id='key2')

    # catalog1 = classes.RootCatalogEntry(kw1)
    # catalog2 = classes.RootCatalogEntry(kw2)
    # catalog3 = classes.CatalogEntry(kw1, catalog2)

    # catalog1.add_to_workspace(w1)
    # catalog2.add_to_workspace(w2)

    all_objs = [w1,
                #KeywordClass,
                class1, class2, class3,
                #u1, u2,
                #it1, it2, it3,
                #kw1, kw2,
                #catalog1, catalog2, catalog3
                ]

    ses.add_all(all_objs)
    ses.commit()


def test_create_derived_classes(connstring=CONNSTRING):
    ses = session.Session(connstring)
    classes = ses.orm
    attrs = ses.orm.attributes

    ## Retrieve the 'Keyword' class, which must exists
    #KeywordClass = ses.class_('keyword')

    # The Keyword Python class must exist in order to create a
    # reference (see below)
    #Keyword = KeywordClass.python_class

    class1 = ses.class_('building')
    Building = class1.python_class

    class4 = classes.KBClass('Church',  explicit_id='church',
                             superclass=class1, notes='A church',
                             attributes=[attrs.Uri('Websites',
                                                   multivalued=True),
                                         attrs.Choice('Number of naves',
                                                      ['One', 'Two',
                                                       'Three or more'],
                                                      default='Two'),
                                         attrs.ObjectReference(
                                             'Nearby buildings', Building,
                                             multivalued=True)])
    class4.realize()
    Church = class4.python_class
    
    class5 = classes.KBClass('Castle',  explicit_id='castle',
                             superclass=class1,
                             notes='A castle (possibly with a dragon)',
                             attributes=[attrs.ObjectReference('Local church',
                                                               Church)]) 
    class5.realize()
    Castle = class5.python_class

    all_objs = [class4, class5]

    ses.add_all(all_objs)
    ses.commit()


def test_create_derived_class_objects(connstring=CONNSTRING):
    ses = session.Session(connstring)

    Church = ses.python_class('church')
    Castle = ses.python_class('castle')

    church1 = Church('Cute little church', 'Unknown church near Siliqua')
    castle1 = Castle('Acquafredda', 'Castle of Siliqua')
    castle2 = Castle('Eleonora d\'Arborea', 'Castle of Sanluri')

    # Here we use the standard mangling rules for attribute names:
    # lowercase, spaces converted to underscores
    castle1.local_church = church1
    church1.nearby_buildings.append(castle1)
    church1.nearby_buildings.append(castle2)
    church1.websites.append('http://www.google.com/')
    church1.websites.append('http://www.xkcd.com/')
    
    all_objs = [church1, castle1, castle2]

    ses.add_all(all_objs)
    ses.commit()

    
if __name__ == '__main__':
    init_db()
    test_create_object_classes()
    test_create_derived_classes()
    test_create_derived_class_objects()

