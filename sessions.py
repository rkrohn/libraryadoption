import glob
import sys
import pandas as pd
import os
import pickle
from collections import defaultdict
from math import ceil
from datetime import timedelta

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#dump data to file
def dump_data(data, filename):

	#save dictionary chunk to file
	pik = (filename)
	with open(pik, "wb") as f:
		pickle.dump(data, f)
#end dump_data

#--- MAIN EXECUTION BEGINS HERE---#

max_inactive = 4 * 3600		#maximum time between commits of the same session (in seconds)

bins = defaultdict(int)

#get list of user commit files to process
files = glob.glob('data_files/user_commits/*')
print("Processing", len(files), "user commit files")

commit_count = 0

#process each file one at a time
for file in files:
	print("Processing", file)

	user_commits = load_pickle(file)

	#for each user in this chunk, step through their commits
	for user, commits in user_commits.items():

		prev = -1	#time of this user's previous commit
		session_start = -1			#UTC time of start of current session
		per_session_count = 1		#number of commits in previous session
		session_count = 1			#number of sessions for this user

		commit_count += len(commits)

		print("User", user, "made", len(commits), "commits")

		#loop all commits made by this user
		for c in commits:

			#compute delay between this commit and the previous (if previous commit exists)
			if prev != -1:
				delay = c['time'] - prev
			else:
				delay = None
				session_start = c['time']

			#process delay if valid
			if delay != None:

				#delay too long, new session
				if delay >= max_inactive:
					print("   ", timedelta(seconds=(prev - session_start)).__str__(), "session with", per_session_count, "commits")
					session_start = c['time']
					per_session_count = 1
				#another commit to current session
				else:
					per_session_count += 1

			prev = c['time']	#update prev for next commit

		#last session for this user
		print("   ", timedelta(seconds=(prev - session_start)).__str__(), "session with", per_session_count, "commits")

	break

print("Processed", commit_count, "commits")