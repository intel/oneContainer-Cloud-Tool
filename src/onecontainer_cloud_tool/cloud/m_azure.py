import base64
import configparser
import os
import json
from pathlib import Path
import sys

from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.identity import DefaultAzureCredential
from azure.mgmt.network.v2020_06_01.models import NetworkSecurityGroup, SecurityRule

from onecontainer_cloud_tool.cloud.abstract_cloud import Cloud
from onecontainer_cloud_tool import config
from onecontainer_cloud_tool import utils
from onecontainer_cloud_tool.logger import logger


class Azure(Cloud):
    """deploy container solutions on azure cloud."""
    def __init__(self):
        self.ini_conf = configparser.ConfigParser()
        try:
            self.ini_conf.read(config.CONFIG_FILE)
        except IOError as e:
            logger.error(f"config file not found: {e}")

    def initialize(self, region):
        """initialize and setup keys."""
        try:
            credential = DefaultAzureCredential(exclude_interactive_browser_credential=False, exclude_managed_identity_credential=True, exclude_shared_token_cache_credential=True)

            subscription_client = SubscriptionClient(credential)
            Azure._get_subscription_id(subscription_client)
            Azure._validate_region(region, subscription_client, self.sub_id)
            utils.SSHkeys()
            self._save_session(region)
        except Exception as e:
            logger.error("Could not log in with Azure, try writing the Environment variables, doing az login (requires azure cli) or with browser.")

    @classmethod
    def _get_subscription_id(cls, subscription_client):
        subs = [
            sub.subscription_id for sub in subscription_client.subscriptions.list()
        ]
        cls.sub_id = subs[0]

    @staticmethod
    def _validate_region(region, subscription_client, subscription_id):
        locations = subscription_client.subscriptions.list_locations(subscription_id)
        valid_region = False
        for location in locations:
            if(location.name==region):
                valid_region = True
                break
        if not valid_region:
            raise ValueError("Specified region is not valid")

    def _save_session(self, region):
        logger.debug(
            f"Writing {region} as region for AZURE in {config.CONFIG_FILE}"
        )
        logger.debug(f"Writing azure session in {config.CONFIG_FILE} file")
        logger.info("Initialization Successful")
        self.ini_conf["AZURE"] = {
            "REGION": region,
        }
        with open(config.CONFIG_FILE, "w") as config_file:
            self.ini_conf.write(config_file)

    @property
    def location(self):
        if(self.ini_conf):
            return self.ini_conf["AZURE"].get("REGION", "eastus")
        return None

    def deploy(self, instance_type: str, container_image: str, machine_image="UbuntuServer"):
        """deploy a container image with a user provided hardware instance."""
        try:
            utils.check_config_exists(config)
            credential = self._get_stored_session()
            subscription_client = SubscriptionClient(credential)
            Azure._get_subscription_id(subscription_client)
            resource_client = ResourceManagementClient(credential, self.sub_id)
            network_client = NetworkManagementClient(credential, self.sub_id)
            compute_client = ComputeManagementClient(credential, self.sub_id)
        except Exception as e:
            logger.error(e)
            logger.error("Could not get session, please run init command")
            sys.exit()
        self._generate_resources_names()
        self._create_resource_group(resource_client)
        ip_address_result, nic_result = self._provision_network_resources(network_client)
        self.ip_address = ip_address_result.ip_address
        CUSTOM_DATA = self._get_cloud_init_script(container_image)
        self._provision_vm(compute_client, machine_image, instance_type, nic_result, CUSTOM_DATA)
        self._write_deployment_conf()
        logger.info("Success!")
        logger.info("You can access the deployed solution via SSH")
        logger.info(f"{self.username}@{self.ip_address}")
        logger.info(
            f"Use the private key file generated to authenticate in the ssh connection"
        )

    def _get_stored_session(self):
        """return stored session."""
        return  DefaultAzureCredential(exclude_interactive_browser_credential=False, exclude_managed_identity_credential=True, exclude_shared_token_cache_credential=True)

    def _generate_resources_names(self):
        """set resource names."""
        self.timestamp = utils.timestamp()
        self.resource_group_name = f"onecontainer-resource-{self.timestamp}"
        self.vnet_name = f"onecontainer-vnet-{self.timestamp}"
        self.subnet_name = f"onecontainer-subnet-{self.timestamp}"
        self.ip_name = f"onecontainer-ip-{self.timestamp}"
        self.ip_config_name = f"onecontainer-ipconfig-{self.timestamp}"
        self.nic_name = f"onecontainer-nic-{self.timestamp}"
        self.nsg_name = f"onecontainer-nsg-{self.timestamp}"
        self.vm_name = f"onecontainer-vm-{self.timestamp}"
        self.username = "azureuser"

    def _create_resource_group(self, resource_client):
        rg_result = resource_client.resource_groups.create_or_update(
            self.resource_group_name, {"location": self.location}
        )
        logger.debug(
            f"Provisioned resource group {rg_result.name} in the {rg_result.location} region"
        )

    def _provision_network_resources(self, network_client):
        self._provision_vnet(network_client)
        subnet_result = self._create_subnet(network_client)
        ip_address_result = self._provision_ip_address(network_client)
        nsg_result = self._create_security_group(network_client)
        nic_result = self._provision_nic(network_client, subnet_result, ip_address_result, nsg_result)
        return (ip_address_result, nic_result)

    def _provision_vnet(self, network_client):
        poller = network_client.virtual_networks.begin_create_or_update(
            self.resource_group_name,
            self.vnet_name,
            {
                "location": self.location,
                "address_space": {"address_prefixes": ["10.0.0.0/16"]},
            },
        )

        vnet_result = poller.result()
        logger.debug(
            f"Provisioned virtual network {vnet_result.name} with address prefixes {vnet_result.address_space.address_prefixes}"
        )

    def _create_subnet(self, network_client):
        poller = network_client.subnets.begin_create_or_update(
            self.resource_group_name,
            self.vnet_name,
            self.subnet_name,
            {"address_prefix": "10.0.0.0/24"},
        )
        subnet_result = poller.result()
        logger.debug(
            f"Provisioned virtual subnet {subnet_result.name} with address prefix {subnet_result.address_prefix}"
        )
        return subnet_result

    def _provision_ip_address(self, network_client):
        poller = network_client.public_ip_addresses.begin_create_or_update(
            self.resource_group_name,
            self.ip_name,
            {
                "location": self.location,
                "sku": {"name": "Standard"},
                "public_ip_allocation_method": "Static",
                "public_ip_address_version": "IPV4",
            },
        )
        ip_address_result = poller.result()

        logger.debug(
            f"Provisioned public IP address {ip_address_result.name} with address {ip_address_result.ip_address}"
        )
        return ip_address_result

    def _create_security_group(self, network_client):
        security_rules = [
            SecurityRule(
                name="http",
                access="Allow",
                description="allow inbound http",
                destination_address_prefix="*",
                destination_port_range="80",
                direction="Inbound",
                priority=505,
                protocol="Tcp",
                source_address_prefix="*",
                source_port_range="80",
            ),
            SecurityRule(
                name="https",
                access="Allow",
                description="allow inbound https",
                destination_address_prefix="*",
                destination_port_range="443",
                direction="Inbound",
                priority=506,
                protocol="Tcp",
                source_address_prefix="*",
                source_port_range="443",
            ),
            SecurityRule(
                name="ssh",
                access="Allow",
                description="allow inbound ssh",
                destination_address_prefix="*",
                destination_port_range="22",
                direction="Inbound",
                priority=500,
                protocol="Tcp",
                source_address_prefix="*",
                source_port_range="22",
            ),
            SecurityRule(
                name="outgoing",
                access="Allow",
                description="allow outgoing traffic",
                destination_address_prefix="*",
                destination_port_range="*",
                direction="Inbound",
                priority=501,
                protocol="Tcp",
                source_address_prefix="*",
                source_port_range="*",
            ),
        ]

        nsg_params = NetworkSecurityGroup(
            location=self.location, security_rules=security_rules
        )
        poller = network_client.network_security_groups.begin_create_or_update(
            self.resource_group_name, self.nsg_name, nsg_params
        )
        nsg_result = poller.result()
        logger.debug(
            f"Provisioned network security group {nsg_result.name}"
        )
        return nsg_result

    def _provision_nic(self, network_client, subnet_result, ip_address_result, nsg_result):
        poller = network_client.network_interfaces.begin_create_or_update(
            self.resource_group_name,
            self.nic_name,
            {
                "location": self.location,
                "ip_configurations": [
                    {
                        "name": self.ip_config_name,
                        "subnet": {"id": subnet_result.id},
                        "public_ip_address": {"id": ip_address_result.id},
                    }
                ],
                "network_security_group": {"id": nsg_result.id},
            },
        )
        nic_result = poller.result()
        logger.debug(f"Provisioned network interface client {nic_result.name}")
        return nic_result


    @staticmethod
    def _get_cloud_init_script(container_image):
        """get prebaked cloud init script to install container daemon and provision container."""
        path: Path = Path(__file__).resolve().parents[1] / "data" / "azure-cloudinit"
        with open(path, "r") as cloud_init_file:
            cloud_init_data = (
                cloud_init_file.read()
                .replace("{{docker-image}}", container_image)
                .encode()
            )
            return base64.b64encode(cloud_init_data).decode("latin-1")


    def _provision_vm(self, compute_client, machine_image, instance_type, nic_result, custom_data):
        """deply virtual machine on azure."""
        logger.debug(
            f"Provisioning virtual machine {self.vm_name}; this operation might take a few minutes."
        )
        poller = compute_client.virtual_machines.begin_create_or_update(
            self.resource_group_name,
            self.vm_name,
            {
                "location": self.location,
                "storage_profile": {
                    "image_reference": {
                        "publisher": "Canonical",
                        "offer": machine_image,
                        "sku": "16.04.0-LTS",
                        "version": "latest",
                    }
                },
                "hardware_profile": {"vm_size": instance_type},
                "os_profile": {
                    "custom_data": custom_data,
                    "computer_name": self.vm_name,
                    "admin_username": self.username,
                    "linux_configuration": {
                        "disable_password_authentication": True,
                        "ssh": {
                            "public_keys": [
                                {
                                    "path": f"/home/{self.username}/.ssh/authorized_keys",
                                    "key_data": utils.SSHkeys().public_key,
                                }
                            ]
                        },
                    },
                },
                "network_profile": {
                    "network_interfaces": [
                        {
                            "id": nic_result.id,
                        }
                    ]
                },
            },
        )
        vm_result = poller.result()
        logger.debug(f"Provisioned virtual machine {vm_result.name}")

    def _write_deployment_conf(self):
        self.ini_conf[f"AZURE-service-{self.timestamp}"] = {
            "resource": self.resource_group_name,
            "ssh_ip": f"{self.username}@{self.ip_address}"
        }
        with open(config.CONFIG_FILE, "w") as config_file:
            self.ini_conf.write(config_file)

    def stop(self):
        """stop running instance and delete resources."""
        try:
            utils.check_config_exists(config)
            credential = self._get_stored_session()
            subscription_client = SubscriptionClient(credential)
            Azure._get_subscription_id(subscription_client)
            resource_client = ResourceManagementClient(credential, self.sub_id)
            resource_groups = self._get_resource_group_list()
            self._remove_resource_groups(resource_client, resource_groups)
        except:
            logger.error("Could not get session, please run init command")
            sys.exit()
        self._remove_config()
        utils.SSHkeys().delete_ssh_keys()
        logger.info("Success. All resources have been terminated.")

    def _get_resource_group_list(self):
        resource_groups = []
        for section in [
            section_name
            for section_name in self.ini_conf.sections()
            if "AZURE-service" in section_name
        ]:
            resource_group_name = dict(self.ini_conf.items(section)).get("resource")
            self.ini_conf.remove_section(section)
            resource_groups.append(resource_group_name)
        return resource_groups

    @staticmethod
    def _remove_resource_groups(resource_client, resource_groups):
        logger.debug("Terminating resources. This may take a while")
        for resource_group_name in resource_groups:
            logger.debug(f"Terminating {resource_group_name} resource group.")
            poller = resource_client.resource_groups.begin_delete(resource_group_name)
            poller.wait()

    def _remove_config(self):
        logger.debug("Removing Azure session from configuration file.")
        self.ini_conf.remove_section("AZURE")
        self.ini_conf.remove_section("AZURE_SESSION")

        if not utils.remove_config_if_empty(self.ini_conf, config):
            with open(config.CONFIG_FILE, "w") as config_file:
                self.ini_conf.write(config_file)


