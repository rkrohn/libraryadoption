#following repo cloning and raw commit data extraction, check to see which cloned repos are missing commit data files, and vice versa

import os.path
import file_utils as utils

#--- MAIN EXECUTION BEGINS HERE---#	
	
#check if all repo clones have corresponding commit data file
for filename in os.listdir("repo_clones"):		
	#extract commit data if commit log file doesn't exist
	if os.path.isfile("commit_data/%s_commits.log" % filename) == False:
		print "no commit data for", filename

		#pull all commit data, and commit contents starting with "import" or "from"
		os.chdir("repo_clones")
		utils.run_bash('''git show --format="#######%%aE, %%aN, %%at" --unified=0 $(git rev-list --all) | awk '/^#####/ || /\-[[:blank:]]*import/ || /\+[[:blank:]]*import/  || /\-[[:blank:]]*from/ || /\+[[:blank:]]*from/'  > ../commit_data/%s_commits.log''' % filename , True)
		os.chdir("..")
		
#check if all commit data files have corresponding repo
for filename in os.listdir("commit_data"):
	#strip the "_commits.log" off the end
	repo_name = filename[:-12]

	#have cloned repo?
	if os.path.isdir("repo_clones/%s" % repo_name) == False:
		print "no repo for", repo_name


#final print
print "Done"