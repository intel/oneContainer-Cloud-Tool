import click


from onecontainer_cloud_tool.logger import logger
from onecontainer_cloud_tool.cloud_services import service
from . import __version__

aws = service("aws")


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--cloud",
    "-c",
    type=click.Choice(["aws"]),
    help="Use a cloud service, options are: aws",
)
@click.pass_context
def cli(ctx, cloud="aws") -> None:
    """onecontainer_cloud_tool - deploy containers using specific HW on the cloud.

    This tool supports deploying container instances to cloud services, mapping to
    specific HW.
    Supported cloud services: aws
    """
    ctx.obj = {"cloud": cloud}


@cli.command("init")
@click.option(
    "--access-key",
    "-ak",
    prompt=True,
    help="Access Key Id to access the cloud service",
    envvar="ACCESS_KEY",
)
@click.option(
    "--secret-key",
    "-sk",
    prompt=True,
    help="Secret Key to access the cloud service",
    envvar="SECRET_KEY",
)
@click.option(
    "--region",
    "-r",
    type=click.Choice(["us-east-1", "us-east-2", "us-west-1", "us-west-2"]),
    default="us-east-1",
    help="The region where the  service be located",
)
@click.pass_context
def init(ctx, access_key, secret_key, region):
    logger.debug("Initializing service")
    if ctx.obj.get("cloud", None) == "aws":
        aws.initialize(access_key, secret_key, region)


@cli.command("start")
@click.option(
    "--machine-image",
    "-mi",
    default="ami-0128839b21d19300e",
    prompt=True,
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
    default="t2.medium",
    prompt=True,
    help="Hardware instance type",
)
@click.pass_context
def start(ctx, machine_image, container_image_url, instance_type):
    logger.debug("Starting container service")
    # Using as sysstacks/dlrs-tensorflow-ubuntu as image.
    if ctx.obj.get("cloud", None) == "aws":
        aws.deploy(instance_type, container_image_url, machine_image)


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
