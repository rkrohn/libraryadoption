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



#--- MAIN EXECUTION BEGINS HERE---#

MAX_DELAY = 9 * 3600		#maximum time between commits of the same session (in seconds)
BIN_SIZE = 0.5			#bin size in hours (0.5 for half hours)

bins = defaultdict(int)

#get list of user commit files to process
files = glob.glob('data_files/user_commits/*')
print("Processing", len(files), "user commit files")

#global counters: total number of commits, users, and sessions
commit_count = 0
user_count = 0
session_total = 0

#session data dictionaries
length_to_commits = defaultdict(int)	#session length (seconds) -> average number of commits per session (sum during processing)
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
		session_commit_count = 1		#number of commits in current session
		user_session_count = 1			#number of sessions for this user

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
				if delay >= MAX_DELAY:
					length = prev - session_start		#length of this session, from first commit to last

					#add this session data to tracking
					length_key = ceil(length / (BIN_SIZE * 3600)) * BIN_SIZE	#compute length of session according to BIN_SIZE
					length_to_commits[length_key] += session_commit_count
					length_to_freq[length_key] += 1

					#reset tracking for new session
					session_start = c['time']
					session_commit_count = 1
					user_session_count += 1
				#another commit to current session
				else:
					session_commit_count += 1

			prev = c['time']	#update prev for next commit

		#handle last session for this user
		length = prev - session_start		#length of this session, from first commit to last

		#add this session data to tracking
		length_key = ceil(length / (BIN_SIZE * 3600)) * BIN_SIZE	#compute length of session according to BIN_SIZE
		length_to_commits[length_key] += session_commit_count
		length_to_freq[length_key] += 1

		print("User", user, "made", len(commits), "commits across", user_session_count, "sessions")

		session_total += user_session_count 		#keep count of total number of sessions across all users

	break

print("Processed", commit_count, "commits and", user_count, "users in", session_total, "sessions")

#also do an average commit count for each binned session length
length_to_avg_commits = {}
for length, commits in length_to_commits.items():
		length_to_avg_commits[length] = commits / length_to_freq[length]

#dump all distribution data to csv
file_utils.dump_dict_csv([length_to_freq, length_to_commits, length_to_avg_commits], ["session length", "frequency", "total number of commits", "average commits per session"], "results/session_analysis/session_length_data_%s.csv" % BIN_SIZE)

#rough plot of frequency distribution - all and short
plot_utils.plot_dict_data(length_to_freq, "session length (hours)", "frequency", "Session Length Distribution", filename = "results/session_analysis/session_length_distribution_%s.png" % BIN_SIZE, log_scale_y = True)
plot_utils.plot_dict_data(length_to_freq, "session length (hours)", "frequency", "Session Length Distribution", filename = "results/session_analysis/session_length_distribution_%s_narrow.png" % BIN_SIZE, x_min = 0, x_max = 24, log_scale_y = True)

#also plot average commits per session
plot_utils.plot_dict_data(length_to_avg_commits, "session length (hours)", "average commits per session", "Session Length vs Average Commits", filename = "results/session_analysis/session_length_avg_commits_%s.png" % BIN_SIZE, log_scale_y = True)
plot_utils.plot_dict_data(length_to_avg_commits, "session length (hours)", "frequency", "Session Length vs Average Commits", filename = "results/session_analysis/session_length_avg_commits_%s_narrow.png" % BIN_SIZE, x_min = 0, x_max = 24, log_scale_y = True)