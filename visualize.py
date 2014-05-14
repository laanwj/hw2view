from __future__ import division, print_function 
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from parse_bg import parse_bg, PRIM_TRIANGLE_STRIP, PRIM_TRIANGLES
import time

window = 0
width, height = 500, 400

gl_types = {
    PRIM_TRIANGLES: GL_TRIANGLES,
    PRIM_TRIANGLE_STRIP: GL_TRIANGLE_STRIP
}

def draw_rect(x, y, width, height, z):
    glBegin(GL_QUADS)
    glVertex3f(x, y, z)
    glVertex3f(x + width, y, z)
    glVertex3f(x + width, y + height, z)
    glVertex3f(x, y + height, z)
    glEnd()

starttime = time.time()
def draw():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, width/height, 1.0, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glRotate((time.time()-starttime)*30.0, 0.0, 1.0, 0.0)

    glColor3f(0.0, 0.0, 1.0)
    #draw_rect(-10.0, -10.0, 20.0, 20.0, -50.0)
    for vertices,facelists in bgdata:
        for typ, faces in facelists:
            glBegin(gl_types[typ])
            for face in faces:
                glColor3f(vertices[face][7]/255.0, vertices[face][6]/255.0, vertices[face][5]/255.0)
                glVertex3f(vertices[face][0], vertices[face][1], vertices[face][2])
            glEnd()
        #break

    glutSwapBuffers()

# fetch data
filename='background/m03/m03.hod'
bgdata = parse_bg(filename)

# initialization
glutInit()
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
glutInitWindowSize(width, height)
glutInitWindowPosition(0, 0)
window = glutCreateWindow("homeworld2 background")
glutDisplayFunc(draw)
glutIdleFunc(draw)
glutMainLoop()

