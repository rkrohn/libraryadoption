import json
import os.path
import subprocess

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
	
#read list of repos to clone and scrape
repos = load_json("all_repos_small.json")
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
idx = 0
limit = 50
for r in repos['items']:
	
	#extract repo name and clone url
	repo_name = r['name']
	clone_url = r['clone_url']
	print repo_name
	
	#check if we have this repo already
	os.chdir("repo_clones")		#clone repos into a particular directory
	#clone repo if doesn't exist
	if os.path.isdir(repo_name) == False:
		#clone repo (ugh...)
		run_bash("git clone %s" % clone_url)	
	
	#DO STUFF
	
	#move to git directory
	os.chdir(repo_name)
	#get list of all matching commit diffs, save to file (if not already done)
	if os.path.isfile("%s/commit_data/%s_commits.log" % (dir, repo_name)) == False:
		run_bash("git grep '^[[:blank:]]*import\|^[[:blank:]]*from' $(git rev-list --all) -- '*.py' > %s/commit_data/%s_commits.log" % (dir, repo_name) , True)	
	
	#one commit sha from httpie to test with
	#0f4dce98c70ca4517128990184c47388e58e04dd
	
	#this is getting close to the command to get commit authors
	#git show 0f4dce98c70ca4517128990184c47388e58e04dd --format="%an" --quiet
	#can pick as many format specifiers as I want (parse only what we need)
	#--quiet option supresses the diff, since we already have the relevant lines
	
	#change back to previous working directory
	os.chdir("../..")
	
	#delete the repo
	#run_bash("rm -r %s" % repo_name)
	#delete other temporary files
	#run_bash("rm commits.log")
	
	#for now, only do 5
	idx = idx + 1
	if idx == limit:
		break

#git grep '^[[:blank:]]*import\| $(git rev-list --all) -- '*.py' > test.out