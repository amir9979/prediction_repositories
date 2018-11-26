import jira
import github3
from collections import Counter
from configuration import ConfigurationCreator


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
    # print "\n".join(
    #     map(lambda x: "{0} git clone {1} {2}".format('call' if x[0] % 10 == 0 else 'start', x[1][0], x[1][1]),
    #         enumerate(apache_repos)))
    configurations = map(lambda x: ConfigurationCreator(x[1]), apache_repos)
    print "\n".join(map(lambda x: "{0} {1}".format('call' if x[0] % 10 == 0 else 'start', x[1].get_cmd_line()),
                        enumerate(configurations)))
    pass