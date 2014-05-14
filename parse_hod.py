#!/usr/bin/python
# Dump hod file...
from __future__ import division, print_function 
import struct

filename='background/m01/m01.hod'
#filename='background/planet/planet.hod'

NESTED={'BGMS'}

PRIM_TRIANGLE_STRIP = 514
PRIM_TRIANGLES = 518

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
    version, = struct.unpack('>I', data[0:4])
    #print('---------------------------------')
    #print('Version', version)
    lod,num,mat,vertmask,numverts = struct.unpack('<IIIII', data[4:24])
    #print('LOD', lod)
    #print('num', num)
    #print('mat', mat)
    #print('vertmask', vertmask)
    #print('numverts', numverts)
    ofs = 24
    vertices = []
    for x in range(0, numverts):
        d = struct.unpack('<ffffBBBB', data[ofs:ofs+4*5])
        ofs += 4 * 5
        vertices.append(d)
    numfacelists, = struct.unpack('<H', data[ofs:ofs+2])
    #print('numfacelists', numfacelists)
    ofs += 2
    facelists = []
    for x in range(0, numfacelists):
        listtype,listcount = struct.unpack('<II', data[ofs:ofs+8])
        ofs += 8
        #print('List', listtype) # 514 strip / 518 list
        #print('  Count', listcount)
        flist = []
        for y in range(0, listcount):
            d, = struct.unpack('<H', data[ofs:ofs+2])
            flist.append(d)
            ofs += 2
        #print(flist)
        facelists.append((listtype, flist))
    #print('---------------------------------')
    return (vertices, facelists)

def parse_block(data, nesting=0):
    ofs = 0
    while ofs < len(data):
        outer_blkid = data[ofs:ofs+4]
        ofs += 4
        indent = ' ' * (nesting * 2)

        size, = struct.unpack('>I', data[ofs:ofs+4])
        ofs += 4

        blkid = data[ofs:ofs+4] # form has nested blkid
        ofs += 4
        size -= 4
        print(indent + outer_blkid + ' (' + blkid + ') size:' + str(size))

        inner = data[ofs:ofs+size]
        if blkid in NESTED:
            parse_block(inner, nesting+1)
        if blkid == 'BMSH':
            bmsh = parse_BMSH(inner)
        ofs += size

f = open(filename, 'rb')
parse_block(f.read())
f.close()

