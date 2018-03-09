#!/usr/bin/env python
# vim:set noet fileencoding=utf8:
'''test if :abbr:`YUM (Yellowdog Updater, Modified)` repositories are reachable

Main features:

* run as user (does not require administrative privileges)
* can use a custom list of repositories
* `Nagios plugin API`_ compatible

.. _Nagios plugin API: https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/pluginapi.html
'''

# stdlib
import atexit
import logging
import optparse
import os
import posix
import shutil
import sys

# dependencies
import yum # tested against version 3.4.3
import yum.Errors





__version__ = '0.0.1'
logger = logging.getLogger(__file__)
EXIT_SUCCESS = 0
EXIT_FAILURE = 1





class Sysexit(SystemExit):
	'''inspiration from BSD `sysexits.h`

	.. Warning::
	   As it subclass :exception:`SystemExit`,
	   the Python interpreter exits on unhandled raises.

	See also:

	* :manpage:`exit(3)`
	* :func:`os._exit` and the following exit codes
	'''
	def __init__(self, code, message=None):
		'''
		:param int code:
		:param str message:
		'''
		super(Sysexit, self).__init__(code)
		self.message = message


	def __str__(self):
		return '' if self.message is None else self.message


	def __repr__(self):
		for k, v in posix.__dict__.items():
			if k[:3] == 'EX_' and v == self.code:
				data = k
				break
		else:
			data = '[{}]'.format(self.code)

		if self.message:
			data+= ': {}'.format(self.message)

		return data



class NotYumBase(yum.YumBase):
	def __init__(self, conf=None, reposdir=None):
		'''custom initialization

		Inspiration from: pakrat_ 0.3.2: ``pakrat.pakrat.yumbase.YumBase``

		.. _pakrat: https://github.com/ryanuber/pakrat/

		:param str conf: path to a :file:`yum.conf`
		:param reposdir: override configuration "reposdir"
		:type reposdir: None or list(str)
		'''
		yum.YumBase.__init__(self)
		self.preconf = yum._YumPreBaseConf()
		if conf is not None:
			self.preconf.fn = conf
		self.prerepoconf = yum._YumPreRepoConf()
		self.__setTemporaryCacheDir()
		self.__fix_paths(reposdir)


	def __setTemporaryCacheDir(self):
		'''create a unique, temporary cache dir

		It will be cleaned up at the end of the script.
		'''
		cache_dir = yum.misc.getCacheDir()
		if not cache_dir:
			logger.error(
				'unable to get a cache dir, '
				'we have been bollocksed'
			)
			raise IOError

		logger.debug('conf.cache_dir: %s', cache_dir)
		self.setCacheDir(
			force=True,
			reuse=False,
			tmpdir=cache_dir,
		)
		atexit.register(
			shutil.rmtree,
			path=cache_dir,
			ignore_errors=True,
		)


	def __fix_paths(self, reposdir=None):
		'''
		:param reposdir: override configuration "reposdir"
		:type reposdir: None or list(str)
		'''
		conf_pwd = os.path.dirname(
			os.path.realpath(self.conf.config_file_path)
		)

		if reposdir is None:
			reposdir = self.conf.reposdir
			reposdir_pwd = conf_pwd
		else:
			reposdir_pwd = os.getcwd()

		self.conf.reposdir = []
		for item in set(reposdir):
			if not os.path.isabs(item):
				item = os.path.realpath(
					os.path.join(
						reposdir_pwd,
						item,
					)
				)
			self.conf.reposdir+= [item]
		logger.debug(
			'conf.reposdir: %s',
			', '.join(self.conf.reposdir),
		)


	def check_repository(self, repository):
		'''attempt to load remote repository metadata

		:param repository:
		:type repository: str or ~yum.yumRepo.YumRepository
		:rtype: bool
		:raise: never
		'''
		result = None
		try:
			if not isinstance(repository, yum.yumRepo.YumRepository):
				repository = self.repos.repos[repository]
			result = repository._getFileRepoXML(
				repository.cachedir + '/repomd.xml',
			)
		except KeyError:
			logger.error('repository not found: %r', repository)
		except yum.Errors.RepoError:
			logger.error(
				'repository in error: %s',
				repository.id,
				exc_info=True
			)
		except:
			logger.error(
				'unhandled exception for: %s',
				repository.id,
				exc_info=True
			)

		if result is None:
			logger.error('unable to access: %s', repository.id)
			return False

		return True


	def check_repositories(self, repositories):
		'''call :meth:`check_repository` on each

		:param repositories:
		:type repositories: list(~yum.yumRepo.YumRepository)
		:rtype: list(tuple(str, bool))
		'''
		return [
			(repository.id, self.check_repository(repository.id))
			for repository in repositories
		]



def check_and_show(yb, repositories, nagios=False):
	'''
	:param yum.YumBase yb:
	:param list repositories: list of repositories to check
	:param bool nagios: if True, change output and return code
	                    to be Nagios compatible
	:type repositories: list(~yum.yumRepo.YumRepository)
	'''
	status = EXIT_SUCCESS
	data = yb.check_repositories(repositories)
	data.sort()

	if nagios:
		# nagios is too dumb to read stderr
		# even if it's said multi-lines output is supported,
		# it does not seems to be always the case
		fmt = '{}: {}; '.format
		stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
		out = err = lambda *a: stdout.write(fmt(*a))
	else:
		fmt = '{}: {}\n'.format
		out = lambda *a: sys.stdout.write(fmt(*a))
		err = lambda *a: sys.stderr.write(fmt(*a))

	for repository_id, is_ok in data:
		if is_ok:
			out.write('OK: {}\n'.format(repository_id))
		else:
			err.write('FAIL: {}\n'.format(repository_id))
			status = EXIT_FAILURE

	if status != EXIT_SUCCESS and nagios:
		sys.stdout.write('\n')
		return 2

	return status




def main():
	''':abbr:`CLI (Command Line Interface)`

	:rtype: int
	'''
	_yumprebaseconf = yum._YumPreBaseConf()

	parser = optparse.OptionParser()
	parser.add_option('-q', '--quiet', action='store_const', const=0, dest='verbose')
	parser.add_option('-v', '--verbose', action='count', default=2)
	parser.add_option('-m', '--man', action='store_true')

	group = optparse.OptionGroup(parser, 'YUM configuration')
	group.add_option('-c', '--conf', default=_yumprebaseconf.fn,
		help='path to configuration file (%default)')
	group.add_option('-R', '--reposdir', action='append',
		help='override yum.conf "reposdir"')
	group.add_option('--logfile', default='/dev/stderr',
		help='path to log file (%default)')
	parser.add_option_group(group)

	group = optparse.OptionGroup(parser, 'Actions')
	group.add_option('--list-repos', action='store_true', default=False)
	group.add_option('--nagios', action='store_true', default=False,
		help='nagios compatible output and return codes')
	parser.add_option_group(group)

	# parse options
	opt, args = parser.parse_args()
	logging.basicConfig(
		format='%(levelname)s: %(message)s',
		datefmt='%F %T',
		level=min(max(logging.CRITICAL - (opt.verbose * 10), logging.DEBUG), logging.CRITICAL)
	)

	if opt.man:
		help(__name__)
		return EXIT_SUCCESS

	yb = NotYumBase(opt.conf, opt.reposdir)

	yb.conf.logfile = opt.logfile

	# act!
	if opt.list_repos:
		for repo in yb.repos.repos.itervalues():
			sys.stdout.write(
				'{}: {}\n'.format(repo.id, repo.name)
			)
		return EXIT_SUCCESS

	if args:
		args = set(args)
		invalid = args.difference(yb.repos.repos)
		if invalid:
			logger.error(
				'invalid repositor%s: %s',
				'y' if len(invalid) == 1 else 'ies',
				', '.join(sorted(invalid)),
			)
			return os.EX_USAGE
		repositories = [
			repository
			for repository in yb.repos.repos.itervalues()
			if repository.id in args
		]
		if not repositories:
			return os.EX_NOINPUT
	else:
		repositories = yb.repos.repos.values()

	if not repositories:
		logger.error('no repositories found')
		return os.EX_CONFIG

	# ...
	return check_and_show(yb, repositories, nagios=opt.nagios)





if __name__ == '__main__':
	sys.exit(main())
