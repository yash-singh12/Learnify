import os
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "learning_path_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "courses")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
TOP_K_DEFAULT = int(os.getenv("TOP_K", 5))

# Global state
class AppState:
    model = None
    course_data = [] # List of dicts: {_id, title, description, ...}
    course_embeddings = None # Numpy array (N, D)

state = AppState()

def load_courses_and_embeddings():
    """Loads courses and their embeddings from MongoDB into memory."""
    print("Loading courses and embeddings from MongoDB...")
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]
    
    # Fetch all courses that have embeddings
    cursor = col.find({"embedding": {"$exists": True, "$ne": None}})
    courses = list(cursor)
    
    if not courses:
        print("WARNING: No courses with embeddings found in DB.")
        state.course_data = []
        state.course_embeddings = None
        client.close()
        return

    # Separate data and embeddings
    data_list = []
    emb_list = []
    
    for doc in courses:
        # Store metadata (convert _id to string)
        doc["id"] = str(doc["_id"])
        del doc["_id"] # Remove original ObjectId to avoid serialization issues
        # Extract embedding
        emb = doc.pop("embedding")
        data_list.append(doc)
        emb_list.append(emb)
        
    state.course_data = data_list
    state.course_embeddings = np.array(emb_list)
    print(f"Loaded {len(state.course_data)} courses into memory.")
    client.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Loading model: {EMBED_MODEL}...")
    state.model = SentenceTransformer(EMBED_MODEL)
    load_courses_and_embeddings()
    yield
    # Shutdown (nothing specific needed)

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class GenerateRequest(BaseModel):
    field1: Optional[str] = ""
    field2: Optional[str] = ""
    field3: Optional[str] = ""
    top_k: Optional[int] = TOP_K_DEFAULT

class CourseResult(BaseModel):
    id: str
    title: str
    description: str
    score: float

class GenerateResponse(BaseModel):
    query: str
    results: List[CourseResult]

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/generate", response_model=GenerateResponse)
def generate_path(req: GenerateRequest):
    if state.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    if state.course_embeddings is None or len(state.course_data) == 0:
        raise HTTPException(status_code=503, detail="No course data available")

    # Concatenate inputs
    query_parts = [req.field1, req.field2, req.field3]
    query_text = " ".join([q.strip() for q in query_parts if q and q.strip()])
    
    if not query_text:
        raise HTTPException(status_code=400, detail="At least one interest field must be provided")

    # Compute user embedding
    user_emb = state.model.encode([query_text]) # Shape (1, D)
    
    # Compute cosine similarity
    # user_emb is (1, D), course_embeddings is (N, D)
    # Result is (1, N)
    scores = cosine_similarity(user_emb, state.course_embeddings)[0]
    
    # Get top K indices
    top_k = req.top_k if req.top_k else TOP_K_DEFAULT
    # argsort returns indices that sort the array. [::-1] reverses it for descending order.
    top_indices = scores.argsort()[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        course = state.course_data[idx]
        score = float(scores[idx])
        results.append(CourseResult(
            id=course["id"],
            title=course["title"],
            description=course["description"],
            score=round(score, 3)
        ))
        
    return GenerateResponse(query=query_text, results=results)

@app.post("/api/reload_embeddings")
def reload_embeddings(token: Optional[str] = None):
    # Simple protection (optional)
    # if token != os.getenv("ADMIN_TOKEN"): raise HTTPException...
    load_courses_and_embeddings()
    return {"status": "reloaded", "count": len(state.course_data)}
