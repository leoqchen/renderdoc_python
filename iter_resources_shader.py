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

def shaderStageShortname( stage: rd.ShaderStage ) -> str:
    if stage == rd.ShaderStage.Vertex:
        return "vert"
    elif stage == rd.ShaderStage.Geometry:
        return "geom"
    elif stage == rd.ShaderStage.Fragment:
        return "frag"
    elif stage == rd.ShaderStage.Compute:
        return "comp"
    else:
        return stage.name

def file_write( dir: str, filename: str, mode: str, content ) -> None:
    os.makedirs( dir, exist_ok=True )

    file = open( "%s/%s" % (dir, filename), mode )
    file.write( content )
    file.close()


#------------------------
#  main
#------------------------
if 'pyrenderdoc' in globals():
    pyrenderdoc.Replay().BlockInvoke(sampleCode)
else:
    rd.InitialiseReplay(rd.GlobalEnvironment(), [])

    if len(sys.argv) <= 1:
        print('Usage: python3 {} filename.rdc'.format(sys.argv[0]))
        sys.exit(1)

    cap,controller = loadCapture(sys.argv[1])

    # Now we can use the controller!
    API = controller.GetAPIProperties()
    print("GetAPIProperties: %s" % API.pipelineType.name)

    print("GetRootActions: %d top-level actions" % len(controller.GetRootActions()))

    print("\nGetResources: %d resources" % len(controller.GetResources()))
    for res in controller.GetResources():
        print( f"{res.resourceId}, {res.name}, {res.type.name}" )

    shaderModule_count = 0
    outputDir = "shader"

    print("\nShader Modules:")
    if (API.pipelineType == rd.GraphicsAPI.Vulkan):
        outputDir += "Vulkan"

        print("\nDisassembly Targets:")
        targets = controller.GetDisassemblyTargets(True)
        for disasm in targets:
            print("  - " + disasm)
        target = targets[0]

        for res in controller.GetResources():
            if( res.type == rd.ResourceType.Shader ):
                shaderModule_count += 1

                shaderRefl = controller.GetShader( res.derivedResources[0], res.resourceId, controller.GetShaderEntryPoints(res.resourceId)[0] )
                print('%s, %s, parent %s, derived %s, %s <- %s <- %s, %s' %
                      (res.name, res.type.name, res.parentResources, res.derivedResources,
                       shaderRefl.encoding.name, shaderRefl.debugInfo.compiler.name, shaderRefl.debugInfo.encoding.name, shaderRefl.stage.name))
                stageName = shaderStageShortname( shaderRefl.stage )

                pseudoCode = controller.DisassembleShader(res.derivedResources[0], shaderRefl, target)
                pseudoDir = "%s/spv_pseudocode/%s" % (outputDir, stageName)
                pseudoFile = "shader_%d.%s" % (res.resourceId, stageName )
                file_write( pseudoDir, pseudoFile, "w", pseudoCode )

                spvBin = shaderRefl.rawBytes
                spvDir = "%s/spv/%s" % (outputDir, stageName)
                spvFile = "shader_%d.spv" % (res.resourceId)
                file_write( spvDir, spvFile, "wb", spvBin )

                glslDir = "%s/glsl/%s" % (outputDir, stageName)
                glslFile = "shader_%d.%s" % (res.resourceId, stageName)
                os.makedirs( glslDir, exist_ok=True )
                os.system( "spirv-cross --vulkan-semantics --stage %s --output %s/%s %s/%s" % (stageName, glslDir, glslFile, spvDir, spvFile))

                spvasmDir = "%s/spvasm/%s" % (outputDir, stageName)
                spvasmFile = "shader_%d.spvasm" % (res.resourceId)
                os.makedirs( spvasmDir, exist_ok=True )
                os.system( "spirv-dis -o %s/%s %s/%s" % (spvasmDir, spvasmFile, spvDir, spvFile))

    elif( API.pipelineType == rd.GraphicsAPI.OpenGL ):
        outputDir += "OpenGL"

        for res in controller.GetResources():
            if( res.type == rd.ResourceType.Shader ):
                shaderModule_count += 1

                shaderRefl = controller.GetShader( res.parentResources[0], res.resourceId, rd.ShaderEntryPoint( "main", rd.ShaderStage.Vertex  ) )
                print('%s, %s, parent %s, %s <- %s <- %s, %s' %
                      (res.name, res.type.name, res.parentResources,
                       shaderRefl.encoding.name, shaderRefl.debugInfo.compiler.name, shaderRefl.debugInfo.encoding.name, shaderRefl.stage.name))
                stageName = shaderStageShortname( shaderRefl.stage )

                glslCode = shaderRefl.debugInfo.files[0].contents
                glslDir = "%s/glsl/%s" % (outputDir, stageName )
                glslFile = "shader_%d.%s" % (res.resourceId, stageName )
                file_write( glslDir, glslFile, "w", glslCode )


    print("Shader Modules count: %d" % shaderModule_count)

    controller.Shutdown()
    cap.Shutdown()

    rd.ShutdownReplay()
