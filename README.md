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

(Based on [mongodb article](https://www.mongodb.com/developer/how-to/seed-database-with-fake-data/)
converted to python).


## References

- (old) blog https://blog.karmacomputing.co.uk/how-to-create-mongodb-replica-set-with-authentication-ubuntu-16-04/
