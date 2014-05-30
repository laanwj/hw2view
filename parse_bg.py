#!/usr/bin/python
# Copyright (c) 2014 Wladimir J. van der Laan
# Distributed under the MIT/X11 software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
'''Parse homeworld 2 background'''
from __future__ import division, print_function 
import struct

NESTED={'BGMS'}

PRIM_TRIANGLES = 514
PRIM_TRIANGLE_STRIP = 518

def parse_BMSH(data):
    '''
    "NRML"
    <num bytes for this form>, {ulong}
    "BMSH"
    <version, of this BasicMesh.
     Note: This should ALWAYS be 1400 (type doesn't matter), big endian(BE)> {ulong}
    <lod of the mesh(es), Little Endian(LE)> {ulong}
    <number of mesh(es) in this BMSH form, LE> {ulong}
    <STAT(material) number used, probably LE> {ulong}
    <vertex mask, this is 27 for Normal MULTi-meshes, and 11 if the vertex data only has X Y Z co-ords (no normals, UVs, of Colours) (ie not a background), LE > {ulong} ???
    <num vertices in this part, LE> {ulong}
    <vertex data...>
    <num face lists\strips, LE>, {ulong}
    <face list data...>
    ---- vtxd ----
    <co-ords, LE> {float, ie single}
    <filler1, always 1, LE> {float, ie single}
    <vertex normal, LE> {float, ie single}
    <filler2, always 1, LE> {float, ie single}
    <uv coords> {float, ie single}
    ---- end ----
    ---- facd ----
    <type of facelists, 514( (optimized?) strips) OR 518(lists), LE>, {ulong}
    <number of faces this this list, not faces, but entries,
      for lists, this is numFaces * 3, for strips, this is, should be, numFaces - 2, LE>, {ulong}
    <face list, in triplets, LE>, ushort (Important!!! This starts from zero! wOBJ starts from 1!)
      (Strips are a bit... different that lists, Stay Sharp)
    ---- end ---- 
    '''
    # From: http://forums.relicnews.com/showthread.php?99226-HOD-File-Format-%28Regardless-of-type%29
    version, = struct.unpack('>I', data[0:4])
    #print('---------------------------------')
    #print('Version', version)
    lod,num,mat,vertsize,numverts = struct.unpack('<IIIII', data[4:24])
    #print('LOD', lod)
    #print('num', num)
    #print('mat', mat)
    #print('vertmask', vertmask)
    #print('numverts', numverts)
    ofs = 24
    vertsize *= 4
    vertdata = data[ofs:ofs+vertsize*numverts]
    ofs += vertsize*numverts
    numfacelists, = struct.unpack('<H', data[ofs:ofs+2])
    #print('numfacelists', numfacelists)
    ofs += 2
    facelists = []
    for x in range(0, numfacelists):
        listtype,listcount = struct.unpack('<II', data[ofs:ofs+8])
        ofs += 8
        if listtype == PRIM_TRIANGLES:
            assert((listcount % 3)==0)
        elif listtype == PRIM_TRIANGLE_STRIP:
            assert(listcount >= 3) # at least one full triangle
        fdata = data[ofs:ofs+2*listcount]
        ofs += 2*listcount
        facelists.append((listtype, listcount, fdata))
    #print('---------------------------------')
    return (numverts, vertsize, vertdata, facelists)

class BackgroundParser(object):
    def __init__(self):
        self.bmshes = []

    def parse_block(self, data, nesting=0):
        ofs = 0
        while ofs < len(data):
            outer_blkid = data[ofs:ofs+4]
            ofs += 4

            size, = struct.unpack('>I', data[ofs:ofs+4])
            ofs += 4

            blkid = data[ofs:ofs+4] # form has nested blkid
            ofs += 4
            size -= 4

            inner = data[ofs:ofs+size]
            if blkid in NESTED:
                self.parse_block(inner, nesting+1)
            if blkid == 'BMSH':
                bmsh = parse_BMSH(inner)
                self.bmshes.append(bmsh)
            ofs += size

def parse_bg(filename):
    parser = BackgroundParser()
    f = open(filename, 'rb')
    parser.parse_block(f.read())
    f.close()
    return parser.bmshes

