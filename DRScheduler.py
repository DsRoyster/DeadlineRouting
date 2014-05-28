#####################################################
#
# Scheduler implementation with various algorithms
#
#####################################################

import numpy
import scipy
import networkx as nx
from bisect import *

from DRCommon import *
from DRTopo import *
from DRLogger import *

class DRScheduler(DRCommon):
	"""
	Scheduler class. First initialize with topo, then feed with requests list, last schedules.
	"""

	def __init__(self, topo, logger = None):
		self.logger = DRLogger(logger)

		if type(topo) == DRTopo:
			self.topo = topo
		elif (type(topo) == nx.classes.digraph.DiGraph) or (type(topo) == nx.classes.graph.Graph):
			self.topo = DRTopo(topo=topo)
		else:
			self.logger.log('[DEBUG] Scheduler: topology input incorrect. Please check.')
			return

		self.logger.log('[INFO] Scheduler: topology loaded with %d nodes and %d edges.' % (len(self.topo.nodes), len(self.topo.edges)))

		self.init()

	def init(self):
		"""
		Initialize parameters for calculation
		"""
		# Event list: time
		self.event_lst = [0, float('inf')]
		# Rate list of each edge edge->(time->rate)
		# 	Rate here is the residual capacity
		#	Ensure that there is one initial timestamp with full capacity and one infinite timestamp with no capacity
		self.rate_lst = {e:{0:self.topo.topo[e[0]][e[1]]['Capacity'], float('inf'):0} for e in self.topo.edges}


	######################################
	# DRRouting Methods

	def DRBFS(self, flow, edge_mark):
		"""
		Find the shortest path regarding the hop counts.
		Using BFS.
		Input:
			flow: (s, t, f, a, d)
			edge_mark: a edge is not counted in if marked as True
		Output:
			p: [s, v1, v2, ..., t]
		"""
		# Distance flag for each node
		d = {v:float('inf') for v in self.topo.nodes}
		# Parent node for each node
		pa = {v:-1 for v in self.topo.nodes}
		# Request info
		s = flow[0]
		t = flow[1]

		# BFS to find a min-hop path
		queue = [s]; hdr = 0; d[s] = 0
		while hdr < len(queue):
			u = queue[hdr]
			hdr += 1

			for v in self.topo.topo.neighbors(u):
				if edge_mark[(u, v)] or d[v] <= d[u] + 1:
					continue
				queue.append(v)
				d[v] = d[u] + 1
				pa[v] = u
				if v == t:
					# This is because when BFS on edges, the first time reaching t meaning the smallest hop it can be reached
					hdr = len(queue)
					break

		if d[t] == float('inf'):
			return False

		p = [t]; v = t
		while v != s and v != -1:
			v = pa[v]
			p.append(v)
		p.reverse()

		return p

	def DRFindMinimalEdge(self, flow, edge_lst):
		"""
		Find the edge in the edge_lst with the minimal cumulative size regarding the flow
		Return: min_edge, min_cum_size
		"""
		arr_time = flow[3]
		end_time = flow[3] + flow[4]
		min_cum_size = float('inf')
		min_edge = (-1, -1)
		for e in edge_lst:
			prev_time = arr_time
			prev_rate = 0
			cum_size = 0
			for time, rate in sorted(self.rate_lst[e].items()):
				if time > arr_time:
					if time < end_time:
						cum_size += prev_rate * (time - prev_time)
					else:
						cum_size += prev_rate * (end_time - prev_time)
						break
				if cum_size >= min_cum_size:
					# Break if already >= minimum
					break
				elif time >= end_time:
					# Break if time exceeds deadline
					break

				prev_time = time
				prev_rate = rate

			if cum_size < min_cum_size:
				min_cum_size = cum_size
				min_edge = e

		return min_edge, min_cum_size

	def DRPathValidation(self, flow, p):
		"""
		Validate if the proposed path can hold the flow size
			If yes, return True and the actual rate allocation based on the strategy that finish it asap;
			If not, return False, the minimum edge and the cumulative size.
		"""
		path_rate_lst = []

		arr_time = flow[3]
		end_time = flow[3] + flow[4]
		edge_lst = [(p[i], p[i+1]) for i in xrange(len(p)-1)]
		# Calculate the bottlenecked rate at each event point
		for evt in self.event_lst:
			min_rate = float('inf')
			for e in edge_lst:
				if evt in self.rate_lst[e].keys() and self.rate_lst[e][evt] < min_rate:
					min_rate = self.rate_lst[e][evt]
			if min_rate < float('inf'):
				path_rate_lst.append((evt, min_rate))

		# Calculate the cumulative size over the bottleneck rates between arr_time and end_time
		prev_time = arr_time
		prev_rate = 0
		cum_size = 0
		rate_alloc = [(-1, 0)]	# Start from time -1 with rate 0, so as a benchmark from the beginning
		for time, rate in path_rate_lst:
			# Each time period is from prev_time -> min{time, end_time}
			if time > prev_time:
				if time < end_time:
					cum_size += prev_rate * (time - prev_time)
					cur_ed_time = time
				else:
					cum_size += prev_rate * (end_time - prev_time)
					cur_ed_time = end_time
				rate_alloc.append((prev_time, prev_rate))

				if cum_size >= flow[2]:
					break
				elif time >= end_time:
					break

			prev_time = time
			prev_rate = rate

		# If it can carry the flow size before deadline
		if cum_size >= flow[2]:
			cum_size -= prev_rate * (cur_ed_time - prev_time)
			new_end_time = float(flow[2] - cum_size) / prev_rate + prev_time
			# Add the finish rate onto the allocation list
			rate_alloc.append((new_end_time, 0))

			return True, edge_lst, self.DRAllocTrim(rate_alloc), new_end_time

		# If not, return the minimum edge regarding the cumulative size
		edge, size = self.DRFindMinimalEdge(flow, edge_lst)
		return False, edge, size

	def DRAllocTrim(self, rate_alloc):
		'''
		Trim the allocation vector so that the 0 items in the front is removed
		'''
		kFlg = -1
		for time, rate in rate_alloc:
			if rate > 0:
				kFlg = rate_alloc.index((time, rate))

		if kFlg > 0:
			rate_alloc = rate_alloc[kFlg:]
		rate_alloc.insert(0, (-1, 0))

		return rate_alloc

	def DRInsertFlow(self, flow, edge_lst, rate_alloc):
		"""
		Insert the flow path and the rate_allocation into the topology.
		Update corresponding rate vectors.
		"""
		st_time = flow[3]
		for time, rate in rate_alloc:
			# Add timestamps onto the event list
			st_pos = bisect_left(self.event_lst, time)
			if self.event_lst[st_pos] == time:
				continue
			self.event_lst.insert(st_pos, time)

		for e in edge_lst:
			# Add timestamps onto edge specific capacity vectors
			# The first allocation is always (-1, 0)
			# Allocation timestamps
			alloc_hdr = 0
			prev_time = rate_alloc[alloc_hdr][0]
			prev_rate = rate_alloc[alloc_hdr][1]
			# Capacity timestamps
			rate_lst = sorted(self.rate_lst[e].items())
			lst_hdr = 0
			time = rate_lst[lst_hdr][0]
			rate = rate_lst[lst_hdr][1]
			cur_cap = rate
			# List to be inserted after the loop
			# insert_lst = []
			# inserted_size = 0

			#print '-------------------'
			#print rate_alloc
			#print rate_lst
			while lst_hdr < len(rate_lst) and alloc_hdr < len(rate_alloc) - 1:
				prev_time = rate_alloc[alloc_hdr][0]
				prev_rate = rate_alloc[alloc_hdr][1]
				time = rate_lst[lst_hdr][0]
				rate = rate_lst[lst_hdr][1]
				#print '--> %f, %f --> %f, %f' % (rate_alloc[alloc_hdr+1][0], rate_alloc[alloc_hdr+1][1], time, rate)
				if time < rate_alloc[alloc_hdr+1][0]:
					# If the capacity timestamp is smaller than the next allocation timestamp, proceed capacity list
					self.rate_lst[e][time] -= prev_rate
					# Store the previous rate for the insert to take place
					cur_cap = rate
					lst_hdr += 1
				elif time == rate_alloc[alloc_hdr+1][0]:
					# If the capacity timestamp equals the next allocation timestamp
					#	First proceed alloc list
					alloc_hdr += 1
					#	Modify the capacity
					self.rate_lst[e][time] -= rate_alloc[alloc_hdr][1]
					# Store the previous rate for the insert to take place
					cur_cap = rate
					#	Proceed the capacity list
					lst_hdr += 1
				else:
					# If the capacity timestamp is larger than even the next allocation timestamp
					#	Insert the allocation and proceed the allocation list
					self.rate_lst[e][rate_alloc[alloc_hdr+1][0]] = cur_cap - rate_alloc[alloc_hdr+1][1]
					# insert_lst.append(rate_alloc[alloc_hdr+1])
					alloc_hdr += 1
				#print rate_alloc
				#print e, time, self.rate_lst[e]
				#print

	def DRFlowRouting(self, flow_lst):
		"""
		Input: [(), ()]
			List of flow tuples
		Output:
			succ_lst, fail_lst
		"""
		# For each flow, recursively find paths until either one can fit in or no path
		succ_lst = []
		fail_lst = []
		for flow in flow_lst:
			edge_mark = {e:False for e in self.topo.edges}
			path, path_edge_list, rate_alloc, finish_time = None, None, None, None
			# 1. Recursively find a path and validate if the path is valid
			while True:
				# 1.1 Find a path, here BFS is using
				p = self.DRBFS(flow, edge_mark)
				if not p:
					break
				# 1.2 Validate the path with cumulative size between arr_time and end_time
				res = self.DRPathValidation(flow, p)
				if res[0]:
					# If true, res[1] is the path edge list, res[2] is the rate allocation, res[3] is the finish time of the flow
					path = p
					path_edge_list = res[1]
					rate_alloc = res[2]
					finish_time = res[3]
					break
				# If false, res[1] is the minimum edge, res[2] is the corresponding cum size
				edge_mark[res[1]] = True
			# 2. If find a valid path, insert the path into the
			if not path_edge_list:
				# Cannot find a path to fit in
				fail_lst.append(flow)
				continue
			# Can find a path, mark and deduce the rate
			self.DRInsertFlow(flow, path_edge_list, rate_alloc)
			succ_lst.append((flow, path, rate_alloc, finish_time))

		return succ_lst, fail_lst

	def DROfflineNoValuation(self, req_lst):
		"""
		Input: [[(), ..., ()], [(), ..., ()]]
			Tuple: flow
			List of tuples: request
			List of lists: all requests
		Output:
			succeeded list, failed list
		"""

		# Initialization
		self.init()
		# Generate the list of all flows
		flow_lst = [tp for l in req_lst for tp in l]

		# Sort all flows by different metrics
		#	No sorting
		#flow_lst_sorted = flow_lst
		#	Sort by flow size
		flow_lst_sorted = sorted(flow_lst, key = lambda x:(x[2]))
		#	Sort by end_time (deadline)
		#flow_lst_sorted = sorted(flow_lst, key = lambda x:(x[3]+x[4]))
		#	Sort by flow size / deadline
		#flow_lst_sorted = sorted(flow_lst, key = lambda x:(float(x[2])/x[4]))

		# Use the Heuristic algorithm for routing
		succ_lst, fail_lst = self.DRFlowRouting(flow_lst_sorted)

		return succ_lst, fail_lst

	def DROnlineNoValuation(self, req_lst):
		"""
		Input: [[(), ..., ()], [(), ..., ()]]
			Tuple: flow
			List of tuples: request
			List of lists: all requests
		Output:
			succeeded list, failed list
		"""

		# Initialization
		self.init()
		# Generate the list of all flows
		flow_lst = [tp for l in req_lst for tp in l]

		# Sort all flows by arriving time
		#	Sort by flow size
		flow_lst_sorted = sorted(flow_lst, key = lambda x:(x[3], x[3]+x[4]))

		# Use the Heuristic algorithm for routing
		succ_lst, fail_lst = self.DRFlowRouting(flow_lst_sorted)

		return succ_lst, fail_lst



	######################################
	# ECMP Routing with PDQ

	def ECMPBFS(self, flow, edge_mark):
		"""
		Find all ECMP using BFS.
		Input:
			flow: (s, t, f, a, d)
			edge_mark: a edge is not counted in if marked as True
		Output:
			p_lst: a list of paths [[s, v11, v12, ..., t], [s, v21, v22, ..., t]]
		"""
		# Distance flag for each node
		d = {v:float('inf') for v in self.topo.nodes}
		# Parent node for each node
		pa = {v:[] for v in self.topo.nodes}
		# Request info
		s = flow[0]
		t = flow[1]

		# BFS to find a min-hop path
		queue = [s]; hdr = 0; d[s] = 0
		while hdr < len(queue):
			u = queue[hdr]
			hdr += 1

			for v in self.topo.topo.neighbors(u):	# This is directed neighbors in the context
				if edge_mark[(u, v)] or d[v] < d[u] + 1:
					continue
				if d[v] > d[u] + 1:
					queue.append(v)
					pa[v] = [u]
				elif d[v] == d[u] + 1:
					pa[v].append(u)
				d[v] = d[u] + 1

		if d[t] == float('inf'):
			return False

		# Iteratively find all paths until there is no
		p_lst = []
		while True:
			p = [t]; v = t; branch = None; branch_idx = None
			while v != s and v != -1:
				if len(pa[v]) > 0:
					if pa[v] > 1:
						branch = v
						branch_idx = 0
					v = pa[v][0]
					p.append(v)
				else:
					break
			if v == s:
				p.reverse()
				p_lst.append(p)
			else:
				break
			if branch:
				pa[branch].pop(branch_idx)

		return p_lst

	def ECMPFlowRouting(self, flow_lst):
		"""
		Input: [(), ()]
			List of flow tuples
		Output:
			succ_lst, fail_lst
		"""
		# For each flow, recursively find paths until either one can fit in or no path
		succ_lst = []
		fail_lst = []
		for flow in flow_lst:
			edge_mark = {e:False for e in self.topo.edges}
			p_lst = self.ECMPBFS(flow, edge_mark)
			if p_lst:
				p_idx = numpy.random.randint(0, len(p_lst))
				p = p_lst[p_idx]

				res = self.DRPathValidation(flow, p)
				path, path_edge_list, rate_alloc, finish_time = None, None, None, None
				if res[0]:
					# If true, res[1] is the path edge list, res[2] is the rate allocation, res[3] is the finish time of the flow
					path = p
					path_edge_list = res[1]
					rate_alloc = res[2]
					finish_time = res[3]
				if not path_edge_list:
					# Cannot find a path to fit in
					fail_lst.append(flow)
					continue
				# Can find a path, mark and deduce the rate
				self.DRInsertFlow(flow, path_edge_list, rate_alloc)
				succ_lst.append((flow, path, rate_alloc, finish_time))
				continue
			fail_lst.append(flow)

		return succ_lst, fail_lst


	def ECMPOffline(self, req_lst):
		"""
		Input: [[(), ..., ()], [(), ..., ()]]
			Tuple: flow
			List of tuples: request
			List of lists: all requests
		Output:
			succeeded list, failed list
		"""

		# Initialization
		self.init()
		# Generate the list of all flows
		flow_lst = [tp for l in req_lst for tp in l]

		# Sort all flows by different metrics
		#	No sorting
		#flow_lst_sorted = flow_lst
		#	Sort by flow size
		flow_lst_sorted = sorted(flow_lst, key = lambda x:(x[3], x[2]))
		#	Sort by end_time (deadline)
		#flow_lst_sorted = sorted(flow_lst, key = lambda x:(x[3]+x[4]))
		#	Sort by flow size / deadline
		#flow_lst_sorted = sorted(flow_lst, key = lambda x:(float(x[2])/x[4]))

		# Use the Heuristic algorithm for routing
		succ_lst, fail_lst = self.ECMPFlowRouting(flow_lst_sorted)

		return succ_lst, fail_lst

