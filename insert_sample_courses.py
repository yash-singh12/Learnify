import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "learning_path_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "courses")

def insert_data():
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]

    # Sample data
    sample_courses = [
        {
            "title": "Frontend Development with React",
            "description": "Learn React, components, hooks, and build single-page applications. Master modern frontend development.",
            "tags": ["web", "frontend", "react", "javascript"],
            "difficulty": "beginner",
            "duration_hours": 12
        },
        {
            "title": "HTML and CSS Fundamentals",
            "description": "Basics of HTML5, CSS3, responsive layouts, and web design principles.",
            "tags": ["web", "html", "css", "design"],
            "difficulty": "beginner",
            "duration_hours": 8
        },
        {
            "title": "Python Programming for Beginners",
            "description": "Introduction to Python syntax, data structures, loops, functions, and building small projects.",
            "tags": ["python", "programming", "backend"],
            "difficulty": "beginner",
            "duration_hours": 15
        },
        {
            "title": "Intro to Machine Learning",
            "description": "Understand supervised learning, regression, classification, and model evaluation basics.",
            "tags": ["ml", "machine-learning", "data-science", "python"],
            "difficulty": "intermediate",
            "duration_hours": 20
        },
        {
            "title": "Data Analysis with Pandas",
            "description": "Data cleaning, manipulation, and analysis using the powerful Pandas library in Python.",
            "tags": ["data", "pandas", "python", "analytics"],
            "difficulty": "intermediate",
            "duration_hours": 10
        },
        {
            "title": "Advanced Node.js Backend",
            "description": "Build scalable REST APIs with Node.js, Express, and MongoDB. Handle authentication and deployment.",
            "tags": ["backend", "nodejs", "javascript", "api"],
            "difficulty": "advanced",
            "duration_hours": 25
        }
    ]

    # Check if collection is empty to avoid duplicates
    if col.count_documents({}) == 0:
        col.insert_many(sample_courses)
        print(f"Inserted {len(sample_courses)} sample courses into '{DB_NAME}.{COLLECTION_NAME}'.")
    else:
        print(f"Collection '{DB_NAME}.{COLLECTION_NAME}' is not empty. Skipping insertion.")

    client.close()

if __name__ == "__main__":
    insert_data()
