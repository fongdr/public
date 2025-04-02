
import subprocess
import requests
from requests.auth import HTTPBasicAuth
import re


##if your work IT installs a firewall that breaks SSL verification
get_around_IT = False
if get_around_IT:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning 
    import warnings
    warnings.simplefilter("ignore", InsecureRequestWarning)

# Jira API configuration
# load from .env or hardcode. I'm not your boss.
import os
from dotenv import load_dotenv
load_dotenv()
JIRA_URL = os.environ.get('JIRA_URL')  # URL for your Jira board
JIRA_USER = os.environ.get('JIRA_USER')  # your username. usually name@companyemail.com
JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN') # may have to generate a JIRA API TOKEN
JIRA_BOARD_PREFIX = os.environ.get('JIRA_BOARD_PREFIX') # ticket prefix before the number

############## TO NOTE #############
# this assumes you prepend your branch names with the ticket number in the form of:
# JIRA_BOARD_PREFIX-<ticket_number>
# example: EXP-1234--FixAllTheThings

JIRA_API_ENDPOINT = "/rest/api/3/issue/{}"  # Endpoint to fetch an issue by ID
# Git repository configuration (ensure you're in a git repo)
GIT_CMD = "git branch" 

# Get the current Git branch name
def get_git_branches():
    done_tickets = []
    in_progress = []
    try:
        search_string = JIRA_BOARD_PREFIX + "-" + "[0-9]{4}"
        lines = subprocess.check_output(GIT_CMD.split()).decode("utf-8").splitlines()
        for line in lines:
            match = re.search(search_string, line.strip())
            if match:
                ticket_id = match.group()
                status, summary = get_jira_issue_status(ticket_id)
                if status is not None:
                    if status != "Done":
                        in_progress.append((ticket_id, status, summary, line))
                    else:
                        done_tickets.append(ticket_id)

        sorted_list = sorted(in_progress, key=lambda x: x[1])
        for ticket_id, status, summary, line in sorted_list:
            print(f"""{status}
      {summary}
      branch:   {line}
      {JIRA_URL}/browse/{ticket_id}
""")

        print(f"""
            {len(done_tickets)} tickets marked as DONE!
            """)
    except subprocess.CalledProcessError as e:
        print("Error getting Git branch name:", e)
        return None

# Fetch the Jira issue status
def get_jira_issue_status(ticket_id):
    url = JIRA_URL + JIRA_API_ENDPOINT.format(ticket_id)
    try:
        response = requests.get(url, auth=HTTPBasicAuth(JIRA_USER, JIRA_API_TOKEN), verify=not get_around_IT)
        if response.status_code == 200:
            issue_data = response.json()
            return issue_data['fields']['status']['name'], issue_data['fields']["summary"]
        else:
            print(f"Error fetching Jira issue {ticket_id}: {response.status_code}")
            return None, None
    except requests.exceptions.RequestException as e:
        print("Error fetching Jira issue:", e)



if __name__ == "__main__":
    get_git_branches()
