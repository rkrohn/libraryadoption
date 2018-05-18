import json
import os.path
import subprocess
import sys

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
	
#run bash command
def run_bash(command, shell=False):
	if shell:
		process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	else:
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
	output, error = process.communicate()

#--- MAIN EXECUTION BEGINS HERE---#	
	
#check for required command line param
if len(sys.argv) != 3:
	print "Must include starting index and # to process for repo cloning process."
	print "Usage: python scrape_imports.py <starting index> <# to process>"
	sys.exit(0)

#read list of repos to clone and scrape
repos = load_json("all_repos.json")
print "Read", len(repos['items']), "repos"

#grab and save current working directory
dir = os.getcwd()

#create directory for repo clones (if doesn't already exist)
if os.path.isdir("repo_clones") == False:
	os.makedirs("repo_clones")
#create directory for commit data (if doesn't already exist)
if os.path.isdir("commit_data") == False:
	os.makedirs("commit_data")

#for each repo:
idx = int(sys.argv[1])		#starting index from command line parameter
limit = int(sys.argv[2])			#for now, do 50 at a time starting from given index
for i in range(idx, idx+limit):
#for r in repos['items']:
	#current repo (when range-based for)
	r = repos['items'][i]

	#extract repo name and clone url
	base_name = r['name']
	clone_url = r['clone_url']
	repo_name = base_name + "__" + r['owner']['login']	#save repos as base_name + owner id
	
	os.chdir("repo_clones")		#clone repos into a particular directory
	
	#legacy fix for bad code: if have repo saved as just base_name, move the files
	if os.path.isdir(base_name):
		os.rename(base_name, repo_name)
	
	#clone repo if doesn't exist
	if os.path.isdir(repo_name) == False:
		#clone repo (ugh...)
		run_bash("git clone %s %s" % (clone_url, repo_name))
	else:
		print "Already cloned", repo_name
	
	#move to git directory
	os.chdir(repo_name)
	
	#legacy fix again: rename commit log file if needed
	if os.path.isfile("%s/commit_data/%s_commits.log" % (dir, base_name)):
		os.rename("%s/commit_data/%s_commits.log" % (dir, base_name), "%s/commit_data/%s_commits.log" % (dir, repo_name))
	
	#get list of all matching commit diffs, save to file (if not already done)
	if os.path.isfile("%s/commit_data/%s_commits.log" % (dir, repo_name)) == False:
		run_bash('''git show --format="#######%%aE, %%aN, %%at" --unified=0 $(git rev-list --all) | awk '/^#####/ || /\-[[:blank:]]*import/ || /\+[[:blank:]]*import/  || /\-[[:blank:]]*from/ || /\+[[:blank:]]*from/'  > %s/commit_data/%s_commits.log''' % (dir, repo_name) , True)	
	
	#change back to previous working directory
	os.chdir("../..")	

	'''
	#INCOMPLETE
	#parse list of commit import statements into more useable form:
	#	list of users across all repos, with id, name, and email (not perfect)
	#	list of commits, each with user id, imported libraries (+ only), and timestamp
	with open("commit_data/%s_commits.log" % repo_name) as f:
		imports_list = ()
		for line in f:
			#commit line
			if "#######" in line:
				#save data from previous commit (if it exists)
				if len(imports_list) != 0:
					print "save stuff"
					break
				#grab new commit data, replace the old
				line = line.replace("#######", "")
				commit = [x.strip() for x in line.split(',')]
				imports_list = ()
				print commit
			#diff line
			else:
				print "diff"
	'''

	#delete the repo
	#run_bash("rm -r %s" % repo_name)
	#delete other temporary files
	#run_bash("rm commits.log")
	
	#stop when reach index limit
	idx = idx + 1
	if idx == limit:
		break

#git grep '^[[:blank:]]*import\| $(git rev-list --all) -- '*.py' > test.out
