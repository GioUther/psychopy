from psychopy import visual, core, event  # Import some libraries from PsychoPy

# Create a window
mywin = visual.Window([800, 600], monitor="testMonitor", units="deg")

# Create some stimuli
grating = visual.GratingStim(win=mywin, mask='circle', size=3, pos=[-4, 0], sf=3)
fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0, rgb=-1)

# Draw the stimuli and update the window
while True:  # This creates a never-ending loop
    grating.phase += 0.05  # Advance phase by 0.05 of a cycle
    grating.draw()
    fixation.draw()
    mywin.flip()

    if len(event.getKeys()) > 0:
        break
    event.clearEvents()

# Cleanup
mywin.close()
core.quit()
