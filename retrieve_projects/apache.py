import jira
import github3
from collections import Counter
from configuration import ConfigurationCreator
import task
import sys


def find_repo_and_jira(key, repos, jira_projects):
    jira_project = filter(lambda p: key in [p.key.strip().lower(), "-".join(p.name.strip().lower().split())], jira_projects)[0]
    github = filter(lambda repo: repo.as_dict()['name'].strip().lower() == key, repos)[0]
    return github.repository.as_dict()['clone_url'], jira_project.key


def get_apache_repos_data():
    gh = github3.login('DebuggerIssuesReport', password='DebuggerIssuesReport1') # DebuggerIssuesReport@mail.com
    repos = list(gh.search_repositories('user:apache language:Java'))
    github_repos = list(set(map(lambda repo: repo.as_dict()['name'].strip().lower(), repos)))
    conn = jira.JIRA(r"http://issues.apache.org/jira")
    jira_projects = conn.projects()
    jira_keys = map(lambda p: p.key.strip().lower(), jira_projects)
    jira_names = map(lambda p: "-".join(p.name.strip().lower().split()), jira_projects)
    jira_elements = list(set(jira_names + jira_keys))
    jira_and_github = map(lambda x: x[0], filter(lambda x: x[1] > 1, Counter(github_repos + jira_elements).most_common()))
    return map(lambda key: find_repo_and_jira(key, repos, jira_projects), jira_and_github)


if __name__ == "__main__":
    apache_repos = get_apache_repos_data()
    distribution_configurations = []
    minor_configurations = []
    configurations = []
    for repo in apache_repos:
        try:
            dist, minor = ConfigurationCreator.create_configurations(repo[1])
            distribution_configurations.append(dist)
            minor_configurations.append(minor)
        except:
            pass
    for configurations, out_file in [(distribution_configurations, "configurations_running.csv"), (minor_configurations, "minor_configurations_running.csv")]:
        manager = task.TaskManager()
        for config in configurations:
            manager.add_task(task.Task(config.get_cmd_line()))
        manager.save_as_csv(out_file)