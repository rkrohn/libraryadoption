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

#--- MAIN EXECUTION BEGINS HERE---#

max_inactive = 9 * 3600		#maximum time between commits of the same session (in seconds)

#flags and values to set operating mode
BIN_WIDTH = 5			#sets number of minutes per bin
PRE_WIN = 6 * 3600		#amount of time, in seconds, to include in the pre-commit activity window
POST_WIN = 6 * 3600		#time, in seconds, to include in post-commit activity window
AVG_ADOPT = 13.94559333795975	#average position of adoption commits within session as percentage
								#(generated by sessions_adopt.py)
POS_MARGIN = 0.1		#percent margin for either side of AVG_ADOPT - will only include non-adopt commits within
						#this window

#get list of user commit files to process
files = glob.glob('data_files/user_commits/*')
print("Processing", len(files), "user commit files")

#global counters
total_commit_count = 0
total_adopt_commits = 0
total_user_count = 0
total_adopt_libs = 0
total_regular_commits_all = 0		#number of non-adopt commits stacked for comparison against adopt commits
									#(only commits that fall near AVG_ADOPT within their session)
total_regular_commits_closest = 0	#same count as above, but only for the closest non-adopt commits

#commit activity variables
adopt_activity_counts = defaultdict(int)	#key is minutes from adoption commit (pos or neg, in BIN_WIDTH increments)
											#value is # of commits made at that time (across all adopt commits by all users)
reg_activity_counts_all = defaultdict(int)		#same as above, but for regular non-adopt commits that fall at AVG_ADOPT
												#within their session, +/- POS_MARGIN
reg_activity_counts_closest = defaultdict(int)	#same as above, but instead of all matching commits, only stack the
												#closest matching from each session

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
		user_adopt_commits = 0	#number of adoption commits by user

		#commit indices
		pre_start = 0			#index of first commit included in pre-commit activity window
		post_end = 0			#index of first commit excluded from post-commit activity window
		session_start = 0		#index of first commit in current session

		total_commit_count += len(commits)		#add users's commits to total count

		#loop all commits made by this user
		for i in range(0, len(commits)):

			#grab current commit for easier access
			c = commits[i]	

			#compute delay between this commit and the previous (if previous commit exists)
			if prev != -1:
				delay = c['time'] - prev
			else:
				delay = None
				session_start = i

			#delay too long, new session, process old session
			if delay != None and delay >= max_inactive:

				#pull start time of session and compute length of session
				start_time = commits[session_start]['time']
				length = prev - start_time

				#activity window boundaries (commit indices) for non-adopt commits
				non_pre_start = 0
				non_post_end = 0

				#track index of non-adopt commit closest to adoption time
				closest_loc = -1
				closest_dist = -1
				closest_pre_start = 0
				closest_post_end = 0

				#find regular (non-adopt) commits that occur at around the same time/percent as the average adopt commit time
				for r_idx in range(session_start, i):
					#grab this regular commit r for easier access
					r = commits[r_idx]

					#skip this commit if adoption
					if r['adopted_libs']:
						continue

					#compute commit time/location as percentage of session length
					if length != 0:
						loc = ((r['time'] - start_time) / length) * 100
					else:
						loc = 0

					#if non-adopt commit and percent loc is close to avg adopt time, add to non-adopt activity total
					if loc < AVG_ADOPT + POS_MARGIN and loc > AVG_ADOPT - POS_MARGIN:
						#find surrounding commits for each matching commit

						#move up pre_start index if necessary so that commit it points to falls within PRE_WIN
						while r['time'] - commits[non_pre_start]['time'] > PRE_WIN:
							non_pre_start += 1
						#move up post_end index if necessary so that commit it points to falls outside POST_WIN
						while non_post_end < len(commits) and commits[non_post_end]['time'] - r['time'] < POST_WIN:
							non_post_end += 1

						surrounding_commits = commits[non_pre_start:non_post_end]	#extract commits that fall within defined activity window

						#for each commit within activity window, compute "minutes from commit" and add to relevant bin counter
						for b in surrounding_commits:
							reg_activity_counts_all[int((b['time'] - r['time']) / (BIN_WIDTH * 60))* BIN_WIDTH] += 1
						total_regular_commits_all += 1

						#keep track of the closest non-adopt commit for later
						if abs(loc - AVG_ADOPT) < closest_dist or closest_dist == -1:
							closest_dist = abs(loc - AVG_ADOPT)
							closest_loc = r_idx
							closest_pre_start = non_pre_start	#and store this commit's activity window
							closest_post_end = non_post_end

				#also stack just the closest commits from each session
				if closest_loc != -1:
					#find surrounding commits of desired commit
					r = commits[closest_loc]	#grab commit for easier access

					surrounding_commits = commits[closest_pre_start:closest_post_end]	#extract commits that fall within defined activity window

					#for each commit within activity window, compute "minutes from commit" and add to relevant bin counter
					for b in surrounding_commits:
						reg_activity_counts_closest[int((b['time'] - r['time']) / (BIN_WIDTH * 60))* BIN_WIDTH] += 1
					total_regular_commits_closest += 1

			#check if current commit contains an adoption, if so add to adoption stack
			if c['adopted_libs']:
				user_adopt_libs += len(c['adopted_libs'])	
				user_adopt_commits += 1	

				#move up pre_start index if necessary so that commit it points to falls within PRE_WIN
				while c['time'] - commits[pre_start]['time'] > PRE_WIN:
					pre_start += 1
				#move up post_end index if necessary so that commit it points to falls outside POST_WIN
				while post_end < len(commits) and commits[post_end]['time'] - c['time'] < POST_WIN:
					post_end += 1

				surrounding_commits = commits[pre_start:post_end]	#extract commits that fall within defined activity window

				#for each commit within activity window, compute "minutes from commit" and add to relevant bin counter
				for a in surrounding_commits:
					adopt_activity_counts[int((a['time'] - c['time']) / (BIN_WIDTH * 60))*BIN_WIDTH] += 1

			prev = c['time']	#update prev for next commit		

		#wrap up current user before moving to next
		print("User", user, "made", len(commits), "commits (" + str(user_adopt_commits), "adoption commits) adopting", user_adopt_libs, "libraries")	

		total_adopt_libs += user_adopt_libs
		total_adopt_commits += user_adopt_commits		

		break

	if total_adopt_commits > 10:
		break

print("Processed", total_commit_count, "commits and", total_user_count, "users")
print("   ", total_adopt_libs, "libraries adopted in", total_adopt_commits, "adoption commits")

exit(0)

print("\nStacked", total_regular_commits_all, "non-adoption commits for comparison (all matching)")
print("Stacked", total_regular_commits_closest, "nearest non-adoption commits for finer comparison")

#post-process totals for plotting
#get list of keys (times) that occur in either adopt or either non-adopt activity dictionary
times = sorted(list(adopt_activity_counts.keys()) + list(set(reg_activity_counts_all.keys()) - set(adopt_activity_counts.keys())))
times = sorted(list(times) + list(set(reg_activity_counts_closest.keys()) - set(times)))


#divide adopt commits totals by total number of adoption commits (average), also convert to lists at the same time
#divide regular commit totals by number of regular commits stacked
adopt_activity_avg = []
non_adopt_activity_avg_all = []
non_adopt_activity_avg_closest = []

for key in times:
	adopt_activity_avg.append(adopt_activity_counts[key] / total_adopt_commits)
	non_adopt_activity_avg_all.append(reg_activity_counts_all[key] / total_regular_commits_all)
	non_adopt_activity_avg_closest.append(reg_activity_counts_closest[key] / total_regular_commits_closest)

#first plot: adoption vs all matching non-adopt
plt.clf()
fig, ax = plt.subplots()
ax.plot(times, adopt_activity_avg, 'r', label='adoption commits')
ax.plot(times, non_adopt_activity_avg_all, 'b', label='non-adopt commits')
plt.legend(loc='best')
plt.axvline(x=0, color='k', lw=0.4)
plt.yscale('log')
plt.savefig("results/activity_analysis/commit_activity_%s_%s.png" % (BIN_WIDTH, "ALL"), bbox_inches='tight')

#second plot: adoption vs closest matching non-adopt
plt.clf()
fig, ax = plt.subplots()
ax.plot(times, adopt_activity_avg, 'r', label='adoption commits')
ax.plot(times, non_adopt_activity_avg_closest, 'b', label='non-adopt commits')
plt.legend(loc='best')
plt.axvline(x=0, color='k', lw=0.4)
plt.yscale('log')
plt.savefig("results/activity_analysis/commit_activity_%s_%s.png" % (BIN_WIDTH, "CLOSEST"), bbox_inches='tight')

print("Comarison plots saved to results/activity_analysis/commit_activity_%s_%s.png and results/activity_analysis/commit_activity_%s_%s.png" % (BIN_WIDTH, "ALL", BIN_WIDTH, "CLOSEST"))

#save adopt and both non-adopt data to csv
col_header = "time_from_commit_(minutes)"
np.savetxt("results/activity_analysis/commit_activity_data_%s.csv" % BIN_WIDTH, np.column_stack(([col_header] + times, ['adopt_activity'] + adopt_activity_avg, ['non_adopt_activity_all'] + non_adopt_activity_avg_all, ['non_adopt_activity_closest'] + non_adopt_activity_avg_closest)), delimiter=",", fmt="%s")