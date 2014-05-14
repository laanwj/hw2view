from __future__ import division, print_function 
from OpenGL.GL import *
from OpenGL.GL import shaders
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

starttime = time.time()

def reshape(w, h):
    global width, height
    width = w
    height = h

def draw():
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, width/height, 1.0, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glRotate((time.time()-starttime)*30.0, 0.0, 1.0, 0.0)

    shaders.glUseProgram(background_shader)

    for numverts,vertsize,vertdata,facelists in bgdata:
        glVertexPointer(4, GL_FLOAT, vertsize, vertdata[0:])
        glEnableClientState(GL_VERTEX_ARRAY)
        glColorPointer(4, GL_BYTE, vertsize, vertdata[16:])
        glEnableClientState(GL_COLOR_ARRAY)
        for typ, count, facedata in facelists:
            glDrawElements(gl_types[typ], count, GL_UNSIGNED_SHORT, facedata)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

    shaders.glUseProgram(0)

    glutSwapBuffers()

def idle():
    glutPostRedisplay()

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
glutReshapeFunc(reshape)
glutIdleFunc(idle)

VERTEX_SHADER = shaders.compileShader("""
#version 120
void main()
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_FrontColor = gl_Color.abgr;
}
""", GL_VERTEX_SHADER)

FRAGMENT_SHADER = shaders.compileShader("""
#version 120
void main()
{
    gl_FragColor = gl_Color;
}""", GL_FRAGMENT_SHADER)
background_shader = shaders.compileProgram(VERTEX_SHADER,FRAGMENT_SHADER)

glutMainLoop()

