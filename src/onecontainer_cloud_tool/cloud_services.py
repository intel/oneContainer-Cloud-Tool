# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020 Intel Corporation
from onecontainer_cloud_tool import aws
from onecontainer_cloud_tool.abstract_cloud import Cloud
from onecontainer_cloud_tool.logger import logger


def service(cloud="aws") -> Cloud:
    """service factory that dispatches to the right cloud service."""
    if cloud == "aws":
        logger.debug("aws service flow.")
        return aws.AWS()
    if cloud == "gcp":
        raise NotImplementedError
    if cloud == "azure":
        raise NotImplementedError
