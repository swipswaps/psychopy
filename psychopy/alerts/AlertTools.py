from psychopy.monitors import Monitor
from psychopy.tools import monitorunittools
from numpy import array
import ast


class TestWin(object):
    """
    Creates a false window with necessary attributes for converting component
    Parameters to pixels.
    """
    def __init__(self, exp, monitor):
        self.useRetina = True
        self.exp = exp
        self.monitor = Monitor(monitor)
        self.size = self.monitor.getSizePix()


def runTest(component):
    """
    Run integrity checks and sends output to the AlertLog system.

    Parameters
    ----------
    component : Component
        The PsychoPy component being tested
    """
    win = TestWin(component.exp, component.exp.settings.params['Monitor'].val)
    units = component.exp.settings.params['Units'].val
    testSize(component, win, units)
    testPos(component, win, units)

def convertParamToPix(value, win, units):
    """
    Convert value to numpy array
    Parameters
    ----------
    value : str, int, float, list, tuple
        Parameter value to be converted to pixels
    win : TestWin object
        A false window with necessary attributes for converting component
        parameters to pixels
    units : str
        Screen units

    Returns
    -------
    numpy array
        Parameter converted to pixels in numpy array
    """
    if isinstance(value, str):
        value = array(ast.literal_eval(value))
    else:
        value = array(value)
    return monitorunittools.convertToPix(value, array([0, 0]), units=units, win=win) * 2

def testSize(component, win, units):
    """
    Runs size testing for component

    Parameters
    ----------
    component: Component
        The component used for size testing
    win : TestWin object
        Used for testing component size in bounds
    units : str`
        Screen units
    """
    if 'size' not in component.params:
        return
    size = convertParamToPix(component.params['size'].val, win, units)

    # Test X
    if size[0] > win.size[0]:
        component.alerts.write(1001, component)
    # Test Y
    if size[1] > win.size[1]:
        component.alerts.write(1002, component)


def testPos(component, win, units):
    """
    Runs position testing for component

    Parameters
    ----------
    component: Component
        The component used for size testing
    win : TestWin object
        Used for testing component position in bounds
    units : str`
        Screen units
    """
    if 'pos' not in component.params:
        return
    pos = convertParamToPix(component.params['pos'].val, win, units)

    # Test X
    if pos[0] > win.size[0]:
        component.alerts.write(1003, component)
    # Test Y
    if pos[1] > win.size[1]:
        component.alerts.write(1004, component)



