#compute and plot import counts, frequencies, and distributions

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

#given dictionary of form key->count, compute frequencies of different counts
def count_freq(data, local = True):
	freq = defaultdict(int)
	min = -1
	max = -1
	for key in data:
		if local and key[0] == '.':
			continue
		freq[data[key]] = freq[data[key]] + 1
		if min == -1 or data[key] < min:
			min = data[key]
		if max == -1 or data[key] > max:
			max = data[key]
	return freq, min, max
		
	
#given frequencies as dictionary, key = size, value = freq, plot them	
def plot_freq(freq, xlabel, ylabel, title, filename = "", x_max = 0, x_min = 0, log_scale = False):
	plt.clf()	
	lists = sorted(freq.items())
	x,y = zip(*lists)
	fig, ax = plt.subplots()
	plt.plot(x,y)
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
#if true, take import exactly as stored, submodules included
#if false, only take top package level, strip submodules
SUB_MODULE = True	

#file count-type specifier
if SUB_MODULE:
	print "Counting with submodules"
	count_type = "SUB"
else:
	print "Counting top-level package only"
	count_type = "TOP"

self_ref_count = 0

#load counts if have them
import_counts_overall = load_json("import_counts_overall_%s.json" % count_type)
import_repo_counts = load_json("import_repo_counts_%s.json" % count_type)
import_user_counts = load_json("import_user_counts_%s.json" % count_type)
if import_counts_overall == False or import_repo_counts == False or import_user_counts == False:
	import_counts_overall = defaultdict(int)	#number of additions across all repos and users
	import_repos = defaultdict(set) #list of repos using library
	import_users = defaultdict(set) #list of users using library

	file_idx = 0

	#for each commit log file:
	for filename in os.listdir('imports_data'):

		#extract repo name
		repo = filename[:-4]

		#read in all commits
		commits = load_json("imports_data/%s" % filename)
		#list of commits, each commit is a list containing user, time, and import dict
		#import dict has keys "+" and "-", leads to list of packages/libraries
		
		#loop all commits
		for commit in commits:		#each commit is user, time, dictionary of imports
			if "+" in commit[2]:	#if additions key
				#update counts/sets for each import package
				for package in commit[2]["+"]:
					#counting with submodules, take package name as-is
					if SUB_MODULE:
						lib = package						
					#not counting with submodules, get parent package only
					else:
						tokens = package.split('.')    #split on .
						lib = ""
						for token in tokens:
							if token == "":
								lib = lib + "."
							else:
								lib = lib + token
								break
					#update counts with correct package string
					import_counts_overall[lib] = import_counts_overall[lib] + 1
					import_repos[lib].add(repo)
					import_users[lib].add(commit[0])

		#period prints
		file_idx = file_idx + 1
		if file_idx % 500 == 0:
			print "finished", file_idx, "files"
			
	#convert sets to counts, throw out any with only 1 usage (try to narrow the field)
	#also convert the sets to lists, so they can be saved as json
	import_repo_counts = defaultdict(int)
	import_user_counts = defaultdict(int)
	import_repos_list = defaultdict(list)
	import_users_list = defaultdict(list)
	for k, v in import_repos.items():
		if len(import_repos[k]) == 1 or len(import_users[k]) == 1:
			del import_repos[k]
			del import_users[k]
			del import_counts_overall[k]
		else:
			import_repo_counts[k] = len(import_repos[k])
			import_user_counts[k] = len(import_users[k])
			import_repos_list[k] = list(import_repos[k])
			import_users_list[k] = list(import_users[k])
			
	#sort the counts (painful conversion, hopefully not too slow)
	import_counts_overall = OrderedDict(sorted(import_counts_overall.items(), key=itemgetter(1), reverse=True))
	import_repo_counts = OrderedDict(sorted(import_repo_counts.items(), key=itemgetter(1), reverse=True))
	import_user_counts = OrderedDict(sorted(import_user_counts.items(), key=itemgetter(1), reverse=True))	

	#save counts to json
	save_json(import_counts_overall, "import_counts_overall_%s.json" % count_type)
	save_json(import_repo_counts, "import_repo_counts_%s.json" % count_type)
	save_json(import_user_counts, "import_user_counts_%s.json" % count_type)

	#save the lists too (why not)
	save_json(import_repos_list, "import_repos_lists_%s.json" % count_type)
	save_json(import_users_list, "import_users_lists_%s.json" % count_type)

	print "results saved to import_??_counts.json (3 files) and import_??_lists.json (2 files)"
else:
	"read in counts, plotting distributions"

for key in import_counts_overall:
	#count self references (begin with ".")
	if key[0] == '.':
		self_ref_count = self_ref_count + 1
	
#plot distributions regardless
#repo count distribution, front and all
repo_count_freq, repo_min, repo_max = count_freq(import_repo_counts)
print "repo counts: min", repo_min, "max", repo_max
plot_freq(repo_count_freq, "number of unique repos importing", "frequency", "Package Import Frequency (%s)" % count_type, filename = "results/repo_count_freq_%s.png" % count_type, log_scale = True)

#user count distribution
user_count_freq, user_min, user_max = count_freq(import_user_counts)
print "user counts: min", user_min, "max", user_max
plot_freq(user_count_freq, "number of unique users importing", "frequency", "Package Import Frequency (%s)" % count_type, filename = "results/user_count_freq_%s.png" % count_type, log_scale = True)

#overall occurrence count distribution
overall_count_freq, overall_min, overall_max = count_freq(import_counts_overall)
print "overall counts: min", overall_min, "max", overall_max
plot_freq(overall_count_freq, "number of times imported", "frequency", "Package Import Frequency (%s)" % count_type, filename = "results/overall_count_freq_%s.png" % count_type, log_scale = True)

#plot again without local (self-ref) modules
#repo count distribution, front and all
repo_count_freq, repo_min, repo_max = count_freq(import_repo_counts, False)
print "repo counts: min", repo_min, "max", repo_max
plot_freq(repo_count_freq, "number of unique repos importing", "frequency", "Package Import Frequency (%s)" % count_type, filename = "results/repo_count_freq_no_path%s.png" % count_type, log_scale = True)

#user count distribution
user_count_freq, user_min, user_max = count_freq(import_user_counts, False)
print "user counts: min", user_min, "max", user_max
plot_freq(user_count_freq, "number of unique users importing", "frequency", "Package Import Frequency (%s)" % count_type, filename = "results/user_count_freq_no_path%s.png" % count_type, log_scale = True)

#overall occurrence count distribution
overall_count_freq, overall_min, overall_max = count_freq(import_counts_overall, False)
print "overall counts: min", overall_min, "max", overall_max
plot_freq(overall_count_freq, "number of times imported", "frequency", "Package Import Frequency (%s)" % count_type, filename = "results/overall_count_freq_no_path%s.png" % count_type, log_scale = True)


print "found", len(import_counts_overall), "unique packages"
print "   ", self_ref_count, "relative paths"
