from pymongo import MongoClient
from dotenv import load_dotenv
import os
import datetime

from faker import Faker
from random import randrange

# Based on:
# https://www.mongodb.com/developer/how-to/seed-database-with-fake-data/
# Converted to python

load_dotenv(verbose=True)  # take environment variables from .env.

fake = Faker()

MONGO_DATABASE_URI = os.getenv("MONGO_DATABASE_URI")


def getClient():
    """Return mongodb client"""
    uri = MONGO_DATABASE_URI
    client = MongoClient(uri)
    return client


def randomIntFromInterval(min, max):
    return randrange(min, max)


def seedDB():
    client = getClient()
    db = client.iot
    collection = db.kitty_litter_time_series
    # Delete everything
    # collection.drop()
    # Make a bunch of time series data
    timeSeriesData = []

    for i in range(0, 100000):
        firstName = fake.first_name()
        lastName = fake.last_name()
        newDay = {
            "timestamp_day": datetime.datetime.utcnow(),
            "cat": fake.word(),
            "owner": {
                "email": fake.email(),
                "firstName": firstName,
                "lastName": lastName,
            },
            "events": [],
        }
        timeSeriesData.append(newDay)
    collection.insert_many(timeSeriesData)
    client.close()


seedDB()
