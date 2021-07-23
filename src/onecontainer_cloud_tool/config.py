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
INSTANCE_LISTING_URL = "https://gist.githubusercontent.com/rahulunair/fce55c7ae341269efc58af8f3fba6c00/raw/576be150fa282cea5c3a57d9cd42ec1b9a8e9da5/instance_listing.json"
