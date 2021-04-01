# Development docs

## Implement a new flag to the tool to list prefered instance types for clouds


My first idea is to use a persitent dictionary a sql table might be an overkill

sqlitedb library looks like something to use

data structure

```python
instances = {
    "aws" : ["m1-large", "t1-large"], 
    "azure": ["instance-1", "instance-2"],
    "gcp": [],
    }
```

Listing of instances can looks like this:

cli tool flag: oca --list_instances

Instances that supports functionality of Intel containers

cloud | instance_type
---------------------
aws   | m1-large
aws   | t1-large
gcp   | instance-1
azure | 

Or depending upon how it looks we can further split the listing for each cloud.
