#!/usr/bin/env python

import sys
import re

class KernelConfig:

	def __init__(self):
        	self.options = dict()

	def parse(self, cfg):
		for line in cfg:
			line = line.strip()

			if not line:
				#print "skip empty line"
				continue;

			if re.search("^#.*$", line):
				m = re.match("^# CONFIG_([^ ]+) is not set$", line)
			
				if m:
					self.options[m.group(1)] = ("simple", "n")
					continue
					# print "CONFIG " + m.group(1) + " is not set"
				else:
					# print "skip comment: " + line
					continue
				continue

			m = re.match("^CONFIG_([^=]+)=([ym])$", line)
			if m:
				self.options[m.group(1)] = ("simple", m.group(2))
				#print "CONFIG " + m.group(1) + " is set to " + m.group(2)
				continue

			m = re.match("^CONFIG_([^=]+)=([-]?[0-9]+)$", line)
			if m:
				self.options[m.group(1)] = ("number", m.group(2))
				#print "CONFIG " + m.group(1) + " is set to " + m.group(2)
				continue

			m = re.match("^CONFIG_([^=]+)=(0x[0-9a-f]+)$", line)
			if m:
				self.options[m.group(1)] = ("number", m.group(2))
				#print "CONFIG " + m.group(1) + " is set to " + m.group(2)
				continue

			m = re.match("^CONFIG_([^=]+)=\"(.*)\"$", line)
			if m:
				self.options[m.group(1)] = ("string", m.group(2))
				#print "CONFIG " + m.group(1) + " is set to " + m.group(2)
				continue

			print "unmatched line: " + line

	def store(self, cfg):
		for opt, value in self.options.iteritems():
			option = "CONFIG_" + opt

			if value[0] == "simple":
				if value[1] == "n":
					cfg.write("# " + option + " is not set\n");
				else:
					cfg.write(option + "=" + value[1] + "\n");
				continue

			if value[0] == "number":
				cfg.write(option + "=" + value[1] + "\n");
				continue

			if value[0] == "string":
				cfg.write(option + "=\"" + value[1] + "\"\n");
				continue

	def trim_by_dist_config(self, dist):
		trimmed = KernelConfig()

		for opt, value in self.options.iteritems():
			if opt not in dist.options:
				trimmed.options[opt] = value
				continue
			if value != dist.options[opt]:
				trimmed.options[opt] = value

		# everything that dist sets and is missing in trimmed,
		# will be explicitly disabled
		for opt in dist.options.iterkeys():
			if opt not in trimmed.options:
				trimmed.options[opt] = ("simple", "n")

		return trimmed

	def combine_with_dist_config(self, dist):
		combined = KernelConfig()
		combined.options = self.options.copy()

		for opt, value in dist.options.iteritems():
			if opt not in combined.options:
				combined.options[opt] = value

		return combined

action = sys.argv[1];

if action == "--trim":

	user_config_file = open(sys.argv[2], 'r')
	dist_config_file = open(sys.argv[3], 'r')

	user_config = KernelConfig()
	dist_config = KernelConfig()

	user_config.parse(user_config_file)
	dist_config.parse(dist_config_file)

	user_config_file.close()
	dist_config_file.close()

	trim_config = user_config.trim_by_dist_config(dist_config)
	trim_config_file = open(sys.argv[4], 'w')
	trim_config.store(trim_config_file)
	trim_config_file.close()

elif action == "--combine":

	user_config_file = open(sys.argv[2], 'r')
	dist_config_file = open(sys.argv[3], 'r')

	user_config = KernelConfig()
	dist_config = KernelConfig()

	user_config.parse(user_config_file)
	dist_config.parse(dist_config_file)

	user_config_file.close()
	dist_config_file.close()

	comb_config = user_config.combine_with_dist_config(dist_config)
	comb_config_file = open(sys.argv[4], 'w')
	comb_config.store(comb_config_file)
	comb_config_file.close()
else:
	sys.stderr.write("unknown action: " + action + "\n")

