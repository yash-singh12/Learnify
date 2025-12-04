# insert_sample_courses.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "learning_path_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "courses")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
col = db[COLLECTION_NAME]

sample_courses = [
  {"title":"Frontend development with React","description":"Learn React, components, hooks, build SPAs.","tags":["web","frontend","react"],"difficulty":"beginner","duration_hours":12},
  {"title":"HTML and CSS fundamentals","description":"Basics of HTML5, CSS3, responsive layouts.","tags":["web","html","css"],"difficulty":"beginner","duration_hours":8},
  {"title":"Python programming for beginners","description":"Intro to Python syntax, data structures, small projects.","tags":["python","programming"],"difficulty":"beginner","duration_hours":15},
  {"title":"Intro to Machine Learning","description":"Supervised learning, regression, classification basics.","tags":["ml","machine-learning"],"difficulty":"intermediate","duration_hours":20},
  {"title":"Data Analysis with Pandas","description":"Data cleaning and analysis with Pandas library.","tags":["data","pandas","python"],"difficulty":"intermediate","duration_hours":10}
]

if col.count_documents({}) == 0:
    col.insert_many(sample_courses)
    print("Inserted sample courses.")
else:
    print("Collection is not empty; no insert performed.")

print("Count:", col.count_documents({}))
print("One sample doc:", col.find_one({}, {"title":1, "description":1, "_id":0}))
client.close()
