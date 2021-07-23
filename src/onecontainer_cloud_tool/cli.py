import json
import sys

import click

from onecontainer_cloud_tool.list_instances import render_data
from onecontainer_cloud_tool.logger import logger
from onecontainer_cloud_tool.services import service

from . import __version__

aws = service("aws")
azure = service("azure")
gcp = service("gcp")


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--cloud",
    "-c",
    type=click.Choice(["aws", "azure", "gcp"]),
    help="Use a cloud service, options are: aws, azure",
)
@click.pass_context
def cli(ctx, cloud=None) -> None:
    """onecontainer_cloud_tool - deploy containers using specific HW on the cloud.

    This tool supports deploying container instances to cloud services, mapping to
    specific HW.
    Supported cloud services: aws
    """
    ctx.obj = {"cloud": cloud}


@cli.command("list_instances")
@click.option(
    "--cloud",
    "-c",
    help="list instances for the cloud",
    type=click.Choice(["aws", "azure", "gcp", "all"]),
)
def list_instances(cloud):
    """list cloud instances for intel."""
    if cloud is None:
        render_data(cloud="all")
    # fix this once gcp instance list is updated
    elif cloud is not "gcp":
        render_data(cloud=cloud)


@cli.command("init")
@click.pass_context
def init(ctx, access_key=None, secret_key=None, region=None):
    logger.debug("Initializing service")
    if ctx.obj.get("cloud", None) == "aws":
        access_key = click.prompt("access key", hide_input=True)
        secret_key = click.prompt("secret key", hide_input=True)
        region = click.prompt("region", default="us-east-1")
        aws.initialize(access_key, secret_key, region)
    elif ctx.obj.get("cloud", None) == "gcp":
        access_key_file = click.prompt("service account key file", hide_input=False)
        try:
            with open(access_key_file, "r") as key_file:
                project_id = json.load(key_file)["project_id"]
        except FileNotFoundError:
            logger.error("given service account key file location incorrect, exiting.")
            sys.exit(1)
        region = click.prompt("region", default="us-west1-a")
        gcp.initialize(access_key_file, project_id, region)
    elif ctx.obj.get("cloud", None) == "azure":
        region = click.prompt("region", default="eastus")
        azure.initialize(region)


@cli.command("start")
@click.option(
    "--container-image-url",
    "-ci",
    default="sysstacks/dlrs-tensorflow2-ubuntu",
    prompt=True,
    help="container image.",
)
@click.pass_context
def start(ctx, container_image_url):
    """start deploying containers on cloud."""

    if ctx.obj.get("cloud", None) == "aws":
        instance_type = click.prompt("instance type", default="m5n.large")
        machine_image = click.prompt("machine image", default="ami-0128839b21d19300e")
        aws.deploy(instance_type, container_image_url, machine_image)
    elif ctx.obj.get("cloud", None) == "gcp":
        machine_type = click.prompt("machine type", default="n2-highmem-80")
        image_project = click.prompt("machine image project", default="cos-cloud")
        machine_image = click.prompt("machine image", default="cos-89-lts")
        #cpu_platform = click.prompt("cpu platform", default="Intel Skylake")
            #cpu_platform,
        gcp.deploy(
            machine_type,
            container_image_url,
            machine_image,
            image_project,
        )
    elif ctx.obj.get("cloud", None) == "azure":
        instance_type = click.prompt("instance type", default="Standard_F2s_v2")
        machine_image = click.prompt(
            "machine image",
            default="UbuntuServer",
            type=click.Choice(["UbuntuServer"]),
        )
        azure.deploy(instance_type, container_image_url, machine_image)


@cli.command("stop")
@click.pass_context
def stop(ctx):
    click.confirm(
        "This action will stop all services. Are you sure you want to proceed?",
        abort=True,
    )
    logger.debug("Stopping container service")
    if ctx.obj.get("cloud", None) == "aws":
        aws.stop()
    elif ctx.obj.get("cloud", None) == "azure":
        azure.stop()
    elif ctx.obj.get("cloud", None) == "gcp":
        gcp.stop()
