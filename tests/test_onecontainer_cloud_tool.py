# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020 Intel Corporation
from onecontainer_cloud_tool import __version__
from onecontainer_cloud_tool.cloud_services import service
import onecontainer_cloud_tool.config as config
import os
import configparser


def test_version():
    assert __version__ == "0.1.0"


def test_aws_init():
    aws = service("aws")
    aws.initialize("access_key", "secret_key", "region")
    assert os.path.isfile(config.CONFIG_FILE)


def test_aws_deploy():
    aws = service("aws")
    num_of_sections = 0
    new_num_of_sections = 0

    if os.path.isfile(config.CONFIG_FILE):
        ini_conf = configparser.ConfigParser()
        ini_conf.read(config.CONFIG_FILE)

        num_of_sections = len(ini_conf.sections())
        aws.deploy(
            "t2.medium", "sysstacks/dlrs-tensorflow-ubuntu", "ami-0128839b21d19300e"
        )

        ini_conf.read(config.CONFIG_FILE)
        new_num_of_sections = len(ini_conf.sections())

    assert new_num_of_sections == num_of_sections + 1


def test_aws_stop():
    aws = service("aws")
    if not os.path.isfile(config.CONFIG_FILE):
        assert False
    aws.stop()
    assert not os.path.isfile(config.CONFIG_FILE)
