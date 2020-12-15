# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020 Intel Corporation
import abc


class Cloud(metaclass=abc.ABCMeta):
    """abstract class for cloud services.
    specific cloud service classes  should implement
    the three abstract methods."""

    @abc.abstractmethod
    def initialize(self):
        """initialize cloud service with keys / tokens."""
        raise NotImplementedError

    @abc.abstractmethod
    def deploy(self):
        """deploy container with a given ami and HW of choice."""
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self):
        """stop container service and cleanup any config files."""
        raise NotImplementedError
