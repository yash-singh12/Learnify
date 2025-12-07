"""
Database helper functions for MongoDB operations.
Handles CRUD operations for users, roadmaps, ratings, and courses.
"""
import os
from datetime import datetime
from typing import List, Dict, Optional
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "learning_path_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "courses")

def get_mongo_client():
    """Get MongoDB client connection."""
    return MongoClient(MONGODB_URI)

def get_collection(name: str):
    """Get a collection by name."""
    client = get_mongo_client()
    db = client[DB_NAME]
    return db[name], client

# ============ USER OPERATIONS ============

def create_user(user_data: dict) -> str:
    """Create a new user and return user_id."""
    col, client = get_collection("users")
    user_data["created_at"] = datetime.utcnow()
    user_data["saved_roadmap_ids"] = []
    result = col.insert_one(user_data)
    client.close()
    return str(result.inserted_id)

def get_user(user_id: str) -> Optional[dict]:
    """Get user by ID."""
    col, client = get_collection("users")
    try:
        user = col.find_one({"_id": ObjectId(user_id)})
        if user:
            user["id"] = str(user["_id"])
            del user["_id"]
        client.close()
        return user
    except:
        client.close()
        return None

def update_user_profile(user_id: str, profile_data: dict) -> bool:
    """Update user profile fields."""
    col, client = get_collection("users")
    try:
        result = col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": profile_data}
        )
        client.close()
        return result.modified_count > 0
    except:
        client.close()
        return False

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email address."""
    col, client = get_collection("users")
    try:
        user = col.find_one({"email": email})
        if user:
            user["id"] = str(user["_id"])
            del user["_id"]
        client.close()
        return user
    except:
        client.close()
        return None


def add_roadmap_to_user(user_id: str, roadmap_id: str) -> bool:
    """Add roadmap ID to user's saved roadmaps list."""
    col, client = get_collection("users")
    try:
        result = col.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"saved_roadmap_ids": ObjectId(roadmap_id)}}
        )
        client.close()
        return result.modified_count > 0
    except:
        client.close()
        return False

# ============ ROADMAP OPERATIONS ============

def create_roadmap(roadmap_data: dict) -> str:
    """Create a new roadmap and return roadmap_id."""
    col, client = get_collection("roadmaps")
    roadmap_data["created_at"] = datetime.utcnow()
    # Convert user_id string to ObjectId
    if "user_id" in roadmap_data and isinstance(roadmap_data["user_id"], str):
        roadmap_data["user_id"] = ObjectId(roadmap_data["user_id"])
    result = col.insert_one(roadmap_data)
    client.close()
    return str(result.inserted_id)

def get_roadmaps_by_user(user_id: str) -> List[dict]:
    """Get all roadmaps for a user."""
    col, client = get_collection("roadmaps")
    try:
        roadmaps = list(col.find({"user_id": ObjectId(user_id)}).sort("created_at", -1))
        for rm in roadmaps:
            rm["id"] = str(rm["_id"])
            rm["user_id"] = str(rm["user_id"])
            del rm["_id"]
        client.close()
        return roadmaps
    except:
        client.close()
        return []

def get_roadmap(roadmap_id: str) -> Optional[dict]:
    """Get roadmap by ID."""
    col, client = get_collection("roadmaps")
    try:
        roadmap = col.find_one({"_id": ObjectId(roadmap_id)})
        if roadmap:
            roadmap["id"] = str(roadmap["_id"])
            roadmap["user_id"] = str(roadmap["user_id"])
            del roadmap["_id"]
        client.close()
        return roadmap
    except:
        client.close()
        return None

def update_roadmap_course_completion(roadmap_id: str, course_id: str, completed: bool, rating: Optional[int] = None) -> bool:
    """Update course completion status and rating in a roadmap."""
    col, client = get_collection("roadmaps")
    try:
        # Update nested course in stages array
        result = col.update_one(
            {
                "_id": ObjectId(roadmap_id),
                "stages.courses.course_id": course_id
            },
            {
                "$set": {
                    "stages.$[].courses.$[course].completed": completed,
                    "stages.$[].courses.$[course].rating": rating
                }
            },
            array_filters=[{"course.course_id": course_id}]
        )
        client.close()
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating roadmap: {e}")
        client.close()
        return False

# ============ RATING OPERATIONS ============

def save_rating(user_id: str, course_id: str, roadmap_id: Optional[str], rating: int, completed: bool, note: str = "") -> str:
    """Save a course rating."""
    col, client = get_collection("ratings")
    rating_data = {
        "user_id": ObjectId(user_id),
        "course_id": course_id,
        "roadmap_id": ObjectId(roadmap_id) if roadmap_id else None,
        "rating": rating,
        "completed": completed,
        "timestamp": datetime.utcnow(),
        "note": note
    }
    result = col.insert_one(rating_data)
    client.close()
    return str(result.inserted_id)

def update_course_ratings(course_id: str, new_rating: int) -> bool:
    """Update course aggregate ratings (incremental update)."""
    col, client = get_collection(COLLECTION_NAME)
    try:
        # Get current course stats
        course = col.find_one({"_id": ObjectId(course_id)})
        if not course:
            client.close()
            return False
        
        # Calculate new average
        old_count = course.get("rating_count", 0)
        old_sum = course.get("rating_sum", 0)
        
        new_count = old_count + 1
        new_sum = old_sum + new_rating
        new_avg = new_sum / new_count
        
        # Update course
        result = col.update_one(
            {"_id": ObjectId(course_id)},
            {
                "$set": {
                    "rating_count": new_count,
                    "rating_sum": new_sum,
                    "avg_rating": new_avg
                }
            }
        )
        client.close()
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating course ratings: {e}")
        client.close()
        return False

# ============ STATS & UTILITIES ============

def get_global_stats() -> dict:
    """Get global statistics for recommendation scoring."""
    col, client = get_collection(COLLECTION_NAME)
    
    # Get max popularity
    max_pop_doc = col.find_one(sort=[("popularity", -1)])
    max_popularity = max_pop_doc.get("popularity", 100) if max_pop_doc else 100
    
    # Calculate global average rating (only courses with ratings)
    pipeline = [
        {"$match": {"rating_count": {"$gt": 0}}},
        {"$group": {
            "_id": None,
            "avg_rating": {"$avg": "$avg_rating"},
            "total_courses": {"$sum": 1}
        }}
    ]
    result = list(col.aggregate(pipeline))
    
    if result:
        global_avg_rating = result[0]["avg_rating"]
    else:
        global_avg_rating = 3.5  # fallback
    
    client.close()
    
    return {
        "max_popularity": max_popularity,
        "global_avg_rating": global_avg_rating
    }

def save_feedback(feedback_data: dict) -> str:
    """Save user feedback."""
    col, client = get_collection("feedback")
    feedback_data["timestamp"] = datetime.utcnow()
    result = col.insert_one(feedback_data)
    client.close()
    return str(result.inserted_id)

def get_all_courses() -> List[dict]:
    """Get all courses with embeddings."""
    col, client = get_collection(COLLECTION_NAME)
    courses = list(col.find({"embedding": {"$exists": True, "$ne": None}}))
    
    for course in courses:
        course["id"] = str(course["_id"])
        del course["_id"]
    
    client.close()
    return courses
