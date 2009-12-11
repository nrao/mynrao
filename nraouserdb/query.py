import logging

from itertools import tee

from urlparse import urlparse, urlunparse
from urllib import urlencode

import urllib2
from urllib2 import URLError

import new

import lxml.etree as ET

from caslib import login_to_cas_service, CASLoginError


_log = logging.getLogger(__name__)


class XMLNS(object):
    '''Utility class to generate xml names using clark notation'''

    def __init__(self, ns=None):
        self.ns = ns

    def __getitem__(self, attr, default=None):
        if self.ns:
            return '{%s}%s' % (self.ns, attr.replace('_', '-'))
        return attr

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)

        except AttributeError:
            return self[attr]

nrao = XMLNS('http://www.nrao.edu/namespaces/nrao')


class TryAuthenticating(RuntimeError):
    '''Perhaps you should try logging in?  Mmmm?'''

    login_url = None
    '''The last url retrieved'''

    def __init__(self, login_url, *args):
        super(TryAuthenticating, self).__init__(*args)
        self.login_url = login_url


class NRAOUserDB(object):

    def __init__(self, url, username=None, password=None, opener=None):
        '''

        :param url:             Location of the QueryFilter service
        :param username:        Account that may query the user database
        :param password:        Password for username
        :param opener:          Optional configured :class:`urllib2.OpenerDirector`
        '''

        self.url = url
        self.username = username
        self.password = password
        self.opener = opener

    def _get_user_data(self, url):
        # This interface is kind of dodgy, we have a few different failure modes to cover.
        try:
            fh = self.opener.open(url)
            login_url = fh.url

        except URLError, e:
            # URLError - We _could_ get this if PST sent an error code
            # other wise it's probably a connection or configuration problem.
            raise TryAuthenticating(getattr(e, 'url', url), str(e))

        doc_str = fh.read(0x4000)

        if doc_str == '<?xml version="1.0" encoding="UTF-8"?>\n':
            return None

        try:
            query_result = ET.fromstring(doc_str)

        except SyntaxError, e: # lxml.etree will generate this
            # Sometimes people say UTF-8, but they don't really mean it.  That's cool.
            if isinstance(e, ET.XMLSyntaxError) and e.code == ET.ErrorTypes.ERR_INVALID_CHAR:
                doc_str = doc_str.decode('latin1', 'UTF-8').encode('utf-8')
                try:
                    query_result = ET.fromstring(doc_str)

                except SyntaxError, e:
                    raise TryAuthenticating(login_url, 'received something that was not well formed xml; maybe a login form?')

            else:
                # Probably the HTML login page
                raise TryAuthenticating(login_url, 'received something that was not well formed xml; maybe a login form?')

	return query_result.find(nrao.user)


    def get_user_data(self, username=None, database_id=None):
        '''Try to retrieve user profile information for a user'''

        scheme, host, path, params, query, fragment = urlparse(self.url)
        if username:
            query = urlencode([('userByAccountNameEquals', username)], True)
        elif database_id:
            query = urlencode([('userById', database_id)], True)
        else:
            raise TypeError('%s.get_user_data requires a username or database_id keyword argument' % type(self).__name__)
        url = urlunparse((scheme, host, path, params, query, fragment))

        _log.info('Retrieving user profile for: %s', username or '#%s' % database_id)

        try:
            user_data = self._get_user_data(url)

        except TryAuthenticating, e:
            # TryAuthenticating may be a good idea, better tell an adult!
            if not e.login_url or not self.username:
                _log.exception(e)
                raise

            # This may raise a URLError or CASLoginError.  There's nothing much
            # to be done about it though, so I'm not handling it.
            _log.info('Failed: %s', e)
            # FIXME: It would be good to check that we haven't been redirected
            # someplace strange before we send off our credentials.  Hopefully
            # certificate validation will lessen this possibility.
            login_to_cas_service(e.login_url, self.username, self.password, opener=self.opener)

            # If that worked, then give it another go
            user_data = self._get_user_data(url)

        if user_data is not None: # FutureWarning says test for None
            return user_data


