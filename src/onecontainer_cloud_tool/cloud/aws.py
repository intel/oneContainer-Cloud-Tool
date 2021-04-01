import configparser
import os
from pathlib import Path
from functools import lru_cache
from typing import Dict, List

import boto3

from onecontainer_cloud_tool.cloud.abstract_cloud import Cloud
from onecontainer_cloud_tool import config
from onecontainer_cloud_tool import utils
from onecontainer_cloud_tool.logger import logger


class AWS(Cloud):
    """interact with aws cloud services to deploy a docker image."""

    def __init__(self):
        self.ini_conf = configparser.ConfigParser()
        try:
            self.ini_conf.read(config.CONFIG_FILE)
        except IOError as e:
            logger.error(f"config file not found: {e}")

    def initialize(self, access_key: str, secret_key: str, region: str) -> None:
        """
        aws_Init.
            Tests AWS credentials, sets region and generates KeyPair to
            be used in the container deployment phase.
            All of this is written in an configuration occ_config.ini file for future use.
        """
        key_file_path = Path.home().resolve() / ".ssh"/ f"{config.KEY_FILE}.pem"
        try:
            ec2_client = boto3.client(
                "ec2",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )
            key_pair = ec2_client.create_key_pair(KeyName=config.KEY_FILE)
            logger.debug(f"Writing private key in {config.KEY_FILE}.pem")
            with open(key_file_path, "w") as key_file:
                key_file.write(key_pair["KeyMaterial"])
            os.chmod(key_file_path, 0o600)
        except Exception as e:
            logger.error(e)
            logger.info(
                "Error in initialization. Credentials are not valid. \nExiting."
            )
            exit(1)

        logger.debug(f"Writing {region} as region for AWS in {config.CONFIG_FILE}")
        logger.debug(f"Writing AWS access and secret key in {config.CONFIG_FILE}")
        logger.debug(f"Writing private key file name in {config.CONFIG_FILE} file")
        logger.debug(f"Writing private key file path in {config.CONFIG_FILE} file")

        self.ini_conf["AWS"] = {
            "REGION": region,
            "ACCESS_KEY": access_key,
            "SECRET_KEY": secret_key,
            "PRIVATE_KEY_FILE": f"{config.KEY_FILE}.pem",
            "PRIVATE_KEY_FILE_PATH": key_file_path,
        }
        with open(config.CONFIG_FILE, "w") as config_file:
            self.ini_conf.write(config_file)

    @classmethod
    @lru_cache(maxsize=10)
    def _get_clients(cls):
        """login to ec2 and ecs."""
        if not hasattr(cls, "ini_conf"):
            logger.debug("ini_conf attribute not found, setting.")
            setattr(cls, "ini_conf", configparser.ConfigParser())
            cls.ini_conf.read(config.CONFIG_FILE)
        aws_access_key_id = cls.ini_conf["AWS"].get("ACCESS_KEY")
        aws_secret_access_key = cls.ini_conf["AWS"].get("SECRET_KEY")
        region_name = cls.ini_conf["AWS"].get("REGION")
        ec2 = boto3.client(
            "ec2",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        ecs = boto3.client(
            "ecs",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        return ec2, ecs

    @classmethod
    def _check_config_file(cls):
        if not os.path.isfile(config.CONFIG_FILE):
            raise FileNotFoundError

    def deploy(self, instance_type: str, image: str, ami: str):
        """deploy container image using the given instance_type and ami"""
        try:
            AWS._check_config_file()
            self.timestamp = utils.timestamp()
            self.cluster_name = f"onecontainer-cluster-{self.timestamp}"
            self.security_group_name = f"onecontainer-security-group-{self.timestamp}"
            self.service_name = f"onecontainer-service-{self.timestamp}"
            self.task_name = f"onecontainer-task-{self.timestamp}"
            self.vpc_id = self._get_default_vpc()
            self.security_group_id = self._config_security_group()
            ec2, ecs = AWS._get_clients()
            ecs.create_cluster(clusterName=self.cluster_name)
            (self.dns, self.ip_address) = self._create_ec2_instance(ec2, instance_type, ami)
            self._register_container_task(ecs, image)
            self._create_service(ecs)
            self._write_config()
            logger.info("Success!")
            logger.info("You can access the deployed solution via SSH")
            logger.info(f"ec2-user@{self.dns}")
            logger.info("or")
            logger.info(f"ec2-user@{self.ip_address}")
            logger.info(
                f"Use the private key file generated to authenticate in the ssh connection"
            )
        except FileNotFoundError:
            logger.error("configuration file not found. please run init command first")
        except Exception as err:
            logger.error(f"failed to deploy service:{err}")

    def _create_vpc(self, ec2):
        """create vpc if it doesn't exist, if it does use the vpc_id to get sec group."""
        try:
            ec2.create_default_vpc()
            logger.debug("default VPC created.")
        except Exception:
            logger.debug("default VPC available.")

    def _create_ec2_instance(self, ec2, instance_type: str, ami: str):
        """launch ec2 instance with an instance type and ami."""
        logger.debug(f"Launching EC2 instances")
        ec2_instance_res = ec2.run_instances(
            ImageId=ami,
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_type,
            IamInstanceProfile={"Name": "ecsInstanceRole"},
            SecurityGroupIds=[self.security_group_id],
            KeyName=self.ini_conf["AWS"].get("PRIVATE_KEY_FILE").split(".")[0],
            UserData="#!/bin/bash \n echo ECS_CLUSTER="
            + self.cluster_name
            + " >> /etc/ecs/ecs.config",
        )
        waiter = ec2.get_waiter("instance_status_ok")
        for ec2_instance in ec2_instance_res["Instances"]:
            waiter.wait(InstanceIds=[ec2_instance["InstanceId"]])
            logger.debug(f'EC2 Instance {ec2_instance["InstanceId"]} created.')
            ec2_reloaded_res = ec2.describe_instances(
                InstanceIds=[ec2_instance["InstanceId"]]
            )
            ec2_instances_reloaded = ec2_reloaded_res["Reservations"][0]["Instances"]
            if ec2_instances_reloaded:
                logger.debug(
                    f'EC2 Instance DNS: {ec2_instances_reloaded[0]["PublicDnsName"]}'
                )
                logger.debug(
                    f"EC2 Instance public ip: {ec2_instances_reloaded[0]['PublicIpAddress']}"
                )
                return (
                    ec2_instances_reloaded[0]["PublicDnsName"],
                    ec2_instances_reloaded[0]["PublicIpAddress"],
                )

    def _register_container_task(
        self,
        ecs: str,
        image: str,
        port_mapping: str = None,
        memory: int = 1000,
        cpu: int = 1024,
    ):
        """Allows configuration of the container and the specification of the image,
        portMappings are not used at the moment but are commented to show how they would be set.
        Memory and CPU  set by default."""
        ecs.register_task_definition(
            networkMode="host",
            containerDefinitions=[
                {
                    "name": f"task_name",
                    "image": image,
                    "essential": True,
                    # "portMappings": [
                    #     {
                    #     "containerPort": 80,
                    #     "hostPort": 80
                    #     }
                    # ],
                    "memory": memory,
                    'pseudoTerminal': True,
                    "cpu": cpu,
                }
            ],
            family=self.task_name,
        )
        logger.debug("Task definition created")

    def _create_service(self, ecs):
        """sets cluster, taskDefinition and service name and then creates the ECS service."""
        ecs.create_service(
            cluster=self.cluster_name,
            serviceName=self.service_name,
            taskDefinition=self.task_name,
            launchType="EC2",
            desiredCount=1,
            clientToken=f"{self.task_name}",
            deploymentConfiguration={
                "maximumPercent": 200,
                "minimumHealthyPercent": 50,
            },
        )
        logger.debug("Service created")

    def _write_config(self):
        """persist cluster config info to config file."""
        self.ini_conf[f"AWS-service-{self.timestamp}"] = {
            "cluster_name": self.cluster_name,
            "default_vpc_id": self.vpc_id,
            "security_group_id": self.security_group_id,
            "task_name": self.task_name,
            "service_name": self.service_name,
            "ssh_ip": f"ec2-user@{self.ip_address}",
            "ssh_dns": f"ec2-user@{self.dns}"
        }
        with open(config.CONFIG_FILE, "w") as config_file:
            self.ini_conf.write(config_file)
        logger.debug(
            f"cluster_name, vpc_id, security_group_id, task_name, service_name written to {config.CONFIG_FILE}"
        )

    def stop(self):
        """stop all running services, delete config file and keys."""
        try:
            AWS._check_config_file()
            instance_ids = []
            cluster_sgs_info = []
            for each_section in [
                section_name
                for section_name in self.ini_conf.sections()
                if "AWS-service" in section_name
            ]:
                section = dict(self.ini_conf.items(each_section))
                self.ini_conf.remove_section(each_section)
                logger.debug(f"Stopping service {each_section}")

                cluster_sgs_info.append(
                    (section["cluster_name"], section["security_group_id"])
                )

                instance_ids += AWS._delete_service(
                    section["cluster_name"],
                    section["service_name"],
                    section["task_name"],
                )

            AWS._remove_key_pair(
                self.ini_conf["AWS"].get("PRIVATE_KEY_FILE").split(".")[0]
            )
            AWS._terminate_cluster_instances(instance_ids, cluster_sgs_info)
            os.remove(self.ini_conf["AWS"].get("PRIVATE_KEY_FILE_PATH"))
            self.ini_conf.remove_section("AWS")
            if not utils.remove_config_if_empty(self.ini_conf, config):
                with open(config.CONFIG_FILE, "w") as config_file:
                    self.ini_conf.write(config_file)

            logger.debug(
                f"{config.KEY_FILE} key file and configuration removed"
            )
        except FileNotFoundError:
            logger.error("configuration file not found. please run init command first")

    def _get_default_vpc(self) -> str:
        try:
            ec2, _ = AWS._get_clients()
            self._create_vpc(ec2) 
        except:
            logger.debug("Using default VPC")
            
        response = ec2.describe_vpcs(
                Filters=[{"Name": "isDefault", "Values": ["true"]}]
            )
        return response["Vpcs"][0]["VpcId"]


    @classmethod
    def _terminate_cluster_instances(cls, instance_ids: List, clusters_info: Dict):
        logger.debug(f"Terminating cluster instances")
        ec2, ecs = AWS._get_clients()
        if instance_ids:
            waiter = ec2.get_waiter("instance_terminated")
            ec2.terminate_instances(
                DryRun=False,
                InstanceIds=instance_ids,
            )
            waiter.wait(InstanceIds=instance_ids)
        # deletion of now empty ECS clusters
        for (cluster_name, security_group_id) in clusters_info:
            logger.debug(f"Removing cluster {cluster_name}")
            ecs.delete_cluster(cluster=cluster_name)
            logger.debug(f"Removing security group {security_group_id}")
            ec2.delete_security_group(
                GroupId=security_group_id,
            )

    @classmethod
    def _remove_key_pair(cls, key_name: str):
        ec2, _ = AWS._get_clients()
        try:
            logger.debug(f"Removing key pair {key_name}")
            ec2.delete_key_pair(KeyName=key_name)
        except:
            logger.debug("Keypair not found")

    @classmethod
    def _delete_service(
        cls, cluster_name: str, service_name: str, task_name: str
    ) -> List:
        """delete ecs services and return ec2 instance ids."""
        _, ecs = AWS._get_clients()
        try:
            ecs.update_service(
                cluster=cluster_name, service=service_name, desiredCount=0
            )
            ecs.delete_service(cluster=cluster_name, service=service_name)
            logger.debug(f"Stopping cluster service {service_name}")
        except:
            logger.debug("Service not found/not active")
        cls._deregister_tasks(ecs, task_name)
        instance_ids = cls._list_ec2_instances(ecs, cluster_name)
        return instance_ids

    @staticmethod
    def _deregister_tasks(ecs, task_name: str):
        """Deregister all task definitions for ECS cluster"""
        response = ecs.list_task_definitions(familyPrefix=task_name, status="ACTIVE")
        for task_definition in response["taskDefinitionArns"]:
            ecs.deregister_task_definition(taskDefinition=task_definition)
        logger.debug(f"Deregistering cluster task {task_name}")

    @staticmethod
    def _list_ec2_instances(ecs, cluster_name: str) -> List:
        """list all EC2 instances within ECS cluster."""
        response = ecs.list_container_instances(cluster=cluster_name)
        instance_ids = []
        if response["containerInstanceArns"]:
            container_instance_resp = ecs.describe_container_instances(
                cluster=cluster_name,
                containerInstances=response["containerInstanceArns"],
            )
            for ec2_instance in container_instance_resp["containerInstances"]:
                instance_id = ec2_instance["ec2InstanceId"]
                instance_ids.append(instance_id)
        return instance_ids

    def _config_security_group(self) -> str:
        """set egress and ingress rules and configure security group."""
    
        ec2, _ = AWS._get_clients()
        response = ec2.create_security_group(
            Description="Security Group to allow EC2 instance to register into cluster",
            GroupName=self.security_group_name,
            VpcId=self.vpc_id,
            TagSpecifications=[
                {
                    "ResourceType": "security-group",
                    "Tags": [
                        {"Key": "sg-app-use", "Value": "one-container-cloud-tool"},
                    ],
                },
            ],
        )
        security_group_id = response["GroupId"]

        ec2.authorize_security_group_egress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "FromPort": 0,
                    "IpProtocol": "tcp",
                    "IpRanges": [
                        {
                            "CidrIp": "0.0.0.0/0",
                            "Description": "Allow outgoing traffic to all destinations",
                        },
                    ],
                    "ToPort": 65535,
                },
            ],
        )
        data = ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 80,
                    "ToPort": 80,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                },
                {
                    "IpProtocol": "tcp",
                    "FromPort": 443,
                    "ToPort": 443,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                },
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                },
            ],

        )
        logger.debug("configured security group for instance.")

        return security_group_id
