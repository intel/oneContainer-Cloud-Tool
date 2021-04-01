"""test no config file."""
import os

import onecontainer_cloud_tool.config as config


def test_no_config():
    """test if config file exists, config_file is created when init is run, this
    test should fail."""
    assert not os.path.isfile(config.CONFIG_FILE)
