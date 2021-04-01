"""cloud service factory."""
from typing import Optional
from onecontainer_cloud_tool.cloud.aws import AWS
from onecontainer_cloud_tool.cloud.m_azure import Azure
from onecontainer_cloud_tool.cloud.abstract_cloud import Cloud


def service(cloud="aws") -> Optional[Cloud]:
    """service factory that dispatches to the right cloud service."""
    if cloud == "aws":
        return AWS()
    elif cloud == "azure":
        return Azure()
    else:
        raise NotImplementedError
