=============================================
 Hacking on nraouserdb: a guide to internals
=============================================

Summary
=======

nraouserdb requests user information from the NRAO user database server, using
caslib to perform the required authentication against the NRAO CAS server.

>>> from minimock import Mock, mock

NRAOUserDB
==========


>>> user_xml = '''<?xml version="1.0" encoding="UTF-8"?>
... <nrao:user xmlns:nrao="http://www.nrao.edu/namespaces/nrao" id="1234"
...  globalid="5678" domestic="true">
...   <nrao:name>
...     <nrao:prefix>Mr</nrao:prefix>
...     <nrao:first-name>Roland</nrao:first-name>
...     <nrao:middle-name>C</nrao:middle-name>
...     <nrao:last-name>Guest</nrao:last-name>
...     <nrao:preferred-name>Dude</nrao:preferred-name>
...   </nrao:name>
...   <nrao:contact-info>
...     <nrao:email-addresses>
...       <nrao:default-email-address addr="roland@example.org">
...         <nrao:description>Work</nrao:description>
...       </nrao:default-email-address>
...     </nrao:email-addresses>
...     <nrao:postal-addresses>
...       <nrao:default-postal-address>
...         <nrao:address-type>Office</nrao:address-type>
...         <nrao:address-type>Other</nrao:address-type>
...         <nrao:streetline>123 Some Pl</nrao:streetline>
...         <nrao:city>Charlottesville</nrao:city>
...         <nrao:state>Virginia</nrao:state>
...         <nrao:country>United States</nrao:country>
...         <nrao:postal-code>22903</nrao:postal-code>
...       </nrao:default-postal-address>
...     </nrao:postal-addresses>
...     <nrao:phone-numbers>
...       <nrao:default-phone-number number="1-434-296-0211">
...         <nrao:description>Work</nrao:description>
...       </nrao:default-phone-number>
...     </nrao:phone-numbers>
...   </nrao:contact-info>
...   <nrao:affiliation-info>
...     <nrao:default-affiliation id="4">
...       <nrao:formal-name>National Radio Astronomy Observatory</nrao:formal-name>
...     </nrao:default-affiliation>
...   </nrao:affiliation-info>
...   <nrao:misc-info>
...     <nrao:gender>male</nrao:gender>
...     <nrao:user-type>NRAO Staff</nrao:user-type>
...     <nrao:user-type>All Others</nrao:user-type>
...   </nrao:misc-info>
...   <nrao:account-info>
...     <nrao:account-name>someuser</nrao:account-name>
...     <nrao:encrypted-password>secret</nrao:encrypted-password>
...     <nrao:entry-status>Unknown</nrao:entry-status>
...   </nrao:account-info>
... </nrao:user>
... '''


>>> import nraouserdb.query
>>> from nraouserdb.query import NRAOUserDB
>>> from caslib import login_to_cas_service
>>> login_to_cas_service = Mock('caslib.login_to_cas_service')
>>> nraouserdb.query.login_to_cas_service = login_to_cas_service
>>> url = 'http://example.org/query'
>>> opener = Mock('urllib2.OpenerDirector')
>>> opened = Mock('urllib.addinfourl')
>>> opened.url = url
>>> opened.geturl.mock_returns = url
>>> opened.read.mock_returns = '<?xml version="1.0" encoding="UTF-8"?>\n'
>>> opener.open.mock_returns = opened
>>> userdb = NRAOUserDB(url, 'db-user', 'db-password', opener)
>>> userdb.get_user_data(username='username')
Called urllib2.OpenerDirector.open(
    'http://example.org/query?userByAccountNameEquals=username')
Called urllib.addinfourl.read(16384)
>>>
>>> opened.read.mock_returns = 'Please login...\n'
>>> userdb.get_user_data(username='username')
Traceback (most recent call last):
TryAuthenticating: received something that was not well formed xml; maybe a login form?
>>> opened.read.mock_returns = ''
>>> userdb.get_user_data(username='username')
Traceback (most recent call last):
TryAuthenticating: received something that was not well formed xml; maybe a login form?
>>> opened.read.mock_returns = user_xml
>>> userdb.get_user_data(username='username')
Called urllib2.OpenerDirector.open(
    'http://example.org/query?userByAccountNameEquals=username')
Called urllib.addinfourl.read(16384)
