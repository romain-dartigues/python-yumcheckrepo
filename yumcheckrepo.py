#!/usr/bin/env python
'''test if YUM repositories are reachables
'''

# stdlib
import atexit
import logging
import multiprocessing.pool
import optparse
import os
import shutil
import sys

# dependencies
import yum # tested against version 3.4.3





logger = logging.getLogger(__file__)





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
		:rtype: list
		:return: list of errors or empty list if none
		'''
		try:
			if not isinstance(repository, yum.yumRepo.YumRepository):
				repository = self.repos.repos[repository]
			return repository.verify()
		except KeyError:
			return ['repository not found: %s' % (repository,)]
		except BaseException as error:
			return ['exception: %s' % (error,)]


	def check_repositories(self, repositories):
		'''
		:param list repositories: list of :class:`yum.yumRepo.YumRepository`
		:return: a list of problems per repository ID
		:rtype: dict
		'''
#		pool = multiprocessing.pool.ThreadPool(
#			processes=len(repositories),
#		)
		pool = multiprocessing.pool.Pool(
			processes=len(repositories),
		)

		results = []
		for repository in repositories:
			results+= [(
				repository.id,
				pool.apply_async(
					self.check_repository,
					(repository.id,),
				),
#				pool.apply_async(repository.verify),
			)]

		problems = {}
		for repo_id, job in results:
			try:
				data = job.get()
			except BaseException as error:
				logger.warning(
					'%s: %r %s',
					repo_id,
					error,
					error,
					exc_info=True
				)
				data = error
			if data:
				problems[repo_id] = data

		return problems



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
		return os.EX_OK

	yb = NotYumBase(opt.conf)

	yb.conf.logfile = opt.logfile

	# act!
	if opt.list_repos:
		for repo in yb.repos.repos.itervalues():
			sys.stdout.write(
				'{}: {}\n'.format(repo.id, repo.name)
			)
		return os.EX_OK

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
	problems = yb.check_repositories(repositories)
	if problems:
		logger.warning(
			'problem(s) found',
		)
		for repo_id, data in problems.iteritems():
			sys.stderr.write(
				'{}: {}\n'.format(
					repo_id,
					', '.join(sorted(data)),
				)
			)
		return 1

	return os.EX_OK





if __name__ == '__main__':
	sys.exit(main())
