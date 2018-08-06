import glob
import sys
import pandas as pd
import os
import pickle
from collections import defaultdict
from math import ceil
from datetime import timedelta
import numpy as np

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

#for a completed session, log all session data
def log_session(user_adopt_sessions, user_adopt_commits, user_adopt_libs):
	length = prev_commit - session_start		#length of this session, from first commit to last

	#print("   ", timedelta(seconds=(length)).__str__(), "session with", session_commit_count, "commits")

	#update user adoption counters if this session contained an adoption
	if session_adopt_commits != 0:
		user_adopt_sessions += 1
		user_adopt_commits += session_adopt_commits
		user_adopt_libs += session_adopt_libs
		#print("      ", session_adopt_commits, "adoption commits adopting", session_adopt_libs, "libraries")

	#add this session data to global tracking
	len_bin = ceil(length / 1800) / 2		#compute half-hour bin for this session
	#update all the counters
	session_length_counts[len_bin]['freq'] += 1					
	session_length_lists[len_bin]['all_commits'].append(session_commit_count) 
	session_length_lists[len_bin]['adopt_commits'].append(session_adopt_commits)
	#session contains adoption?
	if session_adopt_commits != 0:
		session_length_counts[len_bin]['adopt_freq'] += 1
		session_length_lists[len_bin]['commits_when_adopt'].append(session_commit_count)
	else:
		session_length_lists[len_bin]['commits_no_adopt'].append(session_commit_count)

	return user_adopt_sessions, user_adopt_commits, user_adopt_libs
#end log_session

#--- MAIN EXECUTION BEGINS HERE---#
global total_adopt_libs, total_adopt_commits, total_adopt_sessions

max_inactive = 9 * 3600		#maximum time between commits of the same session (in seconds)

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

#functions to set up defaultdict to allow for pickling
def ddi(): return defaultdict(int)
def ddl(): return defaultdict(list)

#all session data balled up into a single mega-object
#some of this is tracked as data is processed, others is constructed from lists after the fact

#first key is session length binned by half-hour
#second key is one of the following, each specific to that particular length:
session_length_counts = defaultdict(ddi)
	#	freq - number of sessions
	#	adopt_freq - number of sessions with an adoption
	#	avg_commit_count - average number of commits for all sessions
	#	avg_adopt_commit_count - average number of adoption commits for all sessions
	#	avg_commits_when_adopt - average number of commits when session contains adoption
	#	avg_commits_no_adopt - average number of commits when session does not contain adoption
session_length_lists = defaultdict(ddl)
	#	all_commits - list of session commit counts
	#	adopt_commits - list of session adoption commit counts
	#	commits_when_adopt - list of session commit counts for sessions containing adoption
	#	commits_no_adopt - list of session commit counts for sessions not containing adoption


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

					user_adopt_sessions, user_adopt_commits, user_adopt_libs = log_session(user_adopt_sessions, user_adopt_commits, user_adopt_libs)		#update all global tracking		

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
		user_adopt_sessions, user_adopt_commits, user_adopt_libs = log_session(user_adopt_sessions, user_adopt_commits, user_adopt_libs)		#update all global tracking			

		print("User", user, "made", len(commits), "commits across", user_sessions, "sessions")
		if user_adopt_sessions != 0:
			print("   ", user_adopt_libs, "libraries adopted in", user_adopt_commits, "commits across", user_adopt_sessions, "sessions")		

		#update global counters based on user's entire history
		total_sessions += user_sessions 		#keep count of total number of sessions across all users
		total_adopt_sessions += user_adopt_sessions
		total_adopt_commits += user_adopt_commits
		total_adopt_libs += user_adopt_libs

print("Processed", total_commit_count, "commits and", total_user_count, "users in", total_sessions, "sessions")
print("   ", total_adopt_libs, "libraries adopted in", total_adopt_commits, " commits across", total_adopt_sessions, "sessions")

#compute averages from lists
for length in session_length_lists:
	session_length_counts[length]['avg_commit_count'] = sum(session_length_lists[length]['all_commits']) / session_length_counts[length]['freq']
	session_length_counts[length]['avg_adopt_commit_count'] = sum(session_length_lists[length]['adopt_commits']) / session_length_counts[length]['freq']
	#average commits when adoption only defined if there is an adoption in at least one session of this length
	if len(session_length_lists[length]['commits_when_adopt']) == 0:
		session_length_counts[length]['avg_commits_when_adopt'] = None
	else:
		session_length_counts[length]['avg_commits_when_adopt'] = sum(session_length_lists[length]['commits_when_adopt']) / session_length_counts[length]['adopt_freq']
	#average commits no adoption only defined if divisor not 0
	if session_length_counts[length]['freq'] - session_length_counts[length]['adopt_freq'] == 0:
		session_length_counts[length]['avg_commits_no_adopt'] = None
	else:
		session_length_counts[length]['avg_commits_no_adopt'] = sum(session_length_lists[length]['commits_no_adopt']) / (session_length_counts[length]['freq'] - session_length_counts[length]['adopt_freq'])

#convert numeric data to sorted np array for output as csv
columns = ['freq', 'adopt_freq', 'avg_commit_count', 'avg_adopt_commit_count', 'avg_commits_when_adopt', 'avg_commits_no_adopt']
results = []
results.append(['length'] + columns)	#headers for data output
for length in sorted(session_length_counts.keys()):
	row = [length]
	for col in columns:
		row.append(session_length_counts[length][col])
	results.append(row)

#save numeric data as csv
np.savetxt("results/sessions_adopt_data.csv", np.array(results), delimiter=",", fmt="%s")
print("\nNumeric results saved to results/sessions_adopt_data.csv")

#pickle up both dictionaries, in case we need them later
dump_data(session_length_counts, "results/session_length_numeric.pkl")
dump_data(session_length_lists, "results/session_length_lists.pkl")