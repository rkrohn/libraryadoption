import glob
import sys
import pandas as pd
import os
import pickle
from collections import defaultdict
from math import ceil
import numpy as np
import file_utils
import plot_utils
from stackoverflow_searcher import Searcher
from datetime import datetime

#given a filepath, load pickled data
def load_pickle(filename):
	with open(filename, "rb") as f:
		data = pickle.load(f)
	return data
#end load_pickle

#given a complete package import, including submodules, strip all the submodules to return only the top-level package
def strip_lib(package):
	tokens = package.split('.')    #split on '.'
	lib = ""
	for token in tokens:
		if token == "":
			lib = lib + "."
		else:
			lib = lib + token
			break
	return lib
#end strip_lib

#given list of libraries, conver to top-level only and remove duplicats
def top_lib(libs):
	res = set()
	for lib in libs:
		short_lib = strip_lib(lib)
		res.add(short_lib)
	return list(res)
#end top_lib

#--- MAIN EXECUTION BEGINS HERE---#

#counters
commit_count = 0
file_count = 0

#declare/initialize a Stackoverflow Searcher
print("Initializing StackOverflow Searcher")
s = Searcher()

#get list of user commit files to process
files = glob.glob('data_files/user_commits/*')
print("\nProcessing", len(files), "user commit files")

#dictionaries: key is top-level library, value is count for that library
adopt_count = defaultdict(int)		#number of adoption commits
added_count = defaultdict(int)		#number of addition commits
delete_count = defaultdict(int)		#number of deletion commits
posts_count = defaultdict(int)		#number of StackOverflow posts
views_count = defaultdict(int)		#number of StackOverflow views

last_commit = -1		#time of last commit across ALL commits (to query SO)

#process each file one at a time
for file in files:
	print("Processing", file)

	user_commits = load_pickle(file)

	#for each user in this chunk, step through their commits
	for user, commits in user_commits.items():

		#loop all commits made by this user
		for c in commits:
			#pull library lists, convert to top-level libraries only, removing duplicates
			added_libs = top_lib(c['add_libs'])
			deleted_libs = top_lib(c['del_libs'])
			adopted_libs = top_lib(c['adopted_libs'])

			time = c['time']	#commit time

			#add to relevant counter
			for lib in added_libs:
				added_count[lib] += 1
			for lib in deleted_libs:
				delete_count[lib] += 1
			for lib in adopted_libs:
				adopt_count[lib] += 1

			if time > last_commit:
				last_commit = time

			commit_count += 1

	file_count += 1
	if file_count % 5 == 0:
		print("finished", commit_count, "commits and", file_count, "files")

print("\nProcessed", commit_count, "commits")
print("   last commit at", datetime.fromtimestamp(last_commit))

#get set of libraries appearing in any of the dictionaries
all_libs = sorted(list(adopt_count.keys()) + list(set(added_count.keys()) - set(adopt_count.keys())))
all_libs = sorted(list(all_libs) + list(set(delete_count.keys()) - set(all_libs)))

print("\nQuerying StackOverflow for", len(all_libs), "libraries")

#datetime of last_commit - end point for all SO searches
end = datetime.fromtimestamp(last_commit)

#query all libs
lib_count = 0
for lib in all_libs:
	#touch counts to make sure all keys/libs represented
	adopt_count[lib] += 0
	added_count[lib] += 0
	delete_count[lib] += 0

	#get the StackOverflow features
	#all posts with this package, ever
	all_posts = s.search(lib, until_date=end)
	posts_count[lib] = len(all_posts)		#total number of posts containing this library
	views_count[lib] = (sum(x[2] for x in all_posts))	#total views of all posts

	lib_count += 1
	if lib_count % 1000 == 0:
		print("finished", lib_count, "libraries")

#save data as csv
file_utils.dump_dict_csv([added_count, delete_count, adopt_count, posts_count, views_count], ["top-level library", "commits adding", "commits deleting", "commits adopting", "StackOverflow posts", "StackOverflow post views"], "results/stackoverflow_analysis/library_counts.csv")
print("Results saved to results/stackoverflow_analysis/library_counts.csv")