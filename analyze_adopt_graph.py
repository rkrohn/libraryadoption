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

	BIN_SIZE = 3		#bin size in hours

	adoption_count = 0	#number of adoption edges processed

	#distributions: key->frequency
	adopt_delay_dist = defaultdict(int)		#delay->number of adoptions with that delay

	#user counts
	user_adopt_source_count = defaultdict(int)	#user id->number of times adopted from
	user_adopt_sink_count = defaultdict(int)	#user id->number of incoming edges (ie, promoter-library pairs)
	user_adopt_repos = defaultdict(set)			#user id->set of repos user adopts in
	user_promote_repos = defaultdict(set)		#user id->set of repos user adopted from in

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
			#break

		#build distribution of adoption delays (considering all possible sources)
		#convert delay (seconds) to binned delay (hours)
		delay = int(int(adoption[3]) / (BIN_SIZE * 3600)) * BIN_SIZE
		#add to relevant distribution field
		adopt_delay_dist[delay] += 1

		#count how often each user is adopted from
		user_adopt_source_count[int(adoption[1])] += 1
		#and how often each user adopts (promoter-lib pairs, not unique libraries)
		user_adopt_sink_count[int(adoption[2])] += 1

		#adoption repos
		user_adopt_repos[int(adoption[2])].add(adoption[0])
		user_promote_repos[int(adoption[1])].add(adoption[0])

	#convert user adopted-from counts to distribution of # of times adopted from -> frequency
	adopt_from_dist = data_utils.dict_to_dist(user_adopt_source_count)
	#and same for adopters
	adopter_dist = data_utils.dict_to_dist(user_adopt_sink_count)

	#sample 1000 users to plot # of incoming edges vs # outgoing edges
	#first, build list of users in either promoter or adopter sets
	users = sorted(list(user_adopt_source_count.keys()) + list(set(user_adopt_sink_count.keys()) - set(user_adopt_source_count.keys())))
	#get list of users with indegree (sink) or outdegree (source) greater than 100
	subset_users = [user for user in users if user_adopt_source_count[user] >= 100 or user_adopt_sink_count[user] >= 100]
	print("Found", len(subset_users), "users with in or out degree >= 100 from", len(users))
	#build dictionaries for just the subset users
	subset_user_adopt_source_count = {}
	subset_user_adopt_sink_count = {}
	for user in subset_users:
		subset_user_adopt_source_count[user] = user_adopt_source_count[user]
		subset_user_adopt_sink_count[user] = user_adopt_sink_count[user]
	#plot (just for kicks)
	plt.clf()
	fig, ax = plt.subplots()
	user, source_count = zip(*sorted(subset_user_adopt_source_count.items()))
	user_2, sink_count = zip(*sorted(subset_user_adopt_sink_count.items()))
	ax.scatter(source_count, sink_count)
	plt.xlabel("outdegree (times adopted from)")
	plt.ylabel("indegree (lib-source pairs when adopting)")
	plt.savefig("results/adopt_graph_analysis/subset_user_edge_counts.png", bbox_inches='tight')

	#convert repo sets to counts
	for user in user_adopt_repos.keys():
		user_adopt_repos[user] = len(user_adopt_repos[user])
	for user in user_promote_repos.keys():
		user_promote_repos[user] = len(user_promote_repos[user])
	#and flip to distribution
	user_adopt_repos_dist = data_utils.dict_to_dist(user_adopt_repos)
	user_promote_repos_dist = data_utils.dict_to_dist(user_promote_repos)

	#dump data to files
	if adoption_count > 60000:		#don't accidentally overwrite with small tests
		file_utils.dump_dict_csv(adopt_delay_dist, ["adoption delay (hours)", "frequency"], "results/adopt_graph_analysis/adopt_delay_dist_%shr.csv" % BIN_SIZE)
		file_utils.dump_dict_csv(adopt_from_dist, ["number of times user adopted from", "number of users"], "results/adopt_graph_analysis/user_adopted_from_dist.csv")	
		file_utils.dump_dict_csv(adopter_dist, ["number of incoming adoption edges (lib-source adoption pairs)", "number of users"], "results/adopt_graph_analysis/user_adopting_edge_dist.csv")	
		file_utils.dump_dict_csv(user_adopt_repos, ["number of unique repos user made adoption commit in (adopter)", "number of users"], "results/adopt_graph_analysis/user_repos_adopted_from.csv")
		file_utils.dump_dict_csv(user_promote_repos, ["number of unique repos user adopted from in (promoter)", "number of users"], "results/adopt_graph_analysis/user_repos_promoted_in.csv")
		file_utils.dump_dict_csv([subset_user_adopt_source_count, subset_user_adopt_sink_count], ["user id", "number of times user adopted from", "number of incoming adoption edges (lib-source pairs)"], "results/adopt_graph_analysis/subset_user_edge_counts.csv")

	print("Processed", adoption_count, "adoption edges")
	print("Results saved to results/adopt_graph_analysis/")
