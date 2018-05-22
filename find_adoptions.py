#searches import data (with first commits as context) for adoption events

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
import data_utils as data


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

#load all commits
print "Loading all import commits..."
all_lib_commits = utils.load_json("datafiles/all_add_commits_%s.json" % module_type)

#load first commits for each user
print "Loading all user/repo first commits..."
first_commits = utils.load_json("datafiles/first_commits.json")

#don't have a compiled commit file, yell at the user
if all_lib_commits == False or first_commits == False:
	print "must have compiled commit list datafiles/all_add_commits_%s.json and user first commits datafiles/first_commits.json" % module_type
	print "exiting"
	sys.exit(0)
	
#compile into a single mega-list, use the lack of a "libs" key to differentiate 
#library imports from first commits
print "Combining commit lists..."
all_commits = all_lib_commits + first_commits

#run through time based on list of commits, where each commit is a dictionary
#	user = user id of commiter
#	repo = repo name (including owner github id for uniqueness)
#	libs = list of imported libraries (TOP or SUB according to boolean flag), not
#			including any relative paths ('.')
#	time = UNIX timestamp of commit

#looking for adoptions defined in the following way
#user uses library for the first time in ANY repo
#	if SIGHT = true, user "sees" commit of library in a repo before they use it
#	if SIGHT = false, user doesn't need to see a commit, library can be preexisting
#		in the repository

#create a list of adoption events, each with the following information
#	origin user = user committing the library that is adopted
#	origin repo = repo the adopted library was committed to
#	origin time = time of origin commit
#	library = library being adopted
#	adopting user = user adopting library from origin user/repo
#	adopting repo = repository committed to by adopting user
#	adoption time = time of adoption commit
#additionally, anything in "origin" may be a list - a user can adopt from 
#		multiple sources simultaneously
#adoption info will be singular, since it is triggered by a single commit
#store in this manner (oh god, what have I done...)
#	dictionary, where library is key
#	for each library, value is list of adoption events
#	each adoption event is a dictionary with keys "source" and "target"
#	source maps to list of source commits, each a dictionary with user, repo, time
#	target maps to a single dictionary with user, repo, time 
adoption_events = defaultdict(list)

#data structures for this big job

#index of processed commits (for periodic prints)
commit_idx = 0
#count of unique adoption events/commits (could have multiple sources)
adoption_count = 0
#for each user, set of libraries they have used; used for simple "is this new?" check
user_quiver = defaultdict(set)	
#for each repo, dict of libraries in repo (key) -> most recent commit info (value)
#commit info is also a dictionary (inception) containing user and time
#overall structure repo->lib->user/time (3 nested dictionaries)
#used to pull most recent commit for a library to check for adoption
repo_imports = defaultdict(lambda: defaultdict(dict))
#for each repo, set of users that are "watching" (users that have committed to repo),
#and time that user "subscribed" (made their first commit)	
#user stored as dictionary, so overall structure is repo->user->time
repo_users = defaultdict(dict)		
#for each user, set of repos they have committed to
user_repos = defaultdict(set)		

print "Looping commits in time order..."
for commit in sorted(all_commits, key=lambda d: d["time"]):		#sorted by time
		#grab some fields for ease of reading and usage
		user, repo, time = data.unfold_dict(commit)

		#user first commit, no imports
		if "libs" not in commit:
			#add user to repo user list, tracking time user first "joined"
			if user not in repo_users[repo]:
				repo_users[repo][user] = time
			#add repo to user repo list
			user_repos[user].add(repo)
			#no adoption check, just adding user-repo relation
		
		#library commit
		else:
			#process each library, one at a time
			for lib in commit["libs"]:
				#if user has committed this library before, no adoption, skip
				if lib in user_quiver[user]:
					continue
				
				#if reach this point, user has not committed this library before
				#potentially have an adoption event, if we can find the "source/origin"
				#two cases:
				
				#user must see commit containing lib
				#we also make an assumption here: if there have been multiple
				#	commits of the lib to the same repo, give credit for the adoption
				#	to the most recent commit only (also simplifies analysis, maybe
				#	change later)
				if SIGHT == True:		
					#new adoption event, init "source" field as empty list
					adopt = dict()
					adopt["source"] = list()	
					
					#check all potential source repos user is subscribed to
					#if most recent lib commit to repo is after user subscribed, 
					#log as an adoption event
					for r in user_repos[user]:
						#if repo has library and most recent commit of lib was after
						#user subscribed, adoption!
						if lib in repo_imports[r] and repo_imports[r][lib]["time"] > repo_users[r][user]:
							#save the adoption! add repo commit to source list
							adopt["source"].append(data.build_dict(repo_imports[r][lib]["user"], r, repo_imports[r][lib]["time"]))
							
					#if adoption has valid sources, set up "target" and save
					if len(adopt["source"]) != 0:
						#set up target data
						adopt["target"] = data.build_dict(user, repo, time)
						#save adoption event to list
						adoption_events[lib].append(adopt)
						adoption_count =  adoption_count + 1
						
					#adoption are not, update the data structures to reflect commit
					user_quiver[user].add(lib)	#user has used lib, add to quiver
					#update most recent commit of this lib in repo
					repo_imports[repo][lib]["user"] = user
					repo_imports[repo][lib]["time"] = time
					#add user to repo user list, tracking time user first "joined"
					if user not in repo_users[repo]:
						repo_users[repo][user] = time
					user_repos[user].add(repo)	#add repo to user's list
				
				#user can adopt from repo contents without "seeing" a commit
				else:	
					print "adoption without visible commit not currently supported"
					print "exiting"
					sys.exit(0)
		
		#period prints
		commit_idx = commit_idx + 1
		if commit_idx % 2500 == 0:
			print "   finished", commit_idx, "commits, found", adoption_count, "adoption events"
			
		#short-circuit for proof of concept: stop when have ~5 adoptions so we can
		#verify the output
		#if adoption_count >= 5:
		#	break
			
#save all adoption events to json (large file incoming, hope it has everything we need)
utils.save_json(adoption_events, "datafiles/adoption_events_%s.json" % (module_type + "_" + adop_type))
print "results saved to datafiles/adoption_events_%s.json" % (module_type + "_" + adop_type)

#regardless, print number of adoptions found
print adoption_count, "adoption events found in", len(all_lib_commits), "import commits"
