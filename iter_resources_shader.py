#!/usr/bin/env python3
import os
import sys
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
    print("GetRootActions: %d top-level actions" % len(controller.GetRootActions()))

    print("\nGetResources: %d resources" % len(controller.GetResources()))
    for res in controller.GetResources():
        print( f"{res.resourceId}, {res.name}, {res.type.name}" )

    print("\nDisassembly Targets:")
    targets = controller.GetDisassemblyTargets(True)
    for disasm in targets:
        print("  - " + disasm)
    target = targets[0]

    shaderModule_count = 0
    outputDir = "shader"

    print("\nShader Modules:")
    for res in controller.GetResources():
        if( res.type == rd.ResourceType.Shader ):
            shaderModule_count += 1
            shaderRefl = controller.GetShader( res.derivedResources[0], res.resourceId, controller.GetShaderEntryPoints(res.resourceId)[0] )
            print('%s, %s, parent %s, derived %s, %s <- %s <- %s, %s' %
                  (res.name, res.type.name, res.parentResources, res.derivedResources,
                   shaderRefl.encoding.name, shaderRefl.debugInfo.compiler.name, shaderRefl.debugInfo.encoding.name, shaderRefl.stage.name))

            disasm = controller.DisassembleShader(res.derivedResources[0], shaderRefl, target)

            fileDir = "%s/pseudocode/%s" % (outputDir, shaderRefl.stage.name)
            os.makedirs(fileDir, exist_ok=True)
            file = open( "%s/shader_%d.txt" % (fileDir, res.resourceId), "w")
            file.write(disasm)
            file.close()
    print("Shader Modules count: %d" % shaderModule_count)

    controller.Shutdown()
    cap.Shutdown()

    rd.ShutdownReplay()
