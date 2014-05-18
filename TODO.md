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
  - Don't bother with the large amount of triangle strips, modern GPUs prefer a lower number of batches
    - glMultiDrawElements is ideally suited for this, it has existed in GL since 1.4
      but only exists as an extension in OpenGL ES2/3
    - Alternativel, use degenerate triangles
      A B C D E E F F G H I J
      This always works
    - Another alternative is primitive restart which exists in OpenGL 3.1+ as extension and 4.4 as 
      extension GL_ARB_ES3_compatibility
      It also exists in ES3 with "fixed index primitive restart" which always uses the highest number
      representable by the type (65535 in case of ushort).

      glEnable(GL_PRIMITIVE_RESTART)
      glPrimitiveRestartIndex()

  - There are 16 'submeshes', could determine which ones are visible using bounding boxes
    This may or may not save 
