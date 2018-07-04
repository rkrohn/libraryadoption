#given that we already generated all the adoption features, add to those the user, repo, package, and time of each user-package event

import json
from datetime import datetime, timedelta
import random as r
from collections import deque
import pickle
import os.path

#global array (list of lists) containing user-package instance feature vectors
data = []
data_month = -1
data_year = -1

#global events generator instance
events = -1

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#dump all currently cached data (for a single month) to file
def dump_data():
	global data, labels	#use global variables

	#no data yet, skip
	if data_year == -1:
		return

	#make sure directory for this year exists
	if os.path.isdir("data_files/complete_event_features/%s" % data_year) == False:
		os.makedirs("data_files/complete_event_features/%s" % data_year)

	#save data array to file
	pik = ("data_files/complete_event_features/%s/%s_events.pkl" % (data_year, data_month))
	with open(pik, "wb") as f:
		pickle.dump(data, f)

	#clear data
	data = []

	print ("saved events for %s-%s" % (data_month, data_year))
#end dump_data

#given a single commit, process and update user/repo library listings and identify any adoption events
#arguments are commit c and initialized StackOverflow Searcher s
def process_commit(c):
	global data, data_month, data_year
	global events
	global commit_count

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
	added_libs = [item for item in added_libs if item not in added_and_deleted]

	#is this new commit from a different month than the current feature data? if so, dump existing to file
	date = datetime.fromtimestamp(time)
	if date.month != data_month or date.year != data_year:
		dump_data()
		data_month = date.month
		data_year = date.year
		events = next_feature(data_year, data_month)	#init new generator for new month

	#loop all libraries added in this commit
	for lib in added_libs:
		#updated, complete feature vector for this user-package event: user, repo, package, time, <all existing features>
		feature_vector = [user, repo, lib, time]
		try:
			event = next(events)
		except StopIteration:
			print("No more event feature vectors")
			exit(0)
		feature_vector.extend(event)		

		#add new instance of feature vector and classication label to overall data
		data.append(feature_vector)

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

#return pre-computed feature vectors one at a time (generator function)
def next_feature(year, month):
	events = load_pickle("data_files/event_features/%s/%s_events.pkl" % (year, month))
	for event in events:
		yield event
#end next_feature

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":
	global commit_count
	commit_count = 0

	#create directory for output files if it doesn't exist
	if os.path.isdir("data_files/complete_event_features") == False:
		os.makedirs("data_files/complete_event_features")

	#stream data from sorted json files
	for year in range(1990, 2019):		#read and process 1990 through 2018
		print("PROCESSING", year)

		#stream from current year's output file
		f = open('data_files/all_commits_by_year/%s_commits_SUB_sorted.json' % year)
		commits = stream(f)

		#process all commits in date order
		for x in commits:
			process_commit(x)		#commit_count incremented here
			if commit_count % 10000 == 0:
				print("finished", commit_count, "commits")
		f.close()

