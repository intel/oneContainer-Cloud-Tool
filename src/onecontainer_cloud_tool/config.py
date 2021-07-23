# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2021 Intel Corporation

"""globals and config."""

from pathlib import Path
import os

from onecontainer_cloud_tool.utils import timestamp

KEY_FILE = f"onecontainer-{timestamp()}"
# create .config directory if doesn't exist
Path(Path.home().resolve() / ".config").mkdir(parents=True, exist_ok=True)
# create .ssh directory if not exists
SSH_PATH=Path(Path.home().resolve() / ".ssh")
SSH_PATH.mkdir(parents=True, exist_ok=True)
os.chmod(SSH_PATH, 0o700)
# config.ini is in ~/.config/occ_config.ini
CONFIG_FILE = Path(Path.home().resolve() / ".config" / "occ_config.ini")
INSTANCE_LISTING_URL = "https://raw.githubusercontent.com/intel/oneContainer-Cloud-Tool/main/src/onecontainer_cloud_tool/data/instance_listing.json"

