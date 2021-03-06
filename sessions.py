import glob
import sys
import pandas as pd
import os
import pickle
from collections import defaultdict
from math import ceil
from datetime import timedelta
import file_utils
import plot_utils

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
	#length of this session, from first commit to last
	length = prev_commit - curr_start		
	#compute length of session according to BIN_SIZE
	length_key = ceil(length / (BIN_SIZE * 3600)) * BIN_SIZE	

	#update user adoption counters if this session contained an adoption
	if curr_adopt_commits != 0:
		user_adopt_sessions += 1
		user_adopt_commits += curr_adopt_commits
		user_adopt_libs += curr_adopt_libs

	#add this session data to global tracking
	#update all the counters
	session_freq[length_key] += 1	#session length frequency
	#session commit counts - all sessions		
	session_avg_commits[length_key] += curr_commit_count
	session_avg_adopt_commits[length_key] += curr_adopt_commits
	#number of commits in session added to lists
	session_commit_counts[length_key].append(curr_commit_count)
	session_adopt_commit_counts[length_key].append(curr_adopt_commits)

	#session contains adoption? update adoption session counters
	if curr_adopt_commits != 0:
		session_adopt_freq[length_key] += 1
		session_avg_commits_when_adopt[length_key] += curr_commit_count
		#session commit count added to adoption sessions list
		session_commits_when_adopt[length_key].append(curr_commit_count)		
		#adoption commit position for sessions with this many commits
		adopt_commit_positions[curr_commit_count].extend(curr_adopt_positions)
		adopt_commit_times[length_key].extend(curr_adopt_times)
	#no adoption, update no-adopt session counters and lists
	else:
		session_avg_commits_no_adopt[length_key] += curr_commit_count
		session_commits_no_adopt[length_key].append(curr_commit_count)	

	return user_adopt_sessions, user_adopt_commits, user_adopt_libs
#end log_session

#--- MAIN EXECUTION BEGINS HERE---#
global total_adopt_libs, total_adopt_commits, total_adopt_sessions, BIN_SIZE

MAX_DELAY = 9 * 3600		#maximum time between commits of the same session (in seconds)
BIN_SIZE = 0.5			#bin size in hours (0.5 for half hours)

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

#session data stored as various dictionaries, binned length is always the key
#some of this is tracked as data is processed, others is constructed from lists after the fact
session_freq = defaultdict(int)					#number of sessions
session_adopt_freq = defaultdict(int)			#number of sessions with adoption
session_avg_commits = defaultdict(int)			#avg commits for all sessions
session_avg_adopt_commits = defaultdict(int)	#average number of adoption commits for all sessions
session_avg_commits_when_adopt = defaultdict(int)		#average number of commits when session contains adoption
session_avg_commits_no_adopt = defaultdict(int)			#average number of commits when session does not contain adoption

#session list data: dictionary of bin length -> list of commit counts for sessions of that length
session_commit_counts = defaultdict(list)		#list of session commit counts for sessions of this length
session_adopt_commit_counts = defaultdict(list)	#list of session adoption commit counts
session_commits_when_adopt = defaultdict(list)	#list of session commit counts for sessions containing adoption
session_commits_no_adopt = defaultdict(list)	#list of session commit counts for sessions not containing adoption

#dictionary tracking adoption event positions within sessions
#key is number of commits in that session, value is list of commit numbers of adoption events (numbers start at 1)
#list covers all adoption events, not just a particular session or user
adopt_commit_positions = defaultdict(list)

#another adoption position dictionary
#key is length of session in seconds - binned, value is time of adoption events measured in seconds from session start
#again, covers all adoption events, not a single session or user
adopt_commit_times = defaultdict(list)

#variable for storing/computing average adoption commit location within session
#for each adoption commit, we add the adoption time as percentage through the session
adopt_times_list = []	#list of adoption times (all adoptions) as percentage of session
avg_adopt_time = 0		#overall average adoption time

#same as above, but exclude single-commit sessions
adopt_times_list_non_zero = []
avg_adopt_time_nonzero = 0

#process each file one at a time
for file in files:
	print("\nProcessing", file)

	user_commits = load_pickle(file)

	total_user_count += len(user_commits)

	#for each user in this chunk, step through their commits
	for user, commits in user_commits.items():

		#session variables/counters
		prev_commit = -1	#time of this user's previous commit
		curr_start = -1			#UTC time of start of current session
		curr_commit_count = 1		#number of commits in current session
		curr_adopt_commits = 0			#number of adoption commits by user in current session
		curr_adopt_libs = 0				#number of libraries adopted by user in current session
		curr_adopt_positions = []		#list of commit numbers of adoption commits
		curr_adopt_times = []			#list of adoption times measured from session start

		#user variables/counters
		user_session_count = 1			#number of sessions for this user
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
				curr_start = c['time']

			#process delay if valid
			if delay != None:

				#delay too long, new session
				if delay >= MAX_DELAY:

					#update all global tracking based on this session
					user_adopt_sessions, user_adopt_commits, user_adopt_libs = log_session(user_adopt_sessions, user_adopt_commits, user_adopt_libs)

					#add adopt time % to total for overall average
					length = prev_commit - curr_start
					for time in curr_adopt_times:	#for all adopt times in session
						if length != 0:
							percent = (time / length) * 100
							avg_adopt_time += percent
							adopt_times_list.append(percent)
							avg_adopt_time_nonzero += percent
							adopt_times_list_non_zero.append(percent)
						else:
							#session length 0, adopt time/percent 0, no change to sum
							adopt_times_list.append(0)

					#reset tracking for new session
					curr_start = c['time']
					curr_commit_count = 1
					curr_adopt_commits = 0
					curr_adopt_libs = 0
					curr_adopt_positions = []
					curr_adopt_times = []

					user_session_count += 1		#add to user's session counter

				#delay not too long, add another commit to current session
				else:
					curr_commit_count += 1

				#check if current commit contains an adoption, if so flag the session as adopting
				if c['adopted_libs']:
					curr_adopt_commits += 1
					curr_adopt_libs += len(c['adopted_libs'])
					curr_adopt_positions.append(curr_commit_count)	#number commits starting at 1
					curr_adopt_times.append(c['time'] - curr_start)

			prev_commit = c['time']	#update prev for next commit

		#handle last session for this user
		user_adopt_sessions, user_adopt_commits, user_adopt_libs = log_session(user_adopt_sessions, user_adopt_commits, user_adopt_libs)		#update all global tracking

		print("User", user, "made", len(commits), "commits across", user_session_count, "sessions")
		if user_adopt_sessions != 0:
			print("   ", user_adopt_libs, "libraries adopted in", user_adopt_commits, "commits across", user_adopt_sessions, "sessions")

		#update global counters based on user's entire history
		total_sessions += user_session_count 		#keep count of total number of sessions across all users
		total_adopt_sessions += user_adopt_sessions
		total_adopt_commits += user_adopt_commits
		total_adopt_libs += user_adopt_libs

print("\nProcessed", total_commit_count, "commits and", total_user_count, "users in", total_sessions, "sessions")
print("   ", total_adopt_libs, "libraries adopted in", total_adopt_commits, "commits across", total_adopt_sessions, "sessions")

#POST-PROCESSING

#compute average commit counts for each binned session length
for length in session_freq.keys():		#loop keys (same for all dicts)
		#overall average commits per session and average adoption commits per session
		session_avg_commits[length] /= session_freq[length]
		session_avg_adopt_commits[length] /= session_freq[length]

		#average commits per session if session contains adoption
		if session_adopt_freq[length] != 0:
			session_avg_commits_when_adopt[length] /= session_adopt_freq[length]
		else:
			session_avg_commits_when_adopt[length] = None
		#average commits per session if session does not contain adoption
		if session_freq[length] - session_adopt_freq[length] != 0:
			session_avg_commits_no_adopt[length] /= (session_freq[length] - session_adopt_freq[length])
		else:
			session_avg_commits_no_adopt[length] = None

#compute overall average adoption time as percentage of session
avg_adopt_time = avg_adopt_time / total_adopt_commits
print("\nAverage adopt time as percentage of session (all sessions):", avg_adopt_time)

#compute average adoption time excluding single-commit sessions
avg_adopt_time_nonzero = avg_adopt_time_nonzero / len(adopt_times_list_non_zero)
print("Average adopt time (no single commit sessions):", avg_adopt_time_nonzero, "\n")

#compute average adoption positions, both by time (binned) and by commit number (exact)
#commit times
avg_adopt_commit_time = {}
for length in session_freq.keys():	#make sure all lengths represented
	if len(adopt_commit_times[length]) != 0:
		avg_adopt_commit_time[length] = sum(adopt_commit_times[length]) / len(adopt_commit_times[length])
	else:
		avg_adopt_commit_time[length] = None
#commit positions
avg_adopt_commit_position = {}
for commit_count in adopt_commit_positions.keys():
	avg_adopt_commit_position[commit_count] = sum(adopt_commit_positions[commit_count]) / len(adopt_commit_positions[commit_count])

#DUMP DATA

#dump all session length data (counts and averages) to single csv
file_utils.dump_dict_csv([session_freq, session_adopt_freq, session_avg_commits, session_avg_adopt_commits, session_commits_when_adopt, session_avg_commits_no_adopt, avg_adopt_commit_time], ["session length (hours)", "number of sessions", "number of sessions containing adoption", "average commits per session", "average adoption commits per session", "average commits for sessions containing adoption", "average commits for sessions without adoption", "average adoption time (seconds from session start)"], "results/session_analysis/session_length_data_%s.csv" % BIN_SIZE)

#average commit positions in separate file
file_utils.dump_dict_csv(avg_adopt_commit_position, ["number of commits in session", "average adoption commit position (first commit = 1)"], "results/session_analysis/session_avg_adopt_commit_pos.csv")

#dump dictionaries of key-> list each to separate csv file
file_utils.dump_dict_of_lists(session_commit_counts, ["session length (hours)", "commit counts ->"], "results/session_analysis/commit_counts_by_session_length_%s.csv" % BIN_SIZE)
file_utils.dump_dict_of_lists(session_adopt_commit_counts, ["session length (hours)", "adopt commit counts ->"], "results/session_analysis/adopt_commit_counts_by_session_length_%s.csv" % BIN_SIZE)
file_utils.dump_dict_of_lists(session_commits_when_adopt, ["session length (hours)", "commit counts (only sessions containing adoption) ->"], "results/session_analysis/commit_counts_when_adopt_by_session_length_%s.csv" % BIN_SIZE)
file_utils.dump_dict_of_lists(session_commits_no_adopt, ["session length (hours)", "commit counts (only sessions without adoption) ->"], "results/session_analysis/commit_counts_when_no_adopt_by_session_length_%s.csv" % BIN_SIZE)
#adoption position lists by session length
file_utils.dump_dict_of_lists(adopt_commit_positions, ["session length (number of commits)", "adoption position (commits numbered from 1) ->"], "results/session_analysis/adopt_commit_pos_by_session_length_%s.csv" % BIN_SIZE)
file_utils.dump_dict_of_lists(adopt_commit_times, ["session length (hours)", "adoption time (seconds from session start) ->"], "results/session_analysis/adopt_time_by_session_length_%s.csv" % BIN_SIZE)

#save adoption time lists to same file
file_utils.dump_lists([adopt_times_list, adopt_times_list_non_zero], ["all adoption times (percentage of session)", "adoption times excluding single-commit sessions (percentage of session)"], "results/session_analysis/adopt_times_lists.csv")

exit(0)		#REMOVE

#GENERATE AND SAVE PLOTS - maybe later, if I still care

#rough plot of frequency distribution - all and short
plot_utils.plot_dict_data(length_to_freq, "session length (hours)", "frequency", "Session Length Distribution", filename = "results/session_analysis/session_length_distribution_%s.png" % BIN_SIZE, log_scale_y = True)
plot_utils.plot_dict_data(length_to_freq, "session length (hours)", "frequency", "Session Length Distribution", filename = "results/session_analysis/session_length_distribution_%s_narrow.png" % BIN_SIZE, x_min = 0, x_max = 24, log_scale_y = True)

#also plot average commits per session
plot_utils.plot_dict_data(length_to_avg_commits, "session length (hours)", "average commits per session", "Session Length vs Average Commits", filename = "results/session_analysis/session_length_avg_commits_%s.png" % BIN_SIZE, log_scale_y = True)
plot_utils.plot_dict_data(length_to_avg_commits, "session length (hours)", "frequency", "Session Length vs Average Commits", filename = "results/session_analysis/session_length_avg_commits_%s_narrow.png" % BIN_SIZE, x_min = 0, x_max = 24, log_scale_y = True)