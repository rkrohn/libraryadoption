#compile all commits to a single file, including library additions and deletions, and commits with no import changes

import os.path
import subprocess
import sys
import urllib2
import io
from collections import defaultdict
import unicodedata
from collections import OrderedDict
from operator import itemgetter
import file_utils as utils	
import package_type

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


#--- MAIN EXECUTION BEGINS HERE---#

#how to count: top-level vs submodules
module_type = package_type.get_type()

#load all commits if have them
all_commits = utils.load_json("data_files/all_commits_%s.json" % module_type)

#don't have a compiled version yet, build it
if all_commits == False:
	#build list of commits, where each commit is a dictionary
	#	user = user id of commiter
	#	repo = repo name (including owner github id for uniqueness)
	#	add_libs = list of added imported libraries (TOP or SUB according to boolean flag), not
	#			including any relative paths ('.')
	#	del_libs = list of deleted imported libraries (same conditions as above
	#	time = UNIX timestamp of commit
	#
	all_commits = list()

	file_idx = 0
	missing_time_count = 0

	#for each repo log file:
	for filename in os.listdir('parsed_commit_data'):

		#extract repo name
		repo = filename[:-4]

		#read in all commits
		commits = utils.load_json("parsed_commit_data/%s" % filename)
		#list of commits, each commit is a list containing user, time, and import dict
		#import dict has keys "+" and "-", leads to list of packages/libraries

		#loop all commits
		for commit in commits:		#each commit is user, time, dictionary of imports

			#verify that commit has valid timestamp
			if len(commit[1]) == 0:
				missing_time_count = missing_time_count + 1
				continue

			#dictionary for new commit, init all fields
			new_commit = {}	
			new_commit["user"] = commit[0]
			new_commit["repo"] = repo
			new_commit["add_libs"] = list()
			new_commit["del_libs"] = list()
			new_commit["time"] = int(commit[1])

			if "+" in commit[2]:	#if additions key		
				#pull packages to include in additions of commit
				for package in commit[2]["+"]:
					#counting with submodules, take package name as-is
					if module_type == "SUB":
						lib = package						
					#not counting with submodules, get parent package only
					else:
						lib = strip_lib(package)
					
					#add package to libs list for this commit if not relative path and not already in list
					if lib[0] != '.' and lib not in new_commit["add_libs"]:
						new_commit["add_libs"].append(lib)

			if "-" in commit[2]:	#if deletions key
				#pull packages to include in deletions of commit
				for package in commit[2]["-"]:
					#counting with submodules, take package name as-is
					if module_type == "SUB":
						lib = package						
					#not counting with submodules, get parent package only
					else:
						lib = strip_lib(package)
					
					#add package to libs list for this commit if not relative path and not already in list
					if lib[0] != '.' and lib not in new_commit["del_libs"]:
						new_commit["del_libs"].append(lib)

					
			#add commit to list of all (may have empty import list)
			all_commits.append(new_commit)

		#period prints
		file_idx = file_idx + 1
		if file_idx % 1000 == 0:
			print "finished", file_idx, "repo files"
			
	#save all commits to json (large file incoming)
	utils.save_json(all_commits, "data_files/all_commits_%s.json" % module_type)

	print "results saved to data_files/all_commits_%s.json" % module_type
	print "   ", missing_time_count, "commits without timestamp (not included in compiled list)"
	
else:
	"read in all commits from data_files/all_commits_%s.json" % module_type

#regardless, print number of total commits
print len(all_commits), "commits total"

