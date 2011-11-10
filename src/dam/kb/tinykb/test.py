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

import access
import attributes as attrs
import classes
import errors as kb_exc
import schema
import session

import pdb

CONNSTRING = 'postgresql://tinykb:tinykb@localhost/tinykb'

def reset_db():
    schema.reset_db(CONNSTRING)

def init_db():
    schema.init_db(CONNSTRING)

def test_create_object_classes(connstring=CONNSTRING):
    ses = session.Session(connstring)

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
    KeywordClass = ses.class_('keyword')

    Keyword = KeywordClass.make_python_class(ses)

    class1 = classes.KBRootClass('Building', explicit_id='building',
                                 notes='Generic building',
                                 attributes=[attrs.Boolean('Visitable',
                                                           default=True),
                                             attrs.Integer('Height', min_=0),
                                             attrs.String('Location'),
                                             attrs.Date('Date of completion')])
    class2 = classes.KBRootClass('Apple',explicit_id='apple',
                                 notes='Generic apple',
                                 attributes=[attrs.Boolean('eating',
                                                           default=True)])
                                 
    class3 = classes.KBRootClass('Orange')

    class6 = classes.KBRootClass('ClassTest1')

    class7 = classes.KBRootClass('ClassTest2')

    class8 = classes.KBRootClass('ClassTest3')
    
    class1.create_table(ses) # FIXME: automatically build parent tables?
    class2.create_table(ses)
    class3.create_table(ses)
    class6.create_table(ses)
    class7.create_table(ses)
    class8.create_table(ses)

    ## Ensure that the Keyword class is visible in all workspaces
    ## FIXME: it should be done automatically
    # KeywordClass.setup_workspace(w1, access.OWNER)

    class1.setup_workspace(w1, access=access.OWNER)
    class2.setup_workspace(w1, access=access.OWNER)
    class3.setup_workspace(w1, access=access.OWNER)
    class6.setup_workspace(w1, access=access.OWNER)
    class7.setup_workspace(w1, access=access.OWNER)
    class8.setup_workspace(w1, access=access.OWNER)

    # it1 = classes.Item()
    # it2 = classes.Item()
    # it3 = classes.Item()

    # it1.add_to_workspace(w1)
    # it2.add_to_workspace(w1)
    # it3.add_to_workspace(w2)

    kw1 = Keyword('key1', 'Just a keyword', explicit_id='key1')
    kw2 = Keyword('key2', explicit_id='key2')
    kw3 = Keyword('key3', 'key3', explicit_id='key3')
    kw4 = Keyword('key4', explicit_id='key4')

    catalog1 = classes.RootCatalogEntry(kw1)
    catalog2 = classes.RootCatalogEntry(kw2)
    catalog3 = classes.CatalogEntry(kw1, catalog2)

    # catalog1.add_to_workspace(w1)
    # catalog2.add_to_workspace(w2)

    all_objs = [w1,
                KeywordClass,
                class1, class2, class3, class6, class7, class8,
                #u1, u2,
                #it1, it2, it3,
                kw1, kw2,
                catalog1, catalog2, catalog3]

    ses.add_all(all_objs)
    ses.commit()


def test_create_derived_classes(connstring=CONNSTRING):
    ses = session.Session(connstring)

    ## Retrieve the 'Keyword' class, which must exists
    KeywordClass = ses.class_('keyword')

    # The Keyword Python class must exist in order to create a
    # reference (see below)
    # FIXME: is it possible to automate it?
    Keyword = KeywordClass.make_python_class()

    class1 = ses.class_('building')

    class4 = classes.KBClass('Church',  explicit_id='church',
                             superclass=class1, notes='A church',
                             attributes=[attrs.Uri('Website'),
                                         attrs.Choice('Number of naves',
                                                      ['One', 'Two',
                                                       'Three or more'],
                                                      default='Two'),
                                         attrs.ObjectReferencesList('Tags',
                                                                    KeywordClass)])
    class4.create_table(ses)
    Church = class4.make_python_class(ses)
    class6=ses.class_('ClassTest1')
    class5 = classes.KBClass('Castle',  explicit_id='castle',
                             superclass=class1,
                             notes='A castle (possibly with a dragon)',
                             attributes=[attrs.ObjectReference('Nearby church',
                                                               Church)]) 
    class5.create_table(ses)
    Castle = class5.make_python_class(ses)

    class9 = classes.KBClass('SubClassTest1',  explicit_id='subclasstest1',
                             superclass=class6,
                             notes='A Test sub class',
                             attributes=[attrs.Uri('Website'),
                                         attrs.Choice('Number of naves',
                                                      ['One', 'Two',
                                                       'Three or more'],
                                                      default='Two')]) 
    class9.create_table(ses)
    SubClassTest1 = class9.make_python_class(ses)

    class10 = classes.KBClass('SubClassTest12',  explicit_id='subclasstest2',
                             superclass=class6,
                             notes='A Test sub class test 2',
                             attributes=[attrs.Uri('Website'),
                                         attrs.Choice('Number of naves',
                                                      ['One', 'Two',
                                                       'Three or more'],
                                                      default='Two')]) 
    class10.create_table(ses)
    SubClassTest2 = class10.make_python_class(ses)

    all_objs = [class4, class5, class9, class10]

    ses.add_all(all_objs)
    ses.commit()


def test_create_derived_class_objects(connstring=CONNSTRING):
    ses = session.Session(connstring)

    Church = ses.python_class('church')
    Castle = ses.python_class('castle')
    Apple = ses.python_class('apple')
    SubClassTest1 = ses.python_class('subclasstest1')
    SubClassTest2 = ses.python_class('subclasstest2')
    
    kw1 = ses.object('key1')
    kw2 = ses.object('key2')
    kw3 = ses.object('key3')
    kw4 = ses.object('key4')

    church1 = Church('Cute little church', 'Unknown church near Siliqua')
    church2 = Church('Bonaria', 'Bonaria di Cagliari')
    castle1 = Castle('Acquafredda', 'Castle of Siliqua')
    castle2 = Castle('Carbonia', 'Castle of Carbonia')
    apple1 = Apple('Red apple', 'Witch\'s apple')
    objSubClassTest1 = SubClassTest1('obj test1', 'obj test1')
    objSubClassTest2 = SubClassTest2('obj test2', 'obj test2')
    
    # Here we use the standard mangling rules for attribute names:
    # lowercase, spaces converted to underscores
    castle1.nearby_church = church1
    castle2.nearby_church = church2
    church1.tags.append(kw1)
    church1.tags.append(kw2)
    church2.tags.append(kw3)
    church2.tags.append(kw4)
    
    all_objs = [church1, castle1, church2, castle2, apple1, objSubClassTest1, objSubClassTest2]

    ses.add_all(all_objs)
    ses.commit()

    
if __name__ == '__main__':
    init_db()
    test_create_object_classes()
    test_create_derived_classes()
    test_create_derived_class_objects()

