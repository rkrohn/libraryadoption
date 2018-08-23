#build dynamic adoption graph (perhaps for a particular library) and save as gexf file

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
import networkx as nx
from networkx.algorithms import bipartite
from lxml import etree
import gexfbuilder as gexf
import datetime
import file_utils as utils
import data_utils as data
import package_type

#--- MAIN EXECUTION BEGINS HERE---#	

#flag to determine adoption definition
#if true, assume user must see library get committed for it to count as an adoption
#	(user is actively "watching" repo when library is committed, but not necessarily 
#	committed for the first time to that repo)
#if false, assume user can adopt from libraries present in the repo when they first
#	start watching - no visible commit required
SIGHT = True

#minimum component size for inclusion in animation
MIN_SIZE = 10

#command line args: 1 optional argument specifies the library to visualize
#if no argument, do the whole graph (slow and large)
if len(sys.argv) > 2:
	print "No more than 1 command line argument allowed."
	print "Usage: adoption_graph_viz.py <optional library>"
	print "exiting"
	sys.exit(0)
elif len(sys.argv) == 2:
	FILTER = True
	LIB = sys.argv[1]
	print "Limiting visualization to", LIB
else:
	print "Visualizing all libraries"
	FILTER = False
	LIB = "ALL"		#for later file names

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
#no library filter, grab all events
if FILTER == False:
	print "   looping libraries..."
	for lib in adoption_events:		#library is key of top-level dictionary
	
		#exclude relative paths (start with '.')
		if lib[0] == '.':
			continue

		events_list.extend(adoption_events[lib])
		
		#period prints
		lib_idx = lib_idx + 1
		if lib_idx % 1000 == 0:
			print "   finished", lib_idx, "libraries"
#have library filter, just grab those events
else:
	print "   pulling events for", LIB
	events_list = adoption_events[LIB]
		
#sort the adoptions by time
#list of events, each event has ["target"]["time"] - sort by that
events_list.sort(key=lambda i: i["target"]["time"])
print len(events_list), "adoption events"				
			
#build initial user graph (all users, not just users involved in adoptions)
print "Initializing user and repo graphs..."
U = nx.Graph()		#user graph
R = nx.Graph()		#repo graph
#add user nodes
for user in user_to_repos:
	U.add_node(int(user))	#add user node

	#add repo nodes
	for repo in user_to_repos[user]:
		R.add_node(repo)

#loop commits through time, add edges
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
		
	#progress prints
	if adoption_index % 1000 == 0:
		print "   finished", adoption_index, "events"	

#get final component counts
print "Getting final graph components..."
n = len(events_list)
user_comps = sorted(nx.connected_component_subgraphs(U), key=len, reverse=True)
repo_comps = sorted(nx.connected_component_subgraphs(R), key=len, reverse=True)

#get list of users and repos involved in components smaller than threshold
print "Locating nodes in small components..."
exclude_users = set()
exclude_repos = set()
for c in user_comps:
	if len(c) < MIN_SIZE:
		exclude_users.update(list(c))
for c in repo_comps:
	if len(c) < MIN_SIZE:
		exclude_repos.update(list(c))
				
#build GEXF file of graph, only include nodes in larger components
#also, timestamp all the edges so we can watch the graph grow!
print "Generating GEFX files..."
#init gefx graph builders
UG = gexf.Graph(directed=True)
RG = gexf.Graph(directed=True)
#loop events
adoption_index = 0
for event in events_list:
	#extract time, convert to date string
	time_raw = event["target"]["time"]	
	time = datetime.datetime.fromtimestamp(time_raw).strftime('%Y-%m-%d')
	
	#loop all sources for this adoption
	for source in event["source"]:
	
		#valid user edge?
		target_user = event["target"]["user"]
		source_user = source["user"]
		if target_user not in exclude_users and source_user not in exclude_users:
			#add users and edge to graph
			UG.add_node(str(source_user))
			UG.add_node(str(target_user))
			UG.add_edge(str(source_user), str(target_user), start=time)
		
		#valid repo edge?
		target_repo = event["target"]["repo"]
		source_repo = source["repo"]
		if target_repo not in exclude_repos and source_repo not in exclude_repos and target_repo != source_repo:
			#add repos and edge to graph
			RG.add_node(str(source_repo))
			RG.add_node(str(target_repo))
			RG.add_edge(str(source_repo), str(target_repo), start=time)
			
	adoption_index = adoption_index + 1	
		
	#progress prints
	if adoption_index % 1000 == 0:
		print "   finished", adoption_index, "events"	

#save gexf file
print "Saving gexf files..."
with open("graphs/%s_user_adopt_graph.gexf" % LIB, "w") as text_file:
    text_file.write(UG.gexf().getvalue())
with open("graphs/%s_repo_adopt_graph.gexf" % LIB, "w") as text_file:
    text_file.write(RG.gexf().getvalue())
print "GEXF files saved to graphs/%s_user_adopt_graph.gexf and graphs/%s_repo_adopt_graph.gexf" % (LIB, LIB)

