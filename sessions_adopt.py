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

#prints key->freq data in sorted order
def print_sorted(bins, filename):
	with open(filename, "wt") as f:
		for key in sorted(bins.keys()):
			f.write("%s %s\n" % (key, bins[key]))
#end print_sorted

#--- MAIN EXECUTION BEGINS HERE---#

max_inactive = 9 * 3600		#maximum time between commits of the same session (in seconds)

bins = defaultdict(int)

#get list of user commit files to process
files = glob.glob('data_files/user_commits/*')
print("Processing", len(files), "user commit files")

#global counters: total number of commits, users, and sessions
commit_count = 0
user_count = 0
session_total = 0
total_adopt_commits = 0
total_adopt_libs = 0

#session data dictionaries
length_to_commits = defaultdict(list)	#session length (seconds) -> number of commits in session
length_to_freq = defaultdict(int)		#session length (seconds) -> frequency (number of sessions with this length)

#process each file one at a time
for file in files:
	print("\nProcessing", file)

	user_commits = load_pickle(file)

	user_count += len(user_commits)

	#for each user in this chunk, step through their commits
	for user, commits in user_commits.items():

		prev = -1	#time of this user's previous commit
		session_start = -1			#UTC time of start of current session
		per_session_count = 1		#number of commits in previous session
		session_count = 1			#number of sessions for this user
		session_adopt = 0			#number of adoption commits by user in current session
		adopt_libs = 0				#number of libraries adopted by user in current session

		commit_count += len(commits)

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
					length = prev - session_start		#length of this session, from first commit to last

					#print("   ", timedelta(seconds=(prev - session_start)).__str__(), "session with", per_session_count, "commits")

					#add this session data to tracking
					length_to_commits[length].append(per_session_count)
					length_to_freq[length] += 1

					#reset tracking for new session
					session_start = c['time']
					per_session_count = 1
					session_adopt = 0
					adopt_libs = 0

					session_count += 1		#increment global session counter
				#another commit to current session
				else:
					per_session_count += 1

				#check if this commit contains an adoption, if so flag the session as adopting
				if c['adopted_libs']:
					session_adopt += 1
					adopt_libs += len(c['adopted_libs'])

			prev = c['time']	#update prev for next commit

		#handle last session for this user
		length = prev - session_start		#length of this session, from first commit to last

		#print("   ", timedelta(seconds=(prev - session_start)).__str__(), "session with", per_session_count, "commits")

		#add this session data to tracking
		length_to_commits[length].append(per_session_count)
		length_to_freq[length] += 1

		print("User", user, "made", len(commits), "commits across", session_count, "sessions")
		if session_adopt != 0:
			print("   ", session_adopt, "adoption commits adopting", adopt_libs, "libraries")

		#update global counters
		session_total += session_count 		#keep count of total number of sessions across all users
		total_adopt_commits += session_adopt
		total_adopt_libs += adopt_libs

	break

print("Processed", commit_count, "commits and", user_count, "users in", session_total, "sessions")
print("   ", total_adopt_commits, "adoption commits adopting", total_adopt_libs, "libraries")

exit(0)

#convert exact length to freq mapping to half hour bins, because not many match-ups
length_bin_to_freq = defaultdict(int)
for length, freq in length_to_freq.items():
		length_bin_to_freq[ceil(length / 1800) / 2] += freq
#print to file and pickle
print_sorted(length_bin_to_freq, "session_length_freq.txt")
dump_data(length_bin_to_freq, "session_length_freq.pkl")

#convert exact length to commit count list to half hour bins also
length_bin_to_commits = defaultdict(list)
for length, commits in length_to_commits.items():
	length_bin_to_commits[ceil(length / 1800) / 2].extend(commits)
#print to file and pickle
print_sorted(length_bin_to_commits, "session_length_commits.txt")
dump_data(length_bin_to_commits, "session_length_commits.pkl")

#also do an average commit count for each binned session length
length_bin_to_average_commits = {}
for length, commits in length_bin_to_commits.items():
		length_bin_to_average_commits[length] = sum(commits)/len(commits)
#print to file and pickle
print_sorted(length_bin_to_average_commits, "session_length_average_commits.txt")
dump_data(length_bin_to_average_commits, "session_length_average_commits.pkl")
