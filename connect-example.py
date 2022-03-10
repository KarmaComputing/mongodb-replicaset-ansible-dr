from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv(verbose=True)  # take environment variables from .env.

MONGO_DATABASE_URI = os.getenv("MONGO_DATABASE_URI")

uri = MONGO_DATABASE_URI

client = MongoClient(uri)
db = client.admin

breakpoint()
