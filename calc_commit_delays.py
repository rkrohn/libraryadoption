import glob
import sys
import pandas as pd
import os
import pickle
from collections import defaultdict
from math import ceil

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

		commit_count += len(commits)

		#loop all commits made by this user
		for c in commits:

			#compute delay between this commit and the previous (if previous commit exists)
			if prev != -1:
				delay = c['time'] - prev
			else:
				delay = None

			#make sure commits in sorted order, quit if not
			if delay != None and delay < 0:
				print("Fail, commits not in time-order")
				exit(0)

			#process delay if valid
			if delay != None:

				#simultaneous commits? (no delay) -> special 0-hour bin
				if prev == c['time']:
					bins[0] += 1
				#valid delay, convert to hours add to correct bin counter
				else:
					bins[ceil(delay / 3600)] += 1		#3600 seconds per hour, round up to nearest hours

			prev = c['time']	#update prev for next commit

#print counts (sorted by key)
for key in sorted(bins.keys()):
	print("%s: %s" % (key, bins[key]))

#and save a pickle too
dump_data(bins, "delay_freq.pkl")

print("Processed", commit_count, "commits")