import os
import sys
import git


class ConfigurationCreator(object):
    REPO_DIR = r"C:\amirelm\repos"
    CONFIGRATION_PATH = r"C:\amirelm\configurations"
    CONFIGRATION = r"""workingDir=C:\amirelm\projects_distributions\{PRODUCT_NAME}
git=C:\amirelm\repos\{PRODUCT_NAME}
issue_tracker_product_name={PRODUCT_NAME}
issue_tracker_url=https://issues.apache.org/jira
issue_tracker=jira
vers=({TAG_1},{TAG_2}, {TAG_3}, {TAG_4},{TAG_5})"""

    def __init__(self, jira_key):
        tags_names = map(lambda x: x.name, git.Repo(os.path.join(ConfigurationCreator.REPO_DIR, jira_key)).tags)
        self.configuration_path = os.path.join(ConfigurationCreator.CONFIGRATION_PATH, jira_key)
        if len(tags_names) < 5:
            return
        self.configuration = ConfigurationCreator.CONFIGRATION.format(PRODUCT_NAME=jira_key, TAG_1=tags_names[0], TAG_2=tags_names[1],
                                                                      TAG_3=tags_names[2], TAG_4=tags_names[3], TAG_5=tags_names[4])
        self.save_configuration()

    def get_configuration(self):
        return self.configuration

    def save_configuration(self):
        with open(self.get_configuration_path(), "wb") as f:
            f.write(self.get_configuration())

    def get_configuration_path(self):
        return self.configuration_path

    def get_cmd_line(self):
        return [sys.executable, 'wrapper.py', self.get_configuration_path()]

