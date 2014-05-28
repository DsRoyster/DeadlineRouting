#####################################################
#
# Generate requests due to different distributions
#
#####################################################

import numpy
import scipy
from DRCommon import *
import numpy

class DRRequest(DRCommon):

	# Global globals
	AVR_ARRV_RATE 	= 2000		# number per second
	AVR_DEADLINE	= 20		# ms
	MIN_FLOW_SIZE	= 2			# KBytes
	MAX_FLOW_SIZE	= 50		# KBytes

	# Query Aggregation globals
	MIN_FLOW_NUMBER	= 1
	MAX_FLOW_NUMBER	= 35

	# Bould of deadline
	MIN_DEADLINE 	= 5			# ms


	@staticmethod
	def QueryAggr(host_lst, flow_num = None, min_flow_num = None, max_flow_num = None, avr_dl = None, min_flow_size = None, max_flow_size = None, receiver = None):
		"""
		Generate one query aggregate workload:
			Multiple senders are sending towards the same receiver
		Input:
			host_lst: 	list of hosts to generate queries
			flow_num: 	number of flows to be generated, default is a random number between MIN_FLOW_NUMBER and MAX_FLOW_NUMBER
			avr_dl:		average deadline, default to AVR_DEADLINE
			min_flow_size/max_flow_size	: range of flow sizes to be generated, default to MIN_FLOW_SIZE and MAX_FLOW_NUMBER
			receiver:	receiver to receive the query aggregations, default to a random host in [0, host_num)
		Output:
			[(s, t, f, a, d)]
		"""
		host_num = len(host_lst)
		sender_lst = [host for host in host_lst]

		if flow_num == None:
			if min_flow_num == None:
				min_flow_num = DRRequest.MIN_FLOW_NUMBER
			if max_flow_num == None:
				max_flow_num = DRRequest.MAX_FLOW_NUMBER
			flow_num = numpy.random.randint(min_flow_num, max_flow_num)
		if avr_dl == None:
			avr_dl = DRRequest.AVR_DEADLINE
		if min_flow_size == None:
			min_flow_size = DRRequest.MIN_FLOW_SIZE
		if max_flow_size == None:
			max_flow_size = DRRequest.MAX_FLOW_SIZE
		if receiver == None:
			receiver = host_lst[numpy.random.randint(0, host_num)]
			if receiver in sender_lst:
				sender_lst.remove(receiver)

		# All flows arrive at the same time
		arriving_time 	= 0
		# Exponential distribution of deadlines
		deadline 		= numpy.random.exponential(avr_dl, size=flow_num)
		for i in xrange(len(deadline)):
			if deadline[i] < DRRequest.MIN_DEADLINE:
				deadline[i] = DRRequest.MIN_DEADLINE
		# Uniform distribution of flow sizes
		flow_size 		= numpy.random.uniform(min_flow_size, max_flow_size, size=flow_num)
		# Uniform distribution of sender choices
		sender 			= numpy.random.randint(0, len(sender_lst), size=flow_num)

		request = []
		for i in xrange(flow_num):
			# Converting the KBytes flow sizes to Mbits flow sizes
			#	Now ms * Gbps = Mbits
			request.append((sender_lst[sender[i]], receiver, float(flow_size[i]) / 125, arriving_time, deadline[i]))

		return request
