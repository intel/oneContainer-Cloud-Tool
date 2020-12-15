# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020 Intel Corporation
"""unified logging for onecontainer cloud tool"""
from pathlib import Path

from loguru import logger


def _mk_log_dir(path: str) -> Path:
    return Path(__file__).parent.absolute() / path


def log_config(
    file_path: Path = _mk_log_dir("logs/onecontainer_cloud_tool.log"),
    file_retention=1,
    file_rotation=30,
    level="DEBUG",
):
    """logger sane defaults."""
    logger.add(
        level=level, sink=file_path, rotation=file_rotation, retention=file_retention
    )


log_config()

if __name__ == "__main__":
    logger.debug("oh oh! let's debug")
