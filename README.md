# Mongodb migration from one datacenter to another

Objective:
- Migrate a MongoDB replicaset cluster live with minimal downtime (ideally no downtime at all)

This repo demonstrates how to migrate a MongoDB replicaset cluster from one MongoDB cluster to another.

The general steps are as follows:

1. Create a new (empty) host in the desired new datacenter with mongodb installed, and same keyfile as the old cluster
2. Add the new (empty) host to the new cluster
3. Wait for the new replica to syncronise with the existing replica set
4. Update any applications, as required, to be aware of the new hosts in the replica set
5. Verify all applications can reach and authenticate with the new cluster
6. Gradually reduce the number of hosts in the old cluster, one at a time, until the old cluster is down

### MongoDB cheet sheet commands

- Which node is the current primary?

	`$ mongo --host localhost:27017 --eval "rs.isMaster().primary"`

	Or
	`rs.hello()`
- Always connect to the mongo primary, not a secondary

	`mongo "mongodb://127.0.0.1/?replicaSet=rs03"`
- MongoDB become admin

	`db.getSiblingDB("admin").auth("username", "password")`


## Setup 

Do settings (update for your settings)

```
cp .env.example .env
```

## Create n hosts
[See high-availability web services](https://github.com/KarmaComputing/high-availability-web-services/tree/8-storage)
```
./hetzner/hetzner-create-n-servers.sh 5 cx11 centos-7
```

Update inventory.yml with the 5 ip addresses in `servers.txt`.

Install mongo as replica set accross all 5 hosts:

```
ansible-playbook -i inventory.yml playbook.yml
```

ssh into one of the nodes:

```
ssh root@<ip-address>
mongo
```

Initiate replica set, and keep terminal session open
```
rs.initiate(
  {
    _id : 'rs03',
    members: [
      { _id : 0, host : "<ip-address>:27017" },
      { _id : 1, host : "<ip-address>:27017" },
      { _id : 2, host : "<ip-address>:27017" },
      { _id : 3, host : "<ip-address>:27017" },
      { _id : 4, host : "<ip-address>:27017" }
    ]
  }
)
```
expected output:
```
{ "ok" : 1 }
rs03:SECONDARY> 
```

Create admin user:

```
admin = db.getSiblingDB("admin")
```

Set password for admin:
```
rs03:PRIMARY> admin.createUser(
...   {
...     user: "admin",
...     pwd: "changeme",
...     roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
...   }
... )
Successfully added user: {
	"user" : "admin",
	"roles" : [
		{
			"role" : "userAdminAnyDatabase",
			"db" : "admin"
		}
	]
}
```
Expected output:
```
Successfully added user: {
	"user" : "admin",
	"roles" : [
		{
			"role" : "userAdminAnyDatabase",
			"db" : "admin"
		}
	]
}
```



Verify login:
```
rs03:PRIMARY> db.getSiblingDB("admin").auth("admin", "changeme")
```
Expected output: `1`


Give admin root role (or `replSetGetStatus`) so can get replica status and other admin tasks: [ref](https://stackoverflow.com/a/29472184)
```
use admin
db.grantRolesToUser('admin', [{ role: 'root', db: 'admin' }])
```


Add non-admin user:
```
use admin
db.createUser({user: "fred", pwd: "changeme", roles: [{role: "userAdminAnyDatabase", db: "admin"}, "readWriteAnyDatabase"]})
```

Expected output:
```
Successfully added user: {
	"user" : "fred",
	"roles" : [
		{
			"role" : "userAdminAnyDatabase",
			"db" : "admin"
		},
		"readWriteAnyDatabase"
	]
}
```

SSH to any node, and automatically login to the current mongo
primary:
```
ssh root@<ip-address>
mongo "mongodb://127.0.0.1/?replicaSet=rs03"
rs03:PRIMARY> db.getSiblingDB("admin").auth("fred", "changeme")
1
rs03:PRIMARY> show dbs
admin   0.000GB
config  0.000GB
local   0.000GB
rs03:PRIMARY>
```

Find only type string logs:
```
db.rawLogs.find({rawLog: {$type: "string"}}).pretty()
```

## Uninstall / Delete whole project

> **Warning** this is destructive.

Remove all nodes from the project:

```
./hetzner/hetzner-delete-all-servers.sh
```


# How to connect to existing cluster using python


Connect to db:
```
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

python connect-example.py
# then type db to see the connection
# Read more: https://pymongo.readthedocs.io/en/stable/tutorial.html
```

# Fill database with dummy data

Pretty crude/basic fill of database:
```
. venv/bin/activate
python seeddb.py
```

## Simulate sending live http logs to mongodb

- Logs get written to database name `logs`
- Into collection named: `rawLogs`

Start generating live logs (fake logs)
```
. venv/bin/activate
log-generator log-generator.conf
```

In another terminal, send logs to mongo (like `tail -f`)

```
. venv/bin/activate
python send-live-logs.py
```

> To send many more logs, a simple way is to use `tmux` and create mutliple terminals, each all sending logs to mongo. The logs will be duplicated, but that's OK for testing.


Note you may want to keep shortening the apache.log locally so you don't fill your own hard drive:  [credit](https://stackoverflow.com/a/18072642)
```
fallocate -c -o 0 -l 1M apache.log
```

Sample result:
```
rs03:PRIMARY> db.rawLogs.findOne()
{
	"_id" : ObjectId("622bd6183dceeab8bc0e2439"),
	"rawLog" : "108.132.11.137 - - [11/Mar/2022:22:47:40 +0000] \"GET /lists HTTP/1.1\" 200 3462\n"
}
rs03:PRIMARY> show dbs
admin          0.001GB
config         0.000GB
iot            0.147GB
local          0.208GB
logs           0.001GB
test_database  0.000GB
```


## View database with a UI

```
docker run -it --name dbgate-instance --restart always -p 3000:3000 dbgate/dbgate
```
Visit: http://127.0.0.1:3000
Then add new Mongodb connection using "Use database URL" option (using .env setting)

# Add new replica to cluster

https://docs.mongodb.com/manual/tutorial/expand-replica-set/#prepare-the-data-directory

Find out the primary node, and connect to it via ssh.

```
db.hello()
```

Once connected to the current Primary node, add the new replica to the MongoDB replicaset config:

> Note, the `priority` is set to `0`, and `votes` to `0` to prevent the new node from being elected as primary. This is important incase client applications are unable to connect to the new node, as this could cause an outage.

> Using a DNS hostname is prefered over and ip address.
```
rs.add( { host: "<ip-address>s:27017", "priority": 0, "votes": 0 } )
```
## Get the status of a new syncing replica:

> No way to know exact progress [ref](https://stackoverflow.com/questions/28180167/how-to-determine-overall-progress-of-the-startup2-btree-bottom-up-step).

1. Authenticate with mongodb
2. Issue `rs.status()`

3. Observe: `"stateStr" : "STARTUP2"` , which mean the node is still syncing with the other replicas

```
		{
			"_id" : 6,
			"name" : "<ip-address>:27017",
			"health" : 1,
			"state" : 5,
			"stateStr" : "STARTUP2",
			"uptime" : 461,
			"optime" : {
				"ts" : Timestamp(0, 0),
				"t" : NumberLong(-1)
			},
			"optimeDate" : ISODate("1970-01-01T00:00:00Z"),
			"syncingTo" : "<ip-address>:27017",
			"syncSourceHost" : "<ip-address>:27017",
			"syncSourceId" : 5,
			"infoMessage" : "",
			"configVersion" : 4,
			"self" : true,
			"lastHeartbeatMessage" : ""
		}
```


## Allow / promote new node to a voting node so it *may* become a primary

> Note *may* become a primary, not always. Only if a node wins the election will it become a primary.

### Change replica priority
See MongoDocs [adjust-replica-set-member-priority](https://docs.mongodb.com/manual/tutorial/adjust-replica-set-member-priority/)


Connect to primary then:

```
db.hello() # find primary
db.getSiblingDB("admin").auth("admin","changeme")
```

Get current config:
```
cfg = rs.conf()
```

Identify which replica you want to change, e.g the sixth one, and change it's priority to `1` (causing it to be a voting node):

```
cfg.members[5].priority = 1
cfg.members[5].votes = 1
```

Save the change:
```
rs03:PRIMARY> rs.reconfig(cfg)
````
Observe:
```
{ "ok" : 1 }
```

# On-prem to AWS connectivity (Wireguard VPN tunneling)

> tldr: Install wireguard on the bastion host, and allow traffic Wireguard only traffic from the basion to the private subnets using two Security groups.


> The first Security Group will allow access to the WireGuard server from the Internet

> The second Security Group will allow access to the internal application from the WireGuard server (and block all other access).

1. **First security group**:
    
	Create a new Security group `wireguard-bastion` for the bastion host to allow incomming traffic (UDP port 51820) and assign this Security Group to the bastion host.


2. **Seccond security group**:

    Create a new Securtiy Group called  `access-from-wireguard-bastion`. With inbound rule to allow all protocol and all port ranges. The `source` must be the id of the `wireguard-bastion` security group.

	Assign this Security Group to each of the mongodb nodes, which will have the effect of on premise wireguard nodes to be able to connect to AWS instances in the private subnets during the dataloading process.



SSH into the bastion/wg server

Install wireguard using centos method https://www.wireguard.com/install/


Ref docs [procustodibus guide wireguard-with-aws-private-subnets](https://www.procustodibus.com/blog/2021/02/wireguard-with-aws-private-subnets/)



## Troubleshooting
### errors when adding a new replica

`F -        [repl writer worker 3] out of memory.`

How to resovle: 

Power off, increase ram, restart mongo service (may take a long time, cpu 100%)
See logs: 
```INDEX    [repl writer worker 8] 	 building index using bulk method; build may temporarily use up to 500 megabytes of RAM``` (500MB is the default for mongodb 3.6)


### `"errmsg" : "Replica set configuration contains 8 voting members, but must be at least 1 and no more than 7",
`
How to resolve: reduce votes to 0, prioroty to 0. 


### `AuthenticationFailed: SCRAM authentication failed, storedKey mismatch`

Are you sure old replicas arn't still trying to connect? Check the source of the error.

### `(not reachable/healthy)` / `Couldn't get a connection within the time limit`



## References

- (old) blog https://blog.karmacomputing.co.uk/how-to-create-mongodb-replica-set-with-authentication-ubuntu-16-04/
(Based on [mongodb article](https://www.mongodb.com/developer/how-to/seed-database-with-fake-data/)
converted to python).
