#compile all addition commits to a single file

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
import file_utils as utils	

#--- MAIN EXECUTION BEGINS HERE---#	


#flag to determine how to count
#if true, take import exactly as stored, submodules included (SUB)
#if false, only take top package level, strip submodules (TOP)
SUB_MODULE = False	

#module-type specifier
if SUB_MODULE:
	print "Compiling submodule commits"
	module_type = "SUB"
else:
	print "Compiling top-level package commits"
	module_type = "TOP"

#load all commits if have them
all_commits = utils.load_json("datafiles/all_add_commits_%s.json" % module_type)

#don't have a compiled version yet, build it
if all_commits == False:
	#build list of commits, where each commit is a dictionary
	#	user = user id of commiter
	#	repo = repo name (including owner github id for uniqueness)
	#	libs = list of imported libraries (TOP or SUB according to boolean flag), not
	#			including any relative paths ('.')
	#	time = UNIX timestamp of commit
	all_commits = list()

	file_idx = 0
	missing_time_count = 0

	#for each repo commit log file:
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
				#verify that commit has valid timestamp
				if len(commit[1]) == 0:
					missing_time_count = missing_time_count + 1
					continue
				
				#dictionary for new commit, init all fields
				new_commit = {}	
				new_commit["user"] = commit[0]
				new_commit["repo"] = repo
				new_commit["libs"] = list()
				new_commit["time"] = int(commit[1])
			
				#pull packages to add to commit
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
					
					#add package to libs list for this commit if not relative path and not already in list
					if lib[0] != '.' and lib not in new_commit["libs"]:
						new_commit["libs"].append(lib)
					
				#add commit to list of all if import list not empty (possible because throwing out relative paths)
				if len(new_commit["libs"]) != 0:
					all_commits.append(new_commit)

		#period prints
		file_idx = file_idx + 1
		if file_idx % 500 == 0:
			print "finished", file_idx, "repo files"
			
	#save all commits to json (large file incoming)
	utils.save_json(all_commits, "datafiles/all_add_commits_%s.json" % module_type)

	print "results saved to datafiles/all_add_commits_%s.json" % module_type
	
else:
	"read in all commits from datafiles/all_add_commits_%s.json" % module_type

#regardless, print number of total commits
print len(all_commits), "commits total"
print "   ", missing_time_count, "commits without timestamp (not included in compiled list)"
