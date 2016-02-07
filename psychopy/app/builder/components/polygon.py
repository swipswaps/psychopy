# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from os import path
from ._base import BaseVisualComponent, Param, getInitVals

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'polygon.png')
tooltip = _translate('Polygon: any regular polygon (line, triangle, square'
                     '...circle)')

# only use _localized values for label values, nothing functional:
_localized = {'nVertices': _translate('Num. vertices'),
              'fillColorSpace': _translate('Fill color-space'),
              'fillColor': _translate('Fill color'),
              'lineColorSpace': _translate('Line color-space'),
              'lineColor': _translate('Line color'),
              'lineWidth': _translate('Line width'),
              'interpolate': _translate('Interpolate'),
              'size': _translate("Size [w,h]")}


class PolygonComponent(BaseVisualComponent):
    """A class for presenting grating stimuli"""

    def __init__(self, exp, parentName, name='polygon', interpolate='linear',
                 units='from exp settings',
                 lineColor='$[1,1,1]', lineColorSpace='rgb', lineWidth=1,
                 fillColor='$[1,1,1]', fillColorSpace='rgb',
                 nVertices=4,
                 pos=(0, 0), size=(0.5, 0.5), ori=0,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        # initialise main parameters from base stimulus
        super(PolygonComponent, self).__init__(
            exp, parentName, name=name, units=units,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Polygon'
        self.url = "http://www.psychopy.org/builder/components/polygon.html"
        self.exp.requirePsychopyLibs(['visual'])
        self.order = ['nVertices']

        # params
        msg = ("How many vertices? 2=line, 3=triangle... (90 approximates a "
               "circle)")
        self.params['nVertices'] = Param(
            nVertices, valType='int',
            updates='constant',
            allowedUpdates=['constant'],
            hint=_translate(msg),
            label=_localized['nVertices'])

        msg = "Choice of color space for the fill color (rgb, dkl, lms, hsv)"
        self.params['fillColorSpace'] = Param(
            fillColorSpace,
            valType='str', allowedVals=['rgb', 'dkl', 'lms', 'hsv'],
            updates='constant',
            hint=_translate(msg),
            label=_localized['fillColorSpace'], categ='Advanced')

        msg = ("Fill color of this shape; Right-click to bring up a "
               "color-picker (rgb only)")
        self.params['fillColor'] = Param(
            fillColor, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate(msg),
            label=_localized['fillColor'], categ='Advanced')

        msg = "Choice of color space for the fill color (rgb, dkl, lms, hsv)"
        self.params['lineColorSpace'] = Param(
            lineColorSpace, valType='str',
            allowedVals=['rgb', 'dkl', 'lms', 'hsv'],
            updates='constant',
            hint=_translate(msg),
            label=_localized['lineColorSpace'], categ='Advanced')

        msg = ("Line color of this shape; Right-click to bring up a "
               "color-picker (rgb only)")
        self.params['lineColor'] = Param(
            lineColor, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate(msg),
            label=_localized['lineColor'], categ='Advanced')

        msg = ("Width of the shape's line (always in pixels - this does NOT "
               "use 'units')")
        self.params['lineWidth'] = Param(
            lineWidth, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate(msg),
            label=_localized['lineWidth'])

        msg = "How should the image be interpolated if/when rescaled"
        self.params['interpolate'] = Param(
            interpolate, valType='str', allowedVals=['linear', 'nearest'],
            updates='constant', allowedUpdates=[],
            hint=_translate(msg),
            label=_localized['interpolate'], categ='Advanced')

        msg = ("Size of this stimulus [w,h]. Note that for a line only the "
               "first value is used, for triangle and rect the [w,h] is as "
               "expected,\n but for higher-order polygons it represents the "
               "[w,h] of the ellipse that the polygon sits on!! ")
        self.params['size'] = Param(
            size, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate(msg),
            label=_localized['size'])

        del self.params['color']
        del self.params['colorSpace']

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params

        # replace variable params with defaults
        inits = getInitVals(self.params)
        if inits['size'].val == '1.0':
            inits['size'].val = '[1.0, 1.0]'

        if self.params['nVertices'].val == '2':
            code = ("%s = visual.Line(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    start=(-%(size)s[0]/2.0, 0), end=(+%(size)s[0]/2.0, 0),\n" % inits)
        elif self.params['nVertices'].val == '3':
            code = ("%s = visual.ShapeStim(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    vertices=[[-%(size)s[0]/2.0,-%(size)s[1]/2.0], [+%(size)s[0]/2.0,-%(size)s[1]/2.0], [0,%(size)s[1]/2.0]],\n" % inits)
        elif self.params['nVertices'].val == '4':
            code = ("%s = visual.Rect(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    width=%(size)s[0], height=%(size)s[1],\n" % inits)
        else:
            code = ("%s = visual.Polygon(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    edges=%s," % str(inits['nVertices'].val) +
                    " size=%(size)s,\n" % inits)

        code += ("    ori=%(ori)s, pos=%(pos)s,\n"
                 "    lineWidth=%(lineWidth)s, lineColor=%(lineColor)s, lineColorSpace=%(lineColorSpace)s,\n"
                 "    fillColor=%(fillColor)s, fillColorSpace=%(fillColorSpace)s,\n"
                 "    opacity=%(opacity)s, " % inits)

        depth = -self.getPosInRoutine()
        code += "depth=%.1f, " % depth

        if self.params['interpolate'].val == 'linear':
            code += "interpolate=True)\n"
        else:
            code += "interpolate=False)\n"

        buff.writeIndentedLines(code)
