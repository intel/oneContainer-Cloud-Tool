import configparser
import os

import pytest

from onecontainer_cloud_tool.services import service
import onecontainer_cloud_tool.config as config


def test_aws_no_init():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        aws = service("aws")
        aws.initialize("access_key", "secret_key", "region")
        assert pytest_wrapped_e.value == 1

def test_aws_no_deploy():
    with pytest.raises(AssertionError) as pytest_wrapped_e:
        aws = service("aws")
        num_of_sections = 0
        new_num_of_sections = 0

        if os.path.isfile(config.CONFIG_FILE):
            ini_conf = configparser.ConfigParser()
            ini_conf.read(config.CONFIG_FILE)

            num_of_sections = len(ini_conf.sections())
            aws.deploy(
                "m5n.large", "sysstacks/dlrs-tensorflow-ubuntu", "ami-0128839b21d19300e"
            )

            ini_conf.read(config.CONFIG_FILE)
            new_num_of_sections = len(ini_conf.sections())
        assert new_num_of_sections == num_of_sections + 1
        assert pytest_wrapped_e == AssertionError
    

def test_aws_stop():
    aws = service("aws")
    aws.stop()
    assert not os.path.isfile(config.CONFIG_FILE)
