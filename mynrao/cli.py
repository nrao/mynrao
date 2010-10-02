import sys

import os.path
import errno

import logging

import copy

import urllib2
from cookielib import MozillaCookieJar

import optparse
import ConfigParser

from getpass import getpass

import lxml.etree as ET

from mynrao import NRAOUserDB, TryAuthenticating


CONFIG_FILE = '~/.mynraorc'

def first(seq):
    '''Return the head element of the sequence.

    >>> first([0, 1, 2, 3])
    0
    >>> first((7, 8, 9))
    7
    >>> first({0: 'zero', 1: 'one'})
    0
    >>> first([])
    >>>
    '''
    for x in seq:
	return x

class Symbol(object):
    _registry = {}
    def __new__(cls, name):
	if name not in cls._registry:
	    cls._registry[name] = object.__new__(cls, name)
	return cls._registry[name]

    def __init__(self, name):
	self.name = name
    def __eq__(self, them):
	if not isinstance(them, type(self)):
	    them = Symbol(them)
	return them is self
    def __repr__(self):
	return self.name

    @classmethod
    def lookup(cls, name):
	return cls._registry[name]


def main():
    class UsageError(RuntimeError): pass

    def preparse_args_dumbly(parser):
	'''Configure and run an option parser in a no side-effects mode.'''

	preparser = copy.copy(parser)

	preparser.print_usage = lambda file=None: None
	preparser.print_version = lambda file=None: None
	preparser.print_help = lambda file=None: None
	# Overriding OptionParser.error with a function that returns is forbidden.
	# But... this works, and it probably isn't going to change.
	preparser.error = lambda msg: None
	# I suppose it doesn't need to be said OptionParser.exit that making
	# OptionParser.exit return is probably forbidden.  But, I'm saying it
	# anyway and I'm violating that rule too.  HAH!
	preparser.exit = lambda code=0, msg=None: None

	return preparser.parse_args()


    try:
	GLOBAL_ID = Symbol('GLOBAL_ID')
	DATABASE_ID = Symbol('DATABASE_ID')
	ACCOUNT_NAME = Symbol('ACCOUNT_NAME')
	EMAIL_ADDRESS = Symbol('EMAIL_ADDRESS')

	parser = optparse.OptionParser()
        parser.add_option('-v', '--verbose', dest='verbose', action='count',
                help='Be verbose(r)')
	parser.add_option('-f', '--file', dest='config',
		help='Load configuration from CONFIG[#SECTION] (%s)' % CONFIG_FILE)
	parser.add_option('-L', '--location', dest='location',
		help='The location of the query filter web service (%default)')
	parser.add_option('-u', '--username', dest='username',
		help='Username to authenticate to the web service (%default)')
	parser.add_option('-p', '--password', dest='password', default=getpass,
		help='Password to authenticate to the web service')
	parser.add_option('-C', '--ca_certs', dest='ca_certs',
		help='Cert/CA file to validate SSL connection against (%default)')
	parser.add_option('-c', '--cookiejar', dest='cookiejar',
		help='Cookie jar to store session information in (%default)')
	parser.add_option('-G', '--globalid', dest='query_by',
		action='store_const', const=GLOBAL_ID,
		help='Arguments are global-ids (not implemented)')
	parser.add_option('-I', '--databaseid', dest='query_by',
		action='store_const', const=DATABASE_ID,
		help='Arguments are database-ids')
	parser.add_option('-A', '--accountname', dest='query_by',
		action='store_const', const=ACCOUNT_NAME,
		help='Arguments are account-names')
	parser.add_option('-E', '--email', dest='query_by',
		action='store_const', const=EMAIL_ADDRESS,
		help='Arguments are email addresses')
	parser.add_option('--pretty', dest='pretty',
		action='store_true', help='Pretty print XML')

	options, args = preparse_args_dumbly(parser)
	user_config_file = options.config

	# Load the user's config file or a default.
	if user_config_file is not None:
	    config_file = user_config_file
	else:
	    config_file = CONFIG_FILE
        if '#' in config_file:
            config_file, section = config_file.split('#', 1)
        else:
            section = None
	config_file = os.path.expanduser(config_file)

	try:
	    fh = open(config_file)

	except IOError, e:
	    # If the user did not specify a config file and it doesn't exist, that's ok.
	    if user_config_file is None and e.errno == errno.ENOENT:
		pass

	    else:
		raise

	else:
	    config = ConfigParser.ConfigParser()
	    config.read(config_file)

	    if not section:
		section = first(config.sections())

	    getcf = lambda k, default=None: config.has_option(section, k) and config.get(section, k) or default
	    parser.set_defaults(
		location=getcf('location'),
		username=getcf('username'),
		password=getcf('password', getpass),
		ca_certs=getcf('ca_certs'),
		cookiejar=getcf('cookiejar'),
		query_by=getcf('query_by'),
	    )

	options, args = parser.parse_args()

	if not options.location:
	    # That's a dealbreaker!
	    raise UsageError('specify the location of the web service to query')

	# Don't use the validating https handler unless it is configured.  This
	# way it won't abort unless the user has configured it.
	https_handler = urllib2.HTTPSHandler
	if options.ca_certs:
	    from caslib.validating_https import ValidatingHTTPSConnection
	    class HTTPSConnection(ValidatingHTTPSConnection):
		ca_certs = options.ca_certs
	    https_handler = HTTPSConnection.HTTPSHandler

	opener = urllib2.build_opener(https_handler)

	if options.cookiejar:
	    cookiejar = MozillaCookieJar(os.path.expanduser(options.cookiejar))
	    try:
		cookiejar.load(ignore_discard=True)
	    except IOError:
		pass
	    opener.add_handler(urllib2.HTTPCookieProcessor(cookiejar=cookiejar))

        if not options.verbose:
            logging.basicConfig(level=logging.WARNING)
        elif options.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.DEBUG)
	userdb = NRAOUserDB(options.location, options.username, options.password, opener)

	for key in args:
	    if options.query_by == DATABASE_ID:
		user = userdb.get_user_data(database_id=key)

	    elif options.query_by == ACCOUNT_NAME:
		user = userdb.get_user_data(username=key)

	    elif options.query_by == EMAIL_ADDRESS:
		user = userdb.get_user_data(email=key)

	    elif options.query_by == GLOBAL_ID:
		user = userdb.get_user_data(global_id=key)

	    else:
		raise UsageError('No such query type exists: %r' % options.query_by)

	    if user is None:
		print >>sys.stderr, "%s: no record found" % key;
		continue

	    if options.pretty:
		# Strip out extra whitespace, so we can have maximum prettiness.
		for el in user.iter():
		    if el.text and not el.text.strip():
			el.text = None
		    if el.tail and not el.tail.strip():
			el.tail = None
		print ET.tostring(user, pretty_print=True, encoding='utf-8')

	    else:
		print ET.tostring(user, encoding='utf-8')

	# FIXME: Add locking to cookiejar, so concurrent instances don't clobber the cookie file.
	if options.cookiejar:
	    try:
		cookiejar.save(ignore_discard=True)
	    except IOError, e:
		print >>sys.stderr, 'Error while saving cookie jar: %s: %s' % ( options.cookiejar, e )

    except UsageError, e:
	print >>sys.stderr, e
	return 64 # EX_USAGE

    except ConfigParser.ParsingError, e:
	print >>sys.stderr, e
	return 78 # EX_CONFIG

    except NotImplementedError, e:
	print >>sys.stderr, e
	return 69 # EX_UNAVAILABLE

    except TryAuthenticating, e:
	print >>sys.stderr, 'Authentication probably failed: ', e
	return 77 # EX_NOPERM

    except IOError, e:
	if isinstance(e, urllib2.URLError) and '_ssl.c' in str(e.reason) and 'error:00000000:lib(0):func(0):reason(0)' in str(e.reason):
	    print >>sys.stderr, 'SSL error'
	else:
	    print >>sys.stderr, e
	return 74 # EX_IOERR

    #except Exception, e:
	#print >>sys.stderr, 'Failure: %s: %s' % (e.__class__.__name__, e)
	#return 70 # EX_SOFTWARE


if __name__ == '__main__':
    sys.exit(main())

