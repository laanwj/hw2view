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
        glVertexAttribPointer(vertex_loc, 4, GL_FLOAT, False, vertsize, vertdata[0:])
        glEnableVertexAttribArray(vertex_loc)
        glVertexAttribPointer(color_loc, 4, GL_BYTE, True, vertsize, vertdata[16:])
        glEnableVertexAttribArray(color_loc)
        for typ, count, facedata in facelists:
            glDrawElements(gl_types[typ], count, GL_UNSIGNED_SHORT, facedata)
        glDisableVertexAttribArray(vertex_loc)
        glDisableVertexAttribArray(color_loc)

    shaders.glUseProgram(0)

    glutSwapBuffers()

def idle():
    glutPostRedisplay()

# fetch data
filename='background/m01.hod'
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
attribute vec4 inVertex;
attribute vec4 inColor;
void main()
{
    gl_Position = gl_ModelViewProjectionMatrix * inVertex;
    gl_FrontColor = inColor.abgr;
}
""", GL_VERTEX_SHADER)

FRAGMENT_SHADER = shaders.compileShader("""
#version 120
void main()
{
    gl_FragColor = gl_Color;
}""", GL_FRAGMENT_SHADER)
background_shader = shaders.compileProgram(VERTEX_SHADER,FRAGMENT_SHADER)
vertex_loc = glGetAttribLocation(background_shader, "inVertex")
color_loc = glGetAttribLocation(background_shader, "inColor")

glutMainLoop()

