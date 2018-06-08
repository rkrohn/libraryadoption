#computes and plots user and repo commit frequencies given parsed commit data

import os.path
import subprocess
import sys
import urllib2
import io
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt
import numpy as np
import unicodedata
import file_utils as utils
import plot_utils
import package_type

#--- MAIN EXECUTION BEGINS HERE---#	

#how to count: top-level vs submodules
module_type = package_type.get_type()

#read mappings from files
email_to_id = utils.load_json("email_to_userid.json")
name_to_id = utils.load_json("name_to_userid.json")

user_all_commit_counts = utils.load_json("data_files/user_all_commit_counts.json")
if user_all_commit_counts == False:
	user_all_commit_counts = defaultdict(int)
repo_all_commit_counts = utils.load_json("data_files/repo_all_commit_counts.json")
if repo_all_commit_counts == False:
	repo_all_commit_counts = defaultdict(int)

if len(repo_commit_counts) == 0 or len(user_commit_counts) == 0:
	print "computing commit counts"

	#read in all commits
	commits = utils.load_json("data_files/all_commits_%s_small.json" % module_type)
	if commits == False:
		print "need compiled commits file data_files/all_commits_%s.json, exiting" % module_type
		exit(0)

	#process each commit
	for commit in commits:
		user_all_commit_counts[commit[user]] += 1
		repo_all_commit_counts[commit[repo]] += 1
			
	print "COMPLETE"

	#save results	
	utils.save_json(user_commit_counts, "data_files/user_all_commit_counts.json")
	utils.save_json(repo_commit_counts, "data_files/repo_all_commit_counts.json")
	print "final commit_counts saved to data_files/user_all_commit_counts.json and data_files/repo_all_commit_counts.json"
else:
	print "commit counts already computed, plotting frequencies"
	
	#user commit plots
	user_all_commit_freq, min_user_commit, max_user_commit = plot_utils.count_freq(user_all_commit_counts)
	plot_utils.plot_freq(user_commit_freq, "user commit count", "freq", filename = "plots/user_all_commit_freq.jpg")
	print "user all commit counts: min =", min_user_commit, ", max =", max_user_commit
	
	#repo commit plots
	repo_all_commit_freq, min_repo_commit, max_repo_commit = plot_utils.count_freq(repo_all_commit_counts)
	plot_utils.plot_freq(repo_all_commit_freq, "repo commit count", "freq", filename = "plots/repo_all_commit_freq.jpg")
	print "repo all commit counts: min =", min_repo_commit, ", max =", max_repo_commit
	
	print "plots saved to plots/user_all_commit_freq.jpg and plots/repo_all_commit_freq.jpg"
	


