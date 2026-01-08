#!/usr/bin/env python3

import sys
from pathlib import Path
import renderdoc as rd

def loadCapture(filename):
    # Open a capture file handle
    cap = rd.OpenCaptureFile()

    # Open a particular file - see also OpenBuffer to load from memory
    result = cap.OpenFile(filename, '', None)

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

    return cap,controller

#------------------------
#  main
#------------------------
if 'pyrenderdoc' in globals():
    pyrenderdoc.Replay().BlockInvoke(sampleCode)
else:
    rd.InitialiseReplay(rd.GlobalEnvironment(), [])

    if len(sys.argv) <= 1:
        print('Usage: python3 {} filename.rdc'.format(sys.argv[0]))
        sys.exit(0)

    cap,controller = loadCapture(sys.argv[1])

    # Now we can use the controller!
    print("%d top-level actions" % len(controller.GetRootActions()))
    print("\n%d resourcs" % len(controller.GetResources()))

    print("\nGetResources:")
    for res in controller.GetResources():
        print( f"{res.resourceId}, {res.name}, {res.type.name}" )

    print("\nShader Modules:")
    for res in controller.GetResources():
        if( res.type == rd.ResourceType.Shader ):
            shaderRefl = controller.GetShader( res.derivedResources[0], res.resourceId, controller.GetShaderEntryPoints(res.resourceId)[0] )
            print('%s, %s, parent %s, derived %s, %s <- %s <- %s, %s' %
                  (res.name, res.type.name, res.parentResources, res.derivedResources,
                   shaderRefl.encoding.name, shaderRefl.debugInfo.compiler.name, shaderRefl.debugInfo.encoding.name, shaderRefl.stage.name))

    controller.Shutdown()
    cap.Shutdown()

    rd.ShutdownReplay()
