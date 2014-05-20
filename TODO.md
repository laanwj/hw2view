- Port to GLES2
  pogles
  https://pypi.python.org/pypi/pogles/1.0
  pogles is a Python package that implements bindings for OpenGL ES v2.0 for Python v2.3 or later and Python v3. It comprises three modules:

Also: https://code.google.com/p/pyglesv2/

- Can we extract directly from the Homeworld2.big file?

- Set/unset automatic rotation
  Implement trackball rotation
  Set automatic rotation speed

- Switch to next background automatically?

- Optimizations
  - Number of bytes per vertex can be trivially brought down to 16 by using float3 vertices

  - There are 16 'submeshes', could determine which ones are visible using bounding boxes
    This may or may not save 

- Make FoV configurable
  I don't know what FoV the original homeworld 2 had
  45 degrees vertical FoV may be too narrow whereas 90 seems to be too wide

