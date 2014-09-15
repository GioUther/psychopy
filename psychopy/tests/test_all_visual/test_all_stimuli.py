import sys, os, copy
from psychopy import visual, monitors, filters, prefs
from psychopy.tools.coordinatetools import pol2cart
from psychopy.tests import utils
import numpy
import pytest
import shutil
from tempfile import mkdtemp

import inspect

"""
Jonas' play area!
"""


def doAttributes(self, stimClass):
    """
    Draw a stimulus using all possible attributes and ways of setting them.
    
    STRUCTURE OF ATTRIBUTE SPECIFICATIONS:
    Set values for all attributes and operations to be tested. 
    The structure is this::
    
        ExampleAttrib = [  # list so that we can loop through them in a specified order
            {'attribute':'size',  # name of the attributeSetter
             'method':'setSize',  # name of corresponding setter method
             'init':90,  # a non-default init value
             'operations':[  # list so that we can loop through them in a specified order.
                 ('*', (1.2, 0.8)),  # should accept x,y-pair
                 ('/', 2)  # should accept scalar
             ]
             }
        ]
    """
    attribs = {}
    
    # For MinimalStim
    MinimalAttribs = [
        {'attribute':'name', 'method':None, 'init':'new init params', 'operations':[('', 'newer params!')]},
        {'attribute':'autoDraw', 'method':'setAutoDraw', 'init':False, 'operations':[]},
    ]
    
    # For WindowMixin. This is not applied here because shaders + units are inherited from window.
    WindowAttribs = [
        #{'attribute':'units', 'method':None, 'init':'pix', 'operations':[]}
    ]  # omit useShaders
    
    # For BaseVisualStim
    BaseVisualAttribs = MinimalAttribs + WindowAttribs + [
        {'attribute':'pos', 'method':'setPos', 'init':(0.1 * self.scaleFactor, 0.1 * self.scaleFactor), 'operations':[('-', (0.2 * self.scaleFactor, 0)), ('/', 2)]}, 
        {'attribute':'size', 'method':'setSize', 'init':1.2 * self.scaleFactor, 'operations':[('*', (1.2, 0.8)), ('/', 1.2)]},
        {'attribute':'ori', 'method':'setOri', 'init':45, 'operations':[('-', 160)]},
        {'attribute':'opacity', 'method':'setOpacity', 'init':0.9, 'operations':[('*', 0.8)]},
    ]
    
    # For ColorMixin
    ColorAttribs = [
        {'attribute':'colorSpace', 'method':None, 'init':'rgb255', 'operations':[('', 'rgb')]},
        {'attribute':'color', 'method':None, 'init':(255, 0, 255), 'operations':[('/', (255, 0, 512)), ('*', 0.8)]},
        {'attribute':'contrast', 'method':'setContrast', 'init':0.9, 'operations':[('-', 0.2)]}
    ]
    
    # For TextureMixin
    TextureAttribs = [
        {'attribute':'texRes', 'method':None, 'init': 16, 'operations':[('*', 2)]},
        {'attribute':'mask', 'method':'setMask', 'init':'raisedCos', 'operations':[('', 'gauss')]},
        {'attribute':'maskParams', 'method':None, 'init':{'fringeWidth':0.8, 'sd':1.5}, 'operations':[]}
    ]
    
    # For GratingStim
    attribs[visual.GratingStim] = BaseVisualAttribs + ColorAttribs + TextureAttribs + [
        {'attribute':'sf', 'method':'setSF', 'init':0.02 / self.scaleFactor, 'operations':[('+', 0.02 / self.scaleFactor)]},
        {'attribute':'phase', 'method':'setPhase', 'init':(0, 0.25), 'operations':[('+', 0.25), ('*', (2, 0))]},
        {'attribute':'tex', 'method':'setTex', 'init':'saw', 'operations':[('', 'sin')]}
    ]
    
    # For ShapeStim
    ShapeAttribsBase = BaseVisualAttribs + [
        {'attribute':'lineWidth', 'method':'setLineWidth', 'init':3, 'operations':[('*', 2)]},
        {'attribute':'lineColorSpace', 'method':None, 'init':'rgb', 'operations':[('', 'rgb')]},
        {'attribute':'lineColor', 'method':'setLineColor', 'init':(0, 0, 1), 'operations':[('', '#FF00FF')]},
        {'attribute':'fillColorSpace', 'method':None, 'init':'rgb255', 'operations':[('', 'rgb')]},
        {'attribute':'fillColor', 'method':'setFillColor', 'init':(0, 255, 0), 'operations':[('/', (1, 512, 1)), ('+', 0.5)]},
        {'attribute':'interpolate', 'method':None, 'init':False, 'operations':[('', True)]}
    ]
    # Vertices is specific to ShapeStim - does not make sense for Polygon, Circle and Rect
    attribs[visual.ShapeStim] = ShapeAttribsBase + [
        {'attribute':'vertices', 'method':'setVertices', 'init':numpy.array(([0.2,0.2], [0.5,0.5], [0.5,0.2], [0,-0.2])) * self.scaleFactor, 'operations':[('+', 0.3 * self.scaleFactor), ('-', numpy.array([[0.1, 0.1], [0.2, 0.2], [0.1, 0.2], [0, -0.1]]) * self.scaleFactor)]},
        {'attribute':'closeShape', 'method':None, 'init':False, 'operations':[]}
    ]
    
    # Adding tests for visual.Polygon, visual.Rect and visual.Circle - easy peacy
    attribs[visual.Polygon] = ShapeAttribsBase + [
        {'attribute':'radius', 'method':'setRadius', 'init':0.4 * self.scaleFactor, 'operations':[('+', 0.2 * self.scaleFactor)]},
        {'attribute':'edges', 'method':'setEdges', 'init':10, 'operations':[('+', 118)]}
    ]
    attribs[visual.Circle] = attribs[visual.Polygon]
    attribs[visual.Rect] = ShapeAttribsBase + [
        {'attribute':'width', 'method':'setWidth', 'init':0.8 * self.scaleFactor, 'operations':[('*', 1.2)]},
        {'attribute':'height', 'method':'setHeight', 'init':0.7 * self.scaleFactor, 'operations':[('*', 0.8)]}
    ]
    
    # PREPERATION
    # Get attributes for this stimulus
    attribList = attribs[stimClass]
    screenshotBaseName = stimClass.__name__ + '_' + self.contextName
    inits = dict([(attribute['attribute'], attribute['init']) for attribute in attribList])
    self.win.flip()  # clear window
    
    # Make a dictionary of default inits. If there's a parent class (self.parent), include those attributes as well in initsDefault.
    stim = stimClass(self.win)  # just to get the default init parameters. Is there another way?
    initsDefault = inspect.getcallargs(stim.__init__, self.win)
    try:
        stimParent = self.parent(self.win)
        initsParent = inspect.getcallargs(stimParent.__init__, self.win)
        initsDefault = dict(initsDefault.items() + initsParent.items())
    except:
        pass
    initsDefault.pop('self', None)
    initsDefault.pop('kwargs', None)

    # Scale params
    try:
        for param in self.scaleParams:
            initsDefault[param] *= self.scaleFactor
    except:
        pass
    # TEST 1: raw init (defaults)
    stim = stimClass(self.win)
    stim.draw()
    utils.compareScreenshot(screenshotBaseName + '_' + 'default.png', self.win)
    
    # intermezzo, now that we have the stimulus we chan check...
    str(stim)
    
    # TEST 2: non-default params set in init
    stim = stimClass(self.win, **inits)
    stim.draw()
    utils.compareScreenshot(screenshotBaseName + '_' + 'nondefault.png', self.win)
    
    # TEST 3: non-default params set using attributeSetters
    # e.g. stim.ori = 45
    stim = stimClass(self.win)
    for attrib in attribList:
        exec('stim.%s = %s' %(attrib['attribute'], attrib['init'].__repr__()))
    stim.draw()
    utils.compareScreenshot(screenshotBaseName + '_' + 'nondefault.png', self.win)
    
    # TEST 4: non-default params set using methods
    # e.g. stim.setOri(45)
    stim = stimClass(self.win)
    for attrib in attribList:
        if attrib['method']:
            exec('stim.%s(%s)' %(attrib['method'], attrib['init'].__repr__()))
        else:
            # Not implemented, use attributeSetter to get things going
            exec('stim.%s = %s' %(attrib['attribute'], attrib['init'].__repr__()))
    stim.draw()
    utils.compareScreenshot(screenshotBaseName + '_' + 'nondefault.png', self.win)
    
    # TEST 5: operations using attributeSetters
    # e.g. stim.ori += 90
    stim = stimClass(self.win, **inits)
    for attrib in attribList:
        for operation, value in attrib['operations']:
            exec('stim.%s %s= %s' %(attrib['attribute'], operation, value.__repr__()))
    stim.draw()
    utils.compareScreenshot(screenshotBaseName + '_' + 'operations.png', self.win)
    
    # TEST 6: operations using methods
    # e.g. stim.setOri(90, '+')
    stim = stimClass(self.win, **inits)
    for attrib in attribList:
        for operation, value in attrib['operations']:
            if attrib['method'] and operation:
                exec('stim.%s(%s, operation=%s)' %(attrib['method'], value.__repr__(), operation.__repr__()))
            elif attrib['method']:
                exec('stim.%s(%s)' %(attrib['method'], value.__repr__()))
            else:
                # Not implemented, use attributeSetter to get things going
                exec('stim.%s %s= %s' %(attrib['attribute'], operation, value.__repr__()))
    stim.draw()
    utils.compareScreenshot(screenshotBaseName + '_' + 'operations.png', self.win)



"""Each test class creates a context subclasses _baseVisualTest to run a series
of tests on a single graphics context (e.g. pyglet with shaders)

To add a new stimulus test use _base so that it gets tested in all contexts

"""

class Test_Window:
    """Some tests just for the window - we don't really care about what's drawn inside it
    """
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-test_window')
        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
    def teardown_class(self):
        shutil.rmtree(self.temp_dir)
    def test_captureMovieFrames(self):
        stim = visual.GratingStim(self.win, dkl=[0,0,1])
        stim.autoDraw = True
        for frameN in range(3):
            stim.phase += 0.3
            self.win.flip()
            self.win.getMovieFrame()
        self.win.saveMovieFrames(os.path.join(self.temp_dir, 'junkFrames.png'))
        self.win.saveMovieFrames(os.path.join(self.temp_dir, 'junkFrames.gif'))
        region = self.win._getRegionOfFrame()
    def test_multiFlip(self):
        self.win.recordFrameIntervals = False #does a reset
        self.win.recordFrameIntervals = True
        self.win.multiFlip(3)
        self.win.multiFlip(3,clearBuffer=False)
        self.win.saveFrameIntervals(os.path.join(self.temp_dir, 'junkFrameInts'))
        fps = self.win.fps()
    def test_callonFlip(self):
        def assertThisIs2(val):
            assert val==2
        self.win.callOnFlip(assertThisIs2, 2)
        self.win.flip()

class _baseVisualTest:
    #this class allows others to be created that inherit all the tests for
    #a different window config
    @classmethod
    def setup_class(self):#run once for each test class (window)
        self.win=None
        self.contextName
        raise NotImplementedError
    @classmethod
    def teardown_class(self):#run once for each test class (window)
        self.win.close()#shutil.rmtree(self.temp_dir)
    def setup(self):#this is run for each test individually
        pass
    def test_auto_draw(self):
        win = self.win
        stims=[]
        stims.append(visual.PatchStim(win))
        stims.append(visual.ShapeStim(win))
        stims.append(visual.TextStim(win))
        for stim in stims:
            assert stim.status==visual.NOT_STARTED
            stim.autoDraw = True
            assert stim.status==visual.STARTED
            stim.autoDraw = False
            assert stim.status==visual.FINISHED
            assert stim.status==visual.STOPPED
            str(stim) #check that str(xxx) is working
    def test_imageAndGauss(self):
        win = self.win
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testimage.jpg')
        #use image stim
        size = numpy.array([2.0,2.0])*self.scaleFactor
        image = visual.ImageStim(win, image=fileName, mask='gauss',
                                 size=size, flipHoriz=True, flipVert=True)
        image.draw()
        utils.compareScreenshot('imageAndGauss_%s.png' %(self.contextName), win)
    def test_gratingImageAndGauss(self):
        win = self.win
        size = numpy.array([2.0,2.0])*self.scaleFactor
        #generate identical image as test_imageAndGauss but using GratingStim
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testimage.jpg')
        if win.units in ['norm','height']:
            sf = -1.0
        else:
            sf = -1.0/size #this will do the flipping and get exactly one cycle
        image = visual.GratingStim(win, tex=fileName, size=size, sf=sf, mask='gauss')
        image.draw()
        utils.compareScreenshot('imageAndGauss_%s.png' %(self.contextName), win)
    def test_greyscaleImage(self):
        win = self.win
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'greyscale.jpg')
        imageStim = visual.ImageStim(win, fileName)
        imageStim.draw()
        utils.compareScreenshot('greyscale_%s.png' %(self.contextName), win)
        str(imageStim) #check that str(xxx) is working
        imageStim.color = [0.1,0.1,0.1]
        imageStim.draw()
        utils.compareScreenshot('greyscaleLowContr_%s.png' %(self.contextName), win)
        imageStim.color = 1
        imageStim.contrast = 0.1#should have identical effect to color=0.1
        imageStim.draw()
        utils.compareScreenshot('greyscaleLowContr_%s.png' %(self.contextName), win)
        imageStim.contrast = 1.0
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'greyscale2.png')
        imageStim.image = fileName
        imageStim.size *= 3
        imageStim.draw()
        utils.compareScreenshot('greyscale2_%s.png' %(self.contextName), win)
    def test_numpyTexture(self):
        win = self.win
        grating = filters.makeGrating(res=64, ori=20.0,
                                     cycles=3.0, phase=0.5,
                                     gratType='sqr', contr=1.0)
        imageStim = visual.ImageStim(win, image=grating,
                                     size = 3*self.scaleFactor,
                                     interpolate=True)
        imageStim.draw()

        utils.compareScreenshot('numpyImage_%s.png' %(self.contextName), win)
        str(imageStim) #check that str(xxx) is working
        #set lowcontrast using color
        imageStim.color = [0.1,0.1,0.1]
        imageStim.draw()
        utils.compareScreenshot('numpyLowContr_%s.png' %(self.contextName), win)
        #now try low contrast using contr
        imageStim.color = 1
        imageStim.contrast = 0.1#should have identical effect to color=0.1
        imageStim.draw()
        utils.compareScreenshot('numpyLowContr_%s.png' %(self.contextName), win)

    def test_gabor(self):
        win = self.win
        #using init
        gabor = visual.PatchStim(win, mask='gauss', ori=-45,
            pos=[0.6*self.scaleFactor, -0.6*self.scaleFactor],
            sf=2.0/self.scaleFactor, size=2*self.scaleFactor,
            interpolate=True)
        gabor.draw()
        utils.compareScreenshot('gabor1_%s.png' %(self.contextName), win)

        #did buffer image also work?
        #bufferImgStim = visual.BufferImageStim(self.win, stim=[gabor])
        #bufferImgStim.draw()
        #utils.compareScreenshot('gabor1_%s.png' %(self.contextName), win)

        #using .set()
        gabor.ori = 45
        gabor.size -= 0.2 * self.scaleFactor
        gabor.setColor([45,30,0.3], colorSpace='dkl')
        gabor.sf += 0.2 / self.scaleFactor
        gabor.pos += [-0.5*self.scaleFactor, 0.5*self.scaleFactor]
        gabor.contrast = 0.8
        gabor.opacity = 0.8
        gabor.draw()
        utils.compareScreenshot('gabor2_%s.png' %(self.contextName), win)
        str(gabor) #check that str(xxx) is working

    #def testMaskMatrix(self):
    #    #aims to draw the exact same stimulus as in testGabor, but using filters
    #    win=self.win
    #    contextName=self.contextName
    #    #create gabor using filters
    #    size=2*self.scaleFactor#to match Gabor1 above
    #    if win.units in ['norm','height']:
    #        sf=1.0/size
    #    else:
    #        sf=2.0/self.scaleFactor#to match Gabor1 above
    #    cycles=size*sf
    #    grating = filters.makeGrating(256, ori=135, cycles=cycles)
    #    gabor = filters.maskMatrix(grating, shape='gauss')
    #    stim = visual.PatchStim(win, tex=gabor,
    #        pos=[0.6*self.scaleFactor, -0.6*self.scaleFactor],
    #        sf=1.0/size, size=size,
    #        interpolate=True)
    #    stim.draw()
    #    utils.compareScreenshot('gabor1_%s.png' %(contextName), win)
    def test_text(self):
        win = self.win
        if self.win.winType=='pygame':
            pytest.skip("Text is different on pygame")
        #set font
        fontFile = os.path.join(prefs.paths['resources'], 'DejaVuSerif.ttf')
        #using init
        stim = visual.TextStim(win,text=u'\u03A8a', color=[0.5, 1.0, 1.0], ori=15,
            height=0.8*self.scaleFactor, pos=[0,0], font='DejaVu Serif',
            fontFiles=[fontFile])
        stim.draw()
        #compare with a LIBERAL criterion (fonts do differ)
        utils.compareScreenshot('text1_%s.png' %(self.contextName), win, crit=20)
        #using set
        stim.text = 'y'
        if sys.platform=='win32':
            stim.font = 'Courier New'
        else:
            stim.font = 'Courier'
        stim.ori = -30.5
        stim.height = 1.0 * self.scaleFactor
        stim.setColor([0.1, -1, 0.8], colorSpace='rgb')
        stim.pos += [-0.5, 0.5]
        stim.contrast = 0.8
        stim.opacity = 0.8
        stim.draw()
        str(stim) #check that str(xxx) is working
        #compare with a LIBERAL criterion (fonts do differ)
        utils.compareScreenshot('text2_%s.png' %(self.contextName), win, crit=20)

    @pytest.mark.needs_sound
    def test_mov(self):
        win = self.win
        if self.win.winType=='pygame':
            pytest.skip("movies only available for pyglet backend")
        #construct full path to the movie file
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testMovie.mp4')
        #check if present
        if not os.path.isfile(fileName):
            raise IOError('Could not find movie file: %s' % os.path.abspath(fileName))
        #then do actual drawing
        pos = [0.6*self.scaleFactor, -0.6*self.scaleFactor]
        mov = visual.MovieStim(win, fileName, pos=pos)
        mov.setFlipVert(True)
        mov.setFlipHoriz(True)
        #for frameN in range(10):
        for frameN in range(2):  # faster test
            mov.draw()
            if frameN==0:
                utils.compareScreenshot('movFrame1_%s.png' %(self.contextName), win)
            win.flip()
        str(mov) #check that str(xxx) is working
    def test_rect(self):
        win = self.win
        rect = visual.Rect(win)
        rect.draw()
        rect.lineColor = 'blue'
        rect.pos = [1, 1]
        rect.ori = 30
        rect.fillColor = 'pink'
        rect.draw()
        str(rect) #check that str(xxx) is working
        rect.width = 1
        rect.height = 1
    def test_circle(self):
        self.parent = visual.ShapeStim
        self.scaleAttribs = ['radius', 'pos']
        doAttributes(self, visual.Circle)
        """
        win = self.win
        circle = visual.Circle(win)
        circle.fillColor = 'red'
        circle.draw()
        circle.lineColor = 'blue'
        circle.fillColor = None
        circle.pos = [0.5, -0.5]
        circle.ori = 30
        circle.draw()
        str(circle) #check that str(xxx) is working
        """
    def test_line(self):
        win = self.win
        line = visual.Line(win)
        line.start = (0, 0)
        line.end = (0.1, 0.1)
        line.contains()  # pass
        line.overlaps()  # pass
        line.draw()
        win.flip()
        str(line) #check that str(xxx) is working
    def test_Polygon(self):
        win = self.win
        cols = ['red','green','purple','orange','blue']
        for n, col in enumerate(cols):
            poly = visual.Polygon(win, edges=n + 5, lineColor=col)
            poly.draw()
        win.flip()
        str(poly) #check that str(xxx) is working
        poly.edges = 3
        poly.radius = 1
    def test_shape(self):
        win = self.win

        shape = visual.ShapeStim(win, lineColor=[1, 1, 1], lineWidth=1.0,
            fillColor=[0.80000000000000004, 0.80000000000000004, 0.80000000000000004],
            vertices=[[-0.5*self.scaleFactor, 0],[0, 0.5*self.scaleFactor],[0.5*self.scaleFactor, 0]],
            closeShape=True, pos=[0, 0], ori=0.0, opacity=1.0, depth=0, interpolate=True)
        shape.draw()
        #NB shape rendering can differ a little, depending on aliasing
        utils.compareScreenshot('shape1_%s.png' %(self.contextName), win, crit=12.5)

        # Using .set()
        shape.contrast = 0.8
        shape.opacity = 0.8
        shape.draw()
        str(shape) #check that str(xxx) is working
        utils.compareScreenshot('shape2_%s.png' %(self.contextName), win, crit=12.5)
    def test_radial(self):
        if self.win.winType=='pygame':
            pytest.skip("RadialStim dodgy on pygame")
        win = self.win
        #using init
        wedge = visual.RadialStim(win, tex='sqrXsqr', color=1,size=2*self.scaleFactor,
            visibleWedge=[0, 45], radialCycles=2, angularCycles=2, interpolate=False)
        wedge.draw()
        thresh = 10
        utils.compareScreenshot('wedge1_%s.png' %(self.contextName), win, crit=thresh)

        #using .set()
        wedge.mask = 'gauss'
        wedge.size = 3 * self.scaleFactor
        wedge.angularCycles = 3
        wedge.radialCycles = 3
        wedge.ori = 180
        wedge.contrast = 0.8
        wedge.opacity = 0.8
        wedge.radialPhase += 0.1
        wedge.angularPhase = 0.1
        wedge.draw()
        str(wedge) #check that str(xxx) is working
        utils.compareScreenshot('wedge2_%s.png' %(self.contextName), win, crit=10.0)
    def test_simpleimage(self):
        win = self.win
        fileName = os.path.join(utils.TESTS_DATA_PATH, 'testimage.jpg')
        if not os.path.isfile(fileName):
            raise IOError('Could not find image file: %s' % os.path.abspath(fileName))
        image = visual.SimpleImageStim(win, image=fileName, flipHoriz=True, flipVert=True)
        str(image) #check that str(xxx) is working
        image.draw()
        utils.compareScreenshot('simpleimage1_%s.png' %(self.contextName), win, crit=5.0) # Should be exact replication
    def test_dotsUnits(self):
        #to test this create a small dense circle of dots and check the circle
        #has correct dimensions
        fieldSize = numpy.array([1.0,1.0])*self.scaleFactor
        pos = numpy.array([0.5,0])*fieldSize
        dots = visual.DotStim(self.win, color=[-1.0,0.0,0.5], dotSize=5,
                              nDots=1000, fieldShape='circle', fieldPos=pos)
        dots.draw()
        utils.compareScreenshot('dots_%s.png' %(self.contextName), self.win, crit=20)
    def test_dots(self):
        #NB we can't use screenshots here - just check that no errors are raised
        win = self.win
        #using init
        dots =visual.DotStim(win, color=(1.0,1.0,1.0), dir=270,
            nDots=500, fieldShape='circle', fieldPos=(0.0,0.0),fieldSize=1*self.scaleFactor,
            dotLife=5, #number of frames for each dot to be drawn
            signalDots='same', #are the signal and noise dots 'different' or 'same' popns (see Scase et al)
            noiseDots='direction', #do the noise dots follow random- 'walk', 'direction', or 'position'
            speed=0.01*self.scaleFactor, coherence=0.9)
        dots.draw()
        win.flip()
        str(dots) #check that str(xxx) is working

        #using .set() and check the underlying variable changed
        prevDirs = copy.copy(dots._dotsDir)
        prevSignals = copy.copy(dots._signalDots)
        prevVerticesPix = copy.copy(dots.verticesPix)
        dots.dir = 20
        dots.coherence = 0.5
        dots.fieldPos = [-0.5, 0.5]
        dots.speed = 0.1 * self.scaleFactor
        dots.opacity = 0.8
        dots.contrast = 0.8
        dots.draw()
        #check that things changed
        assert (prevDirs-dots._dotsDir).sum()!=0, \
            "dots._dotsDir failed to change after dots.setDir()"
        assert prevSignals.sum()!=dots._signalDots.sum(), \
            "dots._signalDots failed to change after dots.setCoherence()"
        assert not numpy.alltrue(prevVerticesPix==dots.verticesPix), \
            "dots.verticesPix failed to change after dots.setPos()"
        win.flip()  # clear
    def test_element_array(self):
        win = self.win
        if not win._haveShaders:
            pytest.skip("ElementArray requires shaders, which aren't available")
        #using init
        thetas = numpy.arange(0,360,10)
        N=len(thetas)

        radii = numpy.linspace(0,1.0,N)*self.scaleFactor
        x, y = pol2cart(theta=thetas, radius=radii)
        xys = numpy.array([x,y]).transpose()
        spiral = visual.ElementArrayStim(win, opacities = 0, nElements=N,sizes=0.5*self.scaleFactor,
            sfs=1.0, xys=xys, oris=-thetas)
        spiral.draw()
        #check that the update function is working by changing vals after first draw() call
        spiral.opacities = 1.0
        spiral.sfs = 3.0
        spiral.draw()
        str(spiral) #check that str(xxx) is working
        utils.compareScreenshot('elarray1_%s.png' %(self.contextName), win)
    def test_aperture(self):
        win = self.win
        if not win.allowStencil:
            pytest.skip("Don't run aperture test when no stencil is available")
        grating = visual.GratingStim(win, mask='gauss',sf=8.0, size=2,color='FireBrick', units='norm')
        aperture = visual.Aperture(win, size=1*self.scaleFactor,pos=[0.8*self.scaleFactor,0])
        aperture.enabled = False
        grating.draw()
        aperture.enabled = True
        str(aperture) #check that str(xxx) is working
        grating.ori = 90
        grating.color = 'black'
        grating.draw()
        utils.compareScreenshot('aperture1_%s.png' %(self.contextName), win)
        #aperture should automatically disable on exit
        for shape, nVert, pos in [(None, 120, (0,0)), ('circle', 17, (.2, -.7)),
                                  ('square', 4, (-.5,-.5)), ('triangle', 3, (1,1))]:
            aperture = visual.Aperture(win, pos=pos, shape=shape, nVert=nVert)
            assert len(aperture.vertices) == nVert
            assert aperture.contains(pos)
    def test_rating_scale(self):
        if self.win.winType=='pygame':
            pytest.skip("RatingScale not available on pygame")
        # try to avoid text; avoid default / 'triangle' because it does not display on win XP
        win = self.win
        rs = visual.RatingScale(win, low=0, high=1, precision=100, size=3, pos=(0,-.4),
                        labels=[' ', ' '], scale=' ',
                        marker='glow', markerStart=0.7, markerColor='darkBlue', autoLog=False)
        str(rs) #check that str(xxx) is working
        rs.draw()
        utils.compareScreenshot('ratingscale1_%s.png' %(self.contextName), win, crit=30.0)
    def test_refresh_rate(self):
        if self.win.winType=='pygame':
            pytest.skip("getMsPerFrame seems to crash the testing of pygame")
        # Faster test
        """
        #make sure that we're successfully syncing to the frame rate
        msPFavg, msPFstd, msPFmed = visual.getMsPerFrame(self.win,nFrames=60, showVisual=True)
        utils.skip_under_travis()             # skip late so we smoke test the code
        assert (1000/150.0 < msPFavg < 1000/40.0), \
            "Your frame period is %.1fms which suggests you aren't syncing to the frame" %msPFavg
        """

#create different subclasses for each context/backend
class TestPygletNorm(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], winType='pyglet', pos=[50,50], allowStencil=True, autoLog=False)
        self.contextName='norm'
        self.scaleFactor=1#applied to size/pos values
class TestPygletHeight(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,64], winType='pyglet', pos=[50,50], allowStencil=False, autoLog=False)
        self.contextName='height'
        self.scaleFactor=1#applied to size/pos values
class TestPygletNormNoShaders(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], monitor='testMonitor', winType='pyglet', pos=[50,50], allowStencil=True, autoLog=False)
        self.win._haveShaders=False
        self.contextName='normNoShade'
        self.scaleFactor=1#applied to size/pos values
class TestPygletNormStencil(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], monitor='testMonitor', winType='pyglet', pos=[50,50], allowStencil=True, autoLog=False)
        self.contextName='stencil'
        self.scaleFactor=1#applied to size/pos values
class TestPygletPix(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(57)
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], monitor=mon, winType='pyglet', pos=[50,50], allowStencil=True,
            units='pix', autoLog=False)
        self.contextName='pix'
        self.scaleFactor=60#applied to size/pos values
class TestPygletCm(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(57.0)
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], monitor=mon, winType='pyglet', pos=[50,50], allowStencil=False,
            units='cm', autoLog=False)
        self.contextName='cm'
        self.scaleFactor=2#applied to size/pos values
class TestPygletDeg(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(57.0)
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], monitor=mon, winType='pyglet', pos=[50,50], allowStencil=True,
            units='deg', autoLog=False)
        self.contextName='deg'
        self.scaleFactor=2#applied to size/pos values
class TestPygletDegFlat(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(10.0) #exagerate the effect of flatness by setting the monitor close
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], monitor=mon, winType='pyglet', pos=[50,50], allowStencil=True,
            units='degFlat', autoLog=False)
        self.contextName='degFlat'
        self.scaleFactor=4#applied to size/pos values
class TestPygletDegFlatPos(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(10.0) #exagerate the effect of flatness by setting the monitor close
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], monitor=mon, winType='pyglet', pos=[50,50], allowStencil=True,
            units='degFlatPos', autoLog=False)
        self.contextName='degFlatPos'
        self.scaleFactor=4#applied to size/pos values
class TestPygameNorm(_baseVisualTest):
    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], winType='pygame', allowStencil=True, autoLog=False)
        self.contextName='norm'
        self.scaleFactor=1#applied to size/pos values
class TestPygamePix(_baseVisualTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(57.0)
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = visual.Window([128,128], monitor=mon, winType='pygame', allowStencil=True,
            units='pix', autoLog=False)
        self.contextName='pix'
        self.scaleFactor=60#applied to size/pos values
#class TestPygameCm(_baseVisualTest):
#    @classmethod
#    def setup_class(self):
#        mon = monitors.Monitor('testMonitor')
#        mon.setDistance(57.0)
#        mon.setWidth(40.0)
#        mon.setSizePix([1024,768])
#        self.win = visual.Window([128,128], monitor=mon, winType='pygame', allowStencil=False,
#            units='cm')
#        self.contextName='cm'
#        self.scaleFactor=2#applied to size/pos values
#class TestPygameDeg(_baseVisualTest):
#    @classmethod
#    def setup_class(self):
#        mon = monitors.Monitor('testMonitor')
#        mon.setDistance(57.0)
#        mon.setWidth(40.0)
#        mon.setSizePix([1024,768])
#        self.win = visual.Window([128,128], monitor=mon, winType='pygame', allowStencil=True,
#            units='deg')
#        self.contextName='deg'
#        self.scaleFactor=2#applied to size/pos values
#

if __name__ == '__main__':
    cls = TestPygletCm()
    cls.setup_class()
    cls.test_radial()
    cls.teardown_class()
