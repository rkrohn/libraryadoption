import json
import os.path
from collections import defaultdict
import pickle
from datetime import datetime

#stream json data one object at a time (generator function)
def stream(f):
	obj_str = ''
	f.read(1) 	#eat first [
	while True:
		c = f.read(1)	#read one character at a time
		#end of file, quit
		if not c:
			#print('EOF')
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

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#dump all currently cached data (for a single month) to file
def dump_dict(chunk, name):

	#save dictionary chunk to file
	pik = ("data_files/user_commits/%s_commits.pkl" % name)
	with open(pik, "wb") as f:
		pickle.dump(chunk, f)

	print ("saved %s users for %s user-ids" % (len(chunk), name))
#end dump_dict

#return pre-computed feature vector one at a time (generator function)
def next_feature(year, month):
	events = load_pickle("data_files/new_event_features/%s/%s_events.pkl" % (year, month))
	for event in events:
		yield event
#end next_feature

#return pre-computed event labels one at a time (generator function)
def next_label(year, month):
	labels = load_pickle("data_files/new_event_features/%s/%s_labels.pkl" % (year, month))
	for label in labels:
		yield label
#end next_label


#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":
	
	data_month = -1
	data_year = -1
	event = [-1]
	event_label = -1

	#dictionary of dictionary of commits by user
	#first key: user id / 1000
	#second key: user id
	#value: list of commits by this user, in time-sorted order
	by_user = defaultdict(lambda: defaultdict(list))

	#make sure directory for files exists
	if os.path.isdir("data_files/user_commits") == False:
		os.makedirs("data_files/user_commits")

	commit_count = 0

	#stream data from sorted json files
	for year in range(1990, 1995): #2018):		#read and process 1993 through 2018

		print("Streaming", year)

		#stream from current year's output file
		f = open('data_files/all_commits_by_year/%s_commits_SUB_sorted.json' % year)
		commits = stream(f)

		#process all commits in date order		
		for c in commits:

			#is this commit from a different month than the current feature data? if so, new feature file stream
			date = datetime.fromtimestamp(c['time'])
			if date.month != data_month or date.year != data_year:
				print("  moving to", str(date.month)+"-"+str(date.year))
				data_month = date.month
				data_year = date.year
				#init new generators for new month: features and labels
				events = next_feature(data_year, data_month)	
				event_labels = next_label(data_year, data_month)

			#build list of adopted libraries from this commit
			#first, skip any event features/labels that are not part of this commit
			while commit_count > event[0]:
				try:
					event = next(events)
					event_label = next(event_labels)
				except StopIteration:
					#finished the current month, but no match for this commit - must be empty event
					event = [-1]
					event_label = -1	
					break

			#match up event features/labels to build list of adopted libraries
			adopted = []
			while commit_count == event[0]:			
				if event_label == 1:
					adopted.append(event[19])
				if (event[20] == 1 and event[19] not in c['add_libs']) or event[1] != c['user'] or event[2] != c['repo']:
					print("FAIL")
					print(commit_count, c)
					print(event, event_label)
					exit(0)
					
				#get next event/label pair
				try:
					event = next(events)
					event_label = next(event_labels)
				except StopIteration:
					#finished the current month, stop
					event = [-1]
					event_label = -1

			#grab user from commit
			if c['user'] == '':
				user = 0
			else:
				user = int(c['user'])

			#get user id / 1000 (integer divide)
			mod = user // 1000

			#add this commit to user's list
			by_user[mod][user].append(c)

			commit_count += 1

			
		f.close()
	exit(0)

	#save each "chunk" (defined by /1000 key) as a separate pickle
	for key in by_user:
		dump_dict(by_user[key], key)
