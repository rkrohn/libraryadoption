from collections import defaultdict
import pickle
import os.path
import glob
import file_utils
import csv

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":

	BIN_SIZE = 6		#bin size in hours

	adoption_count = 0	#number of adoption edges processed

	#distributions: key->frequency
	adopt_delay_dist = defaultdict(int)		#delay->number of adoptions with that delay

	#user counts
	user_adopt_source_count = defaultdict(int)	#user id->number of times adopted from

	#stream each row (adoption edge) individually
	#csv fields: 
	#	0	"repo"
	#	1	"promoter" 
	#	2	"adopter" 
	#	3	"adoption delay (seconds)" 
	#	4	"library" 
	#	5	"promoter commit id" 
	#	6	"adoption commit id"
	#alas, they are all strings, so need to cast the numeric ones
	for adoption in file_utils.stream_csv("data_files/adopt_graph_edges.csv"):
		#count and periodic prints
		adoption_count += 1
		if adoption_count % 50000 == 0:
			print("processed", adoption_count, "adoption edges")

		#build distribution of adoption delays (considering all possible sources)
		#convert delay (seconds) to binned delay (hours)
		delay = int(int(adoption[3]) / (BIN_SIZE * 3600)) * BIN_SIZE
		#add to relevant distribution field
		adopt_delay_dist[delay] += 1

		#count how often each user is adopted from

	#dump data to files
	file_utils.dump_dict_csv(adopt_delay_dist, ["adoption delay (hours)", "frequency"], "results/adopt_graph_analysis/adopt_delay_dist_%shr.csv" % BIN_SIZE)

	print("Processed", adoption_count, "adoption edges")
	print("Results saved to results/adopt_graph_analysis/")
