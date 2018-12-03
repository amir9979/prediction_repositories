import os
import sys
import git


class Configuration(object):
    CONFIGRATION = r"""workingDir={WORKING_DIR}
git=C:\amirelm\repos\{PRODUCT_NAME}
issue_tracker_product_name={PRODUCT_NAME}
issue_tracker_url=https://issues.apache.org/jira
issue_tracker=jira
vers=({VERSIONS})"""

    def __init__(self, jira_key, configuration_path, working_dir, versions=None):
        self.configuration_path = configuration_path
        if versions is None:
            return
        self.configuration = Configuration.CONFIGRATION.format(WORKING_DIR=working_dir, PRODUCT_NAME=jira_key, VERSIONS=versions)
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


def get_versions_by_type(tags):
    import re
    majors = []
    minors = []
    micros = []
    SEPERATORS = ['\.', '\-', '\_']
    template_base = [['([0-9])', '([0-9])([0-9])', '([0-9])$'], ['([0-9])', '([0-9])([0-9])$'], ['([0-9])', '([0-9])', '([0-9])([0-9])$'], ['([0-9])([0-9])', '([0-9])$'], ['([0-9])', '([0-9])', '([0-9])$'], ['([0-9])', '([0-9])$']]
    templates = []
    for base in template_base:
        templates.extend(map(lambda sep: sep.join(base), SEPERATORS))
    templates.extend(['([0-9])([0-9])([0-9])$', '([0-9])([0-9])$'])
    for tag in tags:
        for template in templates:
            values = re.findall(template, tag.name)
            if values:
                values = map(int, values[0])
                if len(values) == 4:
                    micros.append(tag)
                    major, minor1, minor2, micro = values
                    minor = 10 * minor1 + minor2
                elif len(values) == 3:
                    micros.append(tag)
                    major, minor, micro = values
                else:
                    major, minor = values
                    micro = 0
                if micro == 0:
                    minors.append(tag)
                if minor == 0:
                    majors.append(tag)
                break
    return majors, minors, micros


class ConfigurationCreator(object):
    REPO_DIR = r"C:\amirelm\repos"
    CONFIGRATION_PATH = r"C:\amirelm\configurations"
    MINORS_CONFIGRATION_PATH = r"C:\amirelm\minors_configurations"
    DISTRIBUTIONS_WORKING_PATH = r"C:\amirelm\projects_distributions1"
    MINORS_WORKING_PATH = r"C:\amirelm\projects_minors"

    @staticmethod
    def create_configurations(jira_key):
        tags_names = sorted(git.Repo(os.path.join(ConfigurationCreator.REPO_DIR, jira_key)).tags,
                            key=lambda tag: tag.commit.committed_date)
        _, minors, _ = get_versions_by_type(tags_names)
        if len(tags_names) < 5:
            raise RuntimeError("less than 5 versions")
        distribution_configuration = Configuration(jira_key,  os.path.join(ConfigurationCreator.CONFIGRATION_PATH, jira_key),
                                                   os.path.join(ConfigurationCreator.DISTRIBUTIONS_WORKING_PATH, jira_key), ",".join(map(lambda x: x.name, tags_names[:5])))
        minor_configuration = Configuration(jira_key, os.path.join(ConfigurationCreator.MINORS_CONFIGRATION_PATH, jira_key),
                                            os.path.join(ConfigurationCreator.MINORS_WORKING_PATH, jira_key), ",".join(map(lambda x: x.name, minors)))
        return [distribution_configuration, minor_configuration]