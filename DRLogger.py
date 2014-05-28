#####################################################
#
# A logger component to print or write to file
#
#####################################################

from DRCommon import *
import sys
import copy

class DRLogger(DRCommon):
	"""
	Logger
	"""
	SILENT	= -1
	INFO	= 0
	DEBUG 	= 1
	ALL		= 2

	def __init__(self, file = None):
		self.level = DRLogger.INFO

		if file == None:
			self.out = sys.stdout
		elif type(file) == str:
			self.out = open(file, 'w', 0)
		elif type(file) == DRLogger:
			self.out = file.out
			self.level = file.level



	def log(self, msg, level = INFO):
		if self.level >= level and self.level >= 0 and level >= 0:
			# E.g. when system level is DEBUG and information to display is INFO
			self.out.write(msg+'\n')

	def info(self, msg):
		self.log(msg, level = DRLogger.INFO)

	def debug(self, msg):
		self.log(msg, level = DRLogger.DEBUG)

	def all(self, msg):
		self.log(msg, level = DRLogger.ALL)
