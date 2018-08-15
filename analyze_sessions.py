import glob
import sys
import pandas as pd
import os
import pickle
from collections import defaultdict
from math import ceil
from datetime import timedelta
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

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

#given a completed session as list of commit times and index of first adoption (if any),
#generate the pmf of the cpm rate on either side of the adoption event and plot
def session_commits(commit_times, first_adopt):	

	#normalize time scale, partition at adoption if necessary
	if NORM_TIME:
		#if session contains adoption, partition at 0
		if first_adopt != -1:
			#partition commit times at first adoption event
			pre_adopt = commit_times[:first_adopt+1]	#include adoption event here for now
			post_adopt = commit_times[first_adopt:]
			#normalize both sides separately, then combine
			relative_times = normalize(pre_adopt, -100, 0)[:-1]		#remove duplicate adoption event
			relative_times += normalize(post_adopt, 0, 100)
		#otherwise, take all commits at once
		else:
			relative_times = normalize(commit_times, 0, 100)
	#no normalization, just shift the UTC times (seconds) to minutes from some reference point
	else:
		#no adoption, shift times relative to first commit
		if first_adopt == -1:
			relative_times = [int((time - commit_times[0]) / 60) for time in commit_times]
		#adoption session, shift all times relative to first adoption event
		else:
			relative_times = [int((time - commit_times[first_adopt]) / 60) for time in commit_times]

	#build list of minute//percent counters covering entire range
	commit_bins = list(range(int(relative_times[0]), int(relative_times[-1])+1))
	#and list of corresponding commit counts
	commit_counts = [0] * len(commit_bins)
	for time in relative_times:
		commit_counts[int(time) + int(abs(relative_times[0]))] += 1

	#return results
	return commit_bins, commit_counts
#end session_pmf

#for a completed session, log all session data
def log_session(user_adopt_sessions):
	length = session_commit_times[-1] - session_commit_times[0]		#length of this session, from first commit to last

	#compute commit counts, shifted to either session start or first adoption, perhaps normalized
	times, commits = session_commits(session_commit_times, session_first_adopt)

	#add this session commit counts to overall session counters
	#also increment additive counter for all times covered by this session
	#adopt sessions
	if session_first_adopt != -1:
		for i in range(len(times)):
			total_adopt[int(times[i])] += commits[i]	
		for i in range(int(times[0]), int(times[-1])+1):
			adopt_add[i] += 1	
	#non-adopt sessions
	else:
		for i in range(len(times)):
			total_non_adopt[int(times[i])] += commits[i]			
		for i in range(int(times[0]), int(times[-1])+1):
			non_adopt_add[i] += 1

	#update user adoption counters if this session contained an adoption
	if session_first_adopt != -1:
		user_adopt_sessions += 1

	#add this session data to global tracking
	len_bin = ceil(length / 1800) / 2		#compute half-hour bin for this session

	return user_adopt_sessions
#end log_session

#given data and a target range, normalize so data falls in that range only (feature scaling)
def normalize(data, range_start, range_end):
	#empty list? return empty
	if len(data) == 0:
		return []

	#grab min and max from data
	data_min = min(data)
	data_max = max(data)

	#special case: only one element, or all times the same
	if len(data) == 1 or data_min == data_max:
		#set to range_start if range_start is negative (pre-adopt data)
		if range_start < 0:
			return len(data) * [range_start]
		#otherwise, set to 0 (entire session or post-adopt data)
		else:
			return len(data) * [0]

	#X′ = a + [(X − Xmin)(b − a) / (Xmax − Xmin)] 	
	normalized = [range_start + (((x - data_min)*(range_end - range_start))/(data_max - data_min)) for x in data]

	return normalized
#end normalize

#--- MAIN EXECUTION BEGINS HERE---#

max_inactive = 9 * 3600		#maximum time between commits of the same session (in seconds)

#boolean flags to set operating mode
NORM_TIME = True		#normalize all session lengths to same range if true; stack by time otherwise

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

#global session variables: dictionaries with integer time (normalized or not) as key, sum of session function (cpm or pmf) as value
total_adopt = defaultdict(float)
total_non_adopt = defaultdict(float)
#also count of how often each key (time) was added to
adopt_add = defaultdict(int)
non_adopt_add = defaultdict(int)

#functions to set up defaultdict to allow for pickling
def ddi(): return defaultdict(int)
def ddl(): return defaultdict(list)

#process each file one at a time
for file in files:
	print("\nProcessing", file)

	user_commits = load_pickle(file)

	total_user_count += len(user_commits)

	#for each user in this chunk, step through their commits
	for user, commits in user_commits.items():

		#session variables/counters
		session_commit_times = []		#list of commit times in this session
		session_first_adopt = -1		#index (commit number) of first adoption in current session

		#user variables/counters
		user_sessions = 1			#number of sessions for this user
		user_adopt_sessions = 0		#number of sessions featuring adoptions for this user
		user_adopt_commits = 0		#number of adoption commits for this user
		user_adopt_libs = 0			#number of libraries adopted by this user

		total_commit_count += len(commits)

		#loop all commits made by this user
		for c in commits:

			#compute delay between this commit and the previous (if previous commit exists)
			if len(session_commit_times) != 0:
				delay = c['time'] - session_commit_times[-1]
			else:
				delay = None

			#process delay if valid
			if delay != None:

				#delay too long, new session
				if delay >= max_inactive:

					user_adopt_sessions = log_session(user_adopt_sessions)		#update all global tracking		

					#reset session tracking for new session
					session_commit_times = []		#new commit time added below
					session_adopt_positions = []
					session_adopt_times = []
					session_first_adopt = -1

					user_sessions += 1		#add to user's session counter

				#check if current commit contains an adoption, if so flag the session as adopting
				if c['adopted_libs']:
					user_adopt_commits += 1
					user_adopt_libs += len(c['adopted_libs'])		
					#print(user, "adopting", len(c['adopted_libs']), "libraries")

					#first adoption? grab index if so
					if session_first_adopt == -1:
						session_first_adopt = len(session_commit_times)

			session_commit_times.append(c['time'])	#update prev for next commit

		#handle last session for this user
		user_adopt_sessions = log_session(user_adopt_sessions)		#update all global tracking			

		print("User", user, "made", len(commits), "commits across", user_sessions, "sessions")
		if user_adopt_sessions != 0:
			print("   ", user_adopt_libs, "libraries adopted in", user_adopt_commits, "commits across", user_adopt_sessions, "sessions")		

		#update global counters based on user's entire history
		total_sessions += user_sessions 		#keep count of total number of sessions across all users
		total_adopt_sessions += user_adopt_sessions
		total_adopt_commits += user_adopt_commits
		total_adopt_libs += user_adopt_libs

	if total_adopt_sessions >= 100:
		break

print("Processed", total_commit_count, "commits and", total_user_count, "users in", total_sessions, "sessions")
print("   ", total_adopt_libs, "libraries adopted in", total_adopt_commits, "commits across", total_adopt_sessions, "sessions")

#post-process totals for plotting
#divide time totals by number of sessions contributing to that time, also convert to lists at the same time
adopt_times = []
adopt_vals = []
non_times = []
non_vals = []	

#adopt sessions
for key in sorted(total_adopt.keys()):
	adopt_times.append(key)
	adopt_vals.append(total_adopt[key] / adopt_add[key])

#non-adopt sessions	
min_val = non_adopt_add[0]
min_val_key = []
max_val = non_adopt_add[0]
max_val_key = []
for key in sorted(total_non_adopt.keys()):
	non_times.append(key)
	non_vals.append(total_non_adopt[key] / non_adopt_add[key])

#output filename fields
out_code = "NORM" if NORM_TIME else "TIME"

#save adopt and non-adopt dictionaries as pickles
'''
dump_data(adopt_vals, "results/%s_avg_adopt_vals.pkl" % out_code)
dump_data(non_vals, "results/%s_avg_non_adopt_vals.pkl" % out_code)
dump_data(adopt_times, "results/%s_avg_times.pkl" % out_code)
print("Data saved to results/%s_avg_adopt_vals.pkl, results/%s_avg_non_adopt_vals.pkl, and results/%s_avg_times.pkl" % (out_code, out_code, out_code))
'''

#plot adopt and non-adopt curves independently
plt.clf()
fig, ax = plt.subplots()
ax.plot(adopt_times, adopt_vals, 'r', label='adoption sessions')
plt.axvline(x=0, color='k', lw=0.4)
plt.yscale('log')
plt.savefig("results/session_plots/%s_avg_adopt_sessions.png" % out_code, bbox_inches='tight')

plt.clf()
fig, ax = plt.subplots()
ax.plot(non_times, non_vals, 'b', label='non-adopt sessions')
plt.yscale('log')
plt.savefig("results/session_plots/%s_avg_non_adopt_sessions.png" % out_code, bbox_inches='tight')

print("Individual plots saved to results/session_plots/%s_avg_adopt_sessions.png and results/session_plots/%s_avg_non_adopt_sessions.png" % (out_code, out_code))
