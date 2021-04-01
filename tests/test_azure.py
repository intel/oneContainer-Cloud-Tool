import configparser
import os

import pytest

from onecontainer_cloud_tool.services import service
import onecontainer_cloud_tool.config as config

def test_azure_no_init():
    azure = service("azure")
    azure.initialize("region")
    assert not os.path.isfile(config.CONFIG_FILE)


def test_azure_no_deploy():
    azure = service("azure")
    num_of_sections = 0
    new_num_of_sections = 0

    with pytest.raises(AssertionError) as pytest_wrapped_e:
        if os.path.isfile(config.CONFIG_FILE):
            ini_conf = configparser.ConfigParser()
            ini_conf.read(config.CONFIG_FILE)

            num_of_sections = len(ini_conf.sections())
            azure.deploy(
                "m5n.large", "sysstacks/dlrs-tensorflow-ubuntu", "UbuntuServer"
            )

            ini_conf.read(config.CONFIG_FILE)
            new_num_of_sections = len(ini_conf.sections())

        assert new_num_of_sections == num_of_sections + 1
        assert pytest_wrapped_e == AssertionError


def test_azure_stop():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        azure = service("azure")
        azure.stop()
        assert not os.path.isfile(config.CONFIG_FILE)
        assert pytest_wrapped_e.value == 1
