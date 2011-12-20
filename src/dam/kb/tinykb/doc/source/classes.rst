:mod:`orm` --- Dynamically mapped module for KB classes
=======================================================

Each knowledge base :py:class:`Session <session.Session>` instance
provides a ``orm`` property: a dynamically generated Python module
giving access to several class definitions, mapped to the knowledge
base session itself.  Those classes are documented below, with their
:ref:`UML diagram <tinykb_uml_diagram>` and their specs.

For some examples of the session ``orm`` usage, see
:ref:`label-kb-root-class`.

Each ``orm`` session module features one important property:

.. attribute:: orm.attributes
    :noindex:
    
    Dynamically generated Python module providing access to KB class
    attribute types (with transparent mapping to the current KB
    session).  For more details, see :py:mod:`orm.attributes`.

.. _tinykb_uml_diagram:

.. figure:: tinykb-uml.*

   Simplified UML diagram for TinyKB classes defined in the
   :py:mod:`orm` session module.  The actual implementation is
   restricted to the portion within the green dashed line, while the
   rest of the diagram shows not-yet-implemented classes planned for
   better NotreDAM integration.  The blue dashed arrows indicate that
   ``KBObject_1``, ``KBObject_2`` and ``KBObject_n`` (which inherit
   from :py:class:`orm.KBObject`) are dynamically generated from
   :py:class:`orm.KBClass` instances.  Those dynamic classes, in turn,
   can be cross-referenced through
   :py:class:`orm.attributes.ObjectReference` attributes (as defined
   in their respective :py:class:`orm.KBClass`).


.. automodule:: orm
   :members:
