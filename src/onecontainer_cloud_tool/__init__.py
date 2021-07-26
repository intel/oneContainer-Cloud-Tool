import os
import pkg_resources

try:
    version = pkg_resources.get_distribution("onecontainer-cloud-tool").version
except:
    version = None
__version__ = version or "0.2.0"

#os.chdir(os.path.dirname(__file__))
