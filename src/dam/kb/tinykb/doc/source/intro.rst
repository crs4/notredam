Introduction
============

TinyKB is a Python module for implementing and managing *knowledge
bases* composed by cross-referencing *classes* and *objects*
(i.e. class instances) containing both scalar and vectorial
*attributes*.

TinyKB classes are similar to those offered by object-oriented
programming languages: they are defined with a set of strongly-typed
attributes, and support single inheritance; furthermore, they can be
used to dynamically generate Python classes, which in turn can
instantiate Python objects.  Both those Python classes and objects are
automatically mapped and stored into a SQL data base.

TinyKB tries to leverage the full power of the SQL language and DBMSs,
avoiding the "key/value" approach usually adopted when the data schema
is unknown until run-time (i.e. when dealing with "unstructured"
data).  TinyKB reflects class definitions in the underlying SQL DB
schema:

    * classes and attributes are mapped to dynamically generated
      tables and columns;

    * class hierarchies and cross-references are implemented with
      referential constraints;

    * constraints on object attributes are enforced using DBMS checks.

This approach brings three advantages:

    #. the SQL representation of the KB is clean, data-centric and
       application-agnostic;

    #. the SQL DBMS becomes an additional safety layer
       ensuring data integrity;

    #. the knowledge base can be explored and queried with the full
       power of SQL, avoiding excessive ``JOIN`` usage.

TinyKB provides a developer-friendly API which hides its SQL
machinery.  Under the hood, `SQLAlchemy`_, Python metaprogramming and
other run-time features are used to dynamically generate modules and
classes, thus offering a transparent mapping to the underlying
knowledge base.

TinyKB is integrated (and distributed with) `NotreDAM`_, but it could
be easily readapted into a stand-alone product (NotreDAM-specific parts
are outlined throughout this documentation).

This manual illustrates the main TinyKB concepts through several
examples (see :doc:`basics`) and then documents the API of the main
modules.  The last chapter, in particular, explains some details about
design and extension of the SQL DB schema (see :doc:`schema`).

.. warning:: this is an initial release of the documentation for
             TinyKB |version|, as distributed with NotreDAM 1.08rc1.
             The package is still evolving, and its API may still
             change in backward-incompatible ways.

.. _SQLAlchemy: http://www.sqlalchemy.org/

.. _NotreDAM: http://www.notredam.org/
