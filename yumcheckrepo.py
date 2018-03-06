#!/usr/bin/env python
'''test if YUM repositories are reachables
'''

# stdlib
import atexit
import logging
import optparse
import os
import shutil
import sys

# dependencies
import yum # tested against version 3.4.3
import yum.Errors





logger = logging.getLogger(__file__)
EXIT_SUCCESS = 0
EXIT_FAILURE = 1





class NotYumBase(yum.YumBase):
	def __init__(self, conf=None):
		'''create a new YumBase

		Inspiration from: pakrat_: pakrat.pakrat.yumbase.YumBase

		.. _pakrat: https://github.com/ryanuber/pakrat/

		:param str conf: path to a yum.conf
		'''
		yum.YumBase.__init__(self)
		self.preconf = yum._YumPreBaseConf()
		if conf is not None:
			self.preconf.fn = conf
		self.preconf.debuglevel = 0
		self.prerepoconf = yum._YumPreRepoConf()
		self.__setTemporaryCacheDir()


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

		logger.debug('cache_dir: %s', cache_dir)
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


	def check_repository(self, repository):
		'''call :meth:`yum.yumRepo.YumRepository.verify` and catch errors

		:param repository:
		:type repository: str or yum.yumRepo.YumRepository
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
		'''
		:param repositories:
		:type repositories: list(yum.yumRepo.YumRepository)
		:rtype: list(tuple(str, bool))
		'''
		return [
			(repository.id, self.check_repository(repository.id))
			for repository in repositories
		]



def check_and_show(yb, repositories, nagios=False):
	'''
	:param yum.YumBase yb:
	:param repositories:
	:type repositories: list(yum.yumRepo.YumRepository)
	'''
	status = EXIT_SUCCESS
	data = yb.check_repositories(repositories)
	data.sort()

	if nagios:
		# nagios is too dumb to read stderr
		out = err = sys.stdout
	else:
		out, err = sys.stdout, sys.stderr

	for repository_id, is_ok in data:
		if is_ok:
			out.write('OK: {}\n'.format(repository_id))
		else:
			err.write('FAIL: {}\n'.format(repository_id))
			status = EXIT_FAILURE

	if status != EXIT_SUCCESS and nagios:
		return 2

	return status




def main():
	'''CLI

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

	yb = NotYumBase(opt.conf)

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
