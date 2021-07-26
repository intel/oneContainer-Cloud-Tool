"""list available instances."""
from dateutil import parser
from pathlib import Path
import os
from datetime import datetime
from datetime import timedelta
import json
import requests
from rich.console import Console
from rich.table import Table

from onecontainer_cloud_tool.logger import logger
from onecontainer_cloud_tool.config import INSTANCE_LISTING_URL


def fetch_data(url: str) -> dict:
    """parse json file from uri to dictionary"""
    instance_dict = {}
    try:
        instance_dict = requests.get(url).json()
    except requests.ConnectionError:
        logger.error("couldn't get the remote instance file.")
    return instance_dict


def get_local_file(path) -> dict:
    """read local instance_file from disk."""
    with open(path) as fh:
        instance_dict = json.loads(fh.read())
    return instance_dict


def overwrite_instance_file(path, data):
    """overwrite instance file on disk."""
    Path(path).unlink()
    with open(path, "w") as fh:
        fh.write(json.dumps(data))


def recent_instance_file(path) -> bool:
    """check if the instance_list is recent.

    If instance file 30 days old, retrun False, else True.
    """
    try:
        instance_dict: dict = get_local_file(path)
        local_date: str = instance_dict.pop("last_modified", None)
        current_date = datetime.utcnow()
        if parser.parse(local_date) < (current_date - timedelta(days=30)):
            return False
        return True
    except:
        return False


def instance_data(url=INSTANCE_LISTING_URL) -> dict:
    """return dict of instances."""
    path: Path = Path(__file__).resolve().parents[0] / "data" / "instance_listing.json"
    if not recent_instance_file(path):
        instance_dict = fetch_data(url)
        overwrite_instance_file(path, instance_dict)
    else:
        instance_dict = get_local_file(path)
    instance_dict.pop("last_modified", None)
    return instance_dict


def draw_table(contents: dict, csp="all"):
    """draw table with instance list."""
    console = Console()
    table = Table(title="Prefered Instance Types", show_header=True)
    table.add_column("cloud", justify="left")
    table.add_column("family", justify="left")
    table.add_column("size", justify="left")
    cur_version = ""
    if csp == "all":
        for cloud, size_dict in contents["cloud_instances"].items():
            cur_cloud = cloud
            logger.debug(cloud)
            for version, size_list in size_dict.items():
                if cur_version != version:
                    cur_version = version
                else:
                    cur_version = ""
                table.add_row(cur_cloud, cur_version, ", ".join(size_list))
                if cur_cloud != "":
                    cur_cloud = ""
            if(size_dict):
                table.add_row()
    else:
        size_dict = contents["cloud_instances"][csp]
        for version, size_list in size_dict.items():
            if cur_version != version:
                cur_version = version
            else:
                cur_version = ""
            table.add_row(csp, cur_version, ", ".join(size_list))
            if csp != "":
                csp = ""

    console.print(table)


def render_data(uri=None, cloud="all"):
    """get parsed data and render to screen."""
    # TODO:list instances based on cloud
    if cloud is None:
        cloud = all
    if not uri:
        uri = INSTANCE_LISTING_URL

    parsed_dict = instance_data(uri)

    draw_table(parsed_dict, cloud)


def main():
    render_data(INSTANCE_LISTING_URL, cloud="aws")


if __name__ == "__main__":
    # the url should be the remote url
    render_data(INSTANCE_LISTING_URL, cloud="aws")
