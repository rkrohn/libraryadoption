#given unsorted list of commits all_commits_<package type>.json, sort the events by time
#also chunk the commits by year, creating separate output files for each

import json
import datetime
import package_type
import file_utils as utils
import os.path

#given sorted data, write the data to a file
def write_sorted_to_file(data, filename):
	with open(filename, 'w') as f:
    		f.write(str(data))
#end write_sorted_to_file

#--- MAIN EXECUTION BEGINS HERE---#	

#which files to sort: top-level vs submodules
module_type = package_type.get_type()

#read in the data
data = utils.load_json('data_files/all_commits_%s_small.json' % module_type)
if data == False:
	print "commits file does not exist, exiting"
	exit(0)

#sort events by time
ordered_commits = sorted(data, key=lambda k: k['time'])

#save to a single mega-file
write_sorted_to_file(ordered_commits, "data_files/all_commits_%s_sorted.json" % module_type)

print len(ordered_commits), "sorted commits saved to data_files/all_commits_%s_sorted.json" % module_type

#split entire list by year, use dictionary with years as keys to store
year_commits = dict()

#create directory for commits by year files (if doesn't already exist)
if os.path.isdir("data_files/all_commits_by_year") == False:
	os.makedirs("data_files/all_commits_by_year")

#get first and last year occurring in data
first_year = datetime.datetime.fromtimestamp(ordered_commits[0]['time']).year
last_year = datetime.datetime.fromtimestamp(ordered_commits[-1]['time']).year

#split list of commits by year, save each year to a separate file
for year in range(first_year, last_year+1):
	#get this year's commits
	year_commits[year] = [commit for commit in ordered_commits if datetime.datetime.fromtimestamp(commit['time']).year == year]

	#save commits to file
	write_sorted_to_file(year_commits[year], 'data_files/all_commits_by_year/%s_commits_%s_sorted.json' % (year, module_type))

	print "   ", year, ":", len(year_commits[year]), "commits"

print "year-divided commits saved to data_files/all_commits_by_year/<year>_commits_%s_sorted.json"  % module_type
