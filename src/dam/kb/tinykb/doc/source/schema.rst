:mod:`schema` --- SQL DB schema
===============================

This module defines the :py:class:`Schema` class, which contains the SQL
DB tables used for storing the knowledge base.  The tables follow the
:ref:`entity-relationship diagram <tinykb_er_diagram>` reported below.

.. _tinykb_er_diagram:

.. figure:: tinykb-er.*

   Entity-relationship diagram of TinyKB SQL DB schema.  The actual
   implementation is restricted to the portion within the blue area,
   while the rest of the diagram shows not-yet-implemented relations
   planned for better NotreDAM integration.  The root class identifier
   is reported in several places in order to simplify inheritance and
   class visibility checks, enforcing them at the SQL schema level
   (see :py:meth:`orm.Workspace.setup_root_class`).


SQL schema extension principles
-------------------------------

Knowledge base class definitions are stored in the ``class`` table
(with the related ``class_attribute_*`` tables for additional details
on their attributes), while knowledge base objects are stored in the
``object`` table.  When knowledge base classes are realized (see
:py:meth:`orm.KBClass.realize`), TinyKB creates additional
*class-specific object tables* (or *CSO tables* for short).

In general, each class attribute will result in the creation of a
dedicated column in the corresponding CSO table [#]_.  Furthermore,
class hierarchies are reflected in CSO tables according to the
following rules:

    1. each CSO table *shall* have a primary key which is also a
       reference to the ``object`` table;

    2. if a CSO table is related to a derived class, then it *shall
       also* feature a foreign key constraint against the CSO table
       representing the parent class in the inheritance hierarchy.

For example, let's consider the following class hierarchy::

      Building
       |
       +---- Church
              |
              +---- Cathedral

where ``Building`` is the base class.  Then:

    * the ``Building`` CSO table *shall* have a foreign key constraint
      against the ``object`` table (rule 1);

    * the ``Church`` CSO table *shall also* have a foreign key
      constraint against the ``Building`` CSO table (rule 2);

    * the ``Cathedral`` CSO table *shall also* have a foreign key
      constraint against the ``Church`` CSO table (rule 2).

When a new ``Cathedral`` object is added to the knowledge base, then
its attribute values will be stored in the ``Building``, ``Church``
and ``Cathedral`` CSO tables, according to where they have been
inherited from; the object identifier, instead, will appear in all
three tables, and also in the ``object`` table.  Thus, each
``Cathedral`` object is also a legitimate instance of both ``Church``
and ``Building``.

This approach ensures that:

    #. an object cannot appear in a CSO table without also appearing in
       the main "object registry" (i.e. the ``object`` table);

    #. an object cannot appear in a CSO table without also appearing
       in all the ancestor CSO tables.

.. rubric:: Footnotes

.. [#] Multivalued attributes, instead, will result in the creation of
       additional tables, with proper foreign key constraints against the
       CSO table.


API documentation
-----------------

.. warning:: This is an internal module, and its API may (and probably
             will) change.  The E-R diagram, however, is expected to
             remain quite stable over time.  For more details, you
             should check the ``schema.py`` source code and its
             comments.

.. automodule:: schema
   :members:
