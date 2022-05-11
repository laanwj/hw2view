import math
import numpy

def perspective_matrix(fovy, aspect, near, far):
    '''
    Build a perspective matrix (implements gluPerspective).
    '''
    # Based on https://stackoverflow.com/questions/71807942/opengl-gluperspective-implementation
    mat = numpy.zeros((4, 4))
    f = math.tan(math.radians(fovy) / 2.0)
    mat[0][0] = 1.0 / (f * aspect)
    mat[1][1] = 1.0 / f
    mat[2][2] = -(near + far) / (near - far)
    mat[3][2] = -(2.0 * near * far) / (near - far)
    mat[2][3] = -1.0
    return mat
