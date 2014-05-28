#####################################################
#
# Common Definitions Inherited by All Classes
#
#####################################################

class DRCommon(object):
	# Layered Topology Globals
	HOST		= 0
	EDGE		= 1
	AGGR		= 2
	CORE		= 3
	LAYER_MAP	= {'HOST':HOST, 'EDGE':EDGE, 'AGGR':AGGR, 'CORE':CORE,
					HOST:'HOST', EDGE:'EDGE', AGGR:'AGGR', CORE:'CORE',}
