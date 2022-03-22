#!/usr/bin/python3
# Copyright (c) 2014 Wladimir J. van der Laan
# Distributed under the MIT/X11 software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
'''
Show Homeworld 2 backgrounds using OpenGL-based visualization.
'''
from OpenGL.extensions import alternate
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GL.NV.primitive_restart import *
from OpenGL.GLU import *
from parse_bg import parse_bg, PRIM_TRIANGLE_STRIP, PRIM_TRIANGLES
from transformations import Arcball, quaternion_slerp
import ctypes
import glfw
import numpy
import os
import time

window = 0
width, height = 500, 400
wireframe_mode = False
quit_flag = False
slow_flag = False
rotation_speed = 1.0
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

def error_callback(code, message):
    print(f'{code} {message.decode()}')

def window_size_callback(window, w, h):
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

def advance_time(deltatime):
    global animate
    if animate is not None:
        # Continue in auto-spin if arcball not active
        animate[2] += deltatime * 20.0
        arcball._qnow = quaternion_slerp(animate[0], animate[1], animate[2], False) 

def key_callback(window, key, scancode, action, mods):
    '''
    Keyboard: w for wireframe mode
    '''
    global wireframe_mode, slow_flag, quit_flag
    if action == glfw.PRESS and mods == 0:
        if key == glfw.KEY_W:
            wireframe_mode = not wireframe_mode
        if key == glfw.KEY_S:
            slow_flag = not slow_flag
        elif key == glfw.KEY_ESCAPE:
            quit_flag = True

def mouse_button_callback(window, button, action, mods):
    global animate
    (x, y) = glfw.get_cursor_pos(window)
    if button == 0 and mods == 0:
        arcball.active = (action == glfw.PRESS)
        if arcball.active:
            arcball.down([x,y])
            animate = None
        elif numpy.allclose(arcball._qpre, arcball._qnow): # effectively no animation, save CPU cycles
            animate = None
        else:
            animate = [arcball._qpre, arcball._qnow, 1.0]

def cursor_pos_callback(window, x, y):
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
                raise ValueError(f'Unknown primitive type {typ}')

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
    if glInitGl31VERSION() and glPrimitiveRestartIndex: # 3.1+
        primitive_restart_mode = PRIMITIVE_RESTART_CORE
    elif glPrimitiveRestartNV:
        primitive_restart_mode = PRIMITIVE_RESTART_NV
    else:
        print("Warning: Primitive restart not supported, falling back to slow path")

def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description="Homeworld 2 background viewer")
    parser.add_argument('filename', metavar='FILENAME.HOD', help='Name of background mesh')
    return parser.parse_args()

def main():
    global animate, quit_flag, slow_flag

    args = parse_arguments()
    # fetch data
    bgdata = parse_bg(args.filename)

    # initialization
    if not glfw.init():
        return

    glfw.set_error_callback(error_callback)

    window = glfw.create_window(width, height, "homeworld2 background: " + os.path.basename(args.filename), None, None)
    if not window:
        print('Could not create GLFW window')
        glfw.terminate()
        return

    glfw.set_window_size_callback(window, window_size_callback)
    glfw.set_key_callback(window, key_callback)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_pos_callback)

    glfw.make_context_current(window)

    probe_extensions()
    print(f"Primitive restart mode: {['NONE','CORE','NV'][primitive_restart_mode]}")
    create_shaders()
    bgdata = concatenate_primitives(bgdata)
    create_vbos(bgdata)

    window_size_callback(window, *glfw.get_window_size(window))
    lasttime = glfw.get_time()

    while not glfw.window_should_close(window) and not quit_flag:
        draw()
        glfw.swap_buffers(window)

        timescale = 1.0
        if animate is not None:
            if slow_flag:
                glfw.wait_events_timeout(1)
                timescale = 0.005
            else:
                glfw.poll_events()
        else:
            glfw.wait_events()

        curtime = glfw.get_time()
        advance_time((curtime - lasttime) * timescale)
        lasttime = curtime

if __name__ == '__main__':
    main()
