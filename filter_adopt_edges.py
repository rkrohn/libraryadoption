from collections import defaultdict
import pickle
import os.path
import glob
import file_utils
import csv
import data_utils
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":

	LIB = "tensorflow"		#library filter - only include adoptions where library starts with tensorflow

	adoption_count = 0	#number of adoption edges processed

	filtered_edges = []		#list of filtered edges

	#stream each row (adoption edge) individually
	#csv fields: 
	#	0	"repo"
	#	1	"promoter" 
	#	2	"adopter" 
	#	3	"adoption delay (seconds)" 
	#	4	"library" 
	#	5	"promoter commit id" 
	#	6	"adoption commit id"
	#	7	"promoter commit time (UTC)"
	#	8	"adoption commit time (UTC)"
	#alas, they are all strings, so need to cast the numeric ones
	for adoption in file_utils.stream_csv("data_files/adopt_graph_edges.csv"):
		#count and periodic prints
		adoption_count += 1
		if adoption_count % 50000 == 0:
			print("processed", adoption_count, "adoption edges")
			#break

		#if adopted lib matches filter, add to list
		if adoption[4].startswith(LIB):
			filtered_edges.append(adoption)

	#dump data to file
	file_utils.dump_list(filtered_edges, ["repo", "promoter", "adopter", "adoption delay (seconds)", "library", "promoter commit id", "adoption commit id", "promoter commit time (UTC)", "adoption commit time (UTC)"], "data_files/filtered_adopt_graph/%s_adopt_edges.csv" % LIB)

	print("\nProcessed", adoption_count, "adoption edges")
	print("   found", len(filtered_edges), "edges for", LIB)
	print("Results saved to data_files/filtered_adopt_graph/")
