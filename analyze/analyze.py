from scipy.io import arff
from scipy import stats
import numpy

INPUT = r""

with open(INPUT) as f:
    data, meta = arff.loadarff(f)
    numerical_columns = filter(lambda field: data[field].dtype.type == numpy.float_, data.dtype.fields)
    for column in column:
        pass

