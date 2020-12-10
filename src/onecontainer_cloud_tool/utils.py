"""common utilities."""

import datetime
import math
import uuid


def timestamp():
    return math.floor(datetime.datetime.now().timestamp())


def uuid_str():
    str(uuid.uuid4())
