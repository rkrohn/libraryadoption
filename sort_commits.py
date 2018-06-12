#given unsorted list of commits all_commits_<package type>.json, sort the events by time
#also chunk the commits by year, creating separate output files for each

import json
from datetime import datetime, timedelta
import package_type
import file_utils as utils
import os.path
from collections import defaultdict

#given sorted data, write the data to a file
def write_sorted_to_file(data, filename):
	with open(filename, 'w') as f:
    		f.write(str(data))
#end write_sorted_to_file

#--- MAIN EXECUTION BEGINS HERE---#	

#which files to sort: top-level vs submodules
module_type = package_type.get_type()

#read in the data
print "reading in commit data..."
data = utils.load_json('data_files/all_commits_%s.json' % module_type)
if data == False:
	print "commits file does not exist, exiting"
	exit(0)
print "read in", len(data), "commits"

#sort events by time
print "sorting commits..."
ordered_commits = sorted(data, key=lambda k: k['time'])

#save to a single mega-file
print "saving sorted commits..."
write_sorted_to_file(ordered_commits, "data_files/all_commits_%s_sorted.json" % module_type)
print len(ordered_commits), "sorted commits saved to data_files/all_commits_%s_sorted.json" % module_type

#create directory for commits by year files (if doesn't already exist)
if os.path.isdir("data_files/all_commits_by_year") == False:
	os.makedirs("data_files/all_commits_by_year")

#get first year occurring in data
first_year = datetime.fromtimestamp(ordered_commits[0]['time']).year
print "earliest commit in", first_year

#get last year occuring in data - trickier, because there are some rogue overflows
last_year = -1
last_idx = -1
while last_year == -1:
	try:
		date = datetime(1970, 1, 1) + timedelta(ordered_commits[last_idx]['time'])
		last_year = date.year
	except:
		#move index back
		last_idx -= 1
print "latest commit in", last_year

#split entire list by year, use dictionary with years as keys to store
year_commits = defaultdict(list)

#split list of commits by year
for commit in ordered_commits:
	try:
		year = datetime.fromtimestamp(commit['time']).year
	except:
		year = "overflow"
	year_commits[year].append(commit)
	
#save each year to a separate file
for year in year_commits:
	print "   ", year, ":", len(year_commits[year]), "commits"
	#save commits to file if list not empty
	if len(year_commits[year]) != 0:
		write_sorted_to_file(year_commits[year], 'data_files/all_commits_by_year/%s_commits_%s_sorted.json' % (year, module_type))

print "year-divided commits saved to data_files/all_commits_by_year/<year>_commits_%s_sorted.json"  % module_type
