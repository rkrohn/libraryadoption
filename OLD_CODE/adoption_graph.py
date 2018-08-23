#given adoption events and user/repo list, build adoption graph and plot components over time

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
import networkx as nx
from networkx.algorithms import bipartite
import file_utils as utils
import plot_utils	
import package_type

#--- MAIN EXECUTION BEGINS HERE---#	

#flag to determine adoption definition
#if true, assume user must see library get committed for it to count as an adoption
#	(user is actively "watching" repo when library is committed, but not necessarily 
#	committed for the first time to that repo)
#if false, assume user can adopt from libraries present in the repo when they first
#	start watching - no visible commit required
SIGHT = True

#module-type specifier (at this point, more of a file suffix specifier)
module_type = package_type.get_type()
	
#adoption condition specifier (another suffix)
if SIGHT:
	print "Adoption requires direct commit view"
	adop_type = "SIGHT"
else:
	print "Adoption from repo history allowed"
	adop_type = "HISTORY"

#load adoption events
print "Loading all adoption events..."
adoption_events = utils.load_json("datafiles/adoption_events_%s.json" % (module_type + "_" + adop_type))

#read user->repos mapping (to use as user and repo list)
print "Loading user and repo list..."
user_to_repos = utils.load_json("datafiles/user_to_repo_list.json")

#don't have an adoption event file, yell at the user
if adoption_events == False or user_to_repos == False:
	print "must have compiled adoption event list datafiles/adoption_events_%s.json and user to repo mapping datafiles/user_to_repo_list.json" % (module_type + "_" + adop_type)
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

#sort adoptions by time, not library
events_list = []
	
print "Compiling adoption events list by time..."
for lib in adoption_events:		#library is key of top-level dictionary

	events_list.extend(adoption_events[lib])
	
	#period prints
	lib_idx = lib_idx + 1
	if lib_idx % 1000 == 0:
		print "   finished", lib_idx, "libraries"
		
#sort the adoptions by time
#list of events, each event has ["target"]["time"] - sort by that
events_list.sort(key=lambda i: i["target"]["time"])
'''
#verify sort		
idx = 0
for event in events_list:
	if idx %10000 == 0:
		print event["target"]["time"]
	idx = idx + 1
'''
print len(events_list), "adoption events"				
			
#build initial USER graph (all users, not just users involved in adoptions)
print "Initializing user and repo graphs..."
U = nx.Graph()		#user graph
R = nx.Graph()
#add user nodes
for user in user_to_repos:
	U.add_node(int(user))	#add user node

	#add repo nodes
	for repo in user_to_repos[user]:
		R.add_node(repo)
	
#store component counts as list of component counts and correlated list of times
user_comp_data = []
repo_comp_data = []
times = []

#get # of connected components initially (better be #users and #repos)
user_comps = sorted(nx.connected_component_subgraphs(U), key = len, reverse=True)
print len(user_comps), "initial user components (no edges)"
user_comp_data.append(len(user_comps))
repo_comps = sorted(nx.connected_component_subgraphs(R), key = len, reverse=True)
print len(repo_comps), "initial repo components (no edges)"
repo_comp_data.append(len(repo_comps))
times.append(events_list[0]["target"]["time"]-1)
		
#loop commits through time, add edges, count components
print "Processing adoption events by time..."
adoption_index = 0
for event in events_list:
	time = event["target"]["time"]	#extract time
	
	#add edges to graph between source and target
	for source in event["source"]:
		#user edges
		U.add_edge(event["target"]["user"], source["user"])
		#repo edges
		R.add_edge(event["target"]["repo"], source["repo"])
		
	adoption_index = adoption_index + 1	
		
	#get new component counts periodically
	if adoption_index % 1000 == 0:
		user_comps = sorted(nx.connected_component_subgraphs(U), key=len, reverse=True)
		user_comp_data.append(len(user_comps))
		repo_comps = sorted(nx.connected_component_subgraphs(R), key=len, reverse=True)
		repo_comp_data.append(len(repo_comps))
		times.append(time)
		print "   finished", adoption_index, "events"	

#get final component counts
n = len(events_list)
user_comps = sorted(nx.connected_component_subgraphs(U), key=len, reverse=True)
user_comp_data.append(len(user_comps))
repo_comps = sorted(nx.connected_component_subgraphs(R), key=len, reverse=True)
repo_comp_data.append(len(repo_comps))
times.append(events_list[n-1]["target"]["time"])

#plot number of components over time
plot_utils.plot_data(times, user_comp_data, "Time (UNIX)", "Number of Components in User Graph", "Number of Components in User Graph over Time", filename = "results/time_components_user.png", log_scale = False)
print "user component plot saved to results/time_components_user.png"
plot_utils.plot_data(times, repo_comp_data, "Time (UNIX)", "Number of Components in Repo Graph", "Number of Components in Repo Graph over Time", filename = "results/time_components_repo.png", log_scale = False)
print "repo component plot saved to results/time_components_repo.png"