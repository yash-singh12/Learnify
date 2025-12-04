# insert_dummy_courses.py
import os, json
from pymongo import MongoClient, ReplaceOne
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "learning_path_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "courses")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
col = db[COLLECTION_NAME]

with open("courses_dummy.json", "r", encoding="utf-8") as f:
    courses = json.load(f)

ops = []
for c in courses:
    # use title as unique key for idempotent upsert
    ops.append(ReplaceOne({"title": c["title"]}, {**c}, upsert=True))

if ops:
    res = col.bulk_write(ops)
    print("Upserted/modified:", res.bulk_api_result)
else:
    print("No operations")
client.close()
