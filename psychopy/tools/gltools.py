#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OpenGL related helper functions.

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import ctypes
import array
from io import StringIO
from collections import namedtuple, OrderedDict
import pyglet.gl as GL  # using Pyglet for now
from contextlib import contextmanager
from PIL import Image
import numpy as np
import os, sys

# compatible Numpy and OpenGL types for common GL type enums
GL_COMPAT_TYPES = {
    GL.GL_FLOAT: (np.float32, GL.GLfloat),
    GL.GL_DOUBLE: (np.float64, GL.GLdouble),
    GL.GL_UNSIGNED_SHORT: (np.uint16, GL.GLushort),
    GL.GL_UNSIGNED_INT: (np.uint32, GL.GLuint),
    GL.GL_INT: (np.int32, GL.GLint),
    GL.GL_SHORT: (np.int16, GL.GLshort),
    GL.GL_HALF_FLOAT: (np.float16, GL.GLhalfARB),
    GL.GL_UNSIGNED_BYTE: (np.uint8, GL.GLubyte),
    GL.GL_BYTE: (np.int8, GL.GLbyte),
    np.float32: (GL.GL_FLOAT, GL.GLfloat),
    np.float64: (GL.GL_DOUBLE, GL.GLdouble),
    np.uint16: (GL.GL_UNSIGNED_SHORT, GL.GLushort),
    np.uint32: (GL.GL_UNSIGNED_INT, GL.GLuint),
    np.int32: (GL.GL_INT, GL.GLint),
    np.int16: (GL.GL_SHORT, GL.GLshort),
    np.float16: (GL.GL_HALF_FLOAT, GL.GLhalfARB),
    np.uint8: (GL.GL_UNSIGNED_BYTE, GL.GLubyte),
    np.int8: (GL.GL_BYTE, GL.GLbyte)
}


# -------------------------------
# Shader Program Helper Functions
# -------------------------------
#


def createProgram():
    """Create an empty program object for shaders.

    Returns
    -------
    int
        OpenGL program object handle retrieved from a `glCreateProgram` call.

    Examples
    --------
    Building a program with vertex and fragment shader attachments::

        myProgram = createProgram()  # new shader object

        # compile vertex and fragment shader sources
        vertexShader = compileShader(vertShaderSource, GL.GL_VERTEX_SHADER)
        fragmentShader = compileShader(fragShaderSource, GL.GL_FRAGMENT_SHADER)

        # attach shaders to program
        attachShader(myProgram, vertexShader)
        attachShader(myProgram, fragmentShader)

        # link the shader, makes `myProgram` attachments executable by their
        # respective processors and available for use
        linkProgram(myProgram)

        # optional, validate the program
        validateProgram(myProgram)

        # optional, detach and discard shader objects
        detachShader(myProgram, vertexShader)
        detachShader(myProgram, fragmentShader)

        deleteObject(vertexShader)
        deleteObject(fragmentShader)

    You can install the program for use in the current rendering state by
    calling::

        useProgram(myShader) # OR glUseProgram(myShader)
        # set uniforms/attributes and start drawing here ...

    """
    return GL.glCreateProgram()


def createProgramObjectARB():
    """Create an empty program object for shaders.

    This creates an *Architecture Review Board* (ARB) program variant which is
    compatible with older GLSL versions and OpenGL coding practices (eg.
    immediate mode) on some platforms. Use *ARB variants of shader helper
    functions (eg. `compileShaderObjectARB` instead of `compileShader`) when
    working with these ARB program objects. This was included for legacy support
    of existing PsychoPy shaders. However, it is recommended that you use
    :func:`createShader` and follow more recent OpenGL design patterns for new
    code (if possible of course).

    Returns
    -------
    int
        OpenGL program object handle retrieved from a `glCreateProgramObjectARB`
        call.

    Examples
    --------
    Building a program with vertex and fragment shader attachments::

        myProgram = createProgramObjectARB()  # new shader object

        # compile vertex and fragment shader sources
        vertexShader = compileShaderObjectARB(
            vertShaderSource, GL.GL_VERTEX_SHADER_ARB)
        fragmentShader = compileShaderObjectARB(
            fragShaderSource, GL.GL_FRAGMENT_SHADER_ARB)

        # attach shaders to program
        attachObjectARB(myProgram, vertexShader)
        attachObjectARB(myProgram, fragmentShader)

        # link the shader, makes `myProgram` attachments executable by their
        # respective processors and available for use
        linkProgramObjectARB(myProgram)

        # optional, validate the program
        validateProgramARB(myProgram)

        # optional, detach and discard shader objects
        detachObjectARB(myProgram, vertexShader)
        detachObjectARB(myProgram, fragmentShader)

        deleteObjectARB(vertexShader)
        deleteObjectARB(fragmentShader)

    Use the program in the current OpenGL state::

        useProgramObjectARB(myProgram)

    """
    return GL.glCreateProgramObjectARB()


def compileShader(shaderSrc, shaderType):
    """Compile shader GLSL code and return a shader object. Shader objects can
    then be attached to programs an made executable on their respective
    processors.

    Parameters
    ----------
    shaderSrc : str, list of str
        GLSL shader source code.
    shaderType : GLenum
        Shader program type (eg. `GL_VERTEX_SHADER`, `GL_FRAGMENT_SHADER`,
        `GL_GEOMETRY_SHADER`, etc.)

    Returns
    -------
    int
        OpenGL shader object handle retrieved from a `glCreateShader` call.

    Examples
    --------
    Compiling GLSL source code and attaching it to a program object::

        # GLSL vertex shader source
        vertexSource = \
            '''
            #version 330 core
            layout (location = 0) in vec3 vertexPos;

            void main()
            {
                gl_Position = vec4(vertexPos, 1.0);
            }
            '''
        # compile it, specifying `GL_VERTEX_SHADER`
        vertexShader = compileShader(vertexSource, GL.GL_VERTEX_SHADER)
        attachShader(myProgram, vertexShader)  # attach it to `myProgram`

    """
    shaderId = GL.glCreateShader(shaderType)

    if isinstance(shaderSrc, (list, tuple,)):
        nSources = len(shaderSrc)
        srcPtr = (ctypes.c_char_p * nSources)()
        srcPtr[:] = [i.encode() for i in shaderSrc]
    else:
        nSources = 1
        srcPtr = ctypes.c_char_p(shaderSrc.encode())

    GL.glShaderSource(
        shaderId,
        nSources,
        ctypes.cast(
            ctypes.byref(srcPtr),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_char))),
        None)
    GL.glCompileShader(shaderId)

    result = GL.GLint()
    GL.glGetShaderiv(
        shaderId, GL.GL_COMPILE_STATUS, ctypes.byref(result))

    if result.value == GL.GL_FALSE:  # failed to compile for whatever reason
        sys.stderr.write(getInfoLog(shaderId) + '\n')
        deleteObject(shaderId)
        raise RuntimeError("Shader compilation failed, check log output.")

    return shaderId


def compileShaderObjectARB(shaderSrc, shaderType):
    """Compile shader GLSL code and return a shader object. Shader objects can
    then be attached to programs an made executable on their respective
    processors.

    Parameters
    ----------
    shaderSrc : str, list of str
        GLSL shader source code text.
    shaderType : GLenum
        Shader program type. Must be *_ARB enums such as `GL_VERTEX_SHADER_ARB`,
        `GL_FRAGMENT_SHADER_ARB`, `GL_GEOMETRY_SHADER_ARB`, etc.

    Returns
    -------
    int
        OpenGL shader object handle retrieved from a `glCreateShaderObjectARB`
        call.

    """
    shaderId = GL.glCreateShaderObjectARB(shaderType)

    if isinstance(shaderSrc, (list, tuple,)):
        nSources = len(shaderSrc)
        srcPtr = (ctypes.c_char_p * nSources)()
        srcPtr[:] = [i.encode() for i in shaderSrc]
    else:
        nSources = 1
        srcPtr = ctypes.c_char_p(shaderSrc.encode())

    GL.glShaderSourceARB(
        shaderId,
        nSources,
        ctypes.cast(
            ctypes.byref(srcPtr),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_char))),
        None)
    GL.glCompileShaderARB(shaderId)

    result = GL.GLint()
    GL.glGetObjectParameterivARB(
        shaderId, GL.GL_OBJECT_COMPILE_STATUS_ARB, ctypes.byref(result))

    if result.value == GL.GL_FALSE:  # failed to compile for whatever reason
        sys.stderr.write(getInfoLog(shaderId) + '\n')
        deleteObjectARB(shaderId)
        raise RuntimeError("Shader compilation failed, check log output.")

    return shaderId


def embedShaderSourceDefs(shaderSrc, defs):
    """Embed preprocessor definitions into GLSL source code.

    This function generates and inserts ``#define`` statements into existing
    GLSL source code, allowing one to use GLSL preprocessor statements to alter
    program source at compile time.

    Passing ``{'MAX_LIGHTS': 8, 'NORMAL_MAP': False}`` to `defs` will create and
    insert the following ``#define`` statements into `shaderSrc`::

        #define MAX_LIGHTS 8
        #define NORMAL_MAP 0

    As per the GLSL specification, the ``#version`` directive must be specified
    at the top of the file before any other statement (with the exception of
    comments). If a ``#version`` directive is present, generated ``#define``
    statements will be inserted starting at the following line. If no
    ``#version`` directive is found in `shaderSrc`, the statements will be
    prepended to `shaderSrc`.

    Using preprocessor directives, multiple shader program routines can reside
    in the same source text if enclosed by ``#ifdef`` and ``#endif`` statements
    as shown here::

        #ifdef VERTEX
            // vertex shader code here ...
        #endif

        #ifdef FRAGMENT
            // pixel shader code here ...
        #endif

    Both the vertex and fragment shader can be built from the same GLSL code
    listing by setting either ``VERTEX`` or ``FRAGMENT`` as `True`::

        vertexShader = gltools.compileShaderObjectARB(
            gltools.embedShaderSourceDefs(glslSource, {'VERTEX': True}),
            GL.GL_VERTEX_SHADER_ARB)
        fragmentShader = gltools.compileShaderObjectARB(
            gltools.embedShaderSourceDefs(glslSource, {'FRAGMENT': True}),
            GL.GL_FRAGMENT_SHADER_ARB)

    In addition, ``#ifdef`` blocks can be used to prune render code paths. Here,
    this GLSL snippet shows a shader having diffuse color sampled from a texture
    is conditional on ``DIFFUSE_TEXTURE`` being `True`, if not, the material
    color is used instead::

        #ifdef DIFFUSE_TEXTURE
            uniform sampler2D diffuseTexture;
        #endif
        ...
        #ifdef DIFFUSE_TEXTURE
            // sample color from texture
            vec4 diffuseColor = texture2D(diffuseTexture, gl_TexCoord[0].st);
        #else
            // code path for no textures, just output material color
            vec4 diffuseColor = gl_FrontMaterial.diffuse;
        #endif

    This avoids needing to provide two separate GLSL program sources to build
    shaders to handle cases where a diffuse texture is or isn't used.

    Parameters
    ----------
    shaderSrc : str
        GLSL shader source code.
    defs : dict
       Names and values to generate ``#define`` statements. Keys must all be
       valid GLSL preprocessor variable names of type `str`. Values can only be
       `int`, `float`, `str`, `bytes`, or `bool` types. Boolean values `True`
       and `False` are converted to integers `1` and `0`, respectively.

    Returns
    -------
    str
        GLSL source code with ``#define`` statements inserted.

    Examples
    --------
    Defining ``MAX_LIGHTS`` as `8` in a fragment shader program at runtime::

        fragSrc = embedShaderSourceDefs(fragSrc, {'MAX_LIGHTS': 8})
        fragShader = compileShaderObjectARB(fragSrc, GL_FRAGMENT_SHADER_ARB)

    """
    # generate GLSL `#define` statements
    glslDefSrc = ""
    for varName, varValue in defs.items():
        if not isinstance(varName, str):
            raise ValueError("Definition name must be type `str`.")

        if isinstance(varValue, (int, bool, float,)):
            varValue = str(int(varValue))
        elif isinstance(varValue, bytes):
            varValue = varValue.decode('UTF-8')
        elif isinstance(varValue, str):
            pass  # nop
        else:
            raise TypeError("Invalid type for value of `{}`.".format(varName))

        glslDefSrc += '#define {n} "{v}"\n'.format(n=varName, v=varValue)

    # find where the `#version` directive occurs
    versionDirIdx = shaderSrc.find("#version")
    if versionDirIdx != -1:
        srcSplitIdx = shaderSrc.find("\n", versionDirIdx) + 1  # after newline
        srcOut = shaderSrc[:srcSplitIdx] + glslDefSrc + shaderSrc[srcSplitIdx:]
    else:
        # no version directive in source, just prepend defines
        srcOut = glslDefSrc + shaderSrc

    return srcOut


def deleteObject(obj):
    """Delete a shader or program object.

    Parameters
    ----------
    obj : int
        Shader or program object handle. Must have originated from a
        :func:`createProgram`, :func:`compileShader`, `glCreateProgram` or
        `glCreateShader` call.

    """
    if GL.glIsShader(obj):
        GL.glDeleteShader(obj)
    elif GL.glIsProgram(obj):
        GL.glDeleteProgram(obj)
    else:
        raise ValueError('Cannot delete, not a program or shader object.')


def deleteObjectARB(obj):
    """Delete a program or shader object.

    Parameters
    ----------
    obj : int
        Program handle to attach `shader` to. Must have originated from a
        :func:`createProgramObjectARB`, :func:`compileShaderObjectARB,
        `glCreateProgramObjectARB` or `glCreateShaderObjectARB` call.

    """
    GL.glDeleteObjectARB(obj)


def attachShader(program, shader):
    """Attach a shader to a program.

    Parameters
    ----------
    program : int
        Program handle to attach `shader` to. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call.
    shader : int
        Handle of shader object to attach. Must have originated from a
        :func:`compileShader` or `glCreateShader` call.

    """
    if not GL.glIsProgram(program):
        raise ValueError("Value `program` is not a program object.")
    elif not GL.glIsShader(shader):
        raise ValueError("Value `shader` is not a shader object.")
    else:
        GL.glAttachShader(program, shader)


def attachObjectARB(program, shader):
    """Attach a shader object to a program.

    Parameters
    ----------
    program : int
        Program handle to attach `shader` to. Must have originated from a
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call.
    shader : int
        Handle of shader object to attach. Must have originated from a
        :func:`compileShaderObjectARB` or `glCreateShaderObjectARB` call.

    """
    if not GL.glIsProgram(program):
        raise ValueError("Value `program` is not a program object.")
    elif not GL.glIsShader(shader):
        raise ValueError("Value `shader` is not a shader object.")
    else:
        GL.glAttachObjectARB(program, shader)


def detachShader(program, shader):
    """Detach a shader object from a program.

    Parameters
    ----------
    program : int
        Program handle to detach `shader` from. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call.
    shader : int
        Handle of shader object to detach. Must have been previously attached
        to `program`.

    """
    if not GL.glIsProgram(program):
        raise ValueError("Value `program` is not a program.")
    elif not GL.glIsShader(shader):
        raise ValueError("Value `shader` is not a shader object.")
    else:
        GL.glDetachShader(program, shader)


def detachObjectARB(program, shader):
    """Detach a shader object from a program.

    Parameters
    ----------
    program : int
        Program handle to detach `shader` from. Must have originated from a
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call.
    shader : int
        Handle of shader object to detach. Must have been previously attached
        to `program`.

    """
    if not GL.glIsProgram(program):
        raise ValueError("Value `program` is not a program.")
    elif not GL.glIsShader(shader):
        raise ValueError("Value `shader` is not a shader object.")
    else:
        GL.glDetachObjectARB(program, shader)


def linkProgram(program):
    """Link a shader program. Any attached shader objects will be made
    executable to run on associated GPU processor units when the program is
    used.

    Parameters
    ----------
    program : int
        Program handle to link. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call.

    Raises
    ------
    ValueError
        Specified `program` handle is invalid.
    RuntimeError
        Program failed to link. Log will be dumped to `sterr`.

    """
    if GL.glIsProgram(program):
        GL.glLinkProgram(program)
    else:
        raise ValueError("Value `program` is not a shader program.")

    # check for errors
    result = GL.GLint()
    GL.glGetProgramiv(program, GL.GL_LINK_STATUS, ctypes.byref(result))

    if result.value == GL.GL_FALSE:  # failed to link for whatever reason
        sys.stderr.write(getInfoLog(program) + '\n')
        raise RuntimeError(
            'Failed to link shader program. Check log output.')


def linkProgramObjectARB(program):
    """Link a shader program object. Any attached shader objects will be made
    executable to run on associated GPU processor units when the program is
    used.

    Parameters
    ----------
    program : int
        Program handle to link. Must have originated from a
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call.

    Raises
    ------
    ValueError
        Specified `program` handle is invalid.
    RuntimeError
        Program failed to link. Log will be dumped to `sterr`.

    """
    if GL.glIsProgram(program):
        GL.glLinkProgramARB(program)
    else:
        raise ValueError("Value `program` is not a shader program.")

    # check for errors
    result = GL.GLint()
    GL.glGetObjectParameterivARB(
        program,
        GL.GL_OBJECT_LINK_STATUS_ARB,
        ctypes.byref(result))

    if result.value == GL.GL_FALSE:  # failed to link for whatever reason
        sys.stderr.write(getInfoLog(program) + '\n')
        raise RuntimeError(
            'Failed to link shader program. Check log output.')


def validateProgram(program):
    """Check if the program can execute given the current OpenGL state.

    Parameters
    ----------
    program : int
        Handle of program to validate. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call.

    """
    # check validation info
    result = GL.GLint()
    GL.glValidateProgram(program)
    GL.glGetProgramiv(program, GL.GL_VALIDATE_STATUS, ctypes.byref(result))

    if result.value == GL.GL_FALSE:
        sys.stderr.write(getInfoLog(program) + '\n')
        raise RuntimeError('Shader program validation failed.')


def validateProgramARB(program):
    """Check if the program can execute given the current OpenGL state. If
    validation fails, information from the driver is dumped giving the reason.

    Parameters
    ----------
    program : int
        Handle of program object to validate. Must have originated from a
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call.

    """
    # check validation info
    result = GL.GLint()
    GL.glValidateProgramARB(program)
    GL.glGetObjectParameterivARB(
        program,
        GL.GL_OBJECT_VALIDATE_STATUS_ARB,
        ctypes.byref(result))

    if result.value == GL.GL_FALSE:
        sys.stderr.write(getInfoLog(program) + '\n')
        raise RuntimeError('Shader program validation failed.')


def useProgram(program):
    """Use a program object's executable shader attachments in the current
    OpenGL rendering state.

    In order to install the program object in the current rendering state, a
    program must have been successfully linked by calling :func:`linkProgram` or
    `glLinkProgram`.

    Parameters
    ----------
    program : int
        Handle of program to use. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call and was successfully
        linked. Passing `0` or `None` disables shader programs.

    Examples
    --------
    Install a program for use in the current rendering state::

        useProgram(myShader)

    Disable the current shader program by specifying `0`::

        useProgram(0)

    """
    if program is None:
        program = 0

    if GL.glIsProgram(program) or program == 0:
        GL.glUseProgram(program)
    else:
        raise ValueError('Specified `program` is not a program object.')


def useProgramObjectARB(program):
    """Use a program object's executable shader attachments in the current
    OpenGL rendering state.

    In order to install the program object in the current rendering state, a
    program must have been successfully linked by calling
    :func:`linkProgramObjectARB` or `glLinkProgramObjectARB`.

    Parameters
    ----------
    program : int
        Handle of program object to use. Must have originated from a
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call and
        was successfully linked. Passing `0` or `None` disables shader programs.

    Examples
    --------
    Install a program for use in the current rendering state::

        useProgramObjectARB(myShader)

    Disable the current shader program by specifying `0`::

        useProgramObjectARB(0)

    Notes
    -----
    Some drivers may support using `glUseProgram` for objects created by calling
    :func:`createProgramObjectARB` or `glCreateProgramObjectARB`.

    """
    if program is None:
        program = 0

    if GL.glIsProgram(program) or program == 0:
        GL.glUseProgramObjectARB(program)
    else:
        raise ValueError('Specified `program` is not a program object.')


def getInfoLog(obj):
    """Get the information log from a shader or program.

    This retrieves a text log from the driver pertaining to the shader or
    program. For instance, a log can report shader compiler output or validation
    results. The verbosity and formatting of the logs are platform-dependent,
    where one driver may provide more information than another.

    This function works with both standard and ARB program object variants.

    Parameters
    ----------
    obj : int
        Program or shader to retrieve a log from. If a shader, the handle must
        have originated from a :func:`compileShader`, `glCreateShader`,
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call. If a
        program, the handle must have came from a :func:`createProgram`,
        :func:`createProgramObjectARB`, `glCreateProgram` or
        `glCreateProgramObjectARB` call.

    Returns
    -------
    str
        Information log data. Logs can be empty strings if the driver has no
        information available.

    """
    logLength = GL.GLint()
    if GL.glIsShader(obj) == GL.GL_TRUE:
        GL.glGetShaderiv(
            obj, GL.GL_INFO_LOG_LENGTH, ctypes.byref(logLength))
    elif GL.glIsProgram(obj) == GL.GL_TRUE:
        GL.glGetProgramiv(
            obj, GL.GL_INFO_LOG_LENGTH, ctypes.byref(logLength))
    else:
        raise ValueError(
            "Specified value of `obj` is not a shader or program.")

    logBuffer = ctypes.create_string_buffer(logLength.value)
    GL.glGetShaderInfoLog(obj, logLength, None, logBuffer)

    return logBuffer.value.decode('UTF-8')


def getUniformLocations(program, builtins=False):
    """Get uniform names and locations from a given shader program object.

    This function works with both standard and ARB program object variants.

    Parameters
    ----------
    program : int
        Handle of program to retrieve uniforms. Must have originated from a
        :func:`createProgram`, :func:`createProgramObjectARB`, `glCreateProgram`
        or `glCreateProgramObjectARB` call.
    builtins : bool, optional
        Include built-in GLSL uniforms (eg. `gl_ModelViewProjectionMatrix`).
        Default is `False`.

    Returns
    -------
    dict
        Uniform names and locations.

    """
    if not GL.glIsProgram(program):
        raise ValueError(
            "Specified value of `program` is not a program object handle.")

    arraySize = GL.GLint()
    nameLength = GL.GLsizei()

    # cache uniform locations to avoid looking them up before setting them
    nUniforms = GL.GLint()
    GL.glGetProgramiv(program, GL.GL_ACTIVE_UNIFORMS, ctypes.byref(nUniforms))

    unifLoc = None
    if nUniforms.value > 0:
        maxUniformLength = GL.GLint()
        GL.glGetProgramiv(
            program,
            GL.GL_ACTIVE_UNIFORM_MAX_LENGTH,
            ctypes.byref(maxUniformLength))

        unifLoc = {}
        for uniformIdx in range(nUniforms.value):
            unifType = GL.GLenum()
            unifName = (GL.GLchar * maxUniformLength.value)()

            GL.glGetActiveUniform(
                program,
                uniformIdx,
                maxUniformLength,
                ctypes.byref(nameLength),
                ctypes.byref(arraySize),
                ctypes.byref(unifType),
                unifName)

            # get location
            loc = GL.glGetUniformLocation(program, unifName)
            # don't include if -1, these are internal types like 'gl_Vertex'
            if not builtins:
                if loc != -1:
                    unifLoc[unifName.value] = loc
            else:
                unifLoc[unifName.value] = loc

    return unifLoc


def getAttribLocations(program, builtins=False):
    """Get attribute names and locations from the specified program object.

    This function works with both standard and ARB program object variants.

    Parameters
    ----------
    program : int
        Handle of program to retrieve attributes. Must have originated from a
        :func:`createProgram`, :func:`createProgramObjectARB`, `glCreateProgram`
        or `glCreateProgramObjectARB` call.
    builtins : bool, optional
        Include built-in GLSL attributes (eg. `gl_Vertex`). Default is `False`.

    Returns
    -------
    dict
        Attribute names and locations.

    """
    if not GL.glIsProgram(program):
        raise ValueError(
            "Specified value of `program` is not a program object handle.")

    arraySize = GL.GLint()
    nameLength = GL.GLsizei()

    nAttribs = GL.GLint()
    GL.glGetProgramiv(program, GL.GL_ACTIVE_ATTRIBUTES, ctypes.byref(nAttribs))

    attribLoc = None
    if nAttribs.value > 0:
        maxAttribLength = GL.GLint()
        GL.glGetProgramiv(
            program,
            GL.GL_ACTIVE_ATTRIBUTE_MAX_LENGTH,
            ctypes.byref(maxAttribLength))

        attribLoc = {}
        for attribIdx in range(nAttribs.value):
            attribType = GL.GLenum()
            attribName = (GL.GLchar * maxAttribLength.value)()

            GL.glGetActiveAttrib(
                program,
                attribIdx,
                maxAttribLength,
                ctypes.byref(nameLength),
                ctypes.byref(arraySize),
                ctypes.byref(attribType),
                attribName)

            # get location
            loc = GL.glGetAttribLocation(program, attribName.value)
            # don't include if -1, these are internal types like 'gl_Vertex'
            if not builtins:
                if loc != -1:
                    attribLoc[attribName.value] = loc
            else:
                attribLoc[attribName.value] = loc

    return attribLoc

# -----------------------------------
# Framebuffer Objects (FBO) Functions
# -----------------------------------
#
# The functions below simplify the creation and management of Framebuffer
# Objects (FBOs). FBO are containers for image buffers (textures or
# renderbuffers) frequently used for off-screen rendering.
#

# FBO descriptor
Framebuffer = namedtuple(
    'Framebuffer',
    ['id',
     'target',
     'userData']
)


def createFBO(attachments=()):
    """Create a Framebuffer Object.

    Parameters
    ----------
    attachments : :obj:`list` or :obj:`tuple` of :obj:`tuple`
        Optional attachments to initialize the Framebuffer with. Attachments are
        specified as a list of tuples. Each tuple must contain an attachment
        point (e.g. GL_COLOR_ATTACHMENT0, GL_DEPTH_ATTACHMENT, etc.) and a
        buffer descriptor type (Renderbuffer or TexImage2D). If using a combined
        depth/stencil format such as GL_DEPTH24_STENCIL8, GL_DEPTH_ATTACHMENT
        and GL_STENCIL_ATTACHMENT must be passed the same buffer. Alternatively,
        one can use GL_DEPTH_STENCIL_ATTACHMENT instead. If using multisample
        buffers, all attachment images must use the same number of samples!. As
        an example, one may specify attachments as 'attachments=((
        GL.GL_COLOR_ATTACHMENT0, frameTexture), (GL.GL_DEPTH_STENCIL_ATTACHMENT,
        depthRenderBuffer))'.

    Returns
    -------
    :obj:`Framebuffer`
        Framebuffer descriptor.

    Notes
    -----
        - All buffers must have the same number of samples.
        - The 'userData' field of the returned descriptor is a dictionary that
          can be used to store arbitrary data associated with the FBO.
        - Framebuffers need a single attachment to be complete.

    Examples
    --------
    Create an empty framebuffer with no attachments::

        fbo = createFBO()  # invalid until attachments are added

    Create a render target with multiple color texture attachments::

        colorTex = createTexImage2D(1024,1024)  # empty texture
        depthRb = createRenderbuffer(800,600,internalFormat=GL.GL_DEPTH24_STENCIL8)

        # attach images
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo.id)
        attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
        attach(GL.GL_DEPTH_ATTACHMENT, depthRb)
        attach(GL.GL_STENCIL_ATTACHMENT, depthRb)
        # or attach(GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRb)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

        # above is the same as
        with useFBO(fbo):
            attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
            attach(GL.GL_DEPTH_ATTACHMENT, depthRb)
            attach(GL.GL_STENCIL_ATTACHMENT, depthRb)

    Examples of userData some custom function might access::

        fbo.userData['flags'] = ['left_eye', 'clear_before_use']

    Using a depth only texture (for shadow mapping?)::

        depthTex = createTexImage2D(800, 600,
                                    internalFormat=GL.GL_DEPTH_COMPONENT24,
                                    pixelFormat=GL.GL_DEPTH_COMPONENT)
        fbo = createFBO([(GL.GL_DEPTH_ATTACHMENT, depthTex)])  # is valid

        # discard FBO descriptor, just give me the ID
        frameBuffer = createFBO().id

    """
    fboId = GL.GLuint()
    GL.glGenFramebuffers(1, ctypes.byref(fboId))

    # create a framebuffer descriptor
    fboDesc = Framebuffer(fboId, GL.GL_FRAMEBUFFER, dict())

    # initial attachments for this framebuffer
    if attachments:
        with useFBO(fboDesc):
            for attachPoint, imageBuffer in attachments:
                attach(attachPoint, imageBuffer)

    return fboDesc


def attach(attachPoint, imageBuffer):
    """Attach an image to a specified attachment point on the presently bound
    FBO.

    Parameters
    ----------
    attachPoint :obj:`int`
        Attachment point for 'imageBuffer' (e.g. GL.GL_COLOR_ATTACHMENT0).
    imageBuffer : :obj:`TexImage2D` or :obj:`Renderbuffer`
        Framebuffer-attachable buffer descriptor.

    Returns
    -------
    None

    Examples
    --------
    Attach an image to attachment points on the framebuffer::

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo)
        attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
        attach(GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRb)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, lastBoundFbo)

        # same as above, but using a context manager
        with useFBO(fbo):
            attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
            attach(GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRb)

    """
    # We should also support binding GL names specified as integers. Right now
    # you need as descriptor which contains the target and name for the buffer.
    #
    if isinstance(imageBuffer, (TexImage2D, TexImage2DMultisample)):
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            attachPoint,
            imageBuffer.target,
            imageBuffer.id, 0)
    elif isinstance(imageBuffer, Renderbuffer):
        GL.glFramebufferRenderbuffer(
            GL.GL_FRAMEBUFFER,
            attachPoint,
            imageBuffer.target,
            imageBuffer.id)


def isComplete():
    """Check if the currently bound framebuffer is complete.

    Returns
    -------
    :obj:`bool'

    """
    return GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) == \
           GL.GL_FRAMEBUFFER_COMPLETE


def deleteFBO(fbo):
    """Delete a framebuffer.

    Returns
    -------
    :obj:`None'

    """
    GL.glDeleteFramebuffers(
        1, fbo.id if isinstance(fbo, Framebuffer) else int(fbo))


def blitFBO(srcRect, dstRect=None, filter=GL.GL_LINEAR):
    """Copy a block of pixels between framebuffers via blitting. Read and draw
    framebuffers must be bound prior to calling this function. Beware, the
    scissor box and viewport are changed when this is called to dstRect.

    Parameters
    ----------
    srcRect : :obj:`list` of :obj:`int`
        List specifying the top-left and bottom-right coordinates of the region
        to copy from (<X0>, <Y0>, <X1>, <Y1>).
    dstRect : :obj:`list` of :obj:`int` or :obj:`None`
        List specifying the top-left and bottom-right coordinates of the region
        to copy to (<X0>, <Y0>, <X1>, <Y1>). If None, srcRect is used for
        dstRect.
    filter : :obj:`int`
        Interpolation method to use if the image is stretched, default is
        GL_LINEAR, but can also be GL_NEAREST.

    Returns
    -------
    None

    Examples
    --------
    Blitting pixels from on FBO to another::

        # bind framebuffer to read pixels from
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, srcFbo)

        # bind framebuffer to draw pixels to
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, dstFbo)

        gltools.blitFBO((0,0,800,600), (0,0,800,600))

        # unbind both read and draw buffers
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    """
    # in most cases srcRect and dstRect will be the same.
    if dstRect is None:
        dstRect = srcRect

    # GL.glViewport(*dstRect)
    # GL.glEnable(GL.GL_SCISSOR_TEST)
    # GL.glScissor(*dstRect)
    GL.glBlitFramebuffer(srcRect[0], srcRect[1], srcRect[2], srcRect[3],
                         dstRect[0], dstRect[1], dstRect[2], dstRect[3],
                         GL.GL_COLOR_BUFFER_BIT,  # colors only for now
                         filter)

    # GL.glDisable(GL.GL_SCISSOR_TEST)


@contextmanager
def useFBO(fbo):
    """Context manager for Framebuffer Object bindings. This function yields
    the framebuffer name as an integer.

    Parameters
    ----------
    fbo :obj:`int` or :obj:`Framebuffer`
        OpenGL Framebuffer Object name/ID or descriptor.

    Yields
    -------
    int
        OpenGL name of the framebuffer bound in the context.

    Returns
    -------
    None

    Examples
    --------
    Using a framebuffer context manager::

        # FBO bound somewhere deep in our code
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, someOtherFBO)

        ...

        # create a new FBO, but we have no idea what the currently bound FBO is
        fbo = createFBO()

        # use a context to bind attachments
        with bindFBO(fbo):
            attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
            attach(GL.GL_DEPTH_ATTACHMENT, depthRb)
            attach(GL.GL_STENCIL_ATTACHMENT, depthRb)
            isComplete = gltools.isComplete()

        # someOtherFBO is still bound!

    """
    prevFBO = GL.GLint()
    GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(prevFBO))
    toBind = fbo.id if isinstance(fbo, Framebuffer) else int(fbo)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, toBind)
    try:
        yield toBind
    finally:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, prevFBO.value)


# ------------------------------
# Renderbuffer Objects Functions
# ------------------------------
#
# The functions below handle the creation and management of Renderbuffers
# Objects.
#

# Renderbuffer descriptor type
Renderbuffer = namedtuple(
    'Renderbuffer',
    ['id',
     'target',
     'width',
     'height',
     'internalFormat',
     'samples',
     'multiSample',  # boolean, check if a texture is multisample
     'userData']  # dictionary for user defined data
)


def createRenderbuffer(width, height, internalFormat=GL.GL_RGBA8, samples=1):
    """Create a new Renderbuffer Object with a specified internal format. A
    multisample storage buffer is created if samples > 1.

    Renderbuffers contain image data and are optimized for use as render
    targets. See https://www.khronos.org/opengl/wiki/Renderbuffer_Object for
    more information.

    Parameters
    ----------
    width : :obj:`int`
        Buffer width in pixels.
    height : :obj:`int`
        Buffer height in pixels.
    internalFormat : :obj:`int`
        Format for renderbuffer data (e.g. GL_RGBA8, GL_DEPTH24_STENCIL8).
    samples : :obj:`int`
        Number of samples for multi-sampling, should be >1 and power-of-two.
        Work with one sample, but will raise a warning.

    Returns
    -------
    :obj:`Renderbuffer`
        A descriptor of the created renderbuffer.

    Notes
    -----
    The 'userData' field of the returned descriptor is a dictionary that can
    be used to store arbitrary data associated with the buffer.

    """
    width = int(width)
    height = int(height)

    # create a new renderbuffer ID
    rbId = GL.GLuint()
    GL.glGenRenderbuffers(1, ctypes.byref(rbId))
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, rbId)

    if samples > 1:
        # determine if the 'samples' value is valid
        maxSamples = getIntegerv(GL.GL_MAX_SAMPLES)
        if (samples & (samples - 1)) != 0:
            raise ValueError('Invalid number of samples, must be power-of-two.')
        elif samples > maxSamples:
            raise ValueError('Invalid number of samples, must be <{}.'.format(
                maxSamples))

        # create a multisample render buffer storage
        GL.glRenderbufferStorageMultisample(
            GL.GL_RENDERBUFFER,
            samples,
            internalFormat,
            width,
            height)

    else:
        GL.glRenderbufferStorage(
            GL.GL_RENDERBUFFER,
            internalFormat,
            width,
            height)

    # done, unbind it
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)

    return Renderbuffer(rbId,
                        GL.GL_RENDERBUFFER,
                        width,
                        height,
                        internalFormat,
                        samples,
                        samples > 1,
                        dict())


def deleteRenderbuffer(renderBuffer):
    """Free the resources associated with a renderbuffer. This invalidates the
    renderbuffer's ID.

    Returns
    -------
    :obj:`None'

    """
    GL.glDeleteRenderbuffers(1, renderBuffer.id)


# -----------------
# Texture Functions
# -----------------

# 2D texture descriptor. You can 'wrap' existing texture IDs with TexImage2D to
# use them with functions that require that type as input.
#
#   texId = getTextureIdFromAPI()
#   texDesc = TexImage2D(texId, GL.GL_TEXTURE_2D, 1024, 1024)
#   attachFramebufferImage(fbo, texDesc, GL.GL_COLOR_ATTACHMENT0)
#   # examples of custom userData some function might access
#   texDesc.userData['flags'] = ['left_eye', 'clear_before_use']
#
TexImage2D = namedtuple(
    'TexImage2D',
    ['id',
     'target',
     'width',
     'height',
     'internalFormat',
     'pixelFormat',
     'dataType',
     'unpackAlignment',
     'samples',  # always 1
     'multisample',  # always False
     'userData'])


def createTexImage2D(width, height, target=GL.GL_TEXTURE_2D, level=0,
                     internalFormat=GL.GL_RGBA8, pixelFormat=GL.GL_RGBA,
                     dataType=GL.GL_FLOAT, data=None, unpackAlignment=4,
                     texParameters=()):
    """Create a 2D texture in video memory. This can only create a single 2D
    texture with targets GL_TEXTURE_2D or GL_TEXTURE_RECTANGLE.

    Parameters
    ----------
    width : :obj:`int`
        Texture width in pixels.
    height : :obj:`int`
        Texture height in pixels.
    target : :obj:`int`
        The target texture should only be either GL_TEXTURE_2D or
        GL_TEXTURE_RECTANGLE.
    level : :obj:`int`
        LOD number of the texture, should be 0 if GL_TEXTURE_RECTANGLE is the
        target.
    internalFormat : :obj:`int`
        Internal format for texture data (e.g. GL_RGBA8, GL_R11F_G11F_B10F).
    pixelFormat : :obj:`int`
        Pixel data format (e.g. GL_RGBA, GL_DEPTH_STENCIL)
    dataType : :obj:`int`
        Data type for pixel data (e.g. GL_FLOAT, GL_UNSIGNED_BYTE).
    data : :obj:`ctypes` or :obj:`None`
        Ctypes pointer to image data. If None is specified, the texture will be
        created but pixel data will be uninitialized.
    unpackAlignment : :obj:`int`
        Alignment requirements of each row in memory. Default is 4.
    texParameters : :obj:`list` of :obj:`tuple` of :obj:`int`
        Optional texture parameters specified as a list of tuples. These values
        are passed to 'glTexParameteri'. Each tuple must contain a parameter
        name and value. For example, texParameters=[(GL.GL_TEXTURE_MIN_FILTER,
        GL.GL_LINEAR), (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)]

    Returns
    -------
    :obj:`TexImage2D`
        A TexImage2D descriptor.

    Notes
    -----
    The 'userData' field of the returned descriptor is a dictionary that can
    be used to store arbitrary data associated with the texture.

    Previous textures are unbound after calling 'createTexImage2D'.

    Examples
    --------
    Creating a texture from an image file::

        import pyglet.gl as GL  # using Pyglet for now

        # empty texture
        textureDesc = createTexImage2D(1024, 1024, internalFormat=GL.GL_RGBA8)

        # load texture data from an image file using Pillow and NumPy
        from PIL import Image
        import numpy as np
        im = Image.open(imageFile)  # 8bpp!
        im = im.transpose(Image.FLIP_TOP_BOTTOM)  # OpenGL origin is at bottom
        im = im.convert("RGBA")
        pixelData = np.array(im).ctypes  # convert to ctypes!

        width = pixelData.shape[1]
        height = pixelData.shape[0]
        textureDesc = gltools.createTexImage2D(
            width,
            height,
            internalFormat=GL.GL_RGBA,
            pixelFormat=GL.GL_RGBA,
            dataType=GL.GL_UNSIGNED_BYTE,
            data=texture_array.ctypes,
            unpackAlignment=1,
            texParameters=[(GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR),
                           (GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)])

        GL.glBindTexture(GL.GL_TEXTURE_2D, textureDesc.id)

    """
    width = int(width)
    height = int(height)

    if width <= 0 or height <= 0:
        raise ValueError("Invalid image dimensions {} x {}.".format(
            width, height))

    if target == GL.GL_TEXTURE_RECTANGLE:
        if level != 0:
            raise ValueError("Invalid level for target GL_TEXTURE_RECTANGLE, "
                             "must be 0.")
        GL.glEnable(GL.GL_TEXTURE_RECTANGLE)

    colorTexId = GL.GLuint()
    GL.glGenTextures(1, ctypes.byref(colorTexId))
    GL.glBindTexture(target, colorTexId)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, int(unpackAlignment))
    GL.glTexImage2D(target, level, internalFormat,
                    width, height, 0,
                    pixelFormat, dataType, data)

    # apply texture parameters
    if texParameters:
        for pname, param in texParameters:
            GL.glTexParameteri(target, pname, param)

    GL.glBindTexture(target, 0)

    return TexImage2D(colorTexId,
                      target,
                      width,
                      height,
                      internalFormat,
                      pixelFormat,
                      dataType,
                      unpackAlignment,
                      1,
                      False,
                      dict())


# Descriptor for 2D mutlisampled texture
TexImage2DMultisample = namedtuple(
    'TexImage2D',
    ['id',
     'target',
     'width',
     'height',
     'internalFormat',
     'samples',
     'multisample',
     'userData'])


def createTexImage2DMultisample(width, height,
                                target=GL.GL_TEXTURE_2D_MULTISAMPLE, samples=1,
                                internalFormat=GL.GL_RGBA8, texParameters=()):
    """Create a 2D multisampled texture.

    Parameters
    ----------
    width : :obj:`int`
        Texture width in pixels.
    height : :obj:`int`
        Texture height in pixels.
    target : :obj:`int`
        The target texture (e.g. GL_TEXTURE_2D_MULTISAMPLE).
    samples : :obj:`int`
        Number of samples for multi-sampling, should be >1 and power-of-two.
        Work with one sample, but will raise a warning.
    internalFormat : :obj:`int`
        Internal format for texture data (e.g. GL_RGBA8, GL_R11F_G11F_B10F).
    texParameters : :obj:`list` of :obj:`tuple` of :obj:`int`
        Optional texture parameters specified as a list of tuples. These values
        are passed to 'glTexParameteri'. Each tuple must contain a parameter
        name and value. For example, texParameters=[(GL.GL_TEXTURE_MIN_FILTER,
        GL.GL_LINEAR), (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)]

    Returns
    -------
    :obj:`TexImage2DMultisample`
        A TexImage2DMultisample descriptor.

    """
    width = int(width)
    height = int(height)

    if width <= 0 or height <= 0:
        raise ValueError("Invalid image dimensions {} x {}.".format(
            width, height))

    # determine if the 'samples' value is valid
    maxSamples = getIntegerv(GL.GL_MAX_SAMPLES)
    if (samples & (samples - 1)) != 0:
        raise ValueError('Invalid number of samples, must be power-of-two.')
    elif samples <= 0 or samples > maxSamples:
        raise ValueError('Invalid number of samples, must be <{}.'.format(
            maxSamples))

    colorTexId = GL.GLuint()
    GL.glGenTextures(1, ctypes.byref(colorTexId))
    GL.glBindTexture(target, colorTexId)
    GL.glTexImage2DMultisample(
        target, samples, internalFormat, width, height, GL.GL_TRUE)

    # apply texture parameters
    if texParameters:
        for pname, param in texParameters:
            GL.glTexParameteri(target, pname, param)

    GL.glBindTexture(target, 0)

    return TexImage2DMultisample(colorTexId,
                                 target,
                                 width,
                                 height,
                                 internalFormat,
                                 samples,
                                 True,
                                 dict())


def deleteTexture(texture):
    """Free the resources associated with a texture. This invalidates the
    texture's ID.

    Returns
    -------
    :obj:`None'

    """
    GL.glDeleteTextures(1, texture.id)


# ---------------------------
# Vertex Buffer Objects (VBO)
# ---------------------------


#VertexBufferObject = namedtuple(
#    'VertexBufferObject',
#    ['id',
#     'size',
#     'count',
#     'indices',
#     'usage',
#     'dtype',
#     'userData']
#)

class VertexBufferInfo(object):
    """Vertex buffer object (VBO) descriptor.

    This class only stores information about the VBO it refers to, it does not
    contain any actual array data associated with the VBO. Calling
    :func:`createVBO` returns instances of this class.

    Parameters
    ----------
    name : GLuint or int
        OpenGL handle for the buffer.
    target : GLenum or int, optional
        Target used when binding the buffer (e.g. `GL_VERTEX_ARRAY` or
        `GL_ELEMENT_ARRAY_BUFFER`). Default is `GL_VERTEX_ARRAY`)
    usage : GLenum or int, optional
        Usage type for the array (i.e. `GL_STATIC_DRAW`).
    dataType : Glenum, optional
        Data type of array. Default is `GL_FLOAT`.
    size : int, optional
        Size of the buffer in bytes.
    stride : int, optional
        Number of bytes between adjacent attributes. If `0`, values are assumed
        to be tightly packed.
    shape : tuple or list, optional
        Shape of the array used to create this VBO.
    userData : dict, optional
        Optional user defined data associated with the VBO. If `None`,
        `userData` will be initialized as an empty dictionary.

    """
    __slots__ = ['name', 'target', 'usage', 'dataType',
                 'size', 'stride', 'shape', 'userData']

    def __init__(self,
                 name=0,
                 target=GL.GL_ARRAY_BUFFER,
                 usage=GL.GL_STATIC_DRAW,
                 dataType=GL.GL_FLOAT,
                 size=0,
                 stride=0,
                 shape=(0,),
                 userData=None):

        self.name = name
        self.target = target
        self.usage = usage
        self.dataType = dataType
        self.size = size
        self.stride = stride
        self.shape = shape

        if userData is None:
            self.userData = {}
        elif isinstance(userData, dict):
            self.userData = userData
        else:
            raise TypeError('Invalid type for `userData`.')

    def __eq__(self, other):
        """Equality test between VBO object names."""
        return self.name == other.name

    def __ne__(self, other):
        """Inequality test between VBO object names."""
        return self.name != other.name

    @property
    def hasBuffer(self):
        """Check if the VBO assigned to name is a buffer."""
        if self.name != 0 and GL.glIsBuffer(self.name):
            return True

        return False

    def validate(self):
        """Check if the data contained in this descriptor matches what is
        actually present in the OpenGL state.

        Returns
        -------
        bool
            `True` if the information contained in this descriptor matches the
            OpenGL state.

        """
        # fail automatically if these conditions are true
        if self.name == 0 or GL.glIsBuffer(self.name) != GL.GL_TRUE:
            return False

        # get current binding so we don't disturb the current state
        currentVBO = GL.GLint()

        if self.target == GL.GL_VERTEX_ARRAY:
            bindTarget = GL.GL_VERTEX_ARRAY_BINDING
        elif self.target == GL.GL_ELEMENT_ARRAY_BUFFER:
            bindTarget = GL.GL_ELEMENT_ARRAY_BUFFER_BINDING
        else:
            raise ValueError('Invalid `target` type.')

        GL.glGetIntegerv(bindTarget, ctypes.byref(currentVBO))

        # bind buffer at name to validate
        GL.glBindBuffer(self.target, self.name)

        # get buffer parameters
        actualSize = GL.GLint()
        GL.glGetBufferParameteriv(
            self.target, GL.GL_BUFFER_SIZE, ctypes.byref(actualSize))
        actualUsage = GL.GLint()
        GL.glGetBufferParameteriv(
            self.target, GL.GL_BUFFER_USAGE, ctypes.byref(actualUsage))

        # check values against those in this object
        isValid = False
        if self.usage == actualUsage and self.size == actualSize:
            isValid = True

        # return to the original binding
        GL.glBindBuffer(self.target, currentVBO)

        return isValid


def createVBO(data,
              target=GL.GL_ARRAY_BUFFER,
              dataType=GL.GL_FLOAT,
              usage=GL.GL_STATIC_DRAW):
    """Create an array buffer object (VBO).

    Creates a VBO using input data, usually as a `ndarray` or `list`. Attributes
    common to one vertex should occupy a single row of the `data` array.

    Parameters
    ----------
    data : array_like
        A 2D array of values to write to the array buffer. The data type of the
        VBO is inferred by the type of the array. If the input is a Python
        `list` or `tuple` type, the data type of the array will be `GL_FLOAT`.
    target : :obj:`int`
        Target used when binding the buffer (e.g. `GL_VERTEX_ARRAY` or
        `GL_ELEMENT_ARRAY_BUFFER`). Default is `GL_VERTEX_ARRAY`.
    dataType : Glenum, optional
        Data type of array. Input data will be recast to an appropriate type if
        necessary. Default is `GL_FLOAT`.
    usage : GLenum or int, optional
        Usage type for the array (i.e. `GL_STATIC_DRAW`).

    Returns
    -------
    VertexBufferInfo
        A descriptor with vertex buffer information.

    Examples
    --------
    Creating a vertex buffer object with vertex data::

        # vertices of a triangle
        verts = [[ 1.0,  1.0, 0.0],   # v0
                 [ 0.0, -1.0, 0.0],   # v1
                 [-1.0,  1.0, 0.0]]   # v2

        # load vertices to graphics device, return a descriptor
        vboDesc = createVBO(verts)

    Drawing triangles or quads using vertex buffer data::

        nIndices, vSize = vboDesc.shape  # element size

        glBindBuffer(GL_ARRAY_BUFFER, vboDesc.name)
        glVertexPointer(vSize, vboDesc.dataType, 0, None)
        glEnableClientState(GL_VERTEX_ARRAY)

        if vSize == 3:
            drawMode = GL_TRIANGLES
        elif vSize == 4:
            drawMode = GL_QUADS

        glDrawArrays(drawMode, 0, nIndices)
        glFlush()

    Custom data can be associated with this vertex buffer by specifying
    `userData`::

        myVBO = createVBO(data)
        myVBO.userData['startIdx'] = 14  # first index to draw with

        # use it later
        nIndices, vSize = vboDesc.shape  # element size
        startIdx = myVBO.userData['startIdx']
        endIdx = nIndices - startIdx
        glDrawArrays(GL_TRIANGLES, startIdx, endIdx)
        glFlush()

    """
    # build input array
    npType, glType = GL_COMPAT_TYPES[dataType]
    data = np.asarray(data, dtype=npType)

    # get buffer size and pointer
    bufferSize = data.size * ctypes.sizeof(glType)
    bufferStride = data.shape[1] * ctypes.sizeof(glType)
    bufferPtr = data.ctypes.data_as(ctypes.POINTER(glType))

    # create a vertex buffer ID
    bufferName = GL.GLuint()
    GL.glGenBuffers(1, ctypes.byref(bufferName))

    # bind and upload
    GL.glBindBuffer(target, bufferName)
    GL.glBufferData(target, bufferSize, bufferPtr, usage)
    GL.glBindBuffer(target, 0)

    vboInfo = VertexBufferInfo(
        bufferName,
        target,
        usage,
        dataType,
        bufferSize,
        bufferStride,
        data.shape)  # leave userData empty

    return vboInfo


def setVertexAttribPointer(index, vboInfo, offset=0, normalize=False, enable=True):
    """Define an array of vertex attribute data with a VBO descriptor.

    Parameters
    ----------
    index : int
        Index of the attribute to modify.
    vboInfo : VertexBufferInfo
        VBO descriptor.
    offset : int
        Starting index of the attribute in the buffer.
    normalize : bool
        Normalize fixed-point format values when accessed.
    enable : bool
        Enable the vertex attribute array after defining it. Note that you must
        call `glDisableVertexAttribArray` with `index` when done (unless this is
        being called within a presently bound VAO).

    Examples
    --------
    Define a generic attribute from a vertex buffer descriptor::

        # set the vertex location attribute
        setVertexAttribPointer(0, vboDesc)  # 0 is vertex in our shader
        GL.glColor3f(1.0, 0.0, 0.0)  # red triangle

        # draw the triangle
        nIndices, vSize = vboDesc.shape  # element size
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, nIndices)

    If our VBO has interleaved attributes, we can specify `offset` to account
    for this::

        # define vertex attributes
        verts = [[ -1.0, -1.0, 0.0],
                 [ -1.0,  1.0, 0.0],
                 [  1.0,  1.0, 0.0],
                 [  1.0, -1.0, 0.0]]
        texCoords = [[0.0, 0.0],
                     [0.0, 1.0],
                     [1.0, 1.0],
                     [1.0, 0.0]]
        normals = [[ 0.0, 0.0, 1.0],
                   [ 0.0, 0.0, 1.0],
                   [ 0.0, 0.0, 1.0],
                   [ 0.0, 0.0, 1.0]]

        # create interleaved array
        vertexAttribs = np.hstack([
            np.asarray(verts, dtype=np.float32),      # starts at 0
            np.asarray(texCoords, dtype=np.float32),  # starts at 3
            np.asarray(normals, dtype=np.float32)])   # starts at 5

        # create VBO
        vboInterleaved = createVBO(vertexAttribs)

        # ... before rendering, set the attribute pointers
        setVertexAttribPointer(0, vboInterleaved, offset=0)  # vertex pointer
        setVertexAttribPointer(1, vboInterleaved, offset=3)  # texture pointer
        setVertexAttribPointer(2, vboInterleaved, offset=5)  # normals pointer

        # draw the triangles
        nIndices, vSize = vboDesc.shape  # element size
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, nIndices)

        # call these when done if `enable=True`
        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        glDisableVertexAttribArray(2)

    """
    if vboInfo.target != GL.GL_ARRAY_BUFFER:
        raise ValueError('VBO must have `target` type `GL_ARRAY_BUFFER`.')

    _, glType = GL_COMPAT_TYPES[vboInfo.dataType]

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vboInfo.name)
    if enable:
        GL.glEnableVertexAttribArray(index)

    GL.glVertexAttribPointer(
        index,
        vboInfo.shape[1],
        vboInfo.dataType,
        GL.GL_TRUE if normalize else GL.GL_FALSE,
        vboInfo.stride,
        offset * ctypes.sizeof(glType))

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)


def deleteVBO(vbo):
    """Delete a vertex buffer object (VBO).

    Parameters
    ----------
    vbo : VertexBufferInfo
        Descriptor of VBO to delete.

    """
    if GL.glIsBuffer(vbo.name):
        GL.glDeleteBuffers(1, vbo.name)
        vbo.name = GL.GLuint(0)


def createVAO(vertexBuffers, indexBuffer=None):
    """Create a Vertex Array Object (VAO) with specified Vertex Buffer Objects.
    VAOs store buffer binding states, reducing CPU overhead when drawing objects
    with vertex data stored in VBOs.

    Parameters
    ----------
    vertexBuffers : :obj:`list` of :obj:`tuple`
        Specify vertex attributes VBO descriptors apply to.
    indexBuffer : :obj:`list` of :obj:`int`, optional
        Index array of elements. If provided, an element array is created from
        the array. The returned descriptor will have isIndexed=True. This
        requires the VAO be drawn with glDrawElements instead of glDrawArrays.

    Returns
    -------
    VertexArrayObject
        A descriptor with vertex array information.

    Examples
    --------
    Creating a VAO using VBOs::

        vaoDesc = createVAO(vboVerts, vboTexCoords, vboNormals)

    Draw the VAO, rendering the mesh::

        drawVAO(vaoDesc, GL.GL_TRIANGLES)

    """
    if not vertexBuffers:  # in case an empty list is passed
        raise ValueError("No buffers specified.")

    # create a vertex buffer ID
    vaoId = GL.GLuint()
    GL.glGenVertexArrays(1, ctypes.byref(vaoId))
    GL.glBindVertexArray(vaoId)

    nIndices = 0
    hasVertexArray = False
    for attr, vbo in vertexBuffers:
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo.id)
        if attr == GL.GL_VERTEX_ARRAY:
            GL.glVertexPointer(vbo.size, vbo.dtype, 0, None)
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            nIndices = int(vbo.indices / 3)
            hasVertexArray = True
        elif attr == GL.GL_TEXTURE_COORD_ARRAY:
            GL.glTexCoordPointer(vbo.size, vbo.dtype, 0, None)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        elif attr == GL.GL_NORMAL_ARRAY:
            GL.glNormalPointer(vbo.dtype, 0, None)
            GL.glEnableClientState(GL.GL_NORMAL_ARRAY)
        elif attr == GL.GL_COLOR_ARRAY:
            GL.glColorPointer(vbo.size, vbo.dtype, 0, None)
            GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        elif isinstance(attr, int):  # generic attributes
            GL.glVertexAttribPointer(
                attr, vbo.size, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
            GL.glEnableVertexAttribArray(attr)

    if not hasVertexArray:
        # delete the VAO we created
        GL.glBindVertexArray(0)
        GL.glDeleteVertexArrays(1, vaoId)
        raise RuntimeError("Failed to create VAO, no vertex data specified.")

    # bind the EBO if available
    if indexBuffer is not None:
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, indexBuffer.id)
        nIndices = indexBuffer.indices

    GL.glBindVertexArray(0)

    return VertexArrayObject(vaoId, nIndices, indexBuffer is not None, dict())


def drawVAO(vao, mode=GL.GL_TRIANGLES, flush=False):
    """Draw a vertex array using glDrawArrays. This method does not require
    shaders.

    Parameters
    ----------
    vao : :obj:`VertexArrayObject`
        Vertex Array Object (VAO) to draw.
    mode : :obj:`int`, optional
        Drawing mode to use (e.g. GL_TRIANGLES, GL_QUADS, GL_POINTS, etc.)
    flush : :obj:`bool`, optional
        Flush queued drawing commands before returning.

    Returns
    -------
    None

    Examples
    --------
    Creating a VAO and drawing it::

        vaoDesc = createVAO(vboVerts, vboTexCoords, vboNormals)

        # draw the VAO, renders the mesh
        drawVAO(vaoDesc, GL.GL_TRIANGLES)

    """
    # draw the array
    GL.glBindVertexArray(vao.id)

    if vao.isIndexed:
        GL.glDrawElements(mode, vao.indices, GL.GL_UNSIGNED_INT, None)
    else:
        GL.glDrawArrays(mode, 0, vao.indices)

    if flush:
        GL.glFlush()

    # reset
    GL.glBindVertexArray(0)


def deleteVAO(vao):
    """Delete a Vertex Array Object (VAO). This does not delete array buffers
    bound to the VAO.

    Returns
    -------
    :obj:`None'

    """
    GL.glDeleteVertexArrays(1, vao.id)


# -------------------------
# Material Helper Functions
# -------------------------
#
# Materials affect the appearance of rendered faces. These helper functions and
# datatypes simplify the creation of materials for rendering stimuli.
#

Material = namedtuple('Material', ['face', 'params', 'textures', 'userData'])


def createMaterial(params=(), textures=(), face=GL.GL_FRONT_AND_BACK):
    """Create a new material.

    Parameters
    ----------
    params : :obj:`list` of :obj:`tuple`, optional
        List of material modes and values. Each mode is assigned a value as
        (mode, color). Modes can be GL_AMBIENT, GL_DIFFUSE, GL_SPECULAR,
        GL_EMISSION, GL_SHININESS or GL_AMBIENT_AND_DIFFUSE. Colors must be
        a tuple of 4 floats which specify reflectance values for each RGBA
        component. The value of GL_SHININESS should be a single float. If no
        values are specified, an empty material will be created.
    textures :obj:`list` of :obj:`tuple`, optional
        List of texture units and TexImage2D descriptors. These will be written
        to the 'textures' field of the returned descriptor. For example,
        [(GL.GL_TEXTURE0, texDesc0), (GL.GL_TEXTURE1, texDesc1)]. The number of
        texture units per-material is GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS.
    face : :obj:`int`, optional
        Faces to apply material to. Values can be GL_FRONT_AND_BACK, GL_FRONT
        and GL_BACK. The default is GL_FRONT_AND_BACK.

    Returns
    -------
    Material
        A descriptor with material properties.

    Examples
    --------
    Creating a new material with given properties::

        # The values for the material below can be found at
        # http://devernay.free.fr/cours/opengl/materials.html

        # create a gold material
        gold = createMaterial([
            (GL.GL_AMBIENT, (0.24725, 0.19950, 0.07450, 1.0)),
            (GL.GL_DIFFUSE, (0.75164, 0.60648, 0.22648, 1.0)),
            (GL.GL_SPECULAR, (0.628281, 0.555802, 0.366065, 1.0)),
            (GL.GL_SHININESS, 0.4 * 128.0)])

    Use the material when drawing::

        useMaterial(gold)
        drawVAO( ... )  # all meshes will be gold
        useMaterial(None)  # turn off material when done

    Create a red plastic material, but define reflectance and shine later::

        red_plastic = createMaterial()

        # you need to convert values to ctypes!
        red_plastic.values[GL_AMBIENT] = (GLfloat * 4)(0.0, 0.0, 0.0, 1.0)
        red_plastic.values[GL_DIFFUSE] = (GLfloat * 4)(0.5, 0.0, 0.0, 1.0)
        red_plastic.values[GL_SPECULAR] = (GLfloat * 4)(0.7, 0.6, 0.6, 1.0)
        red_plastic.values[GL_SHININESS] = 0.25 * 128.0

        # set and draw
        useMaterial(red_plastic)
        drawVertexbuffers( ... )  # all meshes will be red plastic
        useMaterial(None)

    """
    # setup material mode/value slots
    matDesc = Material(
        face,
        {mode: None for mode in (
            GL.GL_AMBIENT,
            GL.GL_DIFFUSE,
            GL.GL_SPECULAR,
            GL.GL_EMISSION,
            GL.GL_SHININESS)},
        dict(),
        dict())
    if params:
        for mode, param in params:
            matDesc.params[mode] = \
                (GL.GLfloat * 4)(*param) \
                    if mode != GL.GL_SHININESS else GL.GLfloat(param)
    if textures:
        maxTexUnits = getIntegerv(GL.GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS)
        for unit, texDesc in textures:
            if unit <= GL.GL_TEXTURE0 + (maxTexUnits - 1):
                matDesc.textures[unit] = texDesc
            else:
                raise ValueError("Invalid texture unit enum.")

    return matDesc


def useMaterial(material, useTextures=True):
    """Use a material for proceeding vertex draws.

    Parameters
    ----------
    material : :obj:`Material` or None
        Material descriptor to use. Default material properties are set if None
        is specified. This is equivalent to disabling materials.
    useTextures : :obj:`bool`
        Enable textures. Textures specified in a material descriptor's 'texture'
        attribute will be bound and their respective texture units will be
        enabled. Note, when disabling materials, the value of useTextures must
        match the previous call. If there are no textures attached to the
        material, useTexture will be silently ignored.

    Returns
    -------
    None

    Notes
    -----
    1.  If a material mode has a value of None, a color with all components 0.0
        will be assigned.
    2.  Material colors and shininess values are accessible from shader programs
        after calling 'useMaterial'. Values can be accessed via built-in
        'gl_FrontMaterial' and 'gl_BackMaterial' structures (e.g.
        gl_FrontMaterial.diffuse).

    Examples
    --------
    Use a material when drawing::

        useMaterial(metalMaterials.gold)
        drawVAO( ... )  # all meshes drawn will be gold
        useMaterial(None)  # turn off material when done

    """
    if material is not None:
        # setup material color params
        for mode, param in material.params.items():
            if param is not None:
                GL.glMaterialfv(material.face, mode, param)
        # setup textures
        if useTextures and material.textures:
            GL.glEnable(GL.GL_TEXTURE_2D)
            for unit, desc in material.textures.items():
                GL.glActiveTexture(unit)
                GL.glColor4f(1.0, 1.0, 1.0, 1.0)
                GL.glColorMask(True, True, True, True)
                GL.glBindTexture(GL.GL_TEXTURE_2D, desc.id)
    else:
        for mode, param in defaultMaterial.params.items():
            GL.glMaterialfv(GL.GL_FRONT_AND_BACK, mode, param)
        if useTextures:
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glDisable(GL.GL_TEXTURE_2D)


# -------------------------
# Lighting Helper Functions
# -------------------------

Light = namedtuple('Light', ['params', 'userData'])


def createLight(params=()):
    """Create a point light source.

    """
    # setup light mode/value slots
    lightDesc = Light({mode: None for mode in (
        GL.GL_AMBIENT,
        GL.GL_DIFFUSE,
        GL.GL_SPECULAR,
        GL.GL_POSITION,
        GL.GL_SPOT_CUTOFF,
        GL.GL_SPOT_DIRECTION,
        GL.GL_SPOT_EXPONENT,
        GL.GL_CONSTANT_ATTENUATION,
        GL.GL_LINEAR_ATTENUATION,
        GL.GL_QUADRATIC_ATTENUATION)}, dict())

    # configure lights
    if params:
        for mode, value in params:
            if value is not None:
                if mode in [GL.GL_AMBIENT, GL.GL_DIFFUSE, GL.GL_SPECULAR,
                            GL.GL_POSITION]:
                    lightDesc.params[mode] = (GL.GLfloat * 4)(*value)
                elif mode == GL.GL_SPOT_DIRECTION:
                    lightDesc.params[mode] = (GL.GLfloat * 3)(*value)
                else:
                    lightDesc.params[mode] = GL.GLfloat(value)

    return lightDesc


def useLights(lights, setupOnly=False):
    """Use specified lights in successive rendering operations. All lights will
    be transformed using the present modelview matrix.

    Parameters
    ----------
    lights : :obj:`List` of :obj:`Light` or None
        Descriptor of a light source. If None, lighting is disabled.
    setupOnly : :obj:`bool`, optional
        Do not enable lighting or lights. Specify True if lighting is being
        computed via fragment shaders.

    """
    if lights is not None:
        if len(lights) > getIntegerv(GL.GL_MAX_LIGHTS):
            raise IndexError("Number of lights specified > GL_MAX_LIGHTS.")

        GL.glEnable(GL.GL_NORMALIZE)

        for index, light in enumerate(lights):
            enumLight = GL.GL_LIGHT0 + index
            # light properties
            for mode, value in light.params.items():
                if value is not None:
                    GL.glLightfv(enumLight, mode, value)

            if not setupOnly:
                GL.glEnable(enumLight)

        if not setupOnly:
            GL.glEnable(GL.GL_LIGHTING)
    else:
        # disable lights
        if not setupOnly:
            for enumLight in range(getIntegerv(GL.GL_MAX_LIGHTS)):
                GL.glDisable(GL.GL_LIGHT0 + enumLight)

            GL.glDisable(GL.GL_NORMALIZE)
            GL.glDisable(GL.GL_LIGHTING)


def setAmbientLight(color):
    """Set the global ambient lighting for the scene when lighting is enabled.
    This is equivalent to GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, color)
    and does not contribute to the GL_MAX_LIGHTS limit.

    Parameters
    ----------
    color : :obj:`tuple`
        Ambient lighting RGBA intensity for the whole scene.

    Notes
    -----
    If unset, the default value is (0.2, 0.2, 0.2, 1.0) when GL_LIGHTING is
    enabled.

    """
    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, (GL.GLfloat * 4)(*color))


# -------------------------
# 3D Model Helper Functions
# -------------------------
#
# These functions are used in the creation, manipulation and rendering of 3D
# model data.
#

# Header
WavefrontObj = namedtuple(
    'WavefrontObj',
    ['mtlFile',
     'drawGroups',
     'posBuffer',
     'texCoordBuffer',
     'normBuffer',
     'userData']
)


def loadObjFile(objFile):
    """Load a Wavefront OBJ file (*.obj).

    Parameters
    ----------
    objFile : :obj:`str`
        Path to the *.OBJ file to load.

    Returns
    -------
    WavefrontObjModel

    Notes
    -----
    1. This importer should work fine for most sanely generated files.
       Export your model with Blender for best results, even if you used some
       other package to create it.
    2. The model must be triangulated, quad faces are not supported.

    Examples
    --------
    Loading a *.OBJ mode from file::

        objModel = loadObjFile('/path/to/file.obj')

        # load the material (*.mtl) file, textures are also loaded
        materials = loadMtl('/path/to/' + objModel.mtlFile)

    Drawing a mesh previously loaded::

        # apply settings
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glDepthMask(GL.GL_TRUE)
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glCullFace(GL.GL_BACK)
        GL.glDisable(GL.GL_BLEND)

        # lights
        useLights(light0)

        # draw the model
        for group, vao in obj.drawGroups.items():
            useMaterial(materials[group])
            drawVAO(vao)

        # disable materials and lights
        useMaterial(None)
        useLights(None)

    """
    # open the file, read it into memory
    with open(objFile, 'r') as objFile:
        objBuffer = StringIO(objFile.read())

    nVertices = nTextureCoords = nNormals = nFaces = nObjects = nMaterials = 0
    matLibPath = None

    # first pass, examine the file
    for line in objBuffer.readlines():
        if line.startswith('v '):
            nVertices += 1
        elif line.startswith('vt '):
            nTextureCoords += 1
        elif line.startswith('vn '):
            nNormals += 1
        elif line.startswith('f '):
            nFaces += 1
        elif line.startswith('o '):
            nObjects += 1
        elif line.startswith('usemtl '):
            nMaterials += 1
        elif line.startswith('mtllib '):
            matLibPath = line.strip()[7:]

    # error check
    if nVertices == 0:
        raise RuntimeError(
            "Failed to load OBJ file, file contains no vertices.")

    objBuffer.seek(0)

    # attribute data lists
    positionDefs = []
    texCoordDefs = []
    normalDefs = []

    # attribute lists to upload
    vertexAttrList = []
    texCoordAttrList = []
    normalAttrList = []

    # store vertex attributes in dictionaries for easy re-mapping if needed
    vertexAttrs = OrderedDict()
    vertexIndices = OrderedDict()

    # group faces by material, each one will get its own VAO
    materialGroups = OrderedDict()
    materialOffsets = OrderedDict()

    # Parse the buffer for vertex attributes. We would like to create an index
    # buffer were there are no duplicate vertices. So we load attributes and
    # check if it's a duplicate against previously loaded attributes. If so, we
    # re-map it instead of creating a new attribute. Attributes are considered
    # equal if they share the same position, texture coordinate and normal.
    #
    vertexIdx = faceIdx = 0
    materialGroup = None
    for line in objBuffer.readlines():
        line = line.strip()

        if line.startswith('v '):  # new vertex position
            positionDefs.append(tuple(map(float, line[2:].split(' '))))
        elif line.startswith('vt '):  # new vertex texture coordinate
            texCoordDefs.append(tuple(map(float, line[3:].split(' '))))
        elif line.startswith('vn '):  # new vertex normal
            normalDefs.append(tuple(map(float, line[3:].split(' '))))
        elif line.startswith('f '):
            faceDef = []
            for attrs in line[2:].split(' '):
                # check if vertex attribute already loaded, create a new index
                # if not.
                if attrs not in vertexAttrs.keys():
                    p, t, n = map(int, attrs.split('/'))
                    # add to attribute lists
                    vertexAttrList.extend(positionDefs[p - 1])
                    texCoordAttrList.extend(texCoordDefs[t - 1])
                    normalAttrList.extend(normalDefs[n - 1])
                    vertexIndices[attrs] = vertexIdx
                    vertexIdx += 1
                faceDef.append(vertexIndices[attrs])  # attribute exists? remap
            materialGroups[materialGroup].extend(faceDef)
            faceIdx += 1  # for computing material offsets
        # elif line.startswith('o '):
        #    pass
        elif line.startswith('usemtl '):
            materialGroup = line[7:]
            if materialGroup not in materialGroups.keys():
                materialGroups[materialGroup] = []
                materialOffsets[materialGroup] = faceIdx

    # Load all vertex attribute data to the graphics device. If anyone cares,
    # try to make this work by interleaving attributes so we can read from a
    # single buffer. Regardless, we're using VAOs and EBOs when rendering
    # primitives which speeds things up considerably, so it's not needed right
    # now.
    #
    posVBO = createVBO(vertexAttrList)
    texVBO = createVBO(texCoordAttrList, 2)
    normVBO = createVBO(normalAttrList)

    # Create a VAO for each material in the file, each gets it own element
    # buffer array for indexed drawing.
    #
    objVAOs = {}
    for group, elements in materialGroups.items():
        objVAOs[group] = createVAO((
            (GL.GL_VERTEX_ARRAY, posVBO),
            (GL.GL_TEXTURE_COORD_ARRAY, texVBO),
            (GL.GL_NORMAL_ARRAY, normVBO)),
            createVBO(elements,
                      dtype=GL.GL_UNSIGNED_INT,
                      target=GL.GL_ELEMENT_ARRAY_BUFFER))

    return WavefrontObj(matLibPath, objVAOs, posVBO, texVBO, normVBO, dict())


def loadMtlFile(mtlFilePath, texParameters=None):
    """Load a material library (*.mtl).

    """
    # open the file, read it into memory
    with open(mtlFilePath, 'r') as mtlFile:
        mtlBuffer = StringIO(mtlFile.read())

    # default texture parameters
    if texParameters is None:
        texParameters = [(GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR),
                         (GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)]

    foundMaterials = {}
    foundTextures = {}
    thisMaterial = 0
    for line in mtlBuffer.readlines():
        line = line.strip()
        if line.startswith('newmtl '):  # new material
            thisMaterial = line[7:]
            foundMaterials[thisMaterial] = createMaterial()
        elif line.startswith('Ns '):  # specular exponent
            foundMaterials[thisMaterial].params[GL.GL_SHININESS] = \
                GL.GLfloat(float(line[3:]))
        elif line.startswith('Ks '):  # specular color
            foundMaterials[thisMaterial].params[GL.GL_SPECULAR] = \
                (GL.GLfloat * 4)(*list(map(float, line[3:].split(' '))) + [1.0])
        elif line.startswith('Kd '):  # diffuse color
            foundMaterials[thisMaterial].params[GL.GL_DIFFUSE] = \
                (GL.GLfloat * 4)(*list(map(float, line[3:].split(' '))) + [1.0])
        elif line.startswith('Ka '):  # ambient color
            foundMaterials[thisMaterial].params[GL.GL_AMBIENT] = \
                (GL.GLfloat * 4)(*list(map(float, line[3:].split(' '))) + [1.0])
        elif line.startswith('map_Kd '):  # diffuse color map
            # load a diffuse texture from file
            textureName = line[7:]
            if textureName not in foundTextures.keys():
                im = Image.open(
                    os.path.join(os.path.split(mtlFilePath)[0], textureName))
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                im = im.convert("RGBA")
                pixelData = np.array(im).ctypes
                width = pixelData.shape[1]
                height = pixelData.shape[0]
                foundTextures[textureName] = createTexImage2D(
                    width,
                    height,
                    internalFormat=GL.GL_RGBA,
                    pixelFormat=GL.GL_RGBA,
                    dataType=GL.GL_UNSIGNED_BYTE,
                    data=pixelData,
                    unpackAlignment=1,
                    texParameters=texParameters)
            foundMaterials[thisMaterial].textures[GL.GL_TEXTURE0] = \
                foundTextures[textureName]

    return foundMaterials


# -----------------------------
# Misc. OpenGL Helper Functions
# -----------------------------

def getIntegerv(parName):
    """Get a single integer parameter value, return it as a Python integer.

    Parameters
    ----------
    pName : :obj:`int'
        OpenGL property enum to query (e.g. GL_MAJOR_VERSION).

    Returns
    -------
    int

    """
    val = GL.GLint()
    GL.glGetIntegerv(parName, val)

    return int(val.value)


def getFloatv(parName):
    """Get a single float parameter value, return it as a Python float.

    Parameters
    ----------
    pName : :obj:`float'
        OpenGL property enum to query.

    Returns
    -------
    int

    """
    val = GL.GLfloat()
    GL.glGetFloatv(parName, val)

    return float(val.value)


def getString(parName):
    """Get a single string parameter value, return it as a Python UTF-8 string.

    Parameters
    ----------
    pName : :obj:`int'
        OpenGL property enum to query (e.g. GL_VENDOR).

    Returns
    -------
    str

    """
    val = ctypes.cast(GL.glGetString(parName), ctypes.c_char_p).value
    return val.decode('UTF-8')


# OpenGL information type
OpenGLInfo = namedtuple(
    'OpenGLInfo',
    ['vendor',
     'renderer',
     'version',
     'majorVersion',
     'minorVersion',
     'doubleBuffer',
     'maxTextureSize',
     'stereo',
     'maxSamples',
     'extensions',
     'userData'])


def getOpenGLInfo():
    """Get general information about the OpenGL implementation on this machine.
    This should provide a consistent means of doing so regardless of the OpenGL
    interface we are using.

    Returns are dictionary with the following fields:

        vendor, renderer, version, majorVersion, minorVersion, doubleBuffer,
        maxTextureSize, stereo, maxSamples, extensions

    Supported extensions are returned as a list in the 'extensions' field. You
    can check if a platform supports an extension by checking the membership of
    the extension name in that list.

    Returns
    -------
    OpenGLInfo

    """
    return OpenGLInfo(getString(GL.GL_VENDOR),
                      getString(GL.GL_RENDERER),
                      getString(GL.GL_VERSION),
                      getIntegerv(GL.GL_MAJOR_VERSION),
                      getIntegerv(GL.GL_MINOR_VERSION),
                      getIntegerv(GL.GL_DOUBLEBUFFER),
                      getIntegerv(GL.GL_MAX_TEXTURE_SIZE),
                      getIntegerv(GL.GL_STEREO),
                      getIntegerv(GL.GL_MAX_SAMPLES),
                      [i for i in getString(GL.GL_EXTENSIONS).split(' ')],
                      dict())


# ---------------------
# OpenGL/VRML Materials
# ---------------------
#
# A collection of pre-defined materials for stimuli. Keep in mind that these
# materials only approximate real-world equivalents. Values were obtained from
# http://devernay.free.fr/cours/opengl/materials.html (08/24/18). There are four
# material libraries to use, where individual material descriptors are accessed
# via property names.
#
# Usage:
#
#   useMaterial(metalMaterials.gold)
#   drawVAO(myObject)
#   ...
#
mineralMaterials = namedtuple(
    'mineralMaterials',
    ['emerald', 'jade', 'obsidian', 'pearl', 'ruby', 'turquoise'])(
    createMaterial(
        [(GL.GL_AMBIENT, (0.0215, 0.1745, 0.0215, 1.0)),
         (GL.GL_DIFFUSE, (0.07568, 0.61424, 0.07568, 1.0)),
         (GL.GL_SPECULAR, (0.633, 0.727811, 0.633, 1.0)),
         (GL.GL_SHININESS, 0.6 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.135, 0.2225, 0.1575, 1.0)),
         (GL.GL_DIFFUSE, (0.54, 0.89, 0.63, 1.0)),
         (GL.GL_SPECULAR, (0.316228, 0.316228, 0.316228, 1.0)),
         (GL.GL_SHININESS, 0.1 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.05375, 0.05, 0.06625, 1.0)),
         (GL.GL_DIFFUSE, (0.18275, 0.17, 0.22525, 1.0)),
         (GL.GL_SPECULAR, (0.332741, 0.328634, 0.346435, 1.0)),
         (GL.GL_SHININESS, 0.3 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.25, 0.20725, 0.20725, 1.0)),
         (GL.GL_DIFFUSE, (1, 0.829, 0.829, 1.0)),
         (GL.GL_SPECULAR, (0.296648, 0.296648, 0.296648, 1.0)),
         (GL.GL_SHININESS, 0.088 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.1745, 0.01175, 0.01175, 1.0)),
         (GL.GL_DIFFUSE, (0.61424, 0.04136, 0.04136, 1.0)),
         (GL.GL_SPECULAR, (0.727811, 0.626959, 0.626959, 1.0)),
         (GL.GL_SHININESS, 0.6 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.1, 0.18725, 0.1745, 1.0)),
         (GL.GL_DIFFUSE, (0.396, 0.74151, 0.69102, 1.0)),
         (GL.GL_SPECULAR, (0.297254, 0.30829, 0.306678, 1.0)),
         (GL.GL_SHININESS, 0.1 * 128.0)])
)

metalMaterials = namedtuple(
    'metalMaterials',
    ['brass', 'bronze', 'chrome', 'copper', 'gold', 'silver'])(
    createMaterial(
        [(GL.GL_AMBIENT, (0.329412, 0.223529, 0.027451, 1.0)),
         (GL.GL_DIFFUSE, (0.780392, 0.568627, 0.113725, 1.0)),
         (GL.GL_SPECULAR, (0.992157, 0.941176, 0.807843, 1.0)),
         (GL.GL_SHININESS, 0.21794872 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.2125, 0.1275, 0.054, 1.0)),
         (GL.GL_DIFFUSE, (0.714, 0.4284, 0.18144, 1.0)),
         (GL.GL_SPECULAR, (0.393548, 0.271906, 0.166721, 1.0)),
         (GL.GL_SHININESS, 0.2 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.25, 0.25, 0.25, 1.0)),
         (GL.GL_DIFFUSE, (0.4, 0.4, 0.4, 1.0)),
         (GL.GL_SPECULAR, (0.774597, 0.774597, 0.774597, 1.0)),
         (GL.GL_SHININESS, 0.6 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.19125, 0.0735, 0.0225, 1.0)),
         (GL.GL_DIFFUSE, (0.7038, 0.27048, 0.0828, 1.0)),
         (GL.GL_SPECULAR, (0.256777, 0.137622, 0.086014, 1.0)),
         (GL.GL_SHININESS, 0.1 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.24725, 0.1995, 0.0745, 1.0)),
         (GL.GL_DIFFUSE, (0.75164, 0.60648, 0.22648, 1.0)),
         (GL.GL_SPECULAR, (0.628281, 0.555802, 0.366065, 1.0)),
         (GL.GL_SHININESS, 0.4 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.19225, 0.19225, 0.19225, 1.0)),
         (GL.GL_DIFFUSE, (0.50754, 0.50754, 0.50754, 1.0)),
         (GL.GL_SPECULAR, (0.508273, 0.508273, 0.508273, 1.0)),
         (GL.GL_SHININESS, 0.4 * 128.0)])
)

plasticMaterials = namedtuple(
    'plasticMaterials',
    ['black', 'cyan', 'green', 'red', 'white', 'yellow'])(
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.01, 0.01, 0.01, 1.0)),
         (GL.GL_SPECULAR, (0.5, 0.5, 0.5, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0.1, 0.06, 1.0)),
         (GL.GL_DIFFUSE, (0.06, 0, 0.50980392, 1.0)),
         (GL.GL_SPECULAR, (0.50196078, 0.50196078, 0.50196078, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.1, 0.35, 0.1, 1.0)),
         (GL.GL_SPECULAR, (0.45, 0.55, 0.45, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.5, 0, 0, 1.0)),
         (GL.GL_SPECULAR, (0.7, 0.6, 0.6, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.55, 0.55, 0.55, 1.0)),
         (GL.GL_SPECULAR, (0.7, 0.7, 0.7, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.5, 0.5, 0, 1.0)),
         (GL.GL_SPECULAR, (0.6, 0.6, 0.5, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)])
)

rubberMaterials = namedtuple(
    'rubberMaterials',
    ['black', 'cyan', 'green', 'red', 'white', 'yellow'])(
    createMaterial(
        [(GL.GL_AMBIENT, (0.02, 0.02, 0.02, 1.0)),
         (GL.GL_DIFFUSE, (0.01, 0.01, 0.01, 1.0)),
         (GL.GL_SPECULAR, (0.4, 0.4, 0.4, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0.05, 0.05, 1.0)),
         (GL.GL_DIFFUSE, (0.4, 0.5, 0.5, 1.0)),
         (GL.GL_SPECULAR, (0.04, 0.7, 0.7, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0.05, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.4, 0.5, 0.4, 1.0)),
         (GL.GL_SPECULAR, (0.04, 0.7, 0.04, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.05, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.5, 0.4, 0.4, 1.0)),
         (GL.GL_SPECULAR, (0.7, 0.04, 0.04, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.05, 0.05, 0.05, 1.0)),
         (GL.GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0)),
         (GL.GL_SPECULAR, (0.7, 0.7, 0.7, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.05, 0.05, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.5, 0.5, 0.4, 1.0)),
         (GL.GL_SPECULAR, (0.7, 0.7, 0.04, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)])
)

# default material according to the OpenGL spec.
defaultMaterial = createMaterial(
    [(GL.GL_AMBIENT, (0.2, 0.2, 0.2, 1.0)),
     (GL.GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0)),
     (GL.GL_SPECULAR, (0.0, 0.0, 0.0, 1.0)),
     (GL.GL_EMISSION, (0.0, 0.0, 0.0, 1.0)),
     (GL.GL_SHININESS, 0)])
