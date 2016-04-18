#!/usr/bin/python3
# Copyright (c) 2014 Wladimir J. van der Laan
# Distributed under the MIT/X11 software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
'''
Show Homeworld 2 backgrounds using OpenGL-based visualization.
'''
from __future__ import division, print_function 
from OpenGL.GL import *
from OpenGL.GL.NV.primitive_restart import *
from OpenGL.GL import shaders
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.extensions import alternate
from parse_bg import parse_bg, PRIM_TRIANGLE_STRIP, PRIM_TRIANGLES
from transformations import Arcball, quaternion_slerp
import time
import ctypes

window = 0
width, height = 500, 400
wireframe_mode = False
rotation_speed = 1.0
starttime = time.time()
arcball = Arcball()
arcball.active = False
animate = None # autospin
fovy = 45 # field of vision in y - I don't know what original homeworld uses

# Options for primitive restart
PRIMITIVE_RESTART_NONE = 0
PRIMITIVE_RESTART_CORE = 1
PRIMITIVE_RESTART_NV = 2

# Primitive restart type supported (filled in in probe_extensions)
primitive_restart_mode = PRIMITIVE_RESTART_NONE

gl_types = {
    PRIM_TRIANGLES: GL_TRIANGLES,
    PRIM_TRIANGLE_STRIP: GL_TRIANGLE_STRIP
}
PRIMITIVE_RESTART_INDEX = 65535

# extension alternates for GL <2.0
from OpenGL.GL.ARB.vertex_shader import *
from OpenGL.GL.ARB.vertex_buffer_object import *
from OpenGL.GL.ARB.vertex_program import *
glGetAttribLocation = alternate('glGetAttribLocation', glGetAttribLocation, glGetAttribLocationARB)
glEnableVertexAttribArray = alternate('glEnableVertexAttribArray', glEnableVertexAttribArray, glEnableVertexAttribArrayARB)
glDisableVertexAttribArray = alternate('glDisableVertexAttribArray', glDisableVertexAttribArray, glDisableVertexAttribArrayARB)
glVertexAttribPointer = alternate('glVertexAttribPointer', glVertexAttribPointer, glVertexAttribPointerARB)
glGenBuffers = alternate('glGenBuffers', glGenBuffers, glGenBuffersARB)
glBindBuffer = alternate('glBindBuffer', glBindBuffer, glBindBufferARB)
glBufferData = alternate('glBufferData', glBufferData, glBufferDataARB)

def reshape(w, h):
    global width, height
    width = w
    height = h
    arcball.place([w/2, h/2], h/2)

def draw():
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # set up matrices
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovy, width/height, 1.0, 100.0)
    glMatrixMode(GL_MODELVIEW)
    #glLoadIdentity()
    glLoadMatrixf(arcball.matrix().T)

    # rendering time
    if wireframe_mode:
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    else:
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    if primitive_restart_mode == PRIMITIVE_RESTART_CORE:
        glEnable(GL_PRIMITIVE_RESTART)
        glPrimitiveRestartIndex(PRIMITIVE_RESTART_INDEX)
    elif primitive_restart_mode == PRIMITIVE_RESTART_NV:
        glEnableClientState(GL_PRIMITIVE_RESTART_NV)
        glPrimitiveRestartIndexNV(PRIMITIVE_RESTART_INDEX)

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
    if primitive_restart_mode == PRIMITIVE_RESTART_CORE:
        glDisable(GL_PRIMITIVE_RESTART)
    elif primitive_restart_mode == PRIMITIVE_RESTART_NV:
        glDisableClientState(GL_PRIMITIVE_RESTART_NV)

    glutSwapBuffers()

def idle():
    global starttime
    nexttime = time.time()
    deltatime = nexttime-starttime
    starttime = nexttime
    #if animate is not None:
    #    # Continue in auto-spin if arcball not active
    #    animate[2] += deltatime * 20.0
    #    arcball._qnow = quaternion_slerp(animate[0], animate[1], animate[2], False) 
    glutPostRedisplay()

def keypress(key, x, y):
    '''
    Keyboard: w for wireframe mode
    '''
    global wireframe_mode
    if key == 'w':
        wireframe_mode = not wireframe_mode

def mouse(button, state, x, y):
    global animate
    if button == 0:
        arcball.active = (state == 0)
        if arcball.active:
            arcball.down([x,y])
            animate = None
        else:
            animate = [arcball._qpre, arcball._qnow, 1.0]

def motion(x, y):
    if arcball.active:
        arcball.drag([x,y])

def create_shaders():
    global background_shader, vertex_loc, color_loc

    VERTEX_SHADER = shaders.compileShader(b"""
    #version 120
    attribute vec4 inVertex;
    attribute vec4 inColor;
    void main()
    {
        gl_Position = gl_ModelViewProjectionMatrix * inVertex;
        gl_FrontColor = inColor.abgr;
    }
    """, GL_VERTEX_SHADER)

    FRAGMENT_SHADER = shaders.compileShader(b"""
    #version 120
    void main()
    {
        gl_FragColor = gl_Color;
    }""", GL_FRAGMENT_SHADER)
    background_shader = shaders.compileProgram(VERTEX_SHADER,FRAGMENT_SHADER)
    vertex_loc = glGetAttribLocation(background_shader, b"inVertex")
    color_loc = glGetAttribLocation(background_shader, b"inColor")

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

    allvertdata = b''.join(allvertdata)
    allfacedata = b''.join(allfacedata)

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
                if triangle_strip:
                    if primitive_restart_mode == PRIMITIVE_RESTART_NONE:
                        # create two degenerate triangles in between
                        triangle_strip.append(
                                triangle_strip[-1][-2:] +
                                facedata[:2])
                    else:
                        triangle_strip.append(PRIMITIVE_RESTART)
                triangle_strip.append(facedata)
            elif typ == PRIM_TRIANGLES:
                triangles.append(facedata)
            else:
                raise ValueError('Unknown primitive type %d', typ)

        facelists_new = []
        if triangle_strip:
            joined = b''.join(triangle_strip)
            facelists_new.append((PRIM_TRIANGLE_STRIP, len(joined)//2, joined))
        if triangles:
            joined = b''.join(triangles)
            facelists_new.append((PRIM_TRIANGLES, len(joined)//2, joined))

        bgdata_new.append((numverts,vertsize,vertdata,facelists_new))

    return bgdata_new

def probe_extensions():
    global primitive_restart_mode
    primitive_restart_mode = PRIMITIVE_RESTART_NONE
    if glPrimitiveRestartIndex:
        primitive_restart_mode = PRIMITIVE_RESTART_CORE
    elif glPrimitiveRestartNV:
        primitive_restart_mode = PRIMITIVE_RESTART_NV
    else:
        print("Warning: Primitive restart not supported, falling back to slow path")

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
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
    glutInitWindowSize(width, height)
    glutInitWindowPosition(0, 0)
    window = glutCreateWindow(b"homeworld2 background: " + os.path.basename(filename).encode())
    glutDisplayFunc(draw)
    glutReshapeFunc(reshape)
    glutIdleFunc(idle)
    glutKeyboardFunc(keypress)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    probe_extensions()
    print('Primitive restart mode: %s' % (['NONE','CORE','NV'][primitive_restart_mode]))
    create_shaders()
    bgdata = concatenate_primitives(bgdata)
    create_vbos(bgdata)

    glutMainLoop()

