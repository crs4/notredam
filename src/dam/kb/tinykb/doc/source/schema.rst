:mod:`schema` --- SQL DB schema
===============================

This module defines the :py:class:`Schema` class, which contains the SQL
DB tables used for storing the knowledge base.  The tables follow the
:ref:`entity-relationship diagram <tinykb_er_diagram>` reported below.

.. warning:: This is an internal module, and its API may (and probably
             will) change.  The E-R diagram, however, is expected to
             remain quite stable over time.  For more details, you
             should check the ``schema.py`` source code and its
             comments.

.. _tinykb_er_diagram:

.. figure:: tinykb-er.*

   Entity-relationship diagram of TinyKB SQL DB schema.  The actual
   implementation is restricted to the portion within the blue area,
   while the rest of the diagram shows not-yet-implemented relations
   planned for better NotreDAM integration.

.. automodule:: schema
   :members:
