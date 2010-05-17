=============================================
 Hacking on nraouserdb: a guide to internals
=============================================

Summary
=======

nraouserdb requests user information from the NRAO user database server, using
caslib to perform the required authentication against the NRAO CAS server.

Tests and prose to explain internals go here.

>>> import nraouserdb.cli
>>> nraouserdb.cli.first # doctest: +ELLIPSIS
<function first at ...>
>>> nraouserdb.cli.first([1,2,3])
1
