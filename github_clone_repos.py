#clone repos given in all_repos.json, extract commit log, and clean up unwanted (non-py) files as we go

import os.path
import subprocess
import sys
import urllib2
import file_utils as utils
import re

#appends repo name to fail log file for later
def log_fail(root_dir, repo_name):
	with open(root_dir + "/github_files/github_fail_clone.txt", "a") as fail_log:
		fail_log.write(repo_name + "\n")
#end log_fail

#checks if a file contains a valid matching import statement
def contains_import(filename):
	pattern = r"^\s*(from\s(([a-zA-Z]|\.|\_|\d)+)\s){0,1}import(\s(([a-zA-Z]|\.|\_|\d)+)(\sas\s(([a-zA-Z]|\.|\_|\d)+))*,)*(\s(([a-zA-Z]|\.|\_|\d)+)(\sas\s(([a-zA-Z]|\.|\_|\d)+))*)\s*$"
	try:
		if os.path.islink(filename) == False:
			with open(filename, 'r') as f:		
				for line in f:
					if re.search(pattern, line) != None:
						return True		#return true if found import
	except:
		print "fail open", filename
	return False	#no import, return false
#end contains_import

#delete files in directory, leaving only .py (and related) and files containing a matching import
#call on directory to "shrink"
#goal: remove all files from directory recursively that
#	- are not git files
#	- do not contain an import statement
#	- are not a python file (py, pyc, pyd, pyo, py3, pyw, pyx, pxd, pxi, pyi, pyz, pywz, ipynb)
def delete_files(dir):
	delete_count = 0

	#loop all files in directory
	for root, dirs, files in os.walk(dir):
		#skip the hidden directories and files (git stuff)
		files = [f for f in files if not f[0] == '.']
		dirs[:] = [d for d in dirs if not d[0] == '.']

		for file in files:
			#skip python files
			if file.lower().endswith(('.py', '.pyc', '.pyd', '.pyo', '.py3', '.pyw', '.pyx', '.pxd', '.pxi', '.pyi', '.pyz', '.pywz', '.ipynb')):
				continue
			
			#create complete path
			path = os.path.join(root, file)
				
			#skip files containing valid import statement (just to be safe)
			if contains_import(path):
				continue

			#weeded out the "good" files, delete what remains
			#print path
			try:
				#unlink for symlinks
				if os.path.islink(path):
					os.unlink(path)
				#true delete for files
				else:
					os.remove(path)
				delete_count += 1
			except:
				print "fail", path
	print "deleted", delete_count, "files"
#end delete_files	
		
#given repo name and owner login, clone the repo
#returns true if the clone was successful, false otherwise		
def clone_repo(repo_name, base_name, owner):
	#check that repo exists:
	try:
		res = urllib2.urlopen('https://github.com/%s/%s' % (r['owner']['login'], base_name))
	except urllib2.URLError as e:
		res = e
		
	#if can access web page, repo exists, clone
	if res.code in (200, 401):
		#clone repo (ugh...)
		print "Cloning", repo_name
		utils.run_bash("git clone %s %s" % (clone_url, repo_name))
		
		#second check for successful clone, if no directory log fail and return false
		if os.path.isdir(repo_name) == False:
			log_fail(root_dir, repo_name)
			return False
		
		#housekeeping: delete all files in this repo that are not .py (or related) and don't contain import
		delete_files(repo_name)
		
	#repo doesn't exist (or is unreachable), log fail and return false	
	else:	
		log_fail(root_dir, repo_name)
		return False
		
	return True
#end clone_repo

#--- MAIN EXECUTION BEGINS HERE---#	
	
#check for required command line param
if len(sys.argv) != 3:
	print "Must include starting index and # to process for repo cloning process."
	print "Usage: python github_clone_repos.py <starting index> <# to process>"
	sys.exit(0)

#read list of repos to clone
print "Reading repo list..."
repos = utils.load_json("github_files/github_all_repos.json")	
print "Read", len(repos['items']), "repos"

#grab and save current working directory
root_dir = os.getcwd()

#create directory for repo clones (if doesn't already exist)
if os.path.isdir("repo_clones") == False:
	os.makedirs("repo_clones")
#create directory for commit data (if doesn't already exist)
if os.path.isdir("commit_data") == False:
	os.makedirs("commit_data")

#grad command line args: starting index and processing limit
idx = int(sys.argv[1])		#starting index from command line parameter
limit = int(sys.argv[2])			#process <command line var> at a time starting from given index

#move to repo_clones directory, since that's where all the files will be
os.chdir("repo_clones")	

#process each repo
for i in range(idx, idx+limit):
	#current repo to clone
	r = repos['items'][i]

	#extract repo name and clone url
	clone_url = r['clone_url']
	base_name = r['name']
	owner = r['owner']['login']
	repo_name = base_name + "__" + owner	#save repos as base_name + owner id (because repo names not unique)
	
	#clone repo if clone dir doesn't exist, and clean up unwanted files
	if os.path.isdir(repo_name) == False:
		clone_res = clone_repo(repo_name, base_name, owner)
	else:
		clone_res = True
		
	#clone repo if commit log file doesn't exist
	if clone_res and os.path.isfile("%s/commit_data/%s_commits.log" % (root_dir, repo_name)) == False:
		print "Extracting commit data from", repo_name
	
		#move to git directory
		os.chdir(repo_name)

		#get list of all matching commit diffs, save to file (if not already done)
		if os.path.isfile("%s/commit_data/%s_commits.log" % (root_dir, repo_name)) == False:
			#pull all commit data, and commit contents starting with "import" or "from"
			utils.run_bash('''git show --format="#######%%aE, %%aN, %%at" --unified=0 $(git rev-list --all) | awk '/^#####/ || /\-[[:blank:]]*import/ || /\+[[:blank:]]*import/  || /\-[[:blank:]]*from/ || /\+[[:blank:]]*from/'  > %s/commit_data/%s_commits.log''' % (root_dir, repo_name) , True)

		#change back to repo_clones directory
		os.chdir("..")		
					
	#commit log file already exists, skip this repo
	else:
		print "Already cloned and processed", repo_name
	
	#stop when reach index limit
	idx = idx + 1
	if idx == limit:
		break
	
	#period prints
	if idx % 100 == 0:
		print "FINISHED", idx, "REPOS"

#final print
print "Done"