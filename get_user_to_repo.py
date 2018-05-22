#given imports_data files, build dictionary of user->list of contributing repos (import additions only)

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
import file_utils as utils
	

#--- MAIN EXECUTION BEGINS HERE---#	


#build dictionary of user->list of contributing repos (additions only)

#load dict if have it
user_to_repo = utils.load_json("user_to_repo_list.json")
if user_to_repo == False:
	user_to_repo = defaultdict(set)	

	file_idx = 0

	#for each commit log file:
	for filename in os.listdir('imports_data'):

		#extract repo name
		repo = filename[:-4]

		#read in all commits
		commits = utils.load_json("imports_data/%s" % filename)
		#list of commits, each commit is a list containing user, time, and import dict
		#import dict has keys "+" and "-", leads to list of packages/libraries
		
		#loop all commits
		for commit in commits:		#each commit is user, time, dictionary of imports
			if "+" in commit[2]:	#if additions key
				#add repo to list for committing user
				user_to_repo[commit[0]].add(repo)
				
		#period prints
		file_idx = file_idx + 1
		if file_idx % 500 == 0:
			print "finished", file_idx, "files"
			
	#convert sets to counts, throw out any with only 1 usage (try to narrow the field)
	#also convert the sets to lists, so they can be saved as json
	user_to_repo_list = defaultdict(list)
	for k, v in user_to_repo.items():
		user_to_repo_list[k] = list(user_to_repo[k])
			
	#save list to file
	utils.save_json(user_to_repo_list, "user_to_repo_list.json")

	print "results saved to user_to_repo_list.json"
else:
	"file already exists"
