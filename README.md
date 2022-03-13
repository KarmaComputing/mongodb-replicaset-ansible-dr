# Mongodb ansible replica set cluster

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

Keep shortening the apache.log locally so you don't fill your own hard drive:  [credit](https://stackoverflow.com/a/18072642)
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




## References

- (old) blog https://blog.karmacomputing.co.uk/how-to-create-mongodb-replica-set-with-authentication-ubuntu-16-04/
(Based on [mongodb article](https://www.mongodb.com/developer/how-to/seed-database-with-fake-data/)
converted to python).
