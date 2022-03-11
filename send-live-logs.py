from pymongo import MongoClient
from dotenv import load_dotenv
import os

from faker import Faker

# tail Credit https://stackoverflow.com/a/12523371
import time
import subprocess
import select

load_dotenv(verbose=True)  # take environment variables from .env.

fake = Faker()

MONGO_DATABASE_URI = os.getenv("MONGO_DATABASE_URI")


def getClient():
    """Return mongodb client"""
    uri = MONGO_DATABASE_URI
    client = MongoClient(uri)
    return client


def seedDB():
    # tail -f a log file and send it to mongodb
    client = getClient()
    # Delete everything
    # collection.drop()
    f = subprocess.Popen(
        ["tail", "-F", "apache.log"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # noqa: E501
    )
    p = select.poll()
    p.register(f.stdout)

    while True:
        if p.poll(1):
            newLine = f.stdout.readline()
            print(newLine)
            time.sleep(0.05)
            # Raw logs
            db = client.logs
            collection = db.rawLogs
            rawLog = {"rawLog": newLine}
            print(f"Sending new live log to mongo: {rawLog}")
            collection.insert_one(rawLog)


seedDB()
