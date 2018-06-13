import json
import datetime
import random as r

WINDOW = 0.1		#for windowed stats, take last 10% of a user/repo's commits (once user has at least 5 commits in history)

#User class: contains user id/name, dictionary of used lib->time used, and repo->time of last interaction
class User:
	'''
	User Features
	# packages commited - half-life?			len(quiver)
	# packages implicitly seen				len(seen_libs)
	time since last commit					last_commit
	time since last adoption				last_adopt
	intra-commit duration for last 10% of commits		avg_commit_delta
	# repositories commited to				len(repos)
	# repositories commited to in last 10% of commits	last_repos_count()
	% commits with adoptions				adopt_commit_count/commit_count
	% commits with imports					import_commit_count/commit_count
	% commits with adoptions within last 10% of commits	last_adopt_commit_count/len(last_commits)
	% commits with imports within last 10% of commits	last_import_commit_count/len(last_commits)
	# implicitly seen package i				seen_libs_freq[i]
	# implicitly seen package i within last 10% of commits
	# implicitly seen package i / total # implicit packages seen	seen_libs_freq[i]/sum(seen_libs_freq.values())
	# implicitly seen package i within last 10% commits / total # implicit packages seen within last 10% commits
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
	def log_commit(self, time, repo, has_lib = False, adopt = False):
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
		self.last_commits.append({'time': time, 'repo': repo, 'import': has_lib, 'adopt': adopt})
		
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
		

class Repo:
	def __init__(self, name):
		self.name = name	#repo name
		self.libs = {}		#dictionary of library->last time lib used/updated

	#given library used in the repository, update time of last use
	def use_lib(self, lib, time):
		self.libs[lib] = time

	#return the time of last use for a particular library
	def last_interaction(self, lib):
		return self.libs[lib]

#global dictionaries of user and repo objects, key is name/id, value is class object
users = {}
repos = {}

#given a single commit, process and update user/repo library listings and identify any adoption events
def process_commit(c):
	#grab commit fields: user, repo, time
	repo = c['repo']
	time = int(c['time'])
	if c['user'] == '':
		print(c)
		user = 0
	else:
		user = int(c['user'])

	#print(datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S'))

	added_libs = c['add_libs']
	deleted_libs = c['del_libs']

	#change added/deleted_libs so that "moved libs" i.e., libs that are added and deleted in the same commit are not considered for adoptions
	added_and_deleted = set(added_libs).intersection(set(deleted_libs))
	deleted_libs = [item for item in deleted_libs if item not in added_and_deleted]
	added_libs = [item for item in added_libs if item not in added_and_deleted]

	#grab repo object, create if doesn't exist yet
	if repo not in repos:
		repos[repo] = Repo(repo)
	repo = repos[repo]

	#grab user object, create if doesn't exist yet
	if user not in users:
		users[user] = User(user)
	user = users[user]

	#updated_libs are those libraries that were implicitly viewed by the user via a pull (immediately) before a commit
	updated_libs = [lib for lib in repo.libs if repo.last_interaction(lib) > user.last_interaction(repo)]

	#if an added lib is in updated_lib but not in the user's quiver, then it must be an adoption
	adopt = False
	for lib in added_libs:
		if lib in updated_libs and lib not in user.quiver:
			#found an adoption! log it
			user.log_adopt(lib, time)
			adopt = True
			if r.random() > .9:
				print(user.name, 'adopts', lib, 'at:', datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S'))

	#update user state based on new libraries seen
	user.implicit_view(updated_libs, repo, time)	

	#log this commit, import/adoption or not
	if len(added_libs) != 0:
		user.log_commit(time, repo.name, True, adopt)	#yes, commit contains add import
	else:
		user.log_commit(time, repo.name, False, adopt)	#no, commit contains no add imports

	#resolve updates
	for added_lib in added_libs:
		user.use_lib(added_lib, time)
		repo.use_lib(added_lib, time)

#stream json data one object at a time (generator function)
def stream(f):
	obj_str = ''
	f.read(1) 	#eat first [
	while True:
		c = f.read(1)	#read one character at a time
		#end of file, quit
		if not c:
			print('EOF')
			break
		#skip newline characters
		if c == '\n':
			continue
		#remove backslashes
		if c == '\'':
			c = '"'
		obj_str = obj_str + c	#add character to current object string
		#when reach end of object, parse json and return resulting object
		if c == '}':
			obj_str = obj_str.replace('u"', '"')	#remove all unicode prefixes
			yield json.loads(obj_str)		#return json object
			obj_str = ''	#clear for next read
			c = f.read(1) 	#eat comma between objects

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":
	#stream data from sorted json file
	f = open('data_files/all_commits_by_year/2000_commits_SUB_sorted.json')
	commits = stream(f)

	#process all commits in date order
	for x in commits:
		process_commit(x)
	f.close()

	#print some user results (checking the code)
	for user_id, user in users.items():
		if len(user.adopted_libs) > 0:
			print("user", user.name, "adopted", len(user.adopted_libs), "libraries in", user.commit_count, "commits ("+str(user.adopt_commit_count), "adop,", user.import_commit_count, "import)") 
			print("    last 10%:", (str(datetime.timedelta(seconds=round(user.avg_commit_delta))) if len(user.last_commits)>1 else None), "intra-commit delta,", user.last_repos_count(), "repos")
			print("             ", len(user.last_commits), "commits (" + str(user.last_adopt_commit_count), "adopt,", user.last_import_commit_count, "import)")
