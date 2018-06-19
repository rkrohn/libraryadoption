import json
from datetime import datetime, timedelta
import random as r
from collections import deque
from stackoverflow_searcher import Searcher
from User import User
from Repo import Repo
from Package import Package

WINDOW = 0.1		#for windowed stats, take last 10% of a user/repo's commits (once user has at least 5 commits in history)

#global dictionaries of user, repo, and package objects, key is name/id, value is class object
users = {}
repos = {}
packages = {}

#list of commit timestamps for last 10% of ALL commits - used for computing some package features
#commit_history = deque()
#commit_count		#count of ALL commits - defined and initialized in main

#global StackOverflow Searcher
#s = Searcher()

#given a single commit, process and update user/repo library listings and identify any adoption events
#arguments are commit c and initialized StackOverflow Searcher s
def process_commit(c):
	global commit_count, commit_history	#use the global variables
	global s

	#grab commit fields: user, repo, time, added_libs, and deleted_libs
	repo = c['repo']
	time = int(c['time'])
	if c['user'] == '':
		print(c)
		user = 0
	else:
		user = int(c['user'])

	#remove duplicate libraries from lists by converting them to sets
	added_libs = set(c['add_libs'])
	deleted_libs = set(c['del_libs'])

	#change added/deleted_libs so that "moved libs" i.e., libs that are added and deleted in the same commit are not considered for adoptions
	added_and_deleted = added_libs.intersection(deleted_libs)
	deleted_libs = [item for item in deleted_libs if item not in added_and_deleted]
	added_libs = [item for item in added_libs if item not in added_and_deleted]

	if len(added_libs) != len(set(added_libs)):
		print("duplicate libraries!", added_libs)
		exit(0)

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

	adopt = False		#reset flag for this commit
	#loop all libraries added in this commit
	for lib in added_libs:
		#grab/create class object for this package/library
		if lib not in packages:
			packages[lib] = Package(lib)
		package = packages[lib]

		#if an added lib is in updated_lib but not in the user's quiver, then it must be an adoption
		if lib in updated_libs and lib not in user.quiver:
			#found an adoption! log it
			user.log_adopt(lib, time)	#log for user
			package.commit_lib(user, repo, time, adopt=True)
			adopt = True
			if r.random() > .9:
				print("   ", user.name, 'adopts', lib, 'at:', datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S'))
				print("   ", len(s.search(lib, datetime(1, 1, 1), datetime.fromtimestamp(time))), "stackoverflow posts")
				print("    package:", package.add_commits, "commits,", len(package.adopt_users), "adoptions,", len(package.repos), "repos;", "adopt delta t:", str(timedelta(seconds=round(package.avg_adopt_delta))) if len(package.adopt_users) > 1 else None, "commit delta t:", str(timedelta(seconds=round(package.avg_commit_delta))) if package.add_commits > 1 else None)
				print("    deltas in last 10% of all commits:", package.get_deltas(commit_history[0]))

		#not an adoption, just log the package commit				
		else:
			package.commit_lib(user, repo, time, adopt=False)
		

	#update user state based on new libraries seen
	user.implicit_view(updated_libs, repo, time)	

	#log this user commit, import/adoption or not
	if len(added_libs) != 0:
		user.log_commit(time, repo.name, updated_libs, True, adopt)	#yes, commit contains add import
	else:
		user.log_commit(time, repo.name, updated_libs, False, adopt)	#no, commit contains no add imports

	#resolve updates
	for added_lib in added_libs:
		user.use_lib(added_lib, time)
		repo.use_lib(added_lib, time)
	user.finalize()		#finalize pending adoption updates on user

	#add commit timestamp to history list, limit to last 10% (once more than 5 commits)
	#remove earliest commit if history list too long before appending new
	num_commits = len(commit_history)		#number of commits in current history list
	#if list long enough to remove oldest commit, do that 
	if num_commits > 5 and (num_commits) / float(commit_count) > WINDOW:
		commit_history.popleft()	#remove oldest commit		
	#always append newest commit
	commit_history.append(time)

	commit_count += 1	#add to overall commit count	

#end process_commit

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
#end stream

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":
	global commit_count, commit_history, s		#use the global variables
	commit_count = 0
	commit_history = deque()

	#stream data from sorted json file
	f = open('data_files/all_commits_by_year/2011_commits_SUB_sorted.json')
	commits = stream(f)

	#declare/initialize a Stackoverflow Searcher
	s = Searcher()
	#some example queries
	'''
	posts = s.search('numpy', datetime(2000, 1, 1), datetime(2009, 1, 1))
	print(len(posts), "posts,", sum(x[2] for x in posts), "total views")
	posts = s.search('numpy', datetime(2014, 1, 1), datetime(2017, 1, 1))
	print(len(posts), "posts,", sum(x[2] for x in posts), "total views")
	'''	

	#process all commits in date order
	for x in commits:
		process_commit(x)		#commit_count incremented here
		if commit_count % 1000 == 0:
			print("finished", commit_count, "commits,", len(commit_history), "commits in history")
	f.close()

	#print some user results (checking the code)
	for user_id, user in users.items():
		if len(user.adopted_libs) > 0:
			print("user", user.name, "adopted", len(user.adopted_libs), "libraries in", user.commit_count, "commits ("+str(user.adopt_commit_count), "adop,", user.import_commit_count, "import)") 
			print("    last 10%:", (str(timedelta(seconds=round(user.avg_commit_delta))) if len(user.last_commits)>1 else None), "intra-commit delta,", user.last_repos_count(), "repos")
			print("             ", len(user.last_commits), "commits (" + str(user.last_adopt_commit_count), "adopt,", user.last_import_commit_count, "import)")

	#testing the implicit package view query (specific to both a package and a user)
	lib_freq, all_freq = users[1506].lib_view_freq("urlparse")
	print("viewed urlparse", lib_freq, "times, all libraries", all_freq, "times in", len(users[1506].last_commits), "commits")

	lib_freq, all_freq = users[31175].lib_view_freq("curses")
	print("viewed curses", lib_freq, "times, all libraries", all_freq, "times in", len(users[31175].last_commits), "commits")


