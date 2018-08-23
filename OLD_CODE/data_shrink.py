#old script for removing unneeded files from repo clones
#crawls directory tree and removes any files that are not Python and do not contain a matching import statement
#this functionality was later rolled into github_clone_repos.py, so is not used anymore

import json
import os
import os.path
import subprocess
import sys
import urllib2
import re
	
#run bash command
def run_bash(command, shell=False):
	if shell:
		process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	else:
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
	output, error = process.communicate()
	
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

#--- MAIN EXECUTION BEGINS HERE---#	
	
#run in main working directory, containing repo_clones folder of repos to "shrink"
#goal: remove all files from repo clones that
#	- are not git files
#	- do not contain an import statement
#	- are not a python file (py, pyc, pyd, pyo, py3, pyw, pyx, pxd, pxi, pyi, pyz, pywz, ipynb)

delete_count = 0

dir_idx = 0

#loop all files in repo_clones (for now repo_test for safety)
for root, dirs, files in os.walk("repo_clones"):
	#skip the hidden directories and files (git stuff)
	files = [f for f in files if not f[0] == '.']
	dirs[:] = [d for d in dirs if not d[0] == '.']

	dir_idx = dir_idx + 1
	if dir_idx % 5000 == 0:
		print "\nfinished", dir_idx, "  deleted", delete_count, "files",

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
			if os.path.islink(path):
				os.unlink(path)
			else:
				os.remove(path)
			delete_count = delete_count + 1
			#print "deleted", path
			#print "X",
		except:
			#print "fail", path
			print ".",

print "deleted", delete_count, "files"		
		