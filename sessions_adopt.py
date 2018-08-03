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
total_commit_count = 0
total_user_count = 0
total_sessions = 0
total_adopt_commits = 0
total_adopt_libs = 0
total_adopt_sessions = 0

#session data dictionaries
length_to_commits = defaultdict(list)	#session length (seconds) -> number of commits in session
length_to_freq = defaultdict(int)		#session length (seconds) -> frequency (number of sessions with this length)

#process each file one at a time
for file in files:
	print("\nProcessing", file)

	user_commits = load_pickle(file)

	total_user_count += len(user_commits)

	#for each user in this chunk, step through their commits
	for user, commits in user_commits.items():

		#session variables/counters
		prev_commit = -1	#time of this user's previous commit
		session_start = -1			#UTC time of start of current session
		session_commit_count = 1		#number of commits in current session
		session_adopt_commits = 0			#number of adoption commits by user in current session
		session_adopt_libs = 0				#number of libraries adopted by user in current session

		#user variables/counters
		user_sessions = 1			#number of sessions for this user
		user_adopt_sessions = 0		#number of sessions featuring adoptions for this user
		user_adopt_commits = 0		#number of adoption commits for this user
		user_adopt_libs = 0			#number of libraries adopted by this user

		total_commit_count += len(commits)

		#loop all commits made by this user
		for c in commits:

			#compute delay between this commit and the previous (if previous commit exists)
			if prev_commit != -1:
				delay = c['time'] - prev_commit
			else:
				delay = None
				session_start = c['time']

			#process delay if valid
			if delay != None:

				#delay too long, new session
				if delay >= max_inactive:
					length = prev_commit - session_start		#length of this session, from first commit to last

					#print("   ", timedelta(seconds=(length)).__str__(), "session with", session_commit_count, "commits")

					#update user adoption counters if this session contained an adoption
					if session_adopt_commits != 0:
						user_adopt_sessions += 1
						user_adopt_commits += session_adopt_commits
						user_adopt_libs += session_adopt_libs
						#print("      ", session_adopt_commits, "adoption commits adopting", session_adopt_libs, "libraries")

					#add this session data to global tracking
					length_to_commits[length].append(session_commit_count)
					length_to_freq[length] += 1

					#reset session tracking for new session
					session_start = c['time']
					session_commit_count = 1
					session_adopt_commits = 0
					session_adopt_libs = 0

					user_sessions += 1		#add to user's session counter

				#delay not too long, add commit to current session
				else:
					session_commit_count += 1

				#check if current commit contains an adoption, if so flag the session as adopting
				if c['adopted_libs']:
					session_adopt_commits += 1
					session_adopt_libs += len(c['adopted_libs'])
					#print(user, "adopting", len(c['adopted_libs']), "libraries")

			prev_commit = c['time']	#update prev for next commit

		#handle last session for this user
		length = prev_commit - session_start		#length of this session, from first commit to last

		#print("   ", timedelta(seconds=(length)).__str__(), "session with", session_commit_count, "commits")

		#update user adoption counters if this session contained an adoption
		if session_adopt_commits != 0:
			user_adopt_sessions += 1
			user_adopt_commits += session_adopt_commits
			user_adopt_libs += session_adopt_libs
			#print("      ", session_adopt_commits, "adoption commits adopting", session_adopt_libs, "libraries")

		#add this session data to global tracking
		length_to_commits[length].append(session_commit_count)
		length_to_freq[length] += 1

		print("User", user, "made", len(commits), "commits across", user_sessions, "sessions")
		if user_adopt_sessions != 0:
			print("   ", user_adopt_libs, "libraries adopted in", user_adopt_commits, "commits across", user_adopt_sessions, "sessions")		

		#update global counters based on user's entire history
		total_sessions += user_sessions 		#keep count of total number of sessions across all users
		total_adopt_sessions += user_adopt_sessions
		total_adopt_commits += user_adopt_commits
		total_adopt_libs += user_adopt_libs

	break

print("Processed", total_commit_count, "commits and", total_user_count, "users in", total_sessions, "sessions")
print("   ", total_adopt_libs, "libraries adopted in", total_adopt_commits, " commits across", total_adopt_sessions, "sessions")

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
