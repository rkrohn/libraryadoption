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

def cpm_rates(commit_times, first_adopt):
	#convert UTC times (seconds) to minutes from some reference point
	#no adoption, shift times relative to first commit
	if first_adopt == -1:
		relative_times = [int((time - commit_times[0]) / 60) for time in commit_times]
	#adoption session, shift all times relative to first adoption event
	else:
		relative_times = [int((time - commit_times[first_adopt]) / 60) for time in commit_times]

	print(user, user_sessions)
	print("   ", relative_times)

	#build list of minute counters covering entire range
	x = list(range(relative_times[0], relative_times[-1]+1))
	#and list of corresponding cpm rates
	y = [0] * len(x)
	for time in relative_times:
		y[time + abs(relative_times[0])] += 1

	#add extra entries to beginning and end of session with rate 0 for prettier plot
	x.insert(0, x[0]-1)
	y.insert(0, 0)
	x.append(x[-1]+1)
	y.append(0)

	if first_adopt != -1:
		plot_cpm(x, y, "results/cpm_session_plots/user%s_session%s_cpm.png" % (user, user_sessions), True)
	else:
		plot_cpm(x, y, "results/cpm_session_plots/user%s_session%s_cpm.png" % (user, user_sessions))

#end cpm_rates

#given a completed session as list of commit times and index of first adoption (if any),
#generate the pmf of the cpm rate on either side of the adoption event and plot
def session_pmf(commit_times, first_adopt):
	print(commit_times, first_adopt)

	if len(commit_times) >= 3 or first_adopt != -1:
		cpm_rates(commit_times, first_adopt)
	return

	#partition commit list if session contains an adoption event
	if first_adopt != -1:
		pre_adopt = commit_times[:first_adopt]
		post_adopt = commit_times[first_adopt:]
	else:
		pre_adopt = commit_times
		post_adopt = []

	print(pre_adopt, post_adopt)

	#for each session section, convert list of commit times to a by-minute cpm
	#but, we're going to do the pre-adopt section backwards from the adoption event
	cpm_rates(pre_adopt, post_adopt[0])
	cpm_rates(post_adopt)

#end session_pmf

#for a completed session, log all session data
def log_session(user_adopt_sessions):
	length = session_commit_times[-1] - session_commit_times[0]		#length of this session, from first commit to last

	#compute (and plot) the pmf of the cpm, normalized to either side of the first adoption event
	session_pmf(session_commit_times, session_first_adopt)

	commit_count = len(session_commit_times)	#grab commit count as variable

	'''
	print(timedelta(seconds=(length)).__str__(), "session with", commit_count, "commits")
	if session_first_adopt != -1:
		print("   first adopt at", session_commit_times[session_first_adopt])

	#basic commits per minute?
	if length != 0:
		print(commit_count / (length / 60), "commits per minute average")
	else:
		print(commit_count, "commits per minute (0-length session)")
	'''

	#update user adoption counters if this session contained an adoption
	if session_first_adopt != -1:
		user_adopt_sessions += 1

	#add this session data to global tracking
	len_bin = ceil(length / 1800) / 2		#compute half-hour bin for this session

	return user_adopt_sessions
#end log_session

#given x-axis values x and corresponding probability values y, plot the pmf
#note y values must sum to exactly 1
def plot_pmf(x, y, filename):
	custm = stats.rv_discrete(name='custm', values=(x, y))
	fig, ax = plt.subplots(1, 1)
	ax.plot(x, custm.pmf(x), 'bo', ms=2, mec='b')
	ax.vlines(x, 0, custm.pmf(x), colors='b', linestyles='-', lw=0.5)
	plt.title('PMF')
	plt.ylabel('Probability')
	plt.savefig(filename, bbox_inches='tight')	
#end plot_pmf

#given x-axis values x and corresponding cpm rates y, plot the cpm rate as a step function
def plot_cpm(x, y, filename, adopt = False):
	plt.clf()
	plt.step(x, y, where='post')
	plt.title('CPM')
	plt.ylabel('CPM')

	if adopt:
		plt.axvline(x=0, color='r')

	plt.savefig(filename, bbox_inches='tight')	
#end plot_cpm

#--- MAIN EXECUTION BEGINS HERE---#

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

#process each file one at a time
for file in files:
	print("\nProcessing", file)

	user_commits = load_pickle(file)

	total_user_count += len(user_commits)

	#for each user in this chunk, step through their commits
	for user, commits in user_commits.items():

		#REMOVE
		if user != 51047:
			continue

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

			#print("   ", c['user'], c['time'], c['repo'], len(c['adopted_libs']))

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

		#REMOVE
		if user == 51047:
			break

	break

print("Processed", total_commit_count, "commits and", total_user_count, "users in", total_sessions, "sessions")
print("   ", total_adopt_libs, "libraries adopted in", total_adopt_commits, "commits across", total_adopt_sessions, "sessions")

