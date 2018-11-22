import github3
import bugzilla
# bzapi = bugzilla.Bugzilla(r"bugzilla.redhat.com")

RED_HAT_PROJECTS = r'https://raw.githubusercontent.com/RedHatOfficial/RedHatOfficial.github.io/dev/app/data/projects.json'

def get_repos():
    bzapi = bugzilla.Bugzilla(r"partner-bugzilla.redhat.com")
    products = map(lambda product: product['name'], bzapi.getproducts())
    gh = github3.login('DebuggerIssuesReport', password='DebuggerIssuesReport1')
    repos = list(gh.search_repositories('user:{0} language:Java'.format(user)))
