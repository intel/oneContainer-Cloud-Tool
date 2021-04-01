"""common utilities."""

import datetime
import math
from pathlib import Path
import uuid
import os
import sys

from Cryptodome.PublicKey import RSA

from onecontainer_cloud_tool.logger import logger


def timestamp():
    """timestamp."""
    return math.floor(datetime.datetime.now().timestamp())


def uuid_str():
    """get a uuid string."""
    str(uuid.uuid4())


def isfile(file_str):
    """check if file exists."""
    return Path(file_str).is_file()


def check_config_exists(config):
    """check if config file exists."""
    if not isfile(config.CONFIG_FILE):
        raise FileNotFoundError

def remove_config_if_empty(ini_conf, config):
    if(len(ini_conf.sections())==0):
        os.remove(config.CONFIG_FILE)
        return True
    return False

class SSHkeys:
    """generate ephemerial private and public keys."""

    def __init__(self):
        self.private_key_path = Path(Path.home().resolve() / ".ssh"/ "private_key.pem")
        self.private_key = None
        self.public_key = None
        if isfile(self.private_key_path):
            self.read_keys()
        else:
            self.generate_ssh_keys()

    def read_keys(self):
        """read keys from file."""
        try:
            with open(self.private_key_path, "r") as fh:
                self.private_key = fh.read()
                self.set_public_key()
        except IOError as err:
            logger.error(err)

    def generate_ssh_keys(self):
        """generate new ssh keys."""
        key_pair = RSA.generate(4096)
        try:
            # write key to current directory the user is in
            with open(self.private_key_path, "w") as fh:
                private_key = key_pair.export_key().decode()
                fh.write(private_key)
                logger.debug(f"private_key.pem written to {self.private_key_path}")
                self.private_key = private_key
                self.set_public_key()
            os.chmod(self.private_key_path, 0o600)
        except IOError as err:
            logger.error(err)


    def delete_ssh_keys(self):
        """delete ssh keys used to access resource."""
        logger.debug("remove ssh keys.")
        os.remove(self.private_key_path)

    def set_public_key(self):
        if self.private_key is not None:
            key_pair = RSA.import_key(self.private_key)
            self.public_key = (
                key_pair.public_key().export_key(format="OpenSSH").decode()
            )
        else:
            logger.error("private key not found, exiting...")
            sys.exit(1)
