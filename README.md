NRAOUserDB
==========

The nraouserdb module provides a python and command line interface to
retrieving profiles from the NRAO User Database on my.nrao.edu.

Installation
------------

    easy_install -f 'http://www.cv.nrao.edu/~kgroner/python/#nraouserdb' nraouserdb

Command Line
------------

    nraouserdb-query -L http://my.nrao.edu/nrao-2.0/secure/QueryFilter.htm -u $USER -A kgroner
    Password:

    <nrao:user xmlns:nrao="http://www.nrao.edu/namespaces/nrao" id="2947" globalid="2939" domestic="true">
        .
        .
        .
    </nrao:user>

Config File
-----------

    [whatever]
    location=https://mirror.nrao.edu/nrao-2.0/secure/QueryFilter.htm
    username=kgroner
    #Set a password if you don't want to be prompted.  Also, see cookiejar.
    #password=

    # DATABASE_ID or ACCOUNT_NAME or GLOBAL_ID (not implemented)
    query_by=DATABASE_ID

    # nraouserdb-query can save it's session information in
    # this file, so you don't have to authenticate every
    # time.
    cookiejar=~/.nraouserdb-cookies
