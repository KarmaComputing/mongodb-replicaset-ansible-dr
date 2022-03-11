from pymongo import MongoClient
from dotenv import load_dotenv
from faker import Faker
from faker.providers import DynamicProvider
import os

job_provider = DynamicProvider(
    provider_name="job", elements=["designer", "accounting", "developer", "marketing"]
)
age_provider = DynamicProvider(provider_name="age", elements=["20", "25", "30", "40"])
database_provider = DynamicProvider(
    provider_name="database",
    elements=[
        "text",
        "hello",
        "payments",
        "customers",
        "posts",
        "database",
        "databases",
    ],
)
fake = Faker()
fake.add_provider(job_provider)
fake.add_provider(age_provider)
fake.add_provider(database_provider)

load_dotenv(verbose=True)  # take environment variables from .env.

MONGO_DATABASE_URI = os.getenv("MONGO_DATABASE_URI")
MONGO_SLAVE_URI = os.getenv("MONGO_DATABASE_URI")

uri = MONGO_DATABASE_URI
slave = MONGO_SLAVE_URI

client = MongoClient(uri)
client_slave = MongoClient(slave)

db = client.admin
db_slave = client_slave.admin

print("table names", db.list_collection_names())
# inserting 10 database sets in 5 random servers
for _ in range(5):
    database = fake.database()
    posts = db[database]
    posts_slave = db_slave[database]

    for _ in range(10):
        print(fake.name())
        EMPLOYEE = {"Name": fake.name(), "age": fake.age(), "job": fake.job()}
        post_id = posts.insert_one(EMPLOYEE).inserted_id
    # print all values in all used tables
    for post in posts.find():
        print("Values inside table primary server", post)
    for posts_slave in posts_slave.find():
        print("values inside tables secondary servers", posts_slave)

# check for created tables
print("table names in primary server", db.list_collection_names())

# checking all the other servers
print("table names in other servers", db_slave.list_collection_names())
