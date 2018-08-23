#given that we already generated all the adoption features triggered by added libs (both positive and negative),
#add in the negative adoptions that result from updated_libs that are not in added_libs
#dump only these new negative events to negative_event_features
import json
from datetime import datetime, timedelta
import random as r
from collections import deque
import pickle
import os.path
from stackoverflow_searcher import Searcher
from User import User
from Repo import Repo
from Package import Package

WINDOW = 0.1		#for windowed stats, take last 10% of a user/repo's commits (once user has at least 5 commits in history)

#global dictionaries of user, repo, and package objects, key is name/id, value is class object
users = {}
repos = {}
packages = {}

#global array (list of lists) containing user-package instance feature vectors and classifying labels
data = []
labels = []
data_month = -1
data_year = -1

#global events generator instance
events = -1
event_labels = -1

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#given a User user and Package package, generate the tail end of the feature vector for this event: User/Package, Package-only, and SO features (but not User-only features)
def get_negative_features(user, package, time):
	global commit_history

	vector = user.get_package_features(package.name)		#start with user-package features
	vector.extend(package.get_features(time, commit_history[0]))	#add on package features

	#add the StackOverflow features
	#all posts with this package, ever
	all_posts = s.search(package.name, until_date=datetime.fromtimestamp(time))	
	vector.append(len(all_posts))			#total number of posts containing this package
	vector.append(sum(x[2] for x in all_posts))	#total views of all posts

	#posts added in last 30 days (months are too hard)
	recent_posts = s.search(package.name, from_date=datetime.fromtimestamp(time)-timedelta(days=30), until_date=datetime.fromtimestamp(time))
	vector.append(len(recent_posts))		#number of recent posts
	vector.append(sum(x[2] for x in recent_posts))	#total views of recent posts

	return vector
#end get_features

#dump all currently cached data (for a single month) to file
def dump_data():
	global data, labels	#use global variables

	#no data yet, skip
	if data_year == -1:
		return

	#make sure directory for this year exists
	if os.path.isdir("data_files/negative_event_features/%s" % data_year) == False:
		os.makedirs("data_files/negative_event_features/%s" % data_year)

	#save data array to file
	pik = ("data_files/negative_event_features/%s/%s_events.pkl" % (data_year, data_month))
	with open(pik, "wb") as f:
		pickle.dump(data, f)

	#save labels to corresponding file
	pik = ("data_files/negative_event_features/%s/%s_labels.pkl" % (data_year, data_month))
	with open(pik, "wb") as f:
		pickle.dump(labels, f)	

	#clear data and labels
	data = []
	labels = []

	print ("saved events for %s-%s" % (data_month, data_year))
#end dump_data

#given a single commit, process and update user/repo library listings and identify any adoption events
#arguments are commit c and initialized StackOverflow Searcher s
def process_commit(c):
	global commit_count, commit_history	#use the global variables
	global s
	global data, labels, data_month, data_year
	global events, event_labels

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
	if len(added_libs) != 0:
		print("added", added_libs)
	if len(deleted_libs) != 0:
		print("deleted", deleted_libs)

	#change added/deleted_libs so that "moved libs" i.e., libs that are added and deleted in the same commit are not considered for adoptions
	added_and_deleted = added_libs.intersection(deleted_libs)
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

	#is this new commit from a different month than the current feature data? if so, dump existing to file
	date = datetime.fromtimestamp(time)
	if date.month != data_month or date.year != data_year:
		dump_data()
		data_month = date.month
		data_year = date.year
		events = next_feature(data_year, data_month)	#init new generators for new month: features and labels
		event_labels = next_label(data_year, data_month)

	commit_adopt = False		#reset flag for this commit
	#loop all libraries added in this commit
	for lib in added_libs:
		lib_adopt = False	#reset flat for this library
		
		#grab/create class object for this package/library
		if lib not in packages:
			packages[lib] = Package(lib)
		package = packages[lib]

		#get complete feature vector and label for this user-package event
		try:
			event = next(events)
			event_label = next(event_labels)
		except StopIteration:
			print("No more event feature vectors/labels")
			exit(0)
		#verify data fetch working correctly
		if lib != event[2]:
			print(lib, event[2])
			print("library names not matching, fail")
			exit(0)
		else:
			print(lib)
			
		#first features same for added and updated/seen libs (except idx 2, the package name); have to generate the user/package features and the SO features for each "seen" library, but let's save what we can for later
		base_feature_vector = event[0:16]

		#if adoption, do the updates
		if event_label == 1:
			#found an adoption! log it for both user and package
			user.log_adopt(lib, time)	#log for user, 
			commit_adopt = True		#set flag for this commit
			lib_adopt = True		#set flag for this library

		#always log the package commit				
		package.commit_lib(user, repo, time, lib_adopt)			
		
	#loop the negative adoptions - any lib updated in the repo that the user did not commit is a negative adoption
	for lib in updated_libs:
		#user committed this library, already processed, move to next
		if lib in added_libs:
			continue
			
		#grab/create class object for this package/library
		if lib not in packages:
			packages[lib] = Package(lib)
		package = packages[lib]
			
		#for some reason, user chose not to use/adopt this library - negative event
		feature_vector = base_feature_vector	#start with the common features
		feature_vector[2] = lib		#set package name for this instance

		#get the rest of the features: user/package, package, and SO
		feature_vector.extend(get_negative_features(user, package, time))

		#add new instance of feature vector and classification label to overall data
		data.append(feature_vector)
		labels.append(0)	#not an adoption
		print(feature_vector)

	#update user state based on new libraries seen
	user.implicit_view(updated_libs, repo, time)	

	#log this user commit, import/adoption or not
	user.log_commit_minimal(time, repo.name, updated_libs, (len(added_libs) != 0), commit_adopt)	#no added libs, no library import

	#resolve remaining updates
	for added_lib in added_libs:
		user.use_lib(added_lib, time)
		repo.use_lib(added_lib, time)
		
	user.finalize()		#finalize pending adoption updates on user (maintain adopted_libs)

	#add commit timestamp to history list, limit to last 10% (once more than 5 commits)
	num_commits = len(commit_history)		#number of commits in current history list
	#remove earliest commit if history list too long before appending new
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

#return pre-computed feature vector one at a time (generator function)
def next_feature(year, month):
	events = load_pickle("data_files/complete_event_features/%s/%s_events.pkl" % (year, month))
	for event in events:
		yield event
#end next_feature

#return pre-computed event labels one at a time (generator function)
def next_label(year, month):
	labels = load_pickle("data_files/event_features/%s/%s_labels.pkl" % (year, month))
	for label in labels:
		yield label
#end next_label

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":
	global commit_count, commit_history, s		#use the global variables
	commit_count = 0
	commit_history = deque()

	#declare/initialize a Stackoverflow Searcher
	s = Searcher()

	#create directory for output files if it doesn't exist
	if os.path.isdir("data_files/event_features") == False:
		os.makedirs("data_files/event_features")

	#stream data from sorted json files
	for year in range(1990, 1993):		#read and process 1990 through 2018
		print("PROCESSING", year)

		#stream from current year's output file
		f = open('data_files/all_commits_by_year/%s_commits_SUB_sorted.json' % year)
		commits = stream(f)

		#process all commits in date order
		for x in commits:
			process_commit(x)		#commit_count incremented here
			if commit_count % 100 == 0:
				print("finished", commit_count, "commits,", len(commit_history), "commits in history")
		f.close()

