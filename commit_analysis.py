import json
import os.path
from collections import defaultdict
import numpy as np

#stream json data one object at a time (generator function)
def stream(f):
	obj_str = ''
	f.read(1) 	#eat first [
	while True:
		c = f.read(1)	#read one character at a time
		#end of file, quit
		if not c:
			#print('EOF')
			break
		#skip newline characters
		if c == '\n':
			continue
		#remove backslashes
		if c == '\'':
			c = '"'
		obj_str = obj_str + c	#add character to current object string
		#when reach end of object, parse json and return resulting object
		if c == '}':
			obj_str = obj_str.replace('u"', '"')	#remove all unicode prefixes
			yield json.loads(obj_str)		#return json object
			obj_str = ''	#clear for next read
			c = f.read(1) 	#eat comma between objects
#end stream

#--- MAIN EXECUTION BEGINS HERE---#

if __name__ == "__main__":

	output = []		#list of lists for all output
	
	overall_count = 0
	year_count = 0

	import_commit_count = 0
	year_import_commit_count = 0

	addition_commit_count = 0
	year_addition_commit_count = 0

	deletion_commit_count = 0
	year_deletion_commit_count = 0

	additions_count = 0
	year_additions_count = 0

	deletions_count = 0
	year_deletions_count = 0

	all_users = set([])
	year_users = set([])

	repo_adopt = 0
	year_repo_adopt = 0

	#tracking library usage
	quiver = defaultdict(set)		#dictionary of user -> list of packages used
	contents = defaultdict(dict)		#nested dictionary of repo -> package -> time
	last_interaction = defaultdict(lambda:-1)	#dictionary of "<userid>--<reponame>" to time of last interaction

	#add headers to output data
	headers = ["year", "commit_count", "import_commit_count", "num_users", "intra-repo_adopts", "addition_commits", "libraries_added", "deletion_commits", "libraries_deleted"]
	output.append(headers)

	#stream data from sorted json files
	for year in range(1990, 2018):		#read and process 1990 through 2018

		#reset counters/sets for this year
		year_count = 0
		year_import_commit_count = 0
		year_repo_adopt = 0
		year_users = set([])

		#stream from current year's output file
		f = open('data_files/all_commits_by_year/%s_commits_SUB_sorted.json' % year)
		commits = stream(f)

		#process all commits in date order
		for c in commits:
			#grab commit fields: user, repo, time, added_libs, and deleted_libs
			repo = c['repo']
			time = int(c['time'])
			if c['user'] == '':
				user = 0
			else:
				user = int(c['user'])

			#remove duplicate libraries from lists by converting them to sets
			added_libs = set(c['add_libs'])
			deleted_libs = set(c['del_libs'])

			#change added/deleted_libs so that "moved libs" i.e., libs that are added and deleted in the same commit are not considered for adoptions
			added_and_deleted = added_libs.intersection(deleted_libs)
			deleted_libs = [item for item in deleted_libs if item not in added_and_deleted]
			added_libs = [item for item in added_libs if item not in added_and_deleted]

			#updated_libs are those libraries that were implicitly viewed by the user via a pull (immediately) before a commit
			inter_key = str(user)+"--"+repo
			updated_libs = [lib for lib in contents[repo] if contents[repo][lib] > last_interaction[inter_key]]

			#adoption?
			for lib in added_libs:
				#if an added lib is in updated_lib but not in the user's quiver, then it must be an adoption
				if lib in updated_libs and lib not in quiver[user]:
					#found an adoption! update counts
					year_repo_adopt += 1
					repo_adopt += 1


			#if added a library, count as import commit
			if len(added_libs) != 0:
				import_commit_count += 1
				year_import_commit_count += 1

			#add user to sets
			all_users.add(user)
			year_users.add(user)

			#update counts
			year_count += 1
			overall_count += 1

			#commit contains addition?
			if len(added_libs) != 0:
				year_addition_commit_count += 1
				addition_commit_count += 1
				year_additions_count += len(added_libs)
				additions_count += len(added_libs)
			#commit contains deletion?
			if len(deleted_libs) != 0:
				year_deletion_commit_count += 1
				deletion_commit_count += 1
				year_deletions_count += len(deleted_libs)
				deletions_count += len(deleted_libs)

			#update tracking data
			quiver[user].update(added_libs)
			for lib in added_libs:
				contents[repo][lib] = time
			last_interaction[inter_key] = time


		row = [year, year_count, year_import_commit_count, len(year_users), year_repo_adopt, year_addition_commit_count, year_additions_count, year_deletion_commit_count, year_deletions_count]
		output.append(row)

		f.close()

	#add total to bottom
	row = ["total", overall_count, import_commit_count, len(all_users), repo_adopt, addition_commit_count, additions_count, deletion_commit_count, deletions_count]

	#save data to csv
	np.savetxt("results/commit_analysis_by_year.csv", np.array(output), delimiter=",", fmt="%s")
