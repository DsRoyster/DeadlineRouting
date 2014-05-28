#####################################################
#
# Topology Classes for Algorithms
#
#####################################################

import networkx as nx
from DRCommon import *

class DRTopo(DRCommon):
	"""
	Constructor:
		topo: networkx graph object
		file: txt file with specified topology information
		fattree: if it is nonzero number k, generate a k-ary fattree as the topology using all default parameters
	"""

	def __init__(self, topo = None, file = None, fattree = None):
		if topo:
			self.topo = nx.DiGraph(topo)
		elif file:
			self.topo = DRTopo.parseTopoFile(file)
		elif fattree:
			self.topo = nx.DiGraph(DRTopo.genFatTree(fattree))
		else:
			self.topo = nx.DiGraph()
		self.init()

	def init(self):
		"""
		Initializing all parameters other than the topology
		"""
		self.nodes = self.topo.nodes()
		self.edges = self.topo.edges()

		self.layer = {}
		for node, layer in nx.get_node_attributes(self.topo, 'Layer').items():
			if layer not in self.layer:
				self.layer[layer] = []
			self.layer[layer].append(node)
		self.cap = nx.get_edge_attributes(self.topo, 'Capacity')
		self.delay = nx.get_edge_attributes(self.topo, 'Delay')
		self.cost = nx.get_edge_attributes(self.topo, 'Cost')


	@staticmethod
	def parseTopoFile(file):
		"""
		Parse a graph file into a topology
		"""
		dFlg = False	# Directed flg
		sFlg = 0		# State flg
		g = nx.DiGraph()

		f = open(file, 'r')
		ss = f.readlines()
		for s in ss:
			s = s.strip()
			if not s:
				continue
			if s[0] == '#':
				# Commented line
				continue
			elif s[0] == '[':
				# Command line
				if s.upper() == '[DIRECTED]':
					dFlg = True
				elif s.upper() == '[UNDIRECTED]':
					dFlg = False
				elif s.upper() == '[NODES]':
					sFlg = 1
				elif s.upper() == '[EDGES]':
					sFlg = 2
			else:
				s = s.split()
				if sFlg == 1:
					# Format: NodeName Layer
					# 	Layer default = -1
					Layer = -1
					if len(s) > 1:
						Layer = s[1].upper()
					g.add_node(s[0], Layer = Layer)
				elif sFlg == 2:
					# Format: e[0] e[1] Cap Delay Cost
					#	Cap Delay Cost default = 1
					Cost = Delay = Cap = 1
					if len(s) > 4:
						Cost = float(s[4])
					if len(s) > 3:
						Delay = float(s[3])
					if len(s) > 2:
						Cap = float(s[2])
					g.add_edge(s[0], s[1], Capacity = Cap, Delay = Delay, Cost = Cost)
					if not dFlg:
						g.add_edge(s[1], s[0], Capacity = Cap, Delay = Delay, Cost = Cost)

		f.close()
		return g

	@staticmethod
	def writeTopoFile(file, g):
		"""
		Parse a graph file into a topology
		"""
		f = open(file, 'w')

		if type(g) == nx.classes.digraph.DiGraph:
			f.write('[DIRECTED]\n')
		else:
			f.write('[UNDIRECTED]\n')
		f.write('\n[NODES]\n')
		for node in g.nodes():
			f.write(str(node) + ' ' + nx.get_node_attributes(g, 'Layer')[node] + '\n')
		f.write('\n[EDGES]\n')
		for e in g.edges():
			f.write(e[0] + ' ' + e[1] + ' ' + \
					str(g[e[0]][e[1]]['Capacity']) + ' ' + \
					str(g[e[0]][e[1]]['Delay']) + ' ' + \
					str(g[e[0]][e[1]]['Cost']))
			if type(g) == nx.classes.graph.Graph:
				f.write(e[1] + ' ' + e[0] + ' ' + \
						str(g[e[0]][e[1]]['Capacity']) + ' ' + \
						str(g[e[0]][e[1]]['Delay']) + ' ' + \
						str(g[e[0]][e[1]]['Cost']))

		f.close()

	@staticmethod
	def writeTopoFile(file, g):
		"""
		Parse a graph file into a topology
		"""
		f = open(file, 'w')

		if type(g) == nx.classes.digraph.DiGraph:
			f.write('[DIRECTED]\n')
		else:
			f.write('[UNDIRECTED]\n')
		f.write('\n[NODES]\n')
		for node in g.nodes():
			f.write(str(node) + ' ' + nx.get_node_attributes(g, 'Layer')[node] + '\n')
		f.write('\n[EDGES]\n')
		for e in g.edges():
			f.write(e[0] + ' ' + e[1] + ' ' + \
					str(g[e[0]][e[1]]['Capacity']) + ' ' + \
					str(g[e[0]][e[1]]['Delay']) + ' ' + \
					str(g[e[0]][e[1]]['Cost']))
			if type(g) == nx.classes.graph.Graph:
				f.write(e[1] + ' ' + e[0] + ' ' + \
						str(g[e[0]][e[1]]['Capacity']) + ' ' + \
						str(g[e[0]][e[1]]['Delay']) + ' ' + \
						str(g[e[0]][e[1]]['Cost']))

		f.close()


	# Default bandwidth, delay, cost of each link
	DEF_BW	= 1.0		# Gbps
	DEF_DL 	= 1.0		# ms | # of links
	DEF_CT	= 1.0		# # of links

	@staticmethod
	def FatTree(k, attr = None):
		"""
		Generate a k-ary Fat-Tree
			attr: attribute settings
				edge_bw: edge link bandwidth
				aggr_bw: aggr link bandwidth
				core_bw: core link bandwidth
				edge_dl: edge link delay
				aggr_dl: aggr link delay
				core_dl: core link delay
				edge_ct: edge link cost
				aggr_ct: aggr link cost
				core_ct: core link cost
				bw: default bandwidth
				dl: default delay
				ct: default cost
		"""
		g = nx.Graph()

		# Default values for Fat-Tree setting
		if attr == None:
			attr = {'edge_bw':DRTopo.DEF_BW, 'aggr_bw':DRTopo.DEF_BW, 'core_bw':DRTopo.DEF_BW, \
					'edge_dl':DRTopo.DEF_DL, 'aggr_dl':DRTopo.DEF_DL, 'core_dl':DRTopo.DEF_DL, \
					'edge_ct':DRTopo.DEF_CT, 'aggr_ct':DRTopo.DEF_CT, 'core_ct':DRTopo.DEF_CT}
		if 'edge_bw' not in attr.keys():
			if 'bw' in attr.keys():
				attr['edge_bw'] = attr['bw']
			else:
				attr['edge_bw'] = DRTopo.DEF_BW
		if 'aggr_bw' not in attr.keys():
			if 'bw' in attr.keys():
				attr['aggr_bw'] = attr['bw']
			else:
				attr['aggr_bw'] = DRTopo.DEF_BW
		if 'core_bw' not in attr.keys():
			if 'bw' in attr.keys():
				attr['core_bw'] = attr['bw']
			else:
				attr['core_bw'] = DRTopo.DEF_BW
		if 'edge_dl' not in attr.keys():
			if 'dl' in attr.keys():
				attr['edge_dl'] = attr['dl']
			else:
				attr['edge_dl'] = DRTopo.DEF_DL
		if 'aggr_dl' not in attr.keys():
			if 'dl' in attr.keys():
				attr['aggr_dl'] = attr['dl']
			else:
				attr['aggr_dl'] = DRTopo.DEF_DL
		if 'core_dl' not in attr.keys():
			if 'dl' in attr.keys():
				attr['core_dl'] = attr['dl']
			else:
				attr['core_dl'] = DRTopo.DEF_DL
		if 'edge_ct' not in attr.keys():
			if 'ct' in attr.keys():
				attr['edge_ct'] = attr['ct']
			else:
				attr['edge_ct'] = DRTopo.DEF_CT
		if 'aggr_ct' not in attr.keys():
			if 'ct' in attr.keys():
				attr['aggr_ct'] = attr['ct']
			else:
				attr['aggr_ct'] = DRTopo.DEF_CT
		if 'core_ct' not in attr.keys():
			if 'ct' in attr.keys():
				attr['core_ct'] = attr['ct']
			else:
				attr['core_ct'] = DRTopo.DEF_CT

		# Nodes
		g.add_nodes_from(['C-{0}'.format(i) for i in range(0, k*k/4)], Layer = DRCommon.CORE)
		g.add_nodes_from(['A-{0}-{1}'.format(i, j) for i in range(0, k) for j in range(0, k/2)], Layer = DRCommon.AGGR)
		g.add_nodes_from(['E-{0}-{1}'.format(i, j) for i in range(0, k) for j in range(0, k/2)], Layer = DRCommon.EDGE)
		g.add_nodes_from(['H-{0}-{1}-{2}'.format(i, j, l) for i in range(0, k) for j in range(0, k/2) for l in range(0, k/2)], Layer = DRCommon.HOST)

		# Edges
		for i in range(0, k):
			# k pods
			for j in range(0, k/2):
				# k/2 edge/aggr switches
				esw = 'E-{0}-{1}'.format(i, j)
				for l in range(0, k/2):
					# k/2 hosts for each edge switch
					h = 'H-{0}-{1}-{2}'.format(i, j, l)
					g.add_edge(esw, h, Capacity=attr['edge_bw'], Delay=attr['edge_dl'], Cost = attr['edge_ct'])
					# k/2 aggrs for each edge
					asw = 'A-{0}-{1}'.format(i, l)
					g.add_edge(asw, esw, Capacity=attr['aggr_bw'], Delay=attr['aggr_dl'], Cost = attr['aggr_ct'])
				asw = 'A-{0}-{1}'.format(i, j)
				for l in range(0, k/2):
					# k/2 core switches connected to the aggregate switch
					csw = 'C-{0}'.format(j*k/2+l)
					g.add_edge(csw, asw, Capacity=attr['core_bw'], Delay=attr['core_dl'], Cost = attr['core_ct'])

		return DRTopo(nx.DiGraph(g))
