import getpass
import requests
import os

from lxml import html

# Is this required?
from lxml import etree

'''
Author: Himanshu Jaju

This is a small utility code to scrape cses.fi website for accepted solutions
from an account. It requires username and password for accessing solutions of
the account and downloads the latest accepted solution for every solved
problem in {task_id}.{language_ext} file.

The script does not handle a lot of cases at the moment, eg:
1. Does not check for errors in login / logout.
2. Fetches only c++ codes.

Run this code on your terminal :
		python3 scraper.py

The script asks for your account details.
'''

# URLs on cses page
login_url = "https://cses.fi/login/";
logout_url = "https://cses.fi/logout/"
problemset_url = "https://cses.fi/problemset/";
results_url = "https://cses.fi/problemset/view/"

# Add values to this map to support more languages.
language_extension = {"C++": "cc"}

directory = "solved_problems/";

# Returns CSRF Token from login page.
def GetCSRFToken(session_requests):
	result = session_requests.get(login_url)
	tree = html.fromstring(result.text)
	return list(set(tree.xpath("//input[@name='csrf_token']/@value")))[0];

# Logs into the cses website. Asks for user credentials to login.
def Login(username, password, session_requests):
	payload = {
		"nick": username,
		"pass": password,
		"csrf_token": GetCSRFToken(session_requests)
	}
	login_result = session_requests.post(login_url, data = payload)
	return

# Logs out the user at the end of the process
def Logout(session_requests):
	logout_result = session_requests.get(logout_url)
	return

# Checks if the table cell is a green tick.
def IsGreenTick(element):
	return "task-score icon full" == element.get('class')

# Parses and returns a list of ids of solved tasks.
def ParseSolvedProblems(problemset_result_tree):
	rows = problemset_result_tree.xpath("//*/li[@class='task']")
	solved_task_ids = []
	for row in rows:
		columns = row.xpath("span")

		if IsGreenTick(columns[1]):
			problem_link = row.xpath("a")[0].attrib['href']
			task_id = problem_link[-4:]
			solved_task_ids.append(task_id)
	return solved_task_ids

# Returns a list of task ids of solved problems.
def GetSolvedProblems(session_requests):
	problemset_result = session_requests.get(problemset_url)
	tree = html.fromstring(problemset_result.content)
	return ParseSolvedProblems(tree)

# Returns the code from |code_link|.
def GetSolution(session_requests, code_link):
	task_results_url = session_requests.get(code_link)
	tree = html.fromstring(task_results_url.content)
	code = tree.xpath("//pre")[-1]
	return code.text_content()

# Saves the solution to disk.
def SaveTask(session_requests, task_id):
	task_results_url = session_requests.get(results_url + task_id)
	tree = html.fromstring(task_results_url.content)
	rows = tree.xpath("//*/table[@class='wide']/tr")
	for row in rows:
		columns = row.xpath("td")

		language = str(columns[1].text)
		if language not in language_extension:
			continue

		if not IsGreenTick(columns[4]):
			continue

		print("Saving solution for task : " + task_id)
		code_link = columns[5].xpath("a")[0].attrib['href']

		file_name = open(directory + task_id + "." + language_extension[language], "w+")
		file_name.write(GetSolution(session_requests, "https://cses.fi" + code_link))
		file_name.close()
		break

	return

# Runs the entire scraping flow.
def main():
	print("Enter your cses.fi account details")
	username = input("Username : ")
	password = getpass.getpass()

	print("Logging in your account ...")
	session_requests = requests.session()
	Login(username, password, session_requests)

	if not os.path.exists(directory):
		os.makedirs(directory)

	solved_tasks = GetSolvedProblems(session_requests)
	print("You have solved", len(solved_tasks), "tasks.")
	for task_id in solved_tasks:
		SaveTask(session_requests, task_id)

	Logout(session_requests)
	print("Logged out")
	return

if __name__== "__main__":
	main()
