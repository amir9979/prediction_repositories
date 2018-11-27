import os
import re
import csv
import shutil
from numpy import mean, var
from itertools import product

DISTRIBUTIONS_DST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), r"../distributions"))
MAJORS_DST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), r"../majors"))
DISTRIBUTIONS_FILE_NAME = r"distribution_per_version_report.csv"
MAJORS_FILE_NAME = r"distribution_per_majors_report.csv"


class DistributionRow(object):
    def __init__(self, data_dict):
        map(lambda key: setattr(self, key, data_dict[key]), data_dict)
        self.bug = float(self.bug)
        self.valid = float(self.valid)
        self.components = self.bug + self.valid
        self.buggy_percent = self.bug / self.components


class Distribution(object):
    DISTRIBUTIONS_DIR = r"C:\amirelm\projects_distributions"
    DST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), r"../distributions"))

    def __init__(self, file_path):
        self.path = file_path
        with open(self.path) as f:
            lines = list(csv.reader(f))
            header = lines[0]
            self.rows = map(lambda line: DistributionRow(dict(zip(header, line))), lines[1:])

    def get_versions(self):
        return set(map(lambda row: row.version_name, self.rows))

    def get_data(self, granularity=None, buggedType=None):
        rows = self.rows
        if granularity:
            rows = filter(lambda row: row.granularity == granularity, rows)
        if buggedType:
            rows = filter(lambda row: row.buggedType == buggedType, rows)
        bugs = map(lambda row: row.bug, rows)
        valids = map(lambda row: row.valid, rows)
        components = map(lambda row: row.components, rows)
        buggy_percent = map(lambda row: row.buggy_percent, rows)
        data = {'granularity': granularity, 'buggedType': buggedType, 'versions': len(rows)}
        for (function_name, function), variable_name in product([('mean', mean), ('var', var), ('min', min), ('max', max)], ['components', 'valids', 'bugs', 'buggy_percent']):
            data['{0}_{1}'.format(function_name, variable_name)] = function(locals()[variable_name])
        return data

    @staticmethod
    def copy_distribution_files():
        for project_name in os.listdir(Distribution.DISTRIBUTIONS_DIR):
            for src, dst in zip([DISTRIBUTIONS_FILE_NAME, MAJORS_FILE_NAME], [DISTRIBUTIONS_DST_DIR, MAJORS_DST_DIR]):
                src_path = os.path.join(Distribution.DISTRIBUTIONS_DIR, project_name, src)
                dst_path = os.path.join(dst, project_name + ".csv")
                if os.path.exists(src_path):
                    shutil.copyfile(src_path, dst_path)


if __name__ == '__main__':
    Distribution.copy_distribution_files()
    versions = []
    for version in os.listdir(Distribution.DST_DIR):
        versions.extend(Distribution(os.path.join(Distribution.DST_DIR, version)).get_versions())
    pass