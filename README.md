# Mongodb ansibple replica set cluster

Example usage
```
ansible-playbook -i inventory.yml playbook.yml
```

# How to connect to existing cluster using python

Do settings:
```
cp .env.example .env
```

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
log-generator log-generator.conf
```

In another terminal, send logs to mongo (like `tail -f`)

```
python send-live-logs.py
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







## References

- (old) blog https://blog.karmacomputing.co.uk/how-to-create-mongodb-replica-set-with-authentication-ubuntu-16-04/
(Based on [mongodb article](https://www.mongodb.com/developer/how-to/seed-database-with-fake-data/)
converted to python).
