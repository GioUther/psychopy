"""Measure your JND in orientation using a staircase method"""
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
import numpy, random

try:  # try to get a previous parameters file
    expInfo = fromFile('lastParams.pickle')
except:  # if not there then use a default set
    expInfo = {'observer':'jwp', 'refOrientation':0}
expInfo['dateStr'] = data.getDateStr()  # add the current time
# Present a dialogue to change params
dlg = gui.DlgFromDict(expInfo, title='simple JND Exp', fixed=['dateStr'])
if dlg.OK:
    toFile('lastParams.pickle', expInfo)  # save params to file for next time
else:
    core.quit()  # the user hit cancel so exit

# Make a text file to save data
fileName = expInfo['observer'] + expInfo['dateStr']
dataFile = open(fileName+'.csv', 'w')  # a simple text file with 'comma-separated-values'
dataFile.write('targetSide, oriIncrement, correct\n')

# Create the staircase handler
staircase = data.StairHandler(startVal = 20.0,
                          stepType = 'db', stepSizes=[8, 4, 4, 2],
                          nUp=1, nDown=3,  # will home in on the 80% threshold
                          nTrials=1)

# Create window and stimuli
win = visual.Window([800, 600],allowGUI=True,
                    monitor='testMonitor', units='deg')
foil = visual.GratingStim(win, sf=1, size=4, mask='gauss',
                          ori=expInfo['refOrientation'])
target = visual.GratingStim(win, sf=1, size=4, mask='gauss',
                            ori=expInfo['refOrientation'])
fixation = visual.GratingStim(win, color=-1, colorSpace='rgb',
                              tex=None, mask='circle', size=0.2)

# And some handy clocks to keep track of time
globalClock = core.Clock()
trialClock = core.Clock()

# Display instructions and wait
message1 = visual.TextStim(win, pos=[0, 3], text='Hit a key when ready.')
message2 = visual.TextStim(win, pos=[0,-3],
    text="Then press left or right to identify the %.1f deg probe." % expInfo['refOrientation'])
message1.draw()
message2.draw()
fixation.draw()
win.flip()  # To show our newly drawn 'stimuli'

# Pause until there's a keypress
event.waitKeys()


for thisIncrement in staircase:  # Will continue the staircase until it terminates!
    # Set location of stimuli
    targetSide = random.choice([-1, 1])  # Will be either +1(right) or -1(left)
    foil.pos = [-5*targetSide, 0]
    target.pos = [5*targetSide, 0]  # In other location

    # Set orientation of probe
    foil.ori = expInfo['refOrientation'] + thisIncrement

    # Draw all stimuli
    foil.draw()
    target.draw()
    fixation.draw()
    win.flip()

    # Wait 500ms; but use a loop of x frames for more accurate timing
    core.wait(0.5)

    # Blank screen
    fixation.draw()
    win.flip()

    # Get response
    thisResp = None
    while thisResp == None:
        allKeys = event.waitKeys()
        for thisKey in allKeys:
            if thisKey == 'left':
                thisResp = 1 if targetSide == -1 else -1
            elif thisKey=='right':
                thisResp = 1 if targetSide == 1 else -1
            elif thisKey in ['q', 'escape']:
                core.quit()  # Abort experiment
        event.clearEvents()  # Clear other (eg mouse) events - they clog the buffer

    # Add the data to the staircase so it can calculate the next level
    staircase.addData(thisResp)
    dataFile.write('%i,%.3f,%i\n' %(targetSide, thisIncrement, thisResp))
    core.wait(1)

# Staircase has ended
dataFile.close()
staircase.saveAsPickle(fileName)  # Special python binary file to save all the info

# Give some output to user in the command line in the output window
print('reversals:')
print(staircase.reversalIntensities)
approxThreshold = numpy.average(staircase.reversalIntensities[-6:])
print('mean of final 6 reversals = %.3f' % (approxThreshold))

# Give some on-screen feedback
feedback1 = visual.TextStim(
        win, pos=(0, 3),
        text='mean of final 6 reversals = %.3f' % (approxThreshold))

feedback1.draw()
fixation.draw()
win.flip()
event.waitKeys()  # Wait for participant to respond

win.close()
core.quit()
