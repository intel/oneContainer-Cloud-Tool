
  

# oneContainer-cloud-tool

  

The oneContainer-cloud-tool utility helps to deploy containers to public cloud services. The `tool` enables a user to map a service to specific hardware and machine image of choice.

## Requirements

- poetry

- Python >=3.7<=3.8

  

## Installation

To install the tool, you can use either `poetry` or `pip`:

Clone the project:
```bash
git clone https://github.com/intel/oneContainer-Cloud-Tool
```

Install using poetry:

```bash
$ cd oneContainer-cloud-tool
$ poetry install
```

Install using pip:

```bash
$ cd oneContainer-cloud-tool

$ pip install .
```

oneContainer-cloud-tool has been installed and can be accessed as `onecontainer_cloud_tool`.


## Usage

  

  

Let's see what we can do with this tool:

```bash
$ onecontainer_cloud_tool --help

Usage: oneContainer-Cloud-Tool [OPTIONS] COMMAND [ARGS]...

  

onecontainer_cloud_tool - deploy containers using specific HW on the

cloud.


This tool supports deploying container instances to cloud services,

mapping to specific HW. Supported cloud services: aws, azure


Options:

--version Show the version and exit.

-c, --cloud [aws|azure] Use a cloud service, options are: aws, azure

--help Show this message and exit.

Commands:
init
list_instances
start
stop
```
The tool's four commands are `init`, to initialize a cloud service, `start`, to start a container service mapped to specific hardware of choice, `stop`, to delete the deployed service and any collaterals, and finally `list_instances` which includes instance hardware for each cloud service.

### Init cloud provider
To initialize the cloud service, an `access-key`, `secret-key` , `region` and name of the `cloud` service to be used, default cloud service is `aws`.

  

Note: for Azure, the authentication method is through the browser and thus the `access-key`, `secret-key` options are not needed.

```bash
$ onecontainer-cloud-tool init --help
```

Output of the command is:

```bash
Usage: onecontainer-cloud-tool init [OPTIONS]

Options:

-c, --cloud [aws, azure] Use a cloud service, options are: aws

--access-key TEXT Access Key Id to access the cloud service

--secret-key TEXT Secret Key to access the cloud service

--region [us-east-1|us-east-2|us-west-1|us-west-2] 
The region where the service be located

--help Show this message and exit.
```

Keys and configs are persisted on disk, written to `occ_config.ini` file and a `PEM` file (both files are temporary and will be removed on the `stop` command).

The `occ_config.ini` stores initialization information to be use by the start command and is located in the following path:
`~/.config/occ_config.ini`

The `PEM` file is the private key generated to access the instances through SSH. The file is located in the following path:
`~/ssh/key_name.pem`


### Start cloud service

As mentioned above, the `start` command is used to deploy a container service by mapping it to a specific HW of choice. Optionally a machine image name can also be given using the flag `--mi`.

```bash
$ onecontainer-cloud-tool start --help
```


Output of the command is:

  

  

```bash
Usage: onecontainer-cloud-tool start [OPTIONS]


Options:

-c, --cloud [aws, azure] Use a cloud service, options are: aws, azure

--mi TEXT Machine Image required for service

--container-image-url TEXT Container image URL.

--instance-type TEXT HW instance type

--help Show this message and exit.
```

  
The `occ_config.ini` is updated to contain information about the newly created service.

The `PEM` file is associated to the service to allow Secure Shell connection.

This command outputs the information on how to connect to the instance via SSH.

  

  

### Stop cloud service


This command helps to stop the running services.

  

  

```bash
$ onecontainer-cloud-tool stop --help
```

  

  

Output of the command is:

  

  

```bash
Usage: onecontainer-cloud-tool stop [OPTIONS]

Options:

-c, --cloud [aws, azure] Use a cloud service, options are: aws, azure

  

--help Show this message and exit.

```

  

The command will try to stop the running docker service and delete any collaterals.

  

  

The `occ_config.ini` is used for cleanup purposes and then removed.

  

The `PEM` file is also removed.

  

  

Once `stop` is successfully executed, to start a new service, please use `init` first.

  

### List Instances supported for each cloud provider

  

This command lists all HW instances for a given cloud service.

  

  

```bash
$ onecontainer-cloud-tool list_instances --help
```

Output of the command is:

  

```bash

Usage: oneContainer-Cloud-Tool list_instances [OPTIONS]

list cloud instances for intel.
 
Options:

-c, --cloud [aws|azure|all] list instances for the cloud

--help Show this message and exit.

```

  

If the `--cloud` flag is not provided, instances for all cloud services are shown.

  

  

## Examples

This section describes examples that demonstrate how to use the `OneContainer-Cloud-Tool` with the cloud providers.

  

### AWS

Note: In order to succesfully utilize the tool with AWS. A role named `ecsInstanceRole` should be created with the following permissions:  

-  `AmazonEC2ContainerServiceforEC2Role`


#### Initialization

```bash

$ oneContainer-Cloud-Tool --cloud aws init --access-key {your key} --secret-key {your key} --region us-east-1

  

-Writing AWS access and secret key in occ_config.ini

-Writing private key file name in occ_config.ini file

```  

#### Deployment

```bash

$ oneContainer-Cloud-Tool --cloud aws start --machine-image ami-0128839b21d19300e \

--container-image-url sysstacks/dlrs-tensorflow-ubuntu --instance-type m5n.large

  
- Success!

- You can access the deployed solution via SSH

- ec2-user@domain

- or

- ec2@ip-address

```
Note: Omitting `--machine-image` will set the default AMI (Linux 2).

 
#### Stop

```bash
$ oneContainer-Cloud-Tool --cloud aws stop

  
-{key_name}.pem key file, and configuration removed

-Removed configuration from config file.

```

#### Instance Listing
```bash

$ oneContainer-Cloud-Tool list_instances -c aws

Preferred Instance Types:
┏━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ cloud ┃ family  ┃ size                                                                   ┃
┡━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ aws   │ c5      │ 12xlarge, 24xlarge, metal                                              │
│       │ c5d     │ 12xlarge, 24xlarge, metal                                              │
│       │ m5n     │ large, xlarge, 2xlarge, 4xlarge, 8xlarge, 12xlarge, 16xlarge, 24xlarge │
│       │ m5dn    │ large, xlarge, 2xlarge, 4xlarge, 8xlarge, 12xlarge, 16xlarge, 24xlarge │
│       │ r5n     │ large, xlarge, 2xlarge, 4xlarge, 8xlarge, 12xlarge, 16xlarge, 24xlarge │
│       │ r5dn    │ large, xlarge, 2xlarge, 4xlarge, 8xlarge, 12xlarge, 16xlarge, 24xlarge │
│       │ m5zn    │ large, xlarge, 2xlarge, 3xlarge, 6xlarge, 12xlarge, metal              │
│       │ d3      │ xlarge, 2xlarge, 4xlarge, 8xlarge                                      │
│       │ d3en    │ xlarge, 2xlarge, 4xlarge, 6xlarge, 8xlarge, 12xlarge                   │
└───────┴─────────┴────────────────────────────────────────────────────────────────────────┘
```

### Azure


#### Initialization
Note: In order to succesfully login with Azure there are three different methods:

- Environment Variables: Set credentials as env variables. [Azure Environment Variables](https://azuresdkdocs.blob.core.windows.net/$web/python/azure-identity/1.4.0/azure.identity.html#azure.identity.EnvironmentCredential)
- Login with Azure CLI: `az login` [Azure CLI Installation](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- Browser Login: If the previous methods fail, the tool will try an interactive browser login.
  

```bash

$ oneContainer-Cloud-Tool --cloud azure init --region eastus

  

- Writing {region} as region for  AZURE  in config file

- Writing azure session in config file

- Initialization Successful

```

  

Note: Current authentication workflow does not require the use of access keys, as iauthentication is done interactively with the browser.

#### Deployment

```bash

$ oneContainer-Cloud-Tool --cloud azure start --container-image-url sysstacks/dlrs-tensorflow-ubuntu

--instance-type Standard_DS1_v2

  

- Success!

- You can access the deployed solution via SSH

- azureuser@ip-address

- Use the private key file generated to authenticate in the ssh connection

```

Note: Omitting `--machine-image` will set the default UbuntuServer image.

  

#### Stop

```bash

$ oneContainer-Cloud-Tool --cloud azure stop

  

-{key_name}.pem key file, and configuration removed

-Removed configuration from config file.

```

#### Instance Listing
```bash

$ oneContainer-Cloud-Tool list_instances -c azure

Preferred Instance Types:
┏━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ cloud ┃ family       ┃ size                                                                                                                      ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ azure │ F2_series    │ Standard_F2s_v2, Standard_F4s_v2, Standard_F8s_v2, Standard_F16s_v2, Standard_F32s_v2, Standard_F48s_v2, Standard_F64s_v2 │
│       │ D4_Series    │ Standard_D2_v4, Standard_D4_v4, Standard_D8_v4, Standard_D16_v4, Standard_D32_v4, Standard_D48_v4, Standard_D64_v4        │
│       │ Dsv4_series  │ Standard_D2s_v4, Standard_D4s_v4, Standard_D8s_v4, Standard_D16s_v4, Standard_D32s_v4, Standard_D48s_v4, Standard_D64s_v4 │
│       │ Dv3-series   │ Standard_D2_v3, Standard_D4_v3, Standard_D8_v3, Standard_D16_v3, Standard_D32_v3, Standard_D48_v3, Standard_D64_v3        │
└───────┴──────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

```

## Contributing

We'd love to accept your patches, if you have improvements to stacks, send us your pull requests or if you find any issues, raise an issue. Contributions can be anything from documentation updates to optimizations!


## Security Issues

  

  

Security issues can be reported to Intel's security incident response team via https://intel.com/security.

  
  

## Mailing List

  

See our public [mailing list](https://lists.01.org/mailman/listinfo/stacks) page for details on how to contact us. You should only subscribe to the Stacks mailing lists using an email address that you don't mind being public.
