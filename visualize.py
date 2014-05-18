#!/usr/bin/python
from __future__ import division, print_function 
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLUT import *
from OpenGL.GLU import *
from parse_bg import parse_bg, PRIM_TRIANGLE_STRIP, PRIM_TRIANGLES
import time
import ctypes

window = 0
width, height = 500, 400
wireframe_mode = False
rotation_speed = 1.0
starttime = time.time()

gl_types = {
    PRIM_TRIANGLES: GL_TRIANGLES,
    PRIM_TRIANGLE_STRIP: GL_TRIANGLE_STRIP
}
PRIMITIVE_RESTART_INDEX = 65535

def reshape(w, h):
    global width, height
    width = w
    height = h

def draw():
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # set up matrices
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, width/height, 1.0, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glRotate((time.time()-starttime)*rotation_speed, 0.1, 1.0, 0.0)

    # rendering time
    if wireframe_mode:
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    else:
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glEnable(GL_PRIMITIVE_RESTART)
    glPrimitiveRestartIndex(PRIMITIVE_RESTART_INDEX)
    shaders.glUseProgram(background_shader)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
    glEnableVertexAttribArray(vertex_loc)
    glEnableVertexAttribArray(color_loc)
    prims = 0
    for numverts,vertsize,vertdata_offset,facelists in nbgdata:
        glVertexAttribPointer(vertex_loc, 4, GL_FLOAT, False, vertsize, ctypes.c_void_p(vertdata_offset))
        glVertexAttribPointer(color_loc, 4, GL_BYTE, True, vertsize, ctypes.c_void_p(vertdata_offset+16))
        for typ, count, facedata_offset in facelists:
            glDrawElements(gl_types[typ], count, GL_UNSIGNED_SHORT, ctypes.c_void_p(facedata_offset))
    glDisableVertexAttribArray(vertex_loc)
    glDisableVertexAttribArray(color_loc)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
    shaders.glUseProgram(0)
    glDisable(GL_PRIMITIVE_RESTART)

    glutSwapBuffers()

def idle():
    glutPostRedisplay()

def keypress(key, x, y):
    '''
    Keyboard: w for wireframe mode
    '''
    global wireframe_mode
    if key == 'w':
        wireframe_mode = not wireframe_mode

def create_shaders():
    global background_shader, vertex_loc, color_loc

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

def create_vbos(bgdata):
    global ibo,vbo,nbgdata
    # Build vertex and index buffers and new bgdata structure
    # that has pointers into the vertex and index buffers instead of
    # data
    allvertdata = []
    allfacedata = []
    vertdata_ptr = 0
    facedata_ptr = 0
    nbgdata = []
    for numverts,vertsize,vertdata,facelists in bgdata:
        vertdata_offset = vertdata_ptr
        allvertdata.append(vertdata)
        vertdata_ptr += len(vertdata)
        nfacelists = []
        for typ, count, facedata in facelists:
            facedata_offset = facedata_ptr
            allfacedata.append(facedata)
            facedata_ptr += len(facedata)
            nfacelists.append((typ, count, facedata_offset))
        nbgdata.append((numverts, vertsize, vertdata_offset, nfacelists))

    allvertdata = ''.join(allvertdata)
    allfacedata = ''.join(allfacedata)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, len(allvertdata), allvertdata, GL_STATIC_DRAW)
    glBindBuffer(GL_ARRAY_BUFFER, 0)

    ibo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(allfacedata), allfacedata, GL_STATIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

def concatenate_primitives(bgdata):
    import struct
    PRIMITIVE_RESTART = struct.pack('<H',65535)
    bgdata_new = []
    for numverts,vertsize,vertdata,facelists in bgdata:
        # concatenate triangles, as well as triangle strips, into different buffers
        triangles = []
        triangle_strip = []

        for typ, count, facedata in facelists:
            assert(len(facedata) == 2*count)
            if typ == PRIM_TRIANGLE_STRIP:
                triangle_strip.append(facedata)
                triangle_strip.append(PRIMITIVE_RESTART)
            elif typ == PRIM_TRIANGLES:
                triangles.append(facedata)
            else:
                raise ValueError('Unknown primitive type %d', typ)

        facelists_new = []
        if triangle_strip:
            joined = ''.join(triangle_strip)
            facelists_new.append((PRIM_TRIANGLE_STRIP, len(joined)//2, joined))
        if triangles:
            joined = ''.join(triangles)
            facelists_new.append((PRIM_TRIANGLES, len(joined)//2, joined))

        bgdata_new.append((numverts,vertsize,vertdata,facelists_new))

    return bgdata_new

if __name__ == '__main__':
    import sys
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Usage: %s <filename.hod>" % sys.argv[0])
        exit(1)
    # fetch data
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
    glutKeyboardFunc(keypress)

    create_shaders()
    bgdata = concatenate_primitives(bgdata)
    create_vbos(bgdata)

    glutMainLoop()

