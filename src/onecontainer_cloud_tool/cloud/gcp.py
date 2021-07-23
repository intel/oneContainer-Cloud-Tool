import configparser
import sys
import time
from pathlib import Path

import googleapiclient.discovery
from google.oauth2 import service_account
from progress.spinner import MoonSpinner

from onecontainer_cloud_tool import config, utils
from onecontainer_cloud_tool.cloud.abstract_cloud import Cloud
from onecontainer_cloud_tool.logger import logger


class GCP(Cloud):
    """Interact with GCP cloud services to deploy a docker image."""

    def __init__(self):
        # self.project_id = "ssp-data-centric-10491814"
        # Default instance name
        self.instance_name = "occt-vm-instance"
        self.ini_conf = configparser.ConfigParser()
        try:
            self.ini_conf.read(config.CONFIG_FILE)
        except IOError as e:
            logger.error(f"config file not found: {e}")

    def _write_deployment_conf(self):
        self._remove_config()
        self.ini_conf[f"GCP"] = {
            "project_id": self.project_id,
            "zone": self.zone,
            "service_account_key": self.service_account_key,
        }
        with open(config.CONFIG_FILE, "a") as config_file:
            self.ini_conf.write(config_file)

    def _remove_config(self):
        logger.debug("Removing GCP sections from configuration file.")
        self.ini_conf.remove_section("GCP")
        if not utils.remove_config_if_empty(self.ini_conf, config):
            with open(config.CONFIG_FILE, "w") as config_file:
                self.ini_conf.write(config_file)

    def _get_compute_client(self):
        """creates gcp compute client."""
        try:
            self.service_account_key = self.ini_conf["GCP"].get("service_account_key", None)
        except KeyError as ke:
            logger.error(f"no key found: {ke}")
            logger.error(f"exiting...")
            sys.exit(1)
        self.credentials = service_account.Credentials.from_service_account_file(
            self.service_account_key
        )
        self.compute_client = googleapiclient.discovery.build(
            "compute", "v1", credentials=self.credentials
        )

    def initialize(
        self,
        service_account_key: str,
        project_id: str = None,
        region: str = "us-west1-a",
    ) -> None:
        self.service_account_key = Path(service_account_key).absolute()
        self.project_id = project_id
        self.zone = region
        utils.SSHkeys()
        self._write_deployment_conf()

    def deploy(
        self,
        instance_type="n2-highmem-80",
        container_image_url: str = "sysstacks/dlrs-tensorflow2-ubuntu",
        machine_image: str = "cos-stable",
        image_project: str = "cos-cloud",
    ):
        self.timestamp = utils.timestamp()
        self.machine_image = machine_image
        self.image_project = image_project
        self.machine_type = instance_type
        self.container_image_url = container_image_url
        self.project_id = self.ini_conf["GCP"].get("project_id")
        self.zone = self.ini_conf["GCP"].get("zone")
        self.username = "occt-user"
        self._get_compute_client()
        self.container_image_url = container_image_url
        self.public_ssh_key = utils.SSHkeys().public_key
        logger.debug("provisioning virtual machine.")
        operation = self.__create_instance()
        self.__wait_for_operation(operation["name"])
        instance_info = (
            self.compute_client.instances()
            .get(project=self.project_id, zone=self.zone, instance=self.instance_name)
            .execute()
        )
        self.ip_of_instance = instance_info["networkInterfaces"][0]["accessConfigs"][0][
            "natIP"
        ]
        logger.debug("deployed the container on gcp")
        self.__str__()


    def __str__(self) -> str:
        super().__str__()
        print("\n")
        print("successfully deployed the container image on gcp")
        print("## " + "=" * 70 + " ##")
        print(f"public ip address       :: {self.ip_of_instance}")
        print(f"instance user id        :: {self.username}")
        print(f"key file path           :: {utils.SSHkeys().private_key_path}")
        print(f"deployed docker image   :: {self.container_image_url}")
        print(f"compute instance type   :: {self.machine_type}")
        print(f"zone                    :: {self.zone}")
        print(" ##" + "=" * 70 + " ##")
        print("\n")
        return ""
      
    def stop(self):
        """delete the VM instance."""
        logger.debug("deleting instances, ssh keys and config files.")
        utils.SSHkeys().delete_ssh_keys()
        self._get_compute_client()
        self.project_id = self.ini_conf["GCP"].get("project_id")
        self.zone = self.ini_conf["GCP"].get("zone")
        self._remove_config()
        operation = self.__delete_instance()
        logger.debug("delete instance on gcp")
        self.__wait_for_operation(operation["name"])

    def __create_instance(self):
        try:
            # Get the latest Google COS image.
            image_response = (
                self.compute_client.images()
                .getFromFamily(project=self.image_project, family=self.machine_image)
                .execute()
            )
        except Exception as e:
            logger.error(f"error occured in fetching the image, exitinge, {e}")
            sys.exit(1)
        source_disk_image = image_response["selfLink"]
        config = {
            "name": self.instance_name,
            "machineType": f"zones/{self.zone}/machineTypes/{self.machine_type}",
            "disks": [
                {
                    "boot": True,
                    "autoDelete": True,
                    'deviceName': 'boot',
                    'type': 'PERSISTENT',
                    "initializeParams": {
                        'diskSizeGb': 30,
                        "sourceImage": source_disk_image,
                    },
                }
            ],
            "networkInterfaces": [
                {
                    "network": "global/networks/default",
                    "accessConfigs": [
                        {"type": "ONE_TO_ONE_NAT", "name": "External NAT"}
                    ],
                }
            ],
            "metadata": {
                "items": [
                    {
                        "key": "gce-container-declaration",
                        "value": "\nspec:"
                        +"\n  containers:"
                        +"\n    - image: "+ self.container_image_url
                        +"\n      name: " + self.instance_name
                        +"\n      stdin: true"
                        +"\n      tty: true"
                        +"\n  restartPolicy: Always\n",
                    },
                    {"key": "ssh-keys", "value": "occt-user:" + self.public_ssh_key},
                ]
            },
        }

        try:
            return (
                self.compute_client.instances()
                .insert(project=self.project_id, zone=self.zone, body=config)
                .execute()
            )
        except Exception as e:
            logger.error(f"error in creating instance using the given details, {e}")
            sys.exit(1)
        return None

    def __delete_instance(self):
        return (
            self.compute_client.instances()
            .delete(
                project=self.project_id, zone=self.zone, instance=self.instance_name
            )
            .execute()
        )

    def __list_instance_details(self):
        self._get_compute_client()
        result = (
            self.compute_client.instances()
            .list(project=self.project_id, zone=self.zone)
            .execute()
        )
        if "items" in result:
            self.instance_public_ip = result["items"][0]["networkInterfaces"][0][
                "accessConfigs"
            ][0]["natIP"]
        print("unrahul: list instances:: ", result)

    def __wait_for_operation(self, operation):
        with MoonSpinner("Waiting for operation to complete...") as bar:
            while True:
                result = (
                    self.compute_client.zoneOperations()
                    .get(project=self.project_id, zone=self.zone, operation=operation)
                    .execute()
                )

                if result["status"] == "DONE":
                    if "error" in result:
                        raise Exception(result["error"])
                    return result
                time.sleep(0.5)
                bar.next()
