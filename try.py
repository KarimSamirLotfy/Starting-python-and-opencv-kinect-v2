import numpy as np

a= np.array([1000, 2000, 1000, 500, 8])
print(np.interp(a, (0, 10000), (0, 1)))