import scipy.io.arff
from scipy import stats
import numpy
import os
import subprocess
import tempfile
import weka_parser
from collections import Counter
from itertools import product
import json
import arff


class Attribute(object):
    WEKA_HEADER = ["index", 'attribute', 'type', 'nominal_percent', 'integer_percent', 'real_percent', 'missing_values',
                  'missing_percent', 'unique_values', 'unique_percent', 'distinct_values']
    RANKER_HEADER = ['ranker_score', 'index', 'attribute']

    def __init__(self, attribute_name, attribute_data, attribute_metadata):
        self.attribute_name = attribute_name
        self.attribute_type, self.attribute_range = attribute_metadata
        self.is_numeric = attribute_data.dtype.type == numpy.float_
        if self.is_numeric:
            description = stats.describe(attribute_data)
            map(lambda field: setattr(self, field, getattr(description, field)), description._fields)
        else:
            self.historgram = dict(Counter(attribute_data))
        self.ranker_score = -1

    def add_data_from_weka_hedaer(self, data):
        for attr in Attribute.WEKA_HEADER:
            if attr in data:
                setattr(self, attr, data[attr])

    def add_ranker_data(self, data):
        self.ranker_score = float(data['ranker_score'])

    def __repr__(self):
        return self.attribute_name


class WekaClassifier(object):
    def __init__(self, name, weka_path, arguments=None):
        self.name = name
        self.weka_path = weka_path
        if arguments:
            self.arguments = arguments
        else:
            self.arguments = []

    def get_training_path(self):
        return self.weka_path

    def get_testing_path(self):
        return self.weka_path

    def get_arguments(self):
        return self.arguments

    def get_tempfile(self):
        f, path = tempfile.mkstemp()
        os.close(f)
        return path

    def run(self, training_set_path, testing_set_path=None):
        model_path = self.get_tempfile()
        out_file = self.get_tempfile()
        print ['java', '-Xmx4g', '-cp', ArffFile.WEKA_PATH, 'weka.Run', self.get_training_path(), '-x', '10', '-d',
                 model_path, '-t', training_set_path] + self.get_arguments()
        with open(out_file, "wb") as stdout:
            proc = subprocess.Popen(
                ['java', '-Xmx4g', '-cp', ArffFile.WEKA_PATH, 'weka.Run', self.get_training_path(), '-x', '10', '-d',
                 model_path, '-t', training_set_path] + self.get_arguments(),
                stdout=stdout)
            proc.communicate()
            proc.wait()
        with open(out_file) as out:
            training_model = weka_parser.parse_WEKA_scores(out.read())
        testing_model = {}
        if testing_set_path:
            with open(out_file, "wb") as stdout:
                proc = subprocess.Popen(['java', '-Xmx4g', '-cp', ArffFile.WEKA_PATH, 'weka.Run',
                                         self.get_testing_path(), '-l', model_path, '-T', testing_set_path], stdout=stdout)
                proc.communicate()
                proc.wait()
            with open(out_file) as out:
                testing_model = weka_parser.parse_WEKA_scores(out.read())
        os.remove(model_path)
        os.remove(out_file)
        return {"training": training_model, "testing": testing_model}


class RandomForest(WekaClassifier):
    def __init__(self, name, num_trees):
        super(RandomForest, self).__init__(name,
                                           "weka.classifiers.trees.RandomForest", ["-I", str(num_trees),
                                            "-K", "0", "-S", "1", "-num-slots", "1"])


class FilterClassifier(WekaClassifier):
    def __init__(self, name, filter, classifier):
        super(FilterClassifier, self).__init__(name, "weka.classifiers.meta.FilteredClassifier", ["-F", filter, "-W", classifier.get_training_path(), "--"]+ classifier.get_arguments())
        self.base_classifier = classifier

    def get_testing_path(self):
        return self.base_classifier.get_testing_path()


WEKA_CLASSIFIERS = {"random_forest_100": RandomForest("random_forest_100", 100),
                   "random_forest_1000": RandomForest("random_forest_1000", 1000),
                   "NB": WekaClassifier("NB", "weka.classifiers.bayes.NaiveBayes"),
                   "decision_tree": WekaClassifier("decision_tree", "weka.classifiers.trees.J48", ["-C", "0.25", "-M", "2"])}

WEKA_IMBALANCERS = {"SMOTE": "weka.filters.supervised.instance.SMOTE -C 0 -K 5 -P 100.0 -S 1",
                    "ClassBalancer": "weka.filters.supervised.instance.ClassBalancer -num-intervals 10",
                    "Resample": "weka.filters.supervised.instance.Resample -B 0.0 -S 1 -Z 100.0",
                    "SpreadSubsample": "weka.filters.supervised.instance.SpreadSubsample -M 0.0 -X 0.0 -S 1"}


WEKA_ALGORITHMS = dict(WEKA_CLASSIFIERS.items() + map(lambda x: ("{0}_{1}".format(x[0], x[1]),
                                                                 FilterClassifier("{0}_{1}".format(x[0], x[1]), WEKA_IMBALANCERS[x[0]], WEKA_CLASSIFIERS[x[1]])), product(WEKA_IMBALANCERS, WEKA_CLASSIFIERS)))


def object_to_dict(obj):
    if type(obj) in [int, float, bool, str, unicode, long, numpy.float64, type(None)]:
        return obj
    elif type(obj) in [set, list, tuple]:
        return map(object_to_dict, obj)
    elif type(obj) == dict:
        return {k: object_to_dict(v) for k, v in obj.items()}
    else:
        return object_to_dict(obj.__dict__)


def save_object_as_json(obj, out_path):
    with open(out_path, "wb") as f:
        json.dump(object_to_dict(obj), f)


class ArffFile(object):
    CLASS_ATTRIBUTE = "hasBug"
    WEKA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), r"../externals/weka.jar"))

    def __init__(self, arff_path):
        self.arff_path = arff_path
        with open(self.arff_path) as f:
            data, meta = scipy.io.arff.loadarff(f)
        self.attributes = map(lambda field: Attribute(field, data[field], meta[field]), data.dtype.names)
        self.bug_distribution = self.attributes[-1].historgram
        self.get_weka_statistics()
        self.run_weka_ranker()
        self.results = ArffFile.run_all_algorithms(self.arff_path)

    def get_weka_statistics(self):
        proc = subprocess.Popen(['java', '-cp', ArffFile.WEKA_PATH, 'weka.core.Instances', self.arff_path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        lines = map(lambda line: line.replace('%', '').replace('/', ''), filter(lambda line: line, out.splitlines()[5:]))
        values = map(lambda line: dict(zip(Attribute.WEKA_HEADER, line.split())), lines)
        for value in values:
            self.attributes[int(value['index'])-1].add_data_from_weka_hedaer(value)

    def run_weka_ranker(self):
        proc = subprocess.Popen(['java', '-cp', ArffFile.WEKA_PATH, 'weka.attributeSelection.InfoGainAttributeEval'
                                    ,'-i', self.arff_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        lines = filter(lambda line: line, out.splitlines()[12:-3])
        values = map(lambda line: dict(zip(Attribute.RANKER_HEADER, line.split())), lines)
        for value in values:
            self.attributes[int(value['index'])-1].add_ranker_data(value)

    @staticmethod
    def run_all_algorithms(training_path, testing_path=None):
        return dict(map(lambda algorithm: (algorithm, WEKA_ALGORITHMS[algorithm].run(training_path, testing_path)),
                        WEKA_ALGORITHMS))

    @staticmethod
    def arff_build(attributes, data, description="description", relation="relation"):
        dict = {}
        dict['attributes'] = attributes
        dict['data'] = data
        dict['description'] = description
        dict['relation'] = relation
        return dict

    @staticmethod
    def write_to_arff(data, filename):
        with open(filename, 'w') as f:
            f.write(arff.dumps(data))

    @staticmethod
    def load_arff(filename):
        with open(filename, 'r') as f:
            return arff.loads(f.read())

    @staticmethod
    def merge_arff_files(out, paths):
        arff1 = ArffFile.load_arff(paths[0])
        attributes = arff1['attributes']
        data = arff1['data']
        for arff_path in paths[1:]:
            arff_value = ArffFile.load_arff(arff_path)
            assert attributes == arff_value['attributes'], "arff files has different attributes"
            data.extend(arff_value['data'])
        ArffFile.write_to_arff(ArffFile.arff_build(attributes, data), out)


if __name__ == "__main__":
    ArffFile.merge_arff_files(r"c:\temp\merged.arff", [r"C:\amirelm\projects_minors\COMPRESS\weka\All_testing_File_COMPRESS_1_4_rel_1_4.arff", r"C:\amirelm\projects_minors\COMPRESS\weka\All_testing_File_COMPRESS_1_5_rel_1_5.arff", r"C:\amirelm\projects_minors\COMPRESS\weka\All_testing_File_COMPRESS_1_6_rel_1_6.arff", r"C:\amirelm\projects_minors\COMPRESS\weka\All_testing_File_COMPRESS_1_2_rel_1_2.arff",r"C:\amirelm\projects_minors\COMPRESS\weka\All_testing_File_COMPRESS_1_3_rel_1_3.arff"])
    arff = ArffFile(r"c:\temp\merged.arff")
    arff = ArffFile(r"C:\amirelm\projects_minors\OOZIE\weka\All_testing_File_release_4_1_0_release_4_2_0.arff")
    save_object_as_json(arff, r"c:\temp\arff.json")
    pass
