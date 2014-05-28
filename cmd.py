from DRTopo import *
from DRRequest import *
from DRScheduler import *



def printReqLst(req_lst):
	print '%d Requests generated:' % (len(req_lst))
	for req in req_lst:
		print '\tRequest %d (%d)' % (req_lst.index(req)+1, len(req))
		for flow in req:
			print '\t\t%s->%s: %f MBits in [%f, %f]' % ('{%s}' % str(flow[0]), '{%s}' % str(flow[1]), flow[2], flow[3], flow[4])

def printPath(p):
	s = '{%s}' % (p[0])
	for i in range(1, len(p)):
		s += '->{%s}' % (p[i])
	return s

def printResults(succ_lst, fail_lst):
	print 'Success List (%d):' % len(succ_lst)
	for flow, p, rate, finish_time in succ_lst:
		print '\t%s->%s: %f MBits in [%f, %f]' % ('{%s}' % str(flow[0]), '{%s}' % str(flow[1]), flow[2], flow[3], flow[4])
		print '\t\t%s' % (printPath(p))
		print '\t\t%s, finishes at %f' % (rate, finish_time)
	print
	print 'Failed List (%d):' % (len(fail_lst))
	for flow in fail_lst:
		print '\t%s->%s: %f MBits in [%f, %f]' % ('{%s}' % str(flow[0]), '{%s}' % str(flow[1]), flow[2], flow[3], flow[4])
	print






topo = DRTopo.FatTree(4)
hosts = topo.layer[DRCommon.HOST]
scheduler = DRScheduler(topo)

# req_lst = [
# 	[('H-0-0-0', 'H-1-1-1', 0.8, 0, 1)],
# 	[('H-0-0-1', 'H-1-1-0', 0.4, 0, 1)],
# 	[('H-0-0-1', 'H-1-1-1', 0.3, 0, 1)],
# 	[('H-0-0-0', 'H-1-1-0', 0.5, 0, 1)],
# ]

test_num = 50
succ_cum = 0; fail_cum = 0
succ_cum1 = 0; fail_cum1 = 0
succ_cum2 = 0; fail_cum2 = 0
for i in xrange(test_num):
	print 'Run %d in process.' % (i+1)
	num_req = 40
	req_lst = []
	for i in xrange(num_req):
		req = DRRequest.QueryAggr(hosts, flow_num=20)
		req_lst.append(req)

	#printReqLst(req_lst)

	succ_lst, fail_lst = scheduler.DROfflineNoValuation(req_lst)
	succ_cum += len(succ_lst)
	fail_cum += len(fail_lst)
	succ_lst, fail_lst = scheduler.DROnlineNoValuation(req_lst)
	succ_cum1 += len(succ_lst)
	fail_cum1 += len(fail_lst)
	succ_lst, fail_lst = scheduler.ECMPOffline(req_lst)
	succ_cum2 += len(succ_lst)
	fail_cum2 += len(fail_lst)
	#print '================================================================'

b
	#printResults(succ_lst, fail_lst)
	#print len(succ_lst), len(fail_lst)

succ_cum /= float(test_num)
fail_cum /= float(test_num)
succ_cum1 /= float(test_num)
fail_cum1 /= float(test_num)
succ_cum2 /= float(test_num)
fail_cum2 /= float(test_num)
#print succ_cum, fail_cum
#print succ_cum1, fail_cum1
#print succ_cum2, fail_cum2

print 'Algorithm: Deadline-aware Routing Offline'
print '\tSucceeded:', succ_cum
print '\tFailed:', fail_cum
print 'Algorithm: Deadline-aware Routing Online'
print '\tSucceeded:', succ_cum1
print '\tFailed:', fail_cum1
print 'Algorithm: PDQ + ECMP Online'
print '\tSucceeded:', succ_cum2
print '\tFailed:', fail_cum2