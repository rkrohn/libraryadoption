#graph analysis of commit graph (NOT adoption graph) based on raw commit data

import json
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
import networkx as nx
from networkx.algorithms import bipartite
import collections
import matplotlib.pyplot as plt
import unicodedata

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

#computes and plots degree distribution for given node set (assume all nodes if no set given
def deg_dist(graph, title, ylabel, xlabel, filename, node_set = False):	
	#extract distribution
	if node_set == False:
		degree_sequence = graph.degree().values()  # degree sequence
	else:
		degree_sequence = graph.degree(node_set).values()
	degreeCount = collections.Counter(sorted(degree_sequence))
	deg, cnt = zip(*degreeCount.items())

	#plot
	fig, ax = plt.subplots()
	plt.plot(deg, cnt)
	plt.title(title)
	plt.ylabel(ylabel)
	plt.xlabel(xlabel)
	ax.set_xticks([d + 0.4 for d in deg])
	ax.set_xticklabels(deg)
	ax.set_yscale('log')
	ax.set_xscale('log')
	plt.savefig("results/%s.png" % filename)
	plt.clf()
	
	#save as json file
	save_json(degreeCount, "results/%s.json" % filename)
	print "Degree distribution saved to results/%s.json and plotted in results/%s.png" % (filename, filename)
	
#code by Tim, comments by me	
#input: list of bfs successors to start node, start node, traversal level, debug flag
def hops(all_succs, start, level=0, debug=False):
    if debug: print("level:", level)

	#get actual set of successors - neighbors of the start if we have that info, empty list otherwise
    succs = all_succs[start] if start in all_succs else []
    if debug: print("succs:", succs)

	#yield back the current level and the actual number of successors
    lensuccs = len(succs)
    if debug: print("lensuccs:", lensuccs)
    if debug: print()
    if not succs:
        yield level, 0
    else:
        yield level, lensuccs

	#for each actual successor, recursive call with that as start, increase level by 1
    for succ in succs:
        # print("succ:", succ)
        for h in hops(all_succs, succ, level + 1):
			yield h		#yield back h
	
#effective diameter code from Tim, comments by me
#input: graph G (assume networkx), number of test nodes, and percentage factor
def bfs_eff_diam(G, NTestNodes, P):
		#empty graph, return 0
	    if G.number_of_nodes() == 0:
	        return 0
	
		#initialize some variables
	    EffDiam = -1	#effective diameter
	    FullDiam = -1	#full diameter
	    AvgSPL = -1
	
	    DistToCntH = {}	#dictionary of distance in hops to number of nodes
	
	    NodeIdV = nx.nodes(G)	#list of nodes
	    random.shuffle(NodeIdV)	#shuffle node list to get random sample
	
		#pull and process each of the random test nodes
		#keep count of nodes reachable in a cerntain number of hops
	    for tries in range(0, min(NTestNodes, nx.number_of_nodes(G))):
	        NId = NodeIdV[tries]	#id of random node
	        b = nx.bfs_successors(G, NId)	#neighbors of random node
	        for l, h in hops(b, NId):
	            if h is 0: continue
	            if not l + 1 in DistToCntH:
	                DistToCntH[l + 1] = h
	            else:
	                DistToCntH[l + 1] += h
	
	    DistNbrsPdfV = {}
	    SumPathL = 0.0
	    PathCnt = 0.0
	    for i in DistToCntH.keys():
	        DistNbrsPdfV[i] = DistToCntH[i]
	        SumPathL += i * DistToCntH[i]
	        PathCnt += DistToCntH[i]
	
	    oDistNbrsPdfV = collections.OrderedDict(sorted(DistNbrsPdfV.items()))
	
	    CdfV = oDistNbrsPdfV
	    for i in range(1, len(CdfV)):
	        if not i + 1 in CdfV:
	            CdfV[i + 1] = 0
	        CdfV[i + 1] = CdfV[i] + CdfV[i + 1]
	
	    EffPairs = P * CdfV[next(reversed(CdfV))]
	
	    for ValN in CdfV.keys():
	        if CdfV[ValN] > EffPairs: break
	
	    if ValN >= len(CdfV): return next(reversed(CdfV))
	    if ValN is 0: return 1
	    # interpolate
	    DeltaNbrs = CdfV[ValN] - CdfV[ValN - 1];
	    if DeltaNbrs is 0: return ValN;
	    return ValN - 1 + (EffPairs - CdfV[ValN - 1]) / DeltaNbrs	

		
#--- MAIN EXECUTION BEGINS HERE---#	

#read mappings from files
email_to_id = load_json("email_to_userid.json")
name_to_id = load_json("name_to_userid.json")

file_idx = 0

#build bipartite graph, count connected components
print "building graph"
B = nx.Graph()

#add user nodes
for key in email_to_id:
	B.add_node(email_to_id[key], bipartite = 0)		
for key in name_to_id:
	B.add_node(name_to_id[key], bipartite = 0)
		
#add repo nodes and user-repo edges
for filename in os.listdir('commit_data'):
	#add repo node to graph
	B.add_node(filename, bipartite = 1)
	
	for line in io.open("commit_data/%s" % filename, encoding="ISO-8859-1"):
		#commit line
		if line.startswith("#######"):
			#extract commit metadata
			line = line.replace("#######", "")
			commit = [x.strip() for x in line.split(',')]	#email, name, UTC
			#check for diff lines that happen to start with commit flag
			if len(commit) < 3:
				print "BAD COMMIT METADATA"
				continue
			email = commit[0]	#email is first token
			time = commit[-1]	#time is last token
			#name is all the tokens in the middle
			name = ""
			for token in commit[1:-1]:
				name = name + token
			name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore')
		
			#get user_id for this user
			#both name and email empty, skip
			if name == "" and email == "":
				continue
			#have name, pull id
			elif name != "":
				id = name_to_id[name]
			#have email but not name, pull id
			else:
				id = email_to_id[email]
				
			#add edge from repo to user
			B.add_edge(id, filename)

	file_idx = file_idx + 1
	if file_idx % 1000 == 0:
		print "   finished", file_idx, "files"
	
#graph built, get some stats
print "Built graph"

#number of nodes
user_nodes = {n for n, d in B.nodes(data=True) if d['bipartite']==0}
repo_nodes = set(B) - user_nodes
print "   ", len(repo_nodes), "repositories"
print "   ", len(user_nodes), "users"

#connected components
print "connected components"
comps = sorted(nx.connected_component_subgraphs(B), key = len, reverse=True)
print "   ", len(comps), "connected components"
big_comp = comps[0]
user_nodes_big_comp = {n for n, d in big_comp.nodes(data=True) if d['bipartite']==0}
repo_nodes_big_comp = set(big_comp) - user_nodes
print "    largest component contains", len(repo_nodes_big_comp), "repos and", len(user_nodes_big_comp), "users"

#degree distribution - all nodes
deg_dist(B, "Degree Distribution - All Nodes", "Count", "Degree", "overalldegdist")

#degree distribution - user nodes
deg_dist(B, "Degree Distribution - User Nodes", "Count", "Degree", "userdegdist", user_nodes)

#degree distribution - repo nodes
deg_dist(B, "Degree Distribution - Repo Nodes", "Count", "Degree", "repodegdist", repo_nodes)

#hop plot?????





