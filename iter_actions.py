#!/usr/bin/env python3

import sys

# Import renderdoc if not already imported (e.g. in the UI)
if 'renderdoc' not in sys.modules and '_renderdoc' not in sys.modules:
	import renderdoc

# Alias renderdoc for legibility
rd = renderdoc

def sampleCode(controller):
	drawcall_count = 0
	dispatch_count = 0
	ShaderModule_count = 0

	action = controller.GetRootActions()[0]
	while len(action.children) > 0:
		action = action.children[0]

	while action != None:
		action_is_draw_or_dispatch = False

		if action.flags & rd.ActionFlags.Drawcall:
			drawcall_count += 1
			action_is_draw_or_dispatch = True

		if action.flags & rd.ActionFlags.Dispatch:
			dispatch_count += 1
			action_is_draw_or_dispatch = True

		if action_is_draw_or_dispatch:
			controller.SetFrameEvent(action.eventId,False)
			pipeState = controller.GetPipelineState()

			vertexShader = pipeState.GetShader(rd.ShaderStage.Vertex)
			geometryShader = pipeState.GetShader(rd.ShaderStage.Geometry)
			fragmentShader = pipeState.GetShader(rd.ShaderStage.Fragment)
			computeShader = pipeState.GetShader(rd.ShaderStage.Compute)

			print('%d: %s, shader(vertex=%d, geometry=%d, fragment=%d, compute=%d)' % (action.eventId, action.GetName(controller.GetStructuredFile()), vertexShader, geometryShader, fragmentShader, computeShader))

		# Advance to the next action
		action = action.next
		if action is None:
			break

	print('drawcall_count: %d' % drawcall_count)
	print('dispatch_count: %d' % dispatch_count)
	print("")

	for res in controller.GetResources():
		if (res.type == rd.ResourceType.Shader):
			ShaderModule_count += 1
			print('%s, %s, parent %s, derived %s' % (res.name, res.type.name, res.parentResources, res.derivedResources))

	print('ShaderModule_count: %d' % ShaderModule_count)

	sys.exit(0)

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

	return (cap, controller)

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

	sampleCode(controller)

	controller.Shutdown()
	cap.Shutdown()

	rd.ShutdownReplay()

