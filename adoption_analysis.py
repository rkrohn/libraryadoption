#given adoption events and library usage counts, compute some counts and plot some frequency distributions

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
import matplotlib.pylab as plt
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

#given a user, repo, time triple, create a dictionary containing those values
def build_dict(user, repo, time):
	d = {}
	d["user"] = user
	d["repo"] = repo
	d["time"] = time
	return d
	
#given a dict with user, repo, time keys, unfold it
def unfold_dict(d):
	return d["user"], d["repo"], d["time"]
	
#given a sequence of values and a single value x, compute the CDF of x in that sequence
#if list is sorted and supply an index, should run faster
#returns value between 0 and 1	
def get_cdf(seq, x, index = -1):
	count = 0
	if index == -1:
		for value in seq:
			if value <= x:
				count = count + 1
	else:
		count = index
	prob = float(count) / float(len(seq))
	return prob	
	
#given dictionary of form key->count, compute frequencies of different counts
def count_freq(data):
	freq = defaultdict(int)
	min = -1
	max = -1
	for key in data:
		freq[data[key]] = freq[data[key]] + 1
		if min == -1 or data[key] < min:
			min = data[key]
		if max == -1 or data[key] > max:
			max = data[key]
	return freq, min, max
		
	
#given frequencies as dictionary, key = size, value = freq, plot them	
def plot_freq(freq, xlabel, ylabel, title, filename = "", x_max = 0, x_min = 0, log_scale = False, scatter = False):	
	lists = sorted(freq.items())
	x,y = zip(*lists)
	plot_data(x, y, xlabel, ylabel, title, filename, x_max, x_min, log_scale, scatter)	

#plot data given as x and y lists	
def plot_data(x, y, xlabel, ylabel, title, filename = "", x_max = 0, x_min = 0, log_scale = False, scatter = False):
	plt.clf()	
	fig, ax = plt.subplots()

	if scatter:
		plt.scatter(x, y)
	else:
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

#load library usage counts (overall for now)
print "Loading library usage counts..."
usage_counts = load_json("datafiles/import_counts_overall_%s.json" % module_type)

#don't have an adoption event file, yell at the user
if adoption_events == False or usage_counts == False:
	print "must have compiled adoption event list datafiles/adoption_events_%s.json" % (module_type + "_" + adop_type)
	print "exiting"
	sys.exit(0)
	
#adoption events look like this:
#	dictionary, where library is key
#	for each library, value is list of adoption events
#	each adoption event is a dictionary with keys "source" and "target"
#	source maps to list of source commits, each a dictionary with user, repo, time
#	target maps to a single dictionary with user, repo, time 
	
#counters for periodic prints	
lib_idx = 0	
event_idx = 0

#some statistic counts
multi_source = 0	#number of events with multiple sources
max_source = -1		#maximum number of sources for adoption events
intra_repo = 0		#number of target-source pairs where repo is the same
cross_repo = 0		#number of target-source pairs where repo is different
zero_count = 0		#number of target-source pairs with delta t of 0

#count number of adoptions per library
lib_adop_counts = {}

#extract delta-t for each source-target pair
delta_t = []

#get average delta-t for each library
lib_delta = {}
	
print "Looping adoption events by library..."
for lib in adoption_events:		#library is key of top-level dictionary

	lib_delta[lib] = 0

	#loop adoption events for this library
	for event in adoption_events[lib]:
	
		#does adoption have multiple sources?
		if len(event["source"]) > 1:
			multi_source = multi_source + 1
			if len(event["source"]) > max_source:
				max_source = len(event["source"])
			
		#taking each source as a separate event, is adoption intra-repo or cross-repo?
		for source in event["source"]:
			if source["repo"] == event["target"]["repo"]:
				intra_repo = intra_repo + 1
			else:
				cross_repo = cross_repo + 1
			#get time delta, save in places
			delta_t.append(event["target"]["time"] - source["time"])
			lib_delta[lib] = lib_delta[lib] + (event["target"]["time"] - source["time"])
			if delta_t[len(delta_t)-1] == 0:
				zero_count = zero_count + 1
	
		event_idx = event_idx + 1
		if event_idx % 5000 == 0:
			print "   finished", event_idx, "events"
	
	#count adoption events for this library
	lib_adop_counts[lib] = len(adoption_events[lib])
	
	#turn delta-t sum for library into average
	lib_delta[lib] = lib_delta[lib] / float(len(adoption_events[lib]))
	
	#period prints
	lib_idx = lib_idx + 1
	if lib_idx % 1000 == 0:
		print "   finished", lib_idx, "libraries" 
			
#finished, print the counts
print "processed", event_idx, "adoption events across", lib_idx, "libraries"
print "   ", multi_source, "of these events have multiple sources, max number of sources is", max_source
print intra_repo, "adoption source-target pairs within same repo"
print cross_repo, "adoption source-target pairs across different repos"
print zero_count, "adoption source-target pairs with time delay of 0"

#save lib adoption counts sorted most to least
lib_adop_counts_sorted = OrderedDict(sorted(lib_adop_counts.items(), key=itemgetter(1), reverse=True))
save_json(lib_adop_counts_sorted, "datafiles/lib_adop_counts_sorted_%s.json" % (module_type + "_" + adop_type))

#plots use usage counts, adoption counts, and average delta t: 

use_counts = []
adop_counts = []
avg_delta = []
for lib in usage_counts:
	if lib in lib_adop_counts:
		use_counts.append(usage_counts[lib])
		adop_counts.append(lib_adop_counts[lib])
		avg_delta.append(lib_delta[lib])
#total # of usages for library on x, total # of adoptions for lib on y
plot_data(use_counts, adop_counts, "Number of uses", "Number of adoptions", "Uses vs. Adoptions per Library", filename = "results/uses_vs_adoptions.png", scatter = True, log_scale = True)
print "Uses vs. adoptions plot saved to results/uses_vs_adoptions.png"

#frequency distribution of # of adoptions per library
lib_adop_freq, min_lib_adop, max_lib_adop = count_freq(lib_adop_counts)
plot_freq(lib_adop_freq, "library adoption count", "freq", "Frequency of library adoption counts", filename = "results/lib_adop_freq.jpg", log_scale = True)
print "lib adop counts: min =", min_lib_adop, ", max =", max_lib_adop
print "library adoption frequency distribution saved to results/lib_adop_freq.jpg"

#usages of library on x, average delta t on y
plot_data(use_counts, avg_delta, "Number of uses", "Average adoption time delay", "Uses vs. Adoption Time Delay per Library", filename = "results/uses_vs_avgdelta.png", scatter = True, log_scale = True)
print "Uses vs. average delta t plot saved to results/uses_vs_avgdelta.png"
#number of adoptions on x, average delta t on y
plot_data(adop_counts, avg_delta, "Number of adoptions", "Average adoption time delay", "Adoptions vs. Adoption Time Delay per Library", filename = "results/adoptions_vs_avgdelta.png", scatter = True, log_scale = True)
print "Adoptions vs. average delta t plot saved to results/adoptions_vs_avgdelta.png"

#sort the delta-t
delta_t_sorted = sorted(delta_t)
print "Adoption delta t ranges from ", delta_t_sorted[0], "to ", delta_t_sorted[len(delta_t_sorted)-1], "seconds"

#plot CDF and PDF of time deltas
print "Plotting time delta CDF and PDF..."
n = len(delta_t_sorted)		#number of items
idx = 0

#CDF variables
cdf_delta = []
delta_t_sample = []

#PDF variables
bins = range(0, delta_t_sorted[n-1]/86400+1)
counts = [0] * len(bins)

#loop time deltas
for val in delta_t_sorted:
	#get CDF value for every 1000 deltas
	if idx % 1000 == 0:
		delta_t_sample.append(val)
		cdf_delta.append(float(idx) / float(n))
	#put time deltas into 1-day wide bins for PDF
	counts[val/86400] = counts[val/86400] + 1
	
	idx = idx + 1
	
#divide PDF counts by total to get probabilities
probs = [float(item) / float(n) for item in counts]	
	
#plot CDF
plot_data(delta_t_sample, cdf_delta, "Adoption time delay (seconds)", "Probability", "CDF of Adoption Time Delay", filename = "results/adopt_delay_cdf.png")
print "CDF plot saved to results/adopt_delay_cdf.png"

#plot PDF
plot_data(bins, probs, "Adoption time delay (days)", "Probability", "PDF of Adoption Time Delay", filename = "results/adopt_delay_pdf.png", log_scale = True)
print "PDF plot saved to results/adopt_delay_pdf.png"
