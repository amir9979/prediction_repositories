import csv


class Task(object):
    def __init__(self, run_args):
        self.run_args = run_args


class TaskManager(object):
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def save_as_csv(self, out_file):
        with open(out_file, "wb") as f:
            csv.writer(f).writerows(map(lambda task: task.run_args, self.tasks))