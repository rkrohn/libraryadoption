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
			relative_times = [int((time - commit_times[0]) / (BIN_WIDTH * 60)) for time in commit_times]
		#adoption session, shift all times relative to first adoption event
		else:
			relative_times = [int((time - commit_times[first_adopt]) / (BIN_WIDTH * 60)) for time in commit_times]

	#build list of minute/percent counters covering entire range
	commit_bins = list(range(relative_times[0], relative_times[-1]+1))
	#and list of corresponding commit counts
	commit_counts = [0] * len(commit_bins)
	for time in relative_times:
		commit_counts[time + abs(relative_times[0])] += 1
	#multiply bins (times) by bin width to get back on the right scale
	commit_bins = [x * BIN_WIDTH for x in commit_bins]

	#return results
	return commit_bins, commit_counts
#end session_pmf

#for a completed session, log all session data
def log_session():
	#compute commit counts, shifted to either session start or first adoption, perhaps normalized
	times, commits = session_commits(session_commit_times, session_first_adopt)

	#add this session commit counts to overall session counters
	#also increment additive counter for all times covered by this session
	#adopt sessions
	if session_first_adopt != -1:
		for i in range(len(times)):
			total_adopt[times[i]] += commits[i]	
		for i in range(times[0], times[-1]+1):
			adopt_add[i] += 1	
	#non-adopt sessions
	else:
		for i in range(len(times)):
			total_non_adopt[times[i]] += commits[i]			
		for i in range(times[0], times[-1]+1):
			non_adopt_add[i] += 1

	#add this session data to global tracking
	len_bin = ceil(length / 1800) / 2		#compute half-hour bin for this session
#end log_session


#--- MAIN EXECUTION BEGINS HERE---#

max_inactive = 9 * 3600		#maximum time between commits of the same session (in seconds)

#flags and values to set operating mode
BIN_WIDTH = 5			#sets number of minutes per bin
PRE_WIN = 6 * 3600		#amount of time, in seconds, to include in the pre-commit activity window
POST_WIN = 6 * 3600		#time, in seconds, to include in post-commit activity window

#get list of user commit files to process
files = glob.glob('data_files/user_commits/*')
print("Processing", len(files), "user commit files")

#global counters: total number of commits, users, and sessions
total_commit_count = 0
total_user_count = 0
total_adopt_libs = 0

#commit activity variables
activity_counts = defaultdict(int)		#key is minutes from commit (positive or negative, in BIN_WIDTH increments)
										#value is number of commits made at that time (across all commits by all users)

#process each file one at a time
for file in files:
	print("\nProcessing", file)

	user_commits = load_pickle(file)

	total_user_count += len(user_commits)

	#for each user in this chunk, step through their commits
	for user, commits in user_commits.items():

		#user variables
		prev = -1				#time of user's previous commit
		user_adopt_libs = 0		#number of libraries adopted by user

		#commit indices
		pre_start = 0			#index of first commit included in pre-commit activity window
		post_end = 0			#index of first commit excluded from post-commit activity window

		total_commit_count += len(commits)		#add users's commits to total count

		#loop all commits made by this user
		for i in range(0, len(commits)):

			#grab current commit for easier access
			c = commits[i]

			#move up pre_start index if necessary so that commit it points to falls within PRE_WIN
			while c['time'] - commits[pre_start]['time'] > PRE_WIN:
				pre_start += 1
			#move up post_end index if necessary so that commit it points to falls outside POST_WIN
			while post_end < len(commits) and commits[post_end]['time'] - c['time'] < POST_WIN:
				post_end += 1

			surrounding_commits = commits[pre_start:post_end]		#extract commits that fall within defined activity window

			#for each commit within activity window, compute "minutes from commit" and add to relevant bin counter
			for a in surrounding_commits:
				activity_counts[int((a['time'] - c['time']) / (BIN_WIDTH * 60))] += 1

			#check if current commit contains an adoption, if so flag the session as adopting
			if c['adopted_libs']:
				user_adopt_libs += len(c['adopted_libs'])		

			prev = c['time']	#update prev for next commit		

		#wrap up current user before moving to next
		print("User", user, "made", len(commits), "commits adopting", user_adopt_libs, "libraries")		

		total_adopt_libs += user_adopt_libs

print("Processed", total_commit_count, "commits and", total_user_count, "users")
print("   ", total_adopt_libs, "libraries adopted")

#post-process totals for plotting
#divide commits totals by total number of commits (average), also convert to lists at the same time
activity_times = []
activity_avg = []	

#adopt sessions
for key in sorted(activity_counts.keys()):
	activity_times.append(key)
	activity_avg.append(activity_counts[key] / total_commit_count)

#plot
plt.clf()
fig, ax = plt.subplots()
ax.plot(activity_times, activity_avg, 'r', label='adoption sessions')
plt.axvline(x=0, color='k', lw=0.4)
plt.yscale('log')
plt.savefig("results/activity_analysis/avg_commit_activity_%s.png" % BIN_WIDTH, bbox_inches='tight')

exit(0)

#non-adopt
plt.clf()
fig, ax = plt.subplots()
ax.plot(non_times, non_vals, 'b', label='non-adopt sessions')
plt.yscale('log')
plt.xlim([0, 960])
plt.savefig("results/session_analysis/%s_avg_non_adopt_sessions_%s.png" % out_code, bbox_inches='tight')

print("Individual plots saved to results/session_analysis/%s_avg_adopt_sessions_%s.png and results/session_analysis/%s_avg_non_adopt_sessions_%s.png" % (out_code + out_code))

#save adopt and non-adopt data to csv
col_header = "time(%-of-session)" if NORM_TIME else "time(minutes)"
#adopt
np.savetxt("results/session_analysis/%s_avg_adopt_sessions_%s.csv" % out_code, np.column_stack(([col_header] + adopt_times, ['avg_commits'] + adopt_vals)), delimiter=",", fmt="%s")
#non-adopt
np.savetxt("results/session_analysis/%s_avg_non_adopt_sessions_%s.csv" % out_code, np.column_stack(([col_header] + non_times, ['avg_commits'] + non_vals)), delimiter=",", fmt="%s")
print("Data files saved to results/%s_avg_adopt_sessions_%s.csv and results/%s_avg_non_adopt_sessions_%s.csv" % (out_code + out_code))