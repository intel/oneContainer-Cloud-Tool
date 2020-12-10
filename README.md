# oneContainer-cloud-tool
The oneContainer-cloud-tool utility helps to deploy containers to public cloud services. The `tool` enables a user
to map a service to specific hardware and machine image of choice.

## Requirements

- poetry
- Python >=3.7

## Installation

To install the tool, run:

```bash
$ cd oneContainer-cloud-tool
$ poetry install
```

oneContainer-cloud-tool has been installed and can be accessed as `onecontainer_cloud_tool`.

## Usage

Let's see what we can do with this tool:

```bash
$ poetry run onecontainer_cloud_tool --help
```

The output should look like:

```bash
Usage: onecontainer-cloud-tool [OPTIONS] COMMAND [ARGS]...

  onecontainer_cloud_tool - deploy containers using specific HW on
  the cloud.

  This tool supports deploying container instances to cloud services,
  mapping to specific HW. Supported cloud services: aws

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  init
  start
  stop
```

The tool's three options are `init`, to initialize a cloud service, `start`, to start a container service mapped to specific hardware of choice, and finally `stop`, to delete the deployed service and any collaterals.

### Init cloud provider

To initialize the cloud service, an `access-key`, `secret-key` , `region` and name of the `cloud` service to be used, default cloud service is `aws`.

```bash
$ poetry run onecontainer-cloud-tool init --help
```

Output of the command is:

```bash
Usage: onecontainer-cloud-tool init [OPTIONS]

Options:
  -c, --cloud [aws]               Use a cloud service, options are: aws
  --access-key TEXT               Access Key Id to access the cloud service
  --secret-key TEXT               Secret Key to access the cloud service
  --region [us-east-1|us-east-2|us-west-1|us-west-2]
                                  The region where the  service be located
  --help                          Show this message and exit.
```

Keys and configs are persisted on disk, written to `occ_config.ini` file and a `PEM` file (both files are temporary and will be removed on the `stop` command).
The `occ_config.ini` stores initialization information to be use by the start command.
The `PEM` file is the private key generated to access the instances through SSH.

### Start cloud service

As mentioned above, the `start` command is used to deploy a container service by mapping it to a specific HW of choice. Optionally a machine image name can also be given using the flag `--mi`.

```bash
$ poetry run onecontainer-cloud-tool start --help
```

Output of the command is:

```bash
Usage: onecontainer-cloud-tool start [OPTIONS]

Options:
  -c, --cloud [aws]             Use a cloud service, options are: aws
  --mi TEXT                     Machine Image required for service
  --container-image-url TEXT    Container image URL.
  --instance-type TEXT          HW instance type
  --help                        Show this message and exit.
```

The `occ_config.ini` is updated to contain information about the newly created service.
The `PEM` file is associated to the service to allow Secure Shell connection.

### Stop cloud service

This command helps to stop the running services.

```bash
$ poetry run onecontainer-cloud-tool stop --help
```

Output of the command is:

```bash
Usage: onecontainer-cloud-tool stop [OPTIONS]

Options:
  -c, --cloud [aws]  Use a cloud service, options are: aws
  --help             Show this message and exit.
```
The command will try to stop the running docker service and delete any collaterals.

The `occ_config.ini` is used for cleanup purposes and then removed. 
The `PEM` file is also removed.

Once `stop` is successfully executed, to start a new service, please use `init` first.

### Contributing

We'd love to accept your patches, if you have improvements to stacks, send us your pull requests or if you find any issues, raise an issue. Contributions can be anything from documentation updates to optimizations!

### Security Issues

Security issues can be reported to Intel's security incident response team via https://intel.com/security.

### Mailing List

See our public [mailing list](https://lists.01.org/mailman/listinfo/stacks) page for details on how to contact us. You should only subscribe to the Stacks mailing lists using an email address that you don't mind being public.

