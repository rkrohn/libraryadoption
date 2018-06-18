from datetime import datetime, timedelta
import random as r
from stackoverflow_searcher import Searcher

WINDOW = 0.1		#for windowed stats, take last 10% of a user/repo's commits (once user has at least 5 commits in history)

#User class: contains user id/name, dictionary of used lib->time used, and repo->time of last interaction
class User:
	'''
	User Features (specific to a particular package)
	# packages commited - half-life?			len(quiver)
	# packages implicitly seen				len(seen_libs)
	time since last commit					last_commit
	time since last adoption				last_adopt
	intra-commit duration for last 10% of commits		avg_commit_delta
	already adopted library?				check against adopted_libs
	# repositories commited to				len(repos)
	# repositories commited to in last 10% of commits	last_repos_count()
	% commits with adoptions				adopt_commit_count/commit_count
	% commits with imports					import_commit_count/commit_count
	% commits with adoptions within last 10% of commits	last_adopt_commit_count/len(last_commits)
	% commits with imports within last 10% of commits	last_import_commit_count/len(last_commits)
	# implicitly seen package i				seen_libs_freq[i]
	# implicitly seen package i within last 10% of commits	lib_view_freq() - first return value
	# implicitly seen package i / total # implicit packages seen	seen_libs_freq[i]/sum(seen_libs_freq.values())
	# implicitly seen package i within last 10% commits / total # implicit packages seen within last 10% commits	lib_view_freq : first return / second return
	{packages implicitly seen}				seen_libs
	'''

	def __init__(self, name):
		self.name = name
		self.seen_libs = {}	#dictionary of implicitly seen libraries->last time user saw it
		self.seen_libs_freq = {}	#dictionary of implicitly seen libraries-># of times user has seen it
		self.adopted_libs = {}	#dictionary of adopted lib->time of adoption
		self.quiver = {}	#dictionary of used libraries->last time user "used" it
		self.repos = {}		#dictionary of repo name->time of user's last interaction with repo
		self.last_commit = -1	#time of user's last commit
		self.last_adopt = -1	#time of user's last adoption
		self.commit_count = 0	#number of total commits made by user (imports and not)
		self.import_commit_count = 0	#number of commits containing imports made by user
		self.adopt_commit_count = 0	#number of commits resulting in an adoption (may be smaller than #adoptions)

		#windowed history stuff starts here
		self.last_commits = list()	#list of last 10% of commits (time, repo)
		self.avg_commit_delta = None	#average time between last 10% of user's commits
		self.last_import_commit_count = 0	#number of commits containing import in last 10% of user's commits
		self.last_adopt_commit_count = 0	#number of commits producing adoption in last 10% of user's commits
		

	#given a list of repository updated repos, and the repo name, update user state
	def implicit_view(self, repo_libs, repo, time):	
		#update last seen time and seen frequency for each library
		for lib in repo_libs:
			self.seen_libs[lib] = time
			if lib in self.seen_libs_freq:
				self.seen_libs_freq[lib] += 1
			else:
				self.seen_libs_freq[lib] = 1
		self.repos[repo] = time		#update last interaction time for repository

	#given a library the user used, update the last used time in the user's quiver
	def use_lib(self, lib, time):
		self.quiver[lib] = time

	#log new user commit (not necessarily a library commit), along with purpose of commit: regular commit, lib import, or adoption
	def log_commit(self, time, repo, implicit_libs, has_lib = False, adopt = False):
		self.last_commit = time		#update last commit time
		self.commit_count += 1		#update overall commit count

		#update adopt and import commit counts, both global and windowed
		if adopt:
			self.adopt_commit_count += 1
			self.last_adopt_commit_count += 1
		if has_lib:
			self.import_commit_count += 1
			self.last_import_commit_count += 1
		
		#update list of last_commits, so that history is limited to 10% of all of user's commits (once user passes 5 total commits)
		
		#remove earliest commit if history list too long before updating list and delta-t
		num_commits = len(self.last_commits)		#number of commits in current history list

		#if list long enough to remove oldest commit, do that and update
		if (num_commits) / float(self.commit_count) > WINDOW and num_commits > 5:
			removed = self.last_commits.pop(0)	#remove oldest commit
			delta = ((time-self.last_commits[-1]['time']) - (self.last_commits[0]['time']-removed['time'])) / (num_commits-1)	#compute change to average intra-commit delta-t
			self.avg_commit_delta += delta		#update average intra-commit delta

			#update import/adopt windowed commit counts based on removed commit
			if removed['import']:
				self.last_import_commit_count -= 1
			if removed['adopt']:
				self.last_adopt_commit_count -= 1

		#list not too long, just update avg delta-t
		elif num_commits > 1:
			self.avg_commit_delta = ((time-self.last_commits[-1]['time']) + num_commits * self.avg_commit_delta) / num_commits		
		#second commit, explicitly set the average delta
		elif num_commits == 1:
			self.avg_commit_delta = time - self.last_commits[-1]['time']

		#always append newest commit
		self.last_commits.append({'time': time, 'repo': repo, 'import': has_lib, 'adopt': adopt, 'implicit': implicit_libs})
		
	#log new user adoption
	def log_adopt(self, lib, time):
		self.last_adopt = time	#set last adopt time
		self.adopted_libs[lib] = time	

	#for a particular repository, get time of user's last interaction (-1 if no interaction to date)
	def last_interaction(self, repo):
		if repo not in self.repos:
			return -1
		return self.repos[repo]

	#return a count of the repos this user has committed to in the last 10% of their commits
	def last_repos_count(self):
		#build set of repos from commit history
		last_repos = set()
		for commit in self.last_commits:
			last_repos.add(commit['repo'])
		return len(last_repos)		#return number of repos in set
	
	#return two values: a count of how many times a user has seen the query library, and a count of total library implicit views, both within the last 10% of this user's commits
	def lib_view_freq(self, lib):
		lib_count = 0		#number of times, within last 10% of commits, user has implicitly seen the query library
		total_count = 0		#total number of implicit library views within last 10% of commits, where libraries may be viewed (and counted) more than once

		#loop windowed commit history to get counts
		for commit in self.last_commits:
			if lib in commit['implicit']:
				lib_count += 1
			total_count += len(commit['implicit'])
		return lib_count, total_count