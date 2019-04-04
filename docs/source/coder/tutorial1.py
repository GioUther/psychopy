# Import some libraries from PsychoPy
from psychopy import visual, core, event

# Create a window
win = visual.Window([800, 600], monitor="testMonitor", units="deg")

# Create some stimuli
grating = visual.GratingStim(win=win, mask='circle', size=3, pos=[-4, 0], sf=3)
fixation = visual.GratingStim(win=win, size=0.2, pos=[0, 0], sf=0, rgb=-1)

# Draw the stimuli and update the window
while True:  # This creates a never-ending loop
    grating.phase += 0.05  # Advance phase by 0.05 of a cycle
    grating.draw()
    fixation.draw()
    mywin.flip()

    # Break while loop on response
    if len(event.getKeys()) > 0:
        break
    event.clearEvents()

# Cleanup
win.close()
core.quit()
