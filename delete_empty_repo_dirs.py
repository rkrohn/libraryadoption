#crawls the repo_clones directory and deletes all empty directories
#should be run after data_shrink.py

#well, I ran it, and it didn't find anything to delete - so don't bother

import os
import shutil

#--- MAIN EXECUTION BEGINS HERE---#

dir_idx = 0
delete_count = 0

while True:
	to_delete = []	#list of directories to delete

	#crawl the file tree
	for root, dirs, _ in os.walk("repo_clones"):
		#skip the hidden directories
		dirs[:] = [d for d in dirs if not d[0] == '.']

		dir_idx += 1
		if dir_idx % 5000 == 0:
			print "\nfinished", dir_idx, "  deleted", delete_count, "empty directories"

		#identify empty directories to delete
		for d in dirs:
			path = os.path.join(root, d)
			if not os.listdir(path):
				to_delete.append(path)

	#delete directories previously flagged
	if to_delete:
		for d in to_delete:
			#print "deleting", d
			os.rmdir(d)
			delete_count += 1
	#no more to delete, stop
	else:
		break
		
print "\nfinished", dir_idx, "  deleted", delete_count, "empty directories"