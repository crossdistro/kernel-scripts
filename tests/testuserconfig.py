import os
from subprocess import check_call

from kernel.cli import main

user_config = "examples/user.config"
dist_config = "examples/dist.config"
trim_config = "examples/trim.config"
comb_config = "examples/comb.config"
diff_dir = "examples/diff"

out_trim_config = "tmp/trim.config"
out_comb_config = "tmp/comb.config"
out_diff_dir = "tmp/diff"

os.makedirs("tmp/diff", exist_ok=True)

def test_userconfig_trim():
    main(["user-config", "--trim", user_config, dist_config, out_trim_config])
    check_call(["diff", "-u", out_trim_config, trim_config])


def test_userconfig_combine():
    main(["user-config", "--combine", user_config, dist_config, out_comb_config])
    check_call(["diff", "-u", out_comb_config, comb_config])

def test_userconfig_diff():
    main(["user-config", "--diff", user_config, dist_config, comb_config, out_diff_dir])
    check_call(["diff", "-r", "-u", out_diff_dir, diff_dir])
