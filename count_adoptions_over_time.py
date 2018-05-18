#plot adoptions and total import commits over time

import json
import os.path
import subprocess
import sys
import urllib2
import io
from collections import defaultdict
import unicodedata
from collections import OrderedDict
from operator import itemgetter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
from networkx.algorithms import bipartite
from lxml import etree
import datetime
import itertools
import pandas as pd
import numpy as np

#save some data structure to json file
def save_json(data, filename):
	with open(filename, 'w') as fp:
		json.dump(data, fp, indent=4, sort_keys=False)
		
#load json to dictionary
def load_json(filename):
	if os.path.isfile(filename):
		with open(filename) as fp:
			data = json.load(fp)
			return data
	return False
	

#plot data given as x and y lists	
def plot_data(x, y, xlabel, ylabel, title, filename = "", x_max = 0, x_min = 0, log_scale = False):
	plt.clf()	
	fig, ax = plt.subplots()

	plt.plot(x, y)
	plt.title(title)
	plt.xlabel(xlabel)
	plt.ylabel(ylabel)
	if log_scale:
		ax.set_yscale('log')
		ax.set_xscale('log')
	if x_max != 0 and x_min != 0:
		plt.xlim(xmin=x_min, xmax=x_max)
	elif x_max != 0:
		plt.xlim(xmin=0, xmax=x_max)
	elif x_min != 0:
		plt.xlim(xmin=x_min, xmax=x_max)	
	if filename == "":
		plt.show()
	else:
		plt.savefig(filename, bbox_inches='tight')
		
		
#plot data given as x and 2 y lists	- will have 2 y axes on plot
def plot_two_axes(x, data1, data2, xlabel, ylabel1, ylabel2, title, filename = ""):
	plt.clf()	
		
	fig, ax1 = plt.subplots()

	ax1.set_xlabel(xlabel)
	ax1.set_ylabel(ylabel1, color='b')
	ax1.plot(x, data1, 'b-')
	ax1.tick_params(axis='y', labelcolor='b')

	ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

	ax2.set_ylabel(ylabel2, color='r')  # we already handled the x-label with ax1
	ax2.plot(x, data2, 'r-')
	ax2.tick_params(axis='y', labelcolor='r')
	
	plt.title(title)

	fig.tight_layout()  # otherwise the right y-label is slightly clipped	
		
	if filename == "":
		plt.show()
	else:
		plt.savefig(filename, bbox_inches='tight')
	

#--- MAIN EXECUTION BEGINS HERE---#	


#flag to determine how to count
#if true, take import exactly as stored, submodules included (SUB)
#if false, only take top package level, strip submodules (TOP)
SUB_MODULE = False	

#flag to determine adoption definition
#if true, assume user must see library get committed for it to count as an adoption
#	(user is actively "watching" repo when library is committed, but not necessarily 
#	committed for the first time to that repo)
#if false, assume user can adopt from libraries present in the repo when they first
#	start watching - no visible commit required
SIGHT = True

#module-type specifier (at this point, more of a file suffix specifier)
if SUB_MODULE:
	print "Searching for submodule adoptions"
	module_type = "SUB"
else:
	print "Searching for parent module adoptions"
	module_type = "TOP"	
	
#adoption condition specifier (another suffix)
if SIGHT:
	print "Adoption requires direct commit view"
	adop_type = "SIGHT"
else:
	print "Adoption from repo history allowed"
	adop_type = "HISTORY"

#load adoption events
print "Loading all adoption events..."
adoption_events = load_json("datafiles/adoption_events_%s.json" % (module_type + "_" + adop_type))

#load all commits
print "Loading all commits..."
all_commits = load_json("datafiles/all_add_commits_%s.json" % module_type)

#don't have an adoption event file, yell at the user
if adoption_events == False or all_commits == False:
	print "must have compiled adoption event list datafiles/adoption_events_%s.json and all commits list datafiles/all_add_commits_%s.json" % ((module_type + "_" + adop_type), module_type)
	print "exiting"
	sys.exit(0)
	
#adoption events look like this:
#	dictionary, where library is key
#	for each library, value is list of adoption events
#	each adoption event is a dictionary with keys "source" and "target"
#	source maps to list of source commits, each a dictionary with user, repo, time
#	target maps to a single dictionary with user, repo, time 

#list of adoption times (stored as datetime)
times_list = []
#keep track of earliest and latest adoption
latest = -1
earliest = -1
	
print "Compiling adoption events list by time..."
for lib in adoption_events:		#library is key of top-level dictionary

	#exclude relative paths (start with '.')
	if lib[0] == '.':
		continue

	for event in adoption_events[lib]:
		times_list.append(datetime.datetime.fromtimestamp(event["target"]["time"]))
		if event["target"]["time"] < earliest or earliest == -1:
			earliest = event["target"]["time"]
		if event["target"]["time"] > latest or latest == -1:
			latest = event["target"]["time"]

#list of commit times that fall between first and last adoptions (stored as datetime)
commit_times = []
print "Compiling commit times..."
for commit in all_commits:
	if commit["time"] <= latest and commit["time"] >= earliest:
		commit_times.append(datetime.datetime.fromtimestamp(commit["time"]))
		
# Create an empty dataframe
df = pd.DataFrame()
# Create a column from the datetime variable
df['datetime'] = times_list
# Convert that column into a datetime datatype
df['datetime'] = pd.to_datetime(df['datetime'])
# Set the datetime column as the index
df.index = df['datetime'] 

#and another for commit counts
df_c = pd.DataFrame()
df_c['datetime'] = commit_times
df_c['datetime'] = pd.to_datetime(df_c['datetime'])
# Set the datetime column as the index
df_c.index = df_c['datetime'] 

# Group the data by week, and take the count for each week
week_counts = df.resample('W').count()
week_counts.columns = ['adoptions']
commit_week = df_c.resample('W').count()
commit_week.columns = ['commits']
#merge for multi-axis plotting
week_merged = week_counts.merge(commit_week, how='outer', left_index=True, right_index=True)
week_merged.fillna(int(0), inplace=True)
#plot?
plot_data(week_counts.index, week_counts['adoptions'], "time", "number of adoption events per week", "Adoption Events Per Week", filename = "results/adop_over_time_week.png")
#double axis plot
plot_two_axes(week_merged.index, week_merged['adoptions'], week_merged['commits'], "time", "number of adoption events per week", "number of import commits per week", "Adoption Events and Import Commits Per Week", filename = "results/adop_commit_over_time_week.png")

# Group the data by week, and take the count for each week
month_counts = df.resample('M').count()
month_counts.columns = ['adoptions']
commit_month = df_c.resample('M').count()
commit_month.columns = ['commits']
#merge for multi-axis plotting
month_merged = month_counts.merge(commit_month, how='outer', left_index=True, right_index=True)
month_merged.fillna(int(0), inplace=True)
#plot?
plot_data(month_counts.index, month_counts['adoptions'], "time", "number of adoption events per month", "Adoption Events Per Month", filename = "results/adop_over_time_month.png")
#double axis plot
plot_two_axes(month_merged.index, month_merged['adoptions'], month_merged['commits'], "time", "number of adoption events per month", "number of import commits per month", "Adoption Events and Import Commits Per Month", filename = "results/adop_commit_over_time_month.png")
	