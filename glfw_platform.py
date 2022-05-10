'''
Minimal GLFW platform for PyOpenGL. This looks up functions through GLFW
without any knowledge of the underlying platform.
'''
import ctypes
import glfw
from OpenGL.platform import baseplatform

class GLFWPlatform(baseplatform.BasePlatform):
    """GLFW platform"""
    GLES1 = None
    GLES2 = None
    GLES3 = None
    GL = None
    OpenGL = None
    # GLU, GLUT, GLE cannot be looked up through this platform.

    DEFAULT_FUNCTION_TYPE = staticmethod(ctypes.CFUNCTYPE)

    def constructFunction(self,
            functionName, dll,
            resultType=ctypes.c_int, argTypes=(),
            doc = None, argNames = (),
            extension = None,
            deprecated = False,
            module = None,
            force_extension = False,
            error_checker = None,
        ):
        return super().constructFunction(
            functionName, dll,
            resultType, argTypes,
            doc, argNames,
            extension,
            deprecated,
            module,
            True,  # Force lookup through getExtensionProcedure instead of cdll
            None)

    def getExtensionProcedure(self, procname):
        '''
        Look up function pointer for client API function.
        '''
        return glfw.get_proc_address(procname.decode())

    def GetCurrentContext(self):
        '''
        Return context. Must be a hashable value, so take the address.
        '''
        return ctypes.cast(glfw.get_current_context(), ctypes.c_void_p).value
