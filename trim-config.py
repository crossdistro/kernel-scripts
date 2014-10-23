#!/usr/bin/env python

import sys
import re

class KernelConfig:

	def __init__(self):
        	self.options = dict()
                self.old_options = dict()

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

        def value_to_string(self, value):
                if value[0] == "simple":
                        return value[1]

		if value[0] == "number":
			return value[1]

		if value[0] == "string":
			return "\"" + value[1] + "\""

        def config_to_string(self, opt, value):
		option = "CONFIG_" + opt
                valstr = self.value_to_string(value)

		if value == ("simple", "n"):
			return "# " + option + " is not set"
		else:
                    return option + "=" + valstr

	def store(self, cfg):
		for opt, value in self.options.iteritems():
			cfg.write(self.config_to_string(opt, value) + "\n")

        def store_diff(self, cfg):
                for opt, value in self.options.iteritems():
                        optstr = "CONFIG_" + opt
                        newval = self.value_to_string(value)
                        oldval = self.value_to_string(self.old_options[opt])
                        cfg.write(optstr + "=" + newval + " (changed from: " + oldval + ")\n")

	def trim_by_dist_config(self, dist):
		trimmed = KernelConfig()

		# everything that user sets which is not in dist, or
		# differs from dist, will be included in trimmed config
		for opt, value in self.options.iteritems():
			if opt not in dist.options:
				trimmed.options[opt] = value
				continue
			if value != dist.options[opt]:
				trimmed.options[opt] = value

		# everything that dist sets and is missing in user config,
		# will be explicitly disabled in trimmed config
		for opt in dist.options.iterkeys():
			if opt not in self.options:
				trimmed.options[opt] = ("simple", "n")

		return trimmed

	def combine_with_dist_config(self, dist):
		combined = KernelConfig()
		combined.options = self.options.copy()

		for opt, value in dist.options.iteritems():
			if opt not in combined.options:
				combined.options[opt] = value

		return combined

        def compare_user_with_combined(self, comb, dist):
                was_disabled = KernelConfig()
                is_missing = KernelConfig()
                was_changed = KernelConfig()
                new_option = KernelConfig()
                dist_was_disabled = KernelConfig()
                dist_new_option = KernelConfig()
                dist_is_missing = KernelConfig()
                dist_was_changed = KernelConfig()

		for opt, value in self.options.iteritems():
			if value == ("simple", "n"):
				if opt not in comb.options:
					continue
				if value != comb.options[opt]:
                                        was_disabled.options[opt] = comb.options[opt]
					continue
			if opt not in comb.options:
                                is_missing.options[opt] = value
                                continue
                        if value != comb.options[opt]:
                                was_changed.options[opt] = comb.options[opt]
                                was_changed.old_options[opts] = value

                for opt, value in comb.options.iteritems():
                        if opt not in self.options:
                                if value == ("simple", "n"):
                                        continue
                                if opt not in dist.options:
                                        new_option.options[opt] = value
                                else:
                                        dist_new_option.options[opt] = value

                for opt, value in dist.options.iteritems():
                        if opt in self.options:
                                continue
                        if opt not in comb.options:
                                if value != ("simple", "n"):
                                        dist_is_missing.options[opt] = value
                                continue
                        if value != comb.options[opt]:
                                if value == ("simple", "n"):
                                        dist_was_disabled[opt] = comb.options[opt]
                                else:
                                        dist_was_changed.options[opt] = comb.options[opt]
                                        dist_was_changed.old_options[opt] = value

                return (was_disabled, is_missing, was_changed, new_option, dist_new_option, dist_is_missing, dist_was_changed, dist_was_disabled)


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

elif action == "--diff":

	user_config_file = open(sys.argv[2], 'r')
	dist_config_file = open(sys.argv[3], 'r')
	comb_config_file = open(sys.argv[4], 'r')

	user_config = KernelConfig()
	dist_config = KernelConfig()
	comb_config = KernelConfig()

	user_config.parse(user_config_file)
	dist_config.parse(dist_config_file)
	comb_config.parse(comb_config_file)

	user_config_file.close()
	dist_config_file.close()
	comb_config_file.close()

        (was_disabled, is_missing, was_changed, new_option, dist_new_option, dist_is_missing, dist_was_changed, dist_was_disabled) = \
            user_config.compare_user_with_combined(comb_config, dist_config)

        print "The following options were disabled in the user config:\n"
        was_disabled.store(sys.stdout)

        print "\nThe following options from user config are missing:\n"
        is_missing.store(sys.stdout)

        print "\nThe following options from user config changed value:\n"
        was_changed.store_diff(sys.stdout)

        print "\nThe following options were not known by user nor distro config:\n"
        new_option.store(sys.stdout)

        print "\nThe following options were disabled in the distro config\n"
        dist_was_disabled.store(sys.stdout)

        print "\nThe following options from distro config changed value:\n"
        dist_was_changed.store_diff(sys.stdout)

        print "\nThe following options from distro config are missing:\n"
        dist_is_missing.store(sys.stdout)

        print "\nThe following options from distro config are new:\n"
        dist_new_option.store(sys.stdout)

else:
	sys.stderr.write("unknown action: " + action + "\n")

