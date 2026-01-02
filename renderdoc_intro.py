#!/usr/bin/env python3

import sys
from pathlib import Path
import renderdoc as rd

if len(sys.argv) > 1:
    file_path = sys.argv[1]
else:
    print(f"Usage: {Path(sys.argv[0]).name} *.rdc")
    sys.exit(1)

rd.InitialiseReplay(rd.GlobalEnvironment(), [])

# Open a capture file handle
cap = rd.OpenCaptureFile()

# Open a particular file - see also OpenBuffer to load from memory
result = cap.OpenFile(file_path, '', None)

# Make sure the file opened successfully
if result != rd.ResultCode.Succeeded:
    raise RuntimeError("Couldn't open file: " + str(result))

# Make sure we can replay
if not cap.LocalReplaySupport():
    raise RuntimeError("Capture cannot be replayed")

# Initialise the replay
result,controller = cap.OpenCapture(rd.ReplayOptions(), None)

if result != rd.ResultCode.Succeeded:
    raise RuntimeError("Couldn't initialise replay: " + str(result))

# Now we can use the controller!
print("%d top-level actions" % len(controller.GetRootActions()))

controller.Shutdown()

cap.Shutdown()

rd.ShutdownReplay()
