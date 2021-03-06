#given a library to investigate, plot components over time of that library's commit graph (NOT adoption graph)

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
import networkx as nx
from networkx.algorithms import bipartite
import collections
import matplotlib.pyplot as plt
import file_utils as utils
import data_utils as data
import plot_utils	
import package_type
	
#--- MAIN EXECUTION BEGINS HERE---#	
	
#check for required command line param
if len(sys.argv) != 2:
	print "Must include library to investigate"
	print "Usage: python build_lib_first_commit_graph.py <library>"
	sys.exit(0)
	
#pull library to investigate from command line args
lib = sys.argv[1]
print "Analyzing", lib
	
#set string suffix for submodule mode
suf = package_type.get_type()
	
#read library->repos mapping, extract lists for this library
repos_list = utils.load_json("import_repos_lists_%s.json" % suf)[lib]
print len(repos_list), "repos importing", lib
#read library->users mapping
users_list = utils.load_json("import_users_lists_%s.json" % suf)[lib]
print len(users_list), "users importing", lib

#read user->repos mapping
user_to_repos = utils.load_json("user_to_repo_list.json")

'''
Nope, don't need this - no need to check all repos for a user, just the ones that import lib
#make sure ALL the repos are in repos_list (since some seem to be missing?)
for user in user_to_repos:
	for repo in user_to_repos[user]:
		if repo not in repos_list:
			repos_list.append(repo)
print len(repos_list), "repos importing", lib, "(post check)"
'''

#for each user that has imported this library, find the first commit using lib
user_earliest = {}
user_earliest_repo = {}
earliest_time = -1		#get earliest commit
#do this by looping the repos that we know have imported this lib and tracking earliest commit for each user
file_count = 0
print "Reading repo commits"
for repo in repos_list:
	#read repo file
	repo_commits = utils.load_json("imports_data/%s.log" % repo)
	#loop all commits in this repo
	for commit in repo_commits:		#each commit is user, time, dictionary of imports
		#if additions key and commit contains lib, check if earliest for user
		if "+" in commit[2] and ((SUBMODULE and lib in commit[2]["+"]) or (not SUBMODULE and any(item.startswith(lib) for item in commit[2]["+"]))):
			#check earliest for user
			user = commit[0]			
			#new user, save commit (time as int)
			if user not in user_earliest or int(commit[1]) < user_earliest[user]:
				user_earliest[user] = int(commit[1])
				user_earliest_repo[user] = repo
				#track earliest overall commit
				if int(commit[1]) < earliest_time or earliest_time == -1:
					earliest_time = int(commit[1])
		
	#file_count = file_count + 1
	#if file_count % 500 == 0:
	#	print "finished", file_count, "repos"

print len(user_earliest), "first user commits"		
		
#have all users' first commits of this library, now build the graph through time and get connected components at each step
G = nx.Graph()		#new graph
#add user nodes
for user in users_list:
	G.add_node(user, bipartite = 0)
#add repo nodes
for repo in repos_list:
	G.add_node(repo, bipartite = 0)
	
#store component counts as time-># of components
comp_data = {}
	
#get connected components initially (better be #users + #repos)
comps = sorted(nx.connected_component_subgraphs(G), key = len, reverse=True)
print len(comps), "initial components (no edges)"
comp_data[earliest_time-1] = len(comps)		#add to plot (might not want this)

#first, get time sorted list of commits
commits = data.flip_dict(user_earliest, user_earliest_repo)	#flip the dict
commit_index = 0
#add edges for time, get new # of components
print "processing commits in time-order"
for key in sorted(commits):
	#add all edges for this timestep
	for commit in commits[key]:
		user = commit[0]
		repo = commit[1]
		G.add_edge(user, repo)
	#get components again, add to plot data
	comps = sorted(nx.connected_component_subgraphs(G), key = len, reverse=True)
	comp_data[key] = len(comps)		#add to plot
	
	#commit_index = commit_index + 1
	#if commit_index % 500 == 0:
	#	print "finished", commit_index, "commits"
	
#plot # of components over time
plot_utils.plot_data(comp_data, "Time (UNIX)", "Number of Components", "%s: Number of Components over Time" % lib, filename = "results/%s_time_components.png" % lib, x_max = 0, x_min = 0, log_scale = False)
print "plot saved to results/%s_time_components.png" % lib
	
'''  SLOW WAY
for user_id in users_list:
	user = str(user_id)
	print user
	for repo in user_to_repos[user]:
		print repo
		#read repo file
		repo_commits = utils.load_json("imports_data/%s.log" % repo)
		print len(repo_commits)
		#loop all commits in this repo
		for commit in commits:		#each commit is user, time, dictionary of imports
			if "+" in commit[2]:	#if additions key

		break
	break
'''






