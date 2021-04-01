import click


from onecontainer_cloud_tool.logger import logger
from onecontainer_cloud_tool.list_instances import render_data
from onecontainer_cloud_tool.services import service

from . import __version__

aws = service("aws")
azure = service("azure")


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--cloud",
    "-c",
    type=click.Choice(["aws", "azure"]),
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
    type=click.Choice(["aws", "azure", "all"]),
)
def list_instances(cloud):
    """list cloud instances for intel."""
    if cloud is None:
        render_data(cloud="all")
    else:
        render_data(cloud=cloud)


@cli.command("init")
@click.option(
    "--access-key",
    "-ak",
    help="Access Key Id to access the cloud service",
    envvar="ACCESS_KEY",
    hide_input=True,
)
@click.option(
    "--secret-key",
    "-sk",
    help="Secret Key to access the cloud service",
    envvar="SECRET_KEY",
    hide_input=True,
)
@click.option(
    "--region",
    "-r",
    help="The region where the service be located",
)
@click.pass_context
def init(ctx, access_key=None, secret_key=None, region=None):
    logger.debug("Initializing service")
    if ctx.obj.get("cloud", None) == "aws":
        if access_key is None:
            access_key = click.prompt("access key", hide_input=True)
        if secret_key is None:
            secret_key = click.prompt("secret key", hide_input=True)
        if region is None:
            region = "us-east-1"
        aws.initialize(access_key, secret_key, region)
    elif ctx.obj.get("cloud", None) == "azure":
        if region is None:
            region = "eastus"
        azure.initialize(region)


@cli.command("start")
@click.option(
    "--machine-image",
    "-mi",
    default="ami-0128839b21d19300e",
    help="Machine Image required for service",
)
@click.option(
    "--container-image-url",
    "-ci",
    default="sysstacks/dlrs-tensorflow-ubuntu",
    prompt=True,
    help="container image.",
)
@click.option(
    "--instance-type",
    "-i",
    help="Hardware instance type",
)
@click.pass_context
def start(ctx, machine_image, container_image_url, instance_type=None):
    if ctx.obj.get("cloud", None) == "aws":
        if instance_type is None:
            instance_type = click.prompt("instance type", default="m5n.large")
            if machine_image is None:
                machine_image = click.prompt("machine image", default="ami-0128839b21d19300e")
        aws.deploy(instance_type, container_image_url, machine_image)
    elif ctx.obj.get("cloud", None) == "azure":
        if instance_type is None:
            instance_type = click.prompt("instance type", default="Standard_F2s_v2")
            if machine_image is None:
                machine_image = click.prompt("machine image", default="UbuntuServer", type=click.Choice(['UbuntuServer']))
        azure.deploy(instance_type, container_image_url)


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
