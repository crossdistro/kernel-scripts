#!/usr/bin/python

import sys


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
