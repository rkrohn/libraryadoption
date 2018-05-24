#fetches lists of repos to clone, rippling out from the first 1000 Python repos

import requests
from collections import defaultdict
import numpy as np
import time
import file_utils as utils
	
#converts dictionary with unicode keys to int keys	
def dict_key_to_int(data):
	d = {int(k):[int(i) for i in v] for k,v in data.items()}
	return d
#end dict_key_to_int

#fetch first 1000 python repos as selected by github - these appear to be larger/more popular ones
def get_first_repos(auth, headers):
	#check if file exists, if yes just read it in
	data = utils.load_json("github_files/github_all_repos.json")
	if data != False:
		return data

	#well, that seems to have worked... time to do them all!
	#except it's not really ALL, just the first 1000 - can't seem to sort them,
	#so we'll go with what Github thinks is most interesting
	url = 'https://api.github.com/search/repositories?q=language:python&per_page=100'
	#first requests
	r = requests.get(url, auth=auth, headers=headers)
	all_results = r.json()
	url = r.links['next']['url']
	print r.links['last']['url']
	#loop all requests	
	count = 1
	print "finished request", count, "received", len(all_results['items']), "items"
	while url != "":
		#perform request and add results to previous
		r = requests.get(url, auth=auth, headers=headers)
		res = r.json()
		all_results['items'].extend(res['items'])
		count = count + 1
		print "finished request", count, "received", len(res['items']), "items"
		#get url for next request
		if 'next' in r.links:
			url = r.links['next']['url']
		else:
			url = ""
		print url
	#save all results to json file
	with open('github_files/github_all_repos.json', 'w') as fp:
		json.dump(all_results, fp, indent=4, sort_keys=False)

#get contributors for repos
def get_contrib(repos, auth, headers):
	#load existing data (if there)
	all_contrib = utils.load_json("github_files/github_all_contrib.json")	#existing contributors
	user_to_repo = to_int(utils.load_json("github_files/github_user_to_repo.json"))	#user->repos dict
	repo_to_contrib = to_int(utils.load_json("github_files/github_repo_to_contrib.json"))		#repo->contribs dict
	
	#if no contributors list or correlative dictionaries, initialize empty containers
	if all_contrib == False or user_to_repo == False or repo_to_contrib == False:
		user_to_repo = defaultdict(list)	#user id to list of repo ids
		repo_to_contrib = defaultdict(list)  #repo id to list of contrib
		all_contrib = list()
		
	#loop all repos from list, fetch contributors if don't have them	
	repo_count = 0
	for repo in all_repos['items']:
		#check if have contributors for this repo already, skip if yes
		if repo['id'] in repo_to_contrib:
			continue
			
		#need to fetch contributors for this repo
		print "Fetching repo", repo['id']		
		contrib_count = 0
		#get request url for this repo
		url = repo['contributors_url']
		while url != "":
			#get the json!
			r = requests.get(url, auth=auth, headers=headers) 
			res = r.json()
			contrib_count = contrib_count + len(res)
			#parse out this request result
			for usr in res:
				#new usr, add to list of all
				if usr['id'] not in user_to_repo:
					all_contrib.append(usr)
				#always add to correlative structures
				user_to_repo[usr['id']].append(repo['id'])
				repo_to_contrib[repo['id']].append(usr['id'])
			#see if more pages, fetch if yes
			if 'next' in r.links:
				url = r.links['next']['url']
			else:		#no new pages, done
				url = ""
		print "Repo", repo['id'], ":", contrib_count, "contributors"
		repo_count += 1
		
		#intermediate saves... just in case
		if repo_count % 10 == 0:
			#save all contrib to json file
			utils.save_json(all_contrib, "github_files/github_all_contrib.json")
			#save correlative lists
			utils.save_json(user_to_repo, "github_files/github_user_to_repo.json")
			utils.save_json(repo_to_contrib, "github_files/github_repo_to_contrib.json")
			print "saved contributors of", count, "repos"
			
	#all done - save results
	#save all contrib to json file
	utils.save_json(all_contrib, "github_files/github_all_contrib.json")
	#save correlative dictionaries
	utils.save_json(user_to_repo, "github_files/github_user_to_repo.json")
	utils.save_json(repo_to_contrib, "github_files/github_repo_to_contrib.json")
	
	#return results
	return all_contrib, user_to_repo, repo_to_contrib
#end get_contrib
	
#for all users so far, get all their Python repos	
def get_more_repos(all_contrib, all_repos, user_to_repo, repo_to_contrib, auth, headers):
	#since this will take more than 5000 requests, keep a bookmark in a file - in case something goes wrong
	
	#read simple list of users that are done already, will update
	finished_users = utils.load_json("github_files/github_finished_users.json")
	if finished_users == False:
		finished_users = list()
		
	#also keep list of users that don't search properly (private repos?)
	bad_users = utils.load_json("github_files/github_bad_users.json")
	if bad_users == False:
		bad_users = list()
		
	#also maintain a request count, dump if we get close to 5000 and resume later
	request_count = 0
	
	#loop all users (should be all contributors of the 1000 initial repos), fetch their python repos
	for user in all_contrib:
		#check if we did this user already, if so skip
		if user['id'] in finished_users:
			continue
		
		#build request url for this user
		url = "https://api.github.com/search/repositories?q=language:python+user:%s&per_page=100" % (user['login'])
		
		#do request, including any pages
		while url != "":
			#sleep for ~2 seconds before next request, to prevent getting kicked off
			time.sleep(2)
			
			#get the json!
			r = requests.get(url, auth=auth, headers=headers) 
			request_count += 1		#increment request counter
			res = r.json()
			
			#handle bad results and try to continue
			if 'items' not in res:
				#rate limit? wait for 60 seconds and try the same url again
				if res['documentation_url'] == "https://developer.github.com/v3/#rate-limiting":
					print "rate limit wait"
					time.sleep(60)
					continue
				#bad results for this particular user, they might be private now - add to list and skip
				else:
					print res
					bad_users.append(user)
					break	#move to next user
					
			#good results, parse and store
			for repo in res['items']:
				#new repo, add to list of all
				if repo['id'] not in repo_to_contrib:
					all_repos['items'].append(repo)					
				#always add to correlative structures
				user_to_repo[user['id']].append(repo['id'])
				if repo['id'] in repo_to_contrib:
					repo_to_contrib[repo['id']].append(user['id'])
				else:
					repo_to_contrib[repo['id']] = list()
					
			#see if more pages, if so fetch them
			if 'next' in r.links:
				url = r.links['next']['url']
			else:	#no more pages, quit for this user
				url = ""
		
			#intermediate saves and prints
			if request_count % 10 == 0:
				print request_count, "requests done"
			if request_count % 100 == 0:
				#save all repos to json file
				utils.save_json(all_repos, "github_files/github_all_repos.json")
				#save correlative lists
				utils.save_json(user_to_repo, "github_files/github_user_to_repo.json")
				utils.save_json(repo_to_contrib, "github_files/github_repo_to_contrib.json")
				print "Saved", request_count, "repo requests"
				#save bad users list
				utils.save_json(bad_users, "github_files/github_bad_users.json")
				#save list of finished users
				utils.save_json(finished_users, "github_files/github_finished_users.json")
						
		#finished user, add to bookmark
		finished_users.append(user['id'])
		
	#end for users
	
	#final save before return
	#save all repos to json file
	utils.save_json(all_repos, "github_files/github_all_repos.json")
	#save correlative lists
	utils.save_json(user_to_repo, "github_files/github_user_to_repo.json")
	utils.save_json(repo_to_contrib, "github_files/github_repo_to_contrib.json")
	#save bad users list
	utils.save_json(bad_users, "github_files/github_bad_users.json")
	#save list of finished users
	utils.save_json(finished_users, "github_files/github_finished_users.json")
	print "Saved all data to files"
	
	return all_contrib, all_repos, user_to_repo, repo_to_contrib	#return all results
#end get_more_repos
	
#--- MAIN EXECUTION BEGINS HERE---#	

#build request metadata
#user-agent header so I don't get kicked off; plus, accept text-match results
headers = {'User-Agent': 'rkrohn - scraping data for PhD research', 'From': 'rkrohn@nd.edu', 'Accept': 'application/vnd.github.v3.text-match+json', 'Accept': 'application/vnd.github.cloak-preview'}
auth=('rkrohn','c4a6c57e7c775792bc0483d7004aa7f161363f43')

#get first 1000 python repos - DONE
all_repos = get_first_repos(auth, headers)
print len(all_repos['items']), "repos"

#get contributors of these 1000 repos - DONE
all_contrib, user_to_repo, repo_to_contrib = get_contrib(all_repos, auth, headers)
print len(all_contrib), "contributors"

#get all python repos for all users we have so far - roughly 45K - DONE
all_contrib, all_repos, user_to_repo, repo_to_contrib = get_more_repos(all_contrib, all_repos, user_to_repo, repo_to_contrib, auth, headers)
