Basic concepts and examples
===========================

This section explains the basic concepts of TinyKB, through some
simple examples.

Initializing the knowledge base
-------------------------------

The knowledge base can be initialized from the command line, by
executing the ``init_kb.py`` script included in the TinyKB source
code::

    $ python init_kb.py -c 'postgresql://username:password@localhost/tinykb'

The script argument is a DBMS connection string, as supported by
`SQLAlchemy`_.

.. _SQLAlchemy: http://www.sqlalchemy.org/


The knowledge base session
--------------------------

TinyKB is centered around the :py:class:`Session <session.Session>`
class, whose instances handle the connection to the underlying SQL
DBMS, manage transactions and offer several methods for querying and
modifying the contents of the knowledge base.

A new session can be created with::

    from tinykb.session import Session
    ses = Session('postgresql://username:password@localhost/tinykb')

where the constructor argument is the same connection string used for
knowledge base initialization.


.. _label-kb-root-class:

Creating a root class
---------------------

The session object contains an :py:mod:`orm` property, which is a
dynamically-generated module object providing access to several Python
classes mapped to the underlying knowledge base.  In particular,
:py:class:`orm.KBClass` and :py:class:`orm.KBRootClass` can be used to
define new knowledge base classes bound to the session.

Let's say, for example, that we want to define a KB class for
representing buildings (with some related information)::

    orm = ses.orm                  # See docs for the "orm" module
    attrs = ses.orm.attributes     # See docs for the "orm.attributes" module

    kb_building = orm.KBRootClass('Building', explicit_id='building',
                                  notes='Generic building',
                                  attributes=[attrs.Boolean('Open for visits',
                                                            default=True,
                                                            id_='is_open'),
                                              attrs.Integer('Height', min_=0,
                                                            id_='height'),
                                              attrs.String('Location',
                                                           id_='location'),
                                              attrs.Date('Date of completion',
                                                         id_='completion')])

Here, ``kb_building`` is a *root* knowledge base class (i.e. placed at
the top of the inheritance hierarchy), featuring a set of named
attributes with different types.  Those attributes are instances of
several different attribute classes, bound to the session through the
:py:mod:`orm.attributes` property.  The optional ``id_`` keyword
argument provides an attribute identifier (if not provided, it will be
auto-generated from the descriptive name).

Once created, the new knowledge base class can be *realized*,
i.e. implemented in the underlying SQL DBMS::

    ses.realize(kb_building)


Creating objects
----------------

After a class has been realized, its ``python_class`` property
provides the corresponding Python class::

    BuildingClass = kb_building.python_class

``BuildingClass`` derives from :py:class:`orm.KBObject`, which is the
base class for all dynamically-generated Python classes mapped to the
knowledge base.

By instantiating ``BuildingClass`` it is now possible to create Python
objects representing buildings::

    b = BuildingClass('Test building', explicit_id='test_building')
    b.is_open = True
    b.height = 42
    b.location = 'Sesame Street'
    b.completion = '1991-01-12'    # Or datetime.date(1991, 01, 12)

The ``b`` attribute names reflect their respective ``id_`` keyword
arguments, as provided when the knowledge base class attributes were
defined.  Object attribute values are validated on-the-fly according
to their class specification: thus, if you try something like::

    b.height = 'Not an integer value'

or the value does not respect the ``min_=0`` constraint specified when
the attribute was defined::

    b.height = -1

then you will get a :py:exc:`errors.ValidationError` exception.


Creating a derived class
------------------------

TinyKB allows to define derived classes::

    kb_church = ses.orm.KBClass('Church',  explicit_id='church',
                                superclass=kb_building, notes='A church',
                                attributes=[attrs.Choice('Number of naves',
                                                         ['One', 'Two',
                                                          'Three or more'],
                                                         default='Two'),
                                            attrs.ObjectReference(
                                                'Nearby buildings',
                                                target_class=BuildingClass,
                                                multivalued=True)])

Here, we didn't provide the ``id_`` argument to the attribute
constructors, and we used the ``multivalued=True`` flag for the last
one: those choices will be reflected in the class instances (see next
section).

The derived class can be realized and "pythonized", just like the root
class::

    ses.realize(kb_church)
    ChurchClass = kb_church.python_class


A more complex example with ID generation and multivalues
---------------------------------------------------------

Let's now create a new ``ChurchClass`` object, giving a value to its
attributes::

    c = ChurchClass('A test church')
    c.is_open = False
    c.height = 24
    c.location = 'Faraway Place'
    c.completion = '1342-01-01'
    c.number_of_naves = 'Two'
    c.nearby_buildings.append(b)

In this example the ``c`` unique object identifier will be
autogenerated, since the ``explicit_id`` constructor argument was not
provided.

Furthermore, the ``number_of_naves`` and ``nearby_buildings``
attribute identifiers are autogenerated (since ``id_`` was not given
when the class attributes where defined): they resemble their
descriptive names, with some obvious normalization.

It is also interesting to notice the behaviour of the
``nearby_buildings`` attribute: its type describes object references
restricted to instances of ``BuildingClass`` (or its derivatives).
Furthermore, the attribute is declared as ``multivalued``: thus,
instead of being scalar, it is a list (initially empty), whose values
can be added or removed.


Saving objects
--------------

Newly-created objects (in this example, ``b`` and ``c``) are not
automatically persisted in the underlying SQL DB: they need to be
added to the current transaction, which in turn needs to be committed.::

    ses.add_all([b, c])
    ses.commit()

An explicit :py:meth:`commit() <session.Session.commit>` is needed
whenever the knowledge base is being modified, e.g. when objects or
classes are updated or deleted (as we will see in the next sections).


Retrieving classes and objects from the knowledge base
------------------------------------------------------

The knowledge base can be queried in order to retrieve the existing
classes and objects.  Let's say that we've closed the previous working
session (e.g. by exiting the Python interpreter), and that we're
now opening a new one::

    from tinykb.session import Session
    ses = Session('postgresql://username:password@localhost/tinykb')

Class identifiers can be used to retrieve specific :py:class:`KBClass`
instances, or the related Python class::

    kb_building = ses.class_('building')
    ChurchClass = ses.python_class('church')

Here, we've obtained the same knowledge base classes of the previous
examples: thus, ``KBBuilding`` is a :py:class:`ses.orm.KBRootClass
<orm.KBRootClass>` object, while ``ChurchClass`` is a ready-to-use
Python class mapped to the underlying SQL DB.

Specific knowledge base objects can be retrieved using their ID as
well::

    b = ses.object('test_building')

It's also possible to collect all the objects belonging to a given
knowledge base class::

    churches = ses.objects(ChurchClass)

Here, ``churches`` is a SQLAlchemy query object yielding all the
``ChurchClass`` instances.  Since we know that there is one such
instances (i.e. the one we created previously), we can use::

    c = churches[0]

in order to retrieve it.  Otherwise::

    lst = churches.all()

will return a list containing all the ``ChurchClass`` instancess.


Advanced knowledge base queries
-------------------------------

TinyKB is (partly) based on the `SQLAlchemy object-relational
mapper`_, and thus it is possible to use its `query language`_ in order
to explore and filter the contents of the knowledge base.

For example, it is possible to select knowledge base objects according
to the values of their fields.  The ``churches`` query object defined
in the previous section may be used to build new queries, such as::

    q1 = churches.filter(ChurchClass.height > 20)
    q2 = churches.filter(ChurchClass.height > 40)

Given the knowledge base built in the previous examples, ``q1.all()``
will retrieve a list with one element, while ``q2.all()`` will return
an empty list.

It is also possible to use object cross-references for filtering.  If
we need to retrieve all the churches with a nearby building completed
after January 1st, 1901, we could execute something like::

    from datetime import date
    BuildingClass = kb_building.python_class

    q3 = churches.filter(
             ChurchClass.nearby_buildings.any(
                 BuildingClass.completion > date(1901, 01, 01)))

Right now, only a handful of SQLAlchemy query capabilities are exposed
through the TinyKB :py:class:`Session <session.Session>` API, but this
feature is expected to be more widely supported (and documented) in
the next releases.  If you are interested in more advanced knowledge
base queries, you can refer to the ``session.py`` source code for some
hints.

.. _SQLAlchemy object-relational mapper: http://www.sqlalchemy.org/docs/orm/

.. _query language: http://www.sqlalchemy.org/docs/orm/tutorial.html#querying


Deleting objects
----------------

Objects can be deleted by invoking the :py:meth:`delete()
<session.Session.delete>` method of the session object, and committing
the current transaction::

    ses.delete(c)
    ses.commit()


Deleting classes
----------------

Knowledge base classes can be deleted if (and only if) they have no
instances, and they are not referenced by other classes.  Since we
have deleted the only ``ChurchClass`` instance, we can now execute::

    kb_church = ses.class_('church')
    ses.delete(kb_church)
    ses.commit()

After the commit, the class-related SQL DB tables and structures
(i.e. the ones created with :py:meth:`realize()
<orm.KBClass.realize>`) will be cleaned up as well.


NotreDAM integration: workspaces and users
------------------------------------------

.. note:: the following examples will only work when used on a SQL DB
          populated by NotreDAM scripts.

TinyKB is distributed along with `NotreDAM`_, and it currently
supports its *workspaces* through one querying method::

    ws = ses.workspace(1)

here, ``ws`` is a :py:class:`orm.Workspace` instance mapped to the
NotreDAM workspace with ID ``1``.

Class hierarchies can be exposed on one or more workspaces according
to the access rules defined in the :py:mod:`access` module::

    ws.setup_root_class(kb_building, access.OWNER)
    ses.commit()

Access rules are not directly enforced by TinyKB (e.g. read-only class
hierarchies could be updated without any control).  However,
workspaces can be used to easily filter knowledge base queries::

    ws_classes = ses.classes(ws=ws)
    ws_objects = ses.objects(ws=ws)

This way, ``ws_classes`` and ``ws_objects`` will only contain
classes/objects whose root class was previously exposed on ``ws``
using :py:meth:`orm.Workspace.setup_root_class()`.

A similar, limited integration is provided for NotreDAM *users*::

    users = ses.users()

where ``users`` is query object yielding :py:class:`orm.User` instances.

.. _NotreDAM: http://www.notredam.org/
