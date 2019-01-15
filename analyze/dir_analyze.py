import os
import errno
from distutils.dir_util import copy_tree
from itertools import product
from arrfFile import ArffFile, save_object_as_json
import tempfile


class DirAnalyze(object):
    DEBUGGER_WEKA_DIR = "weka"
    DEBUGGER_LEARNING_DIR = "learning"
    DEBUGGER_ONE_BUT_ALL_DIR = r"learning\One"
    DEBUGGER_ALL_BUT_ONE_DIR = r"learning\AllbutOne"
    ANALYZE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), r"../analyze"))
    ANALYZE_RESULTS_DIR = r"analyze_results"
    BUG_TYPES = ["All", "Most"]
    GRANULARITIES = [ "File"]

    def __init__(self, project_name, version_list):
        self.project_name = project_name
        self.project_dir = os.path.join(DirAnalyze.ANALYZE_DIR, self.project_name)
        self.weka_dir = os.path.join(self.project_dir, DirAnalyze.DEBUGGER_WEKA_DIR)
        self.all_but_one_dir = os.path.join(self.project_dir, DirAnalyze.DEBUGGER_ALL_BUT_ONE_DIR)
        self.one_but_all_dir = os.path.join(self.project_dir, DirAnalyze.DEBUGGER_ONE_BUT_ALL_DIR)
        self.results_dir = os.path.join(self.project_dir, DirAnalyze.ANALYZE_RESULTS_DIR)
        self.version_list = version_list
        all_but_one_data = map(lambda x: ("all_but_one_" + x, os.path.join(self.all_but_one_dir, x)),
                               os.listdir(self.all_but_one_dir))
        one_but_all_data = map(lambda x: ("one_but_all_" + x, os.path.join(self.one_but_all_dir, x)),
                               os.listdir(self.one_but_all_dir))
        f, temp_merged_file = tempfile.mkstemp()
        os.close(f)
        for name, folder in one_but_all_data + all_but_one_data + [("weka", self.weka_dir)]:
            for buggedType, granularity in product(DirAnalyze.BUG_TYPES, DirAnalyze.GRANULARITIES):
                trainingFile, testingFile, testing_by_versions = self.get_files(folder, buggedType, granularity)
                for arff_file in [trainingFile, testingFile] + testing_by_versions:
                    if not os.path.exists(arff_file):
                        return
                    save_object_as_json(ArffFile(arff_file), os.path.join(self.results_dir,
                                                                          name + "_" + os.path.basename(
                                                                              arff_file).replace(".arff", ".json")))
                all_results = ArffFile.run_all_algorithms(trainingFile, testingFile)
                save_object_as_json(all_results, os.path.join(self.results_dir, name + "_training_on_testing.json"))
                for ind, arff_file in list(enumerate(testing_by_versions))[1:]:
                    ArffFile.merge_arff_files(temp_merged_file, testing_by_versions[:ind])
                    all_results = ArffFile.run_all_algorithms(temp_merged_file, arff_file)
                    save_object_as_json(all_results, os.path.join(self.results_dir,
                                                                  name + "_partial_training" + os.path.basename(
                                                                      arff_file).replace(".arff", ".json")))
        os.remove(temp_merged_file)

    def get_files(self, folder, buggedType, granularity):
        trainingFile = os.path.join(folder, buggedType + "_training_" + granularity + ".arff")
        testingFile = os.path.join(folder, buggedType + "_testing_" + granularity + ".arff")
        versions = map(lambda x: "_{0}_{1}".format(*x), zip(self.version_list, self.version_list[1:]))
        testing_by_versions = map(lambda x: testingFile.replace(".arff", x + ".arff"), versions)
        return trainingFile, testingFile, testing_by_versions

    @staticmethod
    def make_sure_path_exists(path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    @staticmethod
    def copy_to_local(working_dir, out_dir):
        DirAnalyze.make_sure_path_exists(os.path.join(out_dir, DirAnalyze.ANALYZE_RESULTS_DIR))
        for folder in [DirAnalyze.DEBUGGER_WEKA_DIR, DirAnalyze.DEBUGGER_LEARNING_DIR]:
            copy_tree(os.path.join(working_dir, folder), os.path.join(out_dir, folder))


if __name__ == '__main__':
    from retrieve_projects.configuration import ConfigurationCreator

    # for project in os.listdir(ConfigurationCreator.MINORS_WORKING_PATH):
    #     project_working_dir = os.path.join(ConfigurationCreator.MINORS_WORKING_PATH, project)
    #     DirAnalyze.copy_to_local(project_working_dir, os.path.join(DirAnalyze.ANALYZE_DIR, project))
    # exit()
    for project in os.listdir(ConfigurationCreator.MINORS_WORKING_PATH):
        project_working_dir = os.path.join(ConfigurationCreator.MINORS_WORKING_PATH, project)
        with open(os.path.join(project_working_dir, "configuration")) as configuration:
            versions = filter(lambda x: x.lower().startswith("vers"), configuration.readlines())[0].split("=")[
                1].replace("\n", "").replace("(", "").replace(")", "").split(",")
        analyzer = DirAnalyze(project, versions)
