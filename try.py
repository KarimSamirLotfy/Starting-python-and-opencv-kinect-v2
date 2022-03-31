from scipy import ndimage
import numpy as np
a = np.array([[[1, 2, 0, 0],
              [5, 3, 0, 4],
              [0, 0, 0, 7],
              [9, 3, 0, 0]],
              
              [[1, 3, 0, 0],
              [5, 3, 0, 4],
              [0, 0, 0, 7],
              [9, 3, 0, 0]]
              
              ])

k = np.array([[1]])
t= ndimage.convolve(a, k, mode='constant', cval=0.0)
ndimage.convolve1d([2, 8, 0, 4, 1, 9, 9, 0], weights=[1, 3])
print(t)