#!/usr/bin/env python2

import sys
import re


class KernelConfig:

    def __init__(self):
        self.options = dict()
        self.options_match_distro = dict()
        self.old_options = dict()

    def parse(self, cfg):
        for line in cfg:
            line = line.strip()

            if not line:
                # print "skip empty line"
                continue

            if re.search("^#.*$", line):
                m = re.match("^# CONFIG_([^ ]+) is not set$", line)

                if m:
                    self.options[m.group(1)] = ("simple", "n")
                    # print "CONFIG " + m.group(1) + " is not set"
                else:
                    m = re.match("^# CONFIG_([^ ]+) matches distro$", line)

                    if m:
                        self.options_match_distro[m.group(1)] = True
                    else:
                        # print "skip comment: " + line
                        continue
                continue

            m = re.match("^CONFIG_([^=]+)=([ym])$", line)
            if m:
                self.options[m.group(1)] = ("simple", m.group(2))
                # print "CONFIG " + m.group(1) + " is set to " + m.group(2)
                continue

            m = re.match("^CONFIG_([^=]+)=([-]?[0-9]+)$", line)
            if m:
                self.options[m.group(1)] = ("number", m.group(2))
                # print "CONFIG " + m.group(1) + " is set to " + m.group(2)
                continue

            m = re.match("^CONFIG_([^=]+)=(0x[0-9a-f]+)$", line)
            if m:
                self.options[m.group(1)] = ("number", m.group(2))
                # print "CONFIG " + m.group(1) + " is set to " + m.group(2)
                continue

            m = re.match("^CONFIG_([^=]+)=\"(.*)\"$", line)
            if m:
                self.options[m.group(1)] = ("string", m.group(2))
                # print "CONFIG " + m.group(1) + " is set to " + m.group(2)
                continue

            print "unmatched line: " + line

    def parse_file(self, filename):
        cfg = open(filename, 'r')
        self.parse(cfg)
        cfg.close()

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
        for opt, value in sorted(self.options.items()):
            if opt in self.options_match_distro:
                option = "CONFIG_" + opt
                cfg.write("# " + option + " matches distro\n")
            cfg.write(self.config_to_string(opt, value) + "\n")

    def store_file(self, filename):
        cfg = open(filename, 'w')
        self.store(cfg)
        cfg.close()

    def store_diff(self, cfg):
        for opt, value in sorted(self.options.items()):
            optstr = "CONFIG_" + opt
            newval = self.value_to_string(value)
            oldval = self.value_to_string(self.old_options[opt])
            cfg.write(
                optstr + "=" + newval + " (changed from: " + oldval + ")\n")

    def store_diff_file(self, filename):
        cfg = open(filename, 'w')
        self.store_diff(cfg)
        cfg.close()

    def trim_by_dist_config(self, dist):
        trimmed = KernelConfig()

        # everything that user sets which is not in dist, or
        # differs from dist, will be included in trimmed config
        for opt, value in self.options.iteritems():
            trimmed.options[opt] = value
            if opt in dist.options and value == dist.options[opt]:
                trimmed.options_match_distro[opt] = True

        # everything that dist sets and is missing in user config,
        # will be explicitly disabled in trimmed config
        for opt in dist.options.iterkeys():
            if opt not in self.options:
                trimmed.options[opt] = ("simple", "n")

        return trimmed

    def combine_with_dist_config(self, dist):
        combined = KernelConfig()
        # start with everything from user config that didn't match
        # the corresponding distro config
        for opt, value in self.options.iteritems():
            if opt not in self.options_match_distro:
                combined.options[opt] = value

        # add values from new distro config
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

        # see what was changed against the user config
        for opt, value in self.options.iteritems():
            # options matching the old distro config are not important
            if opt in self.options_match_distro:
                continue
            if value == ("simple", "n"):
                # disabled options that disappeared are not important
                if opt not in comb.options:
                    continue
                # record disabled options that became enabled
                if value != comb.options[opt]:
                    was_disabled.options[opt] = comb.options[opt]
                    continue
            # record options that were enabled and are gone completely
            if opt not in comb.options:
                is_missing.options[opt] = value
                continue
            # record options whose value changed (including being disabled)
            if value != comb.options[opt]:
                was_changed.options[opt] = comb.options[opt]
                was_changed.old_options[opt] = value

        # see what was changed agains the new distro config
        for opt, value in dist.options.iteritems():
            # options handled by the user config diff are skipped here
            if opt in self.options and opt not in self.options_match_distro:
                continue
            # record options that were enabled and are gone completely
            if opt not in comb.options:
                if value != ("simple", "n"):
                    dist_is_missing.options[opt] = value
                continue
            # record options whose value changed (including being disabled)
            if value != comb.options[opt]:
                # record disabled options that became enabled
                if value == ("simple", "n"):
                    dist_was_disabled[opt] = comb.options[opt]
                else:
                    dist_was_changed.options[opt] = comb.options[opt]
                    dist_was_changed.old_options[opt] = value

        # record options that are new, and unknown by user config and/or distro
        # config
        for opt, value in comb.options.iteritems():
            # disabled options are unimportant
            if value == ("simple", "n"):
                continue
            # skip options known to user config (matching distro or not doesn't
            # matter)
            if opt in self.options:
                continue
            # completely new options had values taken from upstream KConfig
            # default
            if opt not in dist.options:
                new_option.options[opt] = value
            else:
                # the rest got value from distro config
                dist_new_option.options[opt] = value

        return (was_disabled, is_missing, was_changed, new_option, dist_new_option, dist_is_missing, dist_was_changed, dist_was_disabled)

action = sys.argv[1]

if action == "--trim":

    user_config = KernelConfig()
    dist_config = KernelConfig()

    user_config.parse_file(sys.argv[2])
    dist_config.parse_file(sys.argv[3])

    trim_config = user_config.trim_by_dist_config(dist_config)
    trim_config.store_file(sys.argv[4])

elif action == "--combine":

    user_config = KernelConfig()
    dist_config = KernelConfig()

    user_config.parse_file(sys.argv[2])
    dist_config.parse_file(sys.argv[3])

    comb_config = user_config.combine_with_dist_config(dist_config)
    comb_config.store_file(sys.argv[4])

elif action == "--diff":

    diff_path = sys.argv[5] + "/"

    user_config = KernelConfig()
    dist_config = KernelConfig()
    comb_config = KernelConfig()

    user_config.parse_file(sys.argv[2])
    dist_config.parse_file(sys.argv[3])
    comb_config.parse_file(sys.argv[4])

    (was_disabled, is_missing, was_changed, new_option, dist_new_option, dist_is_missing, dist_was_changed, dist_was_disabled) = \
        user_config.compare_user_with_combined(comb_config, dist_config)

    was_disabled.store_file(diff_path + "was_disabled")
    is_missing.store_file(diff_path + "is_missing")
    was_changed.store_diff_file(diff_path + "was_changed")
    new_option.store_file(diff_path + "new_options")
    dist_was_disabled.store_file(diff_path + "dist_was_disabled")
    dist_was_changed.store_diff_file(diff_path + "dist_was_changed")
    dist_is_missing.store_file(diff_path + "dist_is_missing")
    dist_new_option.store_file(diff_path + "dist_new_options")

else:
    sys.stderr.write("unknown action: " + action + "\n")