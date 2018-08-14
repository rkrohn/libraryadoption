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

def cpm_rates(commit_times, first_adopt, plot = False):
	#convert UTC times (seconds) to minutes from some reference point
	#no adoption, shift times relative to first commit
	if first_adopt == -1:
		relative_times = [int((time - commit_times[0]) / 60) for time in commit_times]
	#adoption session, shift all times relative to first adoption event
	else:
		relative_times = [int((time - commit_times[first_adopt]) / 60) for time in commit_times]

	#build list of minute counters covering entire range
	x = list(range(relative_times[0], relative_times[-1]+1))
	#and list of corresponding cpm rates
	y = [0] * len(x)
	for time in relative_times:
		y[time + abs(relative_times[0])] += 1

	#add extra entries to beginning and end of session with rate 0 for prettier plot (but not for normalization)
	x_plot = list(x)
	y_plot = list(y)
	x_plot.insert(0, x[0]-1)
	y_plot.insert(0, 0)
	x_plot.append(x[-1]+1)
	y_plot.append(0)

	if plot:
		if first_adopt != -1:
			plot_cpm(x_plot, y_plot, "results/cpm_session_plots/CPM_user%s_session%s.png" % (user, user_sessions), True)
		else:
			plot_cpm(x_plot, y_plot, "results/cpm_session_plots/CPM_user%s_session%s.png" % (user, user_sessions))

	return x, y

#end cpm_rates

#given discontinuous function defined by f(x) = y, convert to pmf
def convert_pmf(x, y):
	#get sum of y values - will use as divisor
	total = sum(y)

	#divide all y values by total, so they all sum to 1
	y[:] = [val / total for val in y]

	return y 		#return updated y (x doesn't change)
#end convert_pmf

#given a completed session as list of commit times and index of first adoption (if any),
#generate the pmf of the cpm rate on either side of the adoption event and plot
def session_commits(commit_times, first_adopt, plot = False):	

	commit_minutes, cpm = cpm_rates(commit_times, first_adopt)

	#convert cpm rates (all whole numbers) to pmf function
	if PMF_SESSION:
		cpm = convert_pmf(commit_minutes, cpm)	

		#plot pmf for this session (optional)
		if plot:
			plot_pmf(commit_minutes, cpm, "results/cpm_session_plots/PMF_user%s_session%s.png" % (user, user_sessions), adopt=(False if first_adopt == -1 else True))
	#no pmf of session, work with commit counts instead (but var has same name)

	#normalize time scale, partition at adoption if necessary
	if NORM_TIME:
		#if session contains adoption, partition at 0
		if first_adopt != -1:
			partition = commit_minutes.index(0)		#find the 0 - partition point
			pre_adopt = commit_minutes[:partition]
			post_adopt = commit_minutes[partition:]

			#normalize both sides separately, then combine
			normalized_times= normalize(pre_adopt, -100, 0)
			normalized_times  += normalize(post_adopt, 0, 100)
		#otherwise, take all commits at once
		else:
			normalized_times = normalize(commit_minutes, -100, 100)

		#plot normalized pmf for this session (optional)
		if plot:
			plot_pmf(normalized_times, cpm, "results/cpm_session_plots/NORM_%s_user%s_session%s_maxlen_%s.png" % (("PMF" if PMF_SESSION else "CPM"), user, user_sessions, max_session_length/3600), adopt=(False if first_adopt == -1 else True))

		#return normalized cpm pmf function
		return normalized_times, cpm

	#no normalize, return standard times
	return commit_minutes, cpm
#end session_pmf

#for a completed session, log all session data
def log_session(user_adopt_sessions):
	length = session_commit_times[-1] - session_commit_times[0]		#length of this session, from first commit to last

	#if session longer than max length, skip this session entirely
	if length > max_session_length and max_session_length != -1:
		return user_adopt_sessions		#unchanged

	#compute (and plot, if desired) the pmf of the cpm, normalized to either side of the first adoption event
	times, commits = session_commits(session_commit_times, session_first_adopt)

	#add this session commit data (pmf or commit counts) to overall session counters
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

	#special case: only one element
	if len(data) == 1:
		#set to range_start if negative
		if data[0] < 0:
			return [range_start]
		#set to 0 if 0
		elif data[0] == 0:
			return [0]

	#X′ = a + [(X − Xmin)(b − a) / (Xmax − Xmin)] 

	data_min = min(data)
	data_max = max(data)

	normalized = [range_start + (((x - data_min)*(range_end - range_start))/(data_max - data_min)) for x in data]

	return normalized
#end normalize

#given x-axis values x and corresponding probability values y, plot the pmf
#note y values must sum to exactly 1
def plot_pmf(x, y, filename, adopt = False):
	custm = stats.rv_discrete(name='custm', values=(x, y))
	fig, ax = plt.subplots(1, 1)
	ax.plot(x, custm.pmf(x), 'bo', ms=2, mec='b')
	ax.vlines(x, 0, custm.pmf(x), colors='b', linestyles='-', lw=0.7)
	plt.title('PMF')
	plt.ylabel('Probability')

	if adopt:
		plt.axvline(x=0, color='r', lw=0.4)

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

#boolean flags to set operating mode
PMF_SESSION = True		#perform PMF normalization on each session if true; skip otherwise
NORM_TIME = True		#normalize all session lengths to same range if true; stack by time otherwise

#set session length limit (in seconds) - any sessions longer than this will not be considered in averages
#set to -1 if want no limit
max_session_length = -1		#16 * 3600

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

print("Processed", total_commit_count, "commits and", total_user_count, "users in", total_sessions, "sessions")
print("   ", total_adopt_libs, "libraries adopted in", total_adopt_commits, "commits across", total_adopt_sessions, "sessions")

#post-process totals for plotting
#divide time totals by number of sessions contributing to that time, also convert to lists at the same time
adopt_times = []
adopt_vals = []
non_times = []
non_vals = []	
if NORM_TIME:
	#adopt sessions
	for key in sorted(total_adopt.keys()):
		adopt_times.append(key)
		adopt_vals.append(total_adopt[key] / total_adopt_sessions)
	#non-adopt sessions	
	total_non_adopt_sessions = total_sessions - total_adopt_sessions
	for key in sorted(total_non_adopt.keys()):
		non_times.append(key)
		non_vals.append(total_non_adopt[key] / total_non_adopt_sessions)
else:
	#adopt sessions
	for key in sorted(total_adopt.keys()):
		adopt_times.append(key)
		adopt_vals.append(total_adopt[key] / adopt_add[key])
	#non-adopt sessions	
	for key in sorted(total_non_adopt.keys()):
		non_times.append(key)
		non_vals.append(total_non_adopt[key] / non_adopt_add[key])

#save adopt and non-adopt dictionaries as pickles
out_tuple = ("PMF" if PMF_SESSION else "CPM", "NORM" if NORM_TIME else "TIME")
dump_data(adopt_vals, "results/%s_%s_avg_adopt_vals_maxlen_%s.pkl" % (out_tuple + (max_session_length//3600,)))
dump_data(non_vals, "results/%s_%s_avg_non_adopt_vals_maxlen_%s.pkl" % (out_tuple + (max_session_length//3600,)))
dump_data(adopt_times, "results/%s_%s_avg_times_maxlen_%s.pkl" % (out_tuple + (max_session_length//3600,)))
print("Data saved to results/%s_%s_avg_adopt_vals_maxlen_%s.pkl, results/%s_%s_avg_non_adopt_vals_maxlen_%s.pkl, and results/%s_%s_avg_times_maxlen_%s.pkl" % (out_tuple + (max_session_length//3600,) + out_tuple + (max_session_length//3600,) + out_tuple + (max_session_length//3600,)))

#plot average pmfs! (separate plots for now)
if PMF_SESSION and NORM_TIME and max_session_length == -1:
	plot_pmf(adopt_times, adopt_vals, "results/cpm_session_plots/PMF_NORM_avg_adopt_sessions_maxlen_%s.png" % (max_session_length//3600), adopt = True)
	plot_pmf(non_times, non_vals, "results/cpm_session_plots/PMF_NORM_avg_non_adopt_sessions_maxlen_%s.png" % (max_session_length//3600), adopt = False)

	print("Average normalized cpm pmf plots saved to results/cpm_session_plots/PMF_NORM_avg_adopt_sessions_maxlen_%s.png and results/cpm_session_plots/PMF_NORM_avg_non_adopt_sessions_maxlen_%s.png" % (max_session_length//3600, max_session_length//3600))
#no time normalization, plot adopt and non-adopt curves independently
elif NORM_TIME == False:
#plot again, this time both on the same line plot
	plt.clf()
	fig, ax = plt.subplots()
	ax.plot(adopt_times, adopt_vals, 'r', label='adoption sessions')
	plt.axvline(x=0, color='r', lw=0.4)
	plt.yscale('log')
	plt.savefig("results/cpm_session_plots/%s_%s_avg_adopt_sessions_maxlen_%s.png" % (out_tuple + (max_session_length//3600,)), bbox_inches='tight')

	print("Modified average normalized cpm pmf plot saved to results/cpm_session_plots/%s_%s_combined_avg_adopt_sessions_maxlen_%s.png" % (out_tuple + (max_session_length//3600,)))

	plt.clf()
	fig, ax = plt.subplots()
	ax.plot(non_times, non_vals, 'b', label='non-adopt sessions')
	plt.yscale('log')
	plt.savefig("results/cpm_session_plots/%s_%s_avg_non_adopt_sessions_maxlen_%s.png" % (out_tuple + (max_session_length//3600,)), bbox_inches='tight')

	print("Individual plots saved to results/cpm_session_plots/%s_%s_avg_adopt_sessions_maxlen_%s.png and results/cpm_session_plots/%s_%s_avg_non_adopt_sessions_maxlen_%s.png" % (out_tuple + (max_session_length//3600,) + out_tuple + (max_session_length//3600,)))

#plot again, this time both on the same line plot
plt.clf()
fig, ax = plt.subplots()
ax.plot(adopt_times, adopt_vals, 'r', label='adoption')
ax.plot(non_times, non_vals, 'b', label='non-adopt')
legend = ax.legend(loc='best', shadow=True, fontsize='x-large')
plt.axvline(x=0, color='r', lw=0.4)
plt.yscale('log')
plt.savefig("results/cpm_session_plots/%s_%s_combined_avg_adopt_sessions_maxlen_%s.png" % (out_tuple + (max_session_length//3600,)), bbox_inches='tight')

print("Modified average normalized cpm pmf plot saved to results/cpm_session_plots/%s_%s_combined_avg_adopt_sessions_maxlen_%s.png" % (out_tuple + (max_session_length//3600,)))