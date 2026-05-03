"""
Enhanced FastAPI backend for Personalized Learning Path application.
Implements user management, multi-factor path generation, roadmap CRUD,
and course completion/rating tracking.
"""
import os
import sys
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import numpy as np

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import backend.db as db
import backend.recommender as recommender

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "learning_path_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "courses")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
TOP_K_DEFAULT = int(os.getenv("TOP_K", 15))
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

# Global state
class AppState:
    model = None
    course_data = []  # List of dicts
    course_embeddings = None  # Numpy array (N, D)

state = AppState()

def load_courses_and_embeddings():
    """Loads courses and their embeddings from MongoDB into memory."""
    print("Loading courses and embeddings from MongoDB...")
    courses = db.get_all_courses()
    
    if not courses:
        print("WARNING: No courses with embeddings found in DB.")
        state.course_data = []
        state.course_embeddings = None
        return
    
    # Separate data and embeddings
    data_list = []
    emb_list = []
    
    for doc in courses:
        # Extract embedding
        emb = doc.pop("embedding")
        data_list.append(doc)
        emb_list.append(emb)
    
    state.course_data = data_list
    state.course_embeddings = np.array(emb_list)
    print(f"Loaded {len(state.course_data)} courses into memory.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Loading model: {EMBED_MODEL}...")
    state.model = SentenceTransformer(EMBED_MODEL)
    load_courses_and_embeddings()
    yield
    # Shutdown (nothing specific needed)

app = FastAPI(
    title="Learnify API",
    description="Personalized Learning Path Generation with Multi-Factor Recommendations",
    version="2.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ REQUEST/RESPONSE MODELS ============

class CreateUserRequest(BaseModel):
    username: str
    email: str
    skills: List[str] = []
    skill_level: str = "beginner"
    hours_per_week: int = 10
    preferred_language: str = "English"

class UpdateProfileRequest(BaseModel):
    skills: List[str]
    skill_level: str
    hours_per_week: int
    preferred_language: str

class GeneratePathRequest(BaseModel):
    user_id: str
    skill_text: str = ""
    goal_text: str = ""
    interests: List[str] = []
    project_based: bool = False
    language: str = ""
    hours_override: Optional[int] = None

class SaveRoadmapRequest(BaseModel):
    user_id: str
    title: str
    query: str
    meta: dict
    stages: List[dict]

class CompleteRequest(BaseModel):
    course_id: str
    rating: Optional[int] = None  # 1-5

class FeedbackRequest(BaseModel):
    user_id: Optional[str] = None
    message: str
    page: Optional[str] = None

# ============ ENDPOINTS ============

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model": EMBED_MODEL,
        "courses_loaded": len(state.course_data),
        "model_loaded": state.model is not None
    }

# -------- USER MANAGEMENT --------

@app.post("/api/users")
def create_user(req: CreateUserRequest):
    """Create a new user account."""
    try:
        user_id = db.create_user(req.dict())
        return {
            "user_id": user_id,
            "status": "created",
            "username": req.username
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    """Get user profile by ID."""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/users/{user_id}/profile")
def update_profile(user_id: str, req: UpdateProfileRequest):
    """Update user profile."""
    success = db.update_user_profile(user_id, req.dict())
    if not success:
        raise HTTPException(status_code=404, detail="User not found or update failed")
    return {"status": "updated", "user_id": user_id}

@app.get("/api/users/by-email/{email}")
def get_user_by_email(email: str):
    """Get user profile by email address."""
    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# -------- PATH GENERATION --------

@app.post("/api/generate")
def generate_path(req: GeneratePathRequest):
    """
    Generate personalized learning path with multi-factor scoring.
    Returns staged roadmap: Beginner, Advanced, Projects.
    """
    if state.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    if state.course_embeddings is None or len(state.course_data) == 0:
        raise HTTPException(status_code=503, detail="No course data available")
    
    # Get user data
    user = db.get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Override hours if specified
    if req.hours_override:
        user['hours_per_week'] = req.hours_override
    
    # Override language if specified
    if req.language:
        user['preferred_language'] = req.language
    
    # Build comprehensive query text
    query_text = recommender.build_user_query_text(req.dict(), user)
    
    if not query_text:
        raise HTTPException(status_code=400, detail="Please provide at least one search criterion")
    
    # Compute user embedding
    user_emb = state.model.encode([query_text])
    
    # Get global stats for scoring
    global_stats = db.get_global_stats()
    
    # Compute multi-factor scores
    scored_courses = recommender.compute_multi_factor_scores(
        user_emb=user_emb,
        user_data=user,
        courses=state.course_data,
        course_embeddings=state.course_embeddings,
        global_stats=global_stats,
        query_text=query_text,
        request_data=req.dict()
    )
    
    # Sequence into stages
    stages = recommender.sequence_into_stages(
        scored_courses,
        top_n=TOP_K_DEFAULT,
        project_based_preference=req.project_based
    )
    
    # Get top raw candidates for debugging/transparency
    top_candidates = sorted(scored_courses, key=lambda x: x['final_score'], reverse=True)[:20]
    raw_candidates = [
        {
            'id': c.get('id'),
            'title': c.get('title'),
            'score': round(c.get('final_score', 0), 3),
            'difficulty': c.get('difficulty')
        }
        for c in top_candidates
    ]
    
    # Build clean display query for user
    display_query = recommender.build_display_query_text(req.dict(), user)
    
    return {
        "query": display_query,
        "stages": stages,
        "raw_candidates": raw_candidates,
        "total_matches": len(scored_courses)
    }

# -------- ROADMAP MANAGEMENT --------

@app.post("/api/roadmaps")
def save_roadmap(req: SaveRoadmapRequest):
    """Save a generated roadmap for a user."""
    try:
        roadmap_id = db.create_roadmap(req.dict())
        # Add to user's saved roadmaps
        db.add_roadmap_to_user(req.user_id, roadmap_id)
        return {
            "roadmap_id": roadmap_id,
            "status": "saved"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save roadmap: {str(e)}")

@app.get("/api/roadmaps")
def get_roadmaps(user_id: str = Query(..., description="User ID to fetch roadmaps for")):
    """Get all roadmaps for a user."""
    try:
        roadmaps = db.get_roadmaps_by_user(user_id)
        return {"roadmaps": roadmaps, "count": len(roadmaps)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch roadmaps: {str(e)}")

@app.get("/api/roadmaps/{roadmap_id}")
def get_roadmap_detail(roadmap_id: str):
    """Get detailed roadmap by ID."""
    roadmap = db.get_roadmap(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return roadmap

@app.post("/api/roadmaps/{roadmap_id}/complete")
def mark_course_complete(roadmap_id: str, req: CompleteRequest):
    """
    Mark a course as complete in a roadmap.
    Optionally submit a rating (1-5).
    Updates course aggregate ratings.
    """
    # Get roadmap to verify it exists and get user_id
    roadmap = db.get_roadmap(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    
    # Update roadmap course completion
    success = db.update_roadmap_course_completion(
        roadmap_id,
        req.course_id,
        True,
        req.rating
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update roadmap")
    
    # Save rating if provided
    if req.rating:
        if req.rating < 1 or req.rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        db.save_rating(
            user_id=roadmap['user_id'],
            course_id=req.course_id,
            roadmap_id=roadmap_id,
            rating=req.rating,
            completed=True
        )
        
        # Update course aggregate ratings
        db.update_course_ratings(req.course_id, req.rating)
    
    return {
        "status": "completed",
        "course_id": req.course_id,
        "rating_submitted": req.rating is not None
    }

# -------- UTILITY ENDPOINTS --------

@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    """Submit user feedback."""
    try:
        feedback_id = db.save_feedback(req.dict())
        return {
            "status": "received",
            "feedback_id": feedback_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")

@app.post("/api/reload_embeddings")
def reload_embeddings(token: Optional[str] = Query(None, description="Admin token")):
    """
    Admin-only endpoint to reload course embeddings from database.
    Requires ADMIN_TOKEN in query parameter.
    """
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Admin functionality not configured")
    
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid admin token")
    
    try:
        load_courses_and_embeddings()
        return {
            "status": "reloaded",
            "count": len(state.course_data),
            "embedding_dim": state.course_embeddings.shape[1] if state.course_embeddings is not None else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload: {str(e)}")

# -------- INFO ENDPOINTS --------

@app.get("/api/stats")
def get_stats():
    """Get platform statistics."""
    try:
        global_stats = db.get_global_stats()
        return {
            "total_courses": len(state.course_data),
            "global_avg_rating": round(global_stats.get('global_avg_rating', 0), 2),
            "max_popularity": global_stats.get('max_popularity', 0)
        }
    except Exception as e:
        return {
            "total_courses": len(state.course_data),
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
