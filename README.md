# 🎓 Learnify - Personalized Learning Path Generator

A sophisticated learning recommendation system that generates personalized course roadmaps using multi-factor scoring algorithms and semantic search.

## ✨ Features

### Core Functionality
- **User Profiles**: Create and manage learning profiles with skills, experience level, and time availability
- **Multi-Factor Recommendations**: Advanced scoring algorithm combining:
  - Semantic similarity (45%) - AI-powered content matching
  - Tag overlap (15%) - Skills and interests alignment  
  - Difficulty matching (10%) - Appropriate challenge level
  - Quality ratings (15%) - Bayesian average of user reviews
  - Popularity (5%) - Community preferences
  - Time-fit (10%) - Matches available hours/week
- **Staged Learning Paths**: Recommendations organized into:
  - **Beginner**: Foundation courses
  - **Advanced**: Intermediate and advanced topics
  - **Projects**: Hands-on capstone projects
- **Roadmap Management**: Save, track, and manage learning roadmaps
- **Progress Tracking**: Mark courses complete and rate your experience
- **Dynamic Ratings**: Course ratings update in real-time as users submit reviews

### Technical Highlights
- FastAPI backend with 13 REST endpoints
- Sentence transformers for semantic embeddings (all-MiniLM-L6-v2)
- MongoDB for flexible document storage
- Responsive SPA frontend with hash-based routing
- LocalStorage-based user persistence (no authentication required for prototype)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (local or Atlas)
- `mongoimport` and `mongoexport` tools (optional, for data management)

### Installation

1. **Clone and navigate to directory**
```bash
cd /path/to/Learnify
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your MongoDB URI and settings
```

Required environment variables:
```bash
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=learning_path_db
COLLECTION_NAME=courses
EMBED_MODEL=all-MiniLM-L6-v2
TOP_K=15
ADMIN_TOKEN=your_secret_token_here
TARGET_WEEKS=8
```

4. **Insert sample course data** (if not already done)
```bash
python3 insert_dummy_courses.py
```

5. **Compute embeddings for courses**
```bash
python3 backend/embedding.py --force
```

6. **Start the backend server**
```bash
uvicorn main:app --reload --port 8000
```

7. **Open the frontend**
```bash
# Simply open index.html in your browser
# Or use a simple HTTP server:
python3 -m http.server 8080
# Then visit http://localhost:8080
```

## 📖 Usage Guide

### Complete User Flow

#### 1. Create Your Profile
- Open the app and navigate to **Profile** page
- Enter username and email
- Add your current skills (e.g., "Python", "HTML", "JavaScript")
- Select your skill level: Beginner / Intermediate / Advanced
- Set hours available per week
- Choose preferred language
- Click **Save Profile**

#### 2. Generate Learning Path
- Navigate to **Generate Path** page
- Fill in:
  - **Current Skills**: What you already know (e.g., "Basic Python, HTML/CSS")
  - **Goal**: What you want to become (e.g., "Full-stack developer")
  - **Interests**: Additional topics (e.g., "React, APIs, Machine Learning")
  - **Project-based**: Check if you prefer hands-on projects
- Click **Generate Learning Path**
- Review the staged roadmap with scores and rationales
- Click **💾 Save this Roadmap** to save it

#### 3. Track Your Progress
- Navigate to **My Roadmaps**
- Click on a saved roadmap to view details
- Check "Mark as Complete" when you finish a course
- **Rate the course** (1-5 stars) when prompted
- Your ratings help improve recommendations for everyone!

### API Testing

#### Create a User
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "skills": ["python", "ml"],
    "skill_level": "beginner",
    "hours_per_week": 10,
    "preferred_language": "English"
  }'

# Response: {"user_id": "64abc123...", "status": "created"}
```

#### Generate Learning Path
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "skill_text": "basic python programming",
    "goal_text": "become a data scientist",
    "interests": ["machine learning", "pandas", "visualization"],
    "project_based": true
  }'
```

#### Save Roadmap
```bash
curl -X POST http://localhost:8000/api/roadmaps \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "title": "Data Science Path",
    "query": "python machine learning pandas",
    "meta": {"project_based": true},
    "stages": [...]
  }'
```

#### Mark Course Complete with Rating
```bash
curl -X POST http://localhost:8000/api/roadmaps/ROADMAP_ID/complete \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "COURSE_ID",
    "rating": 5
  }'
```

#### Get User Roadmaps
```bash
curl http://localhost:8000/api/roadmaps?user_id=YOUR_USER_ID
```

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Reload Embeddings (Admin Only)
```bash
curl -X POST "http://localhost:8000/api/reload_embeddings?token=YOUR_ADMIN_TOKEN"
```

## 🏗️ Architecture

### Backend Structure
```
backend/
├── db.py              # MongoDB CRUD operations
├── recommender.py     # Multi-factor scoring engine
└── embedding.py       # Embedding computation

main.py                # FastAPI app with 13 endpoints
```

### Frontend Structure
```
index.html             # Multi-page SPA structure
app.js                 # Routing, API integration, UI logic
```

### Database Collections

#### `courses`
```javascript
{
  "_id": ObjectId,
  "title": "HTML & CSS Fundamentals",
  "description": "Learn HTML5, CSS3...",
  "tags": ["web", "html", "css"],
  "difficulty": "beginner",
  "duration_hours": 8,
  "language": "English",
  "course_type": "video",
  "is_project": false,
  "prereqs": [],
  "popularity": 520,
  "avg_rating": 4.4,
  "rating_count": 230,
  "rating_sum": 1012,
  "embedding": [0.019, -0.006, ...],  // 384-dim vector
  "source_url": "https://...",
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### `users`
```javascript
{
  "_id": ObjectId,
  "username": "alice",
  "email": "alice@example.com",
  "skills": ["python", "ml"],
  "skill_level": "beginner",
  "hours_per_week": 10,
  "preferred_language": "English",
  "saved_roadmap_ids": [ObjectId, ...],
  "created_at": "2025-12-03T..."
}
```

#### `roadmaps`
```javascript
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "title": "Data Science Path",
  "query": "python machine learning",
  "meta": {"project_based": true},
  "stages": [
    {
      "name": "Beginner",
      "description": "Foundation courses",
      "courses": [
        {
          "course_id": "64abc...",
          "title": "Python for Beginners",
          "score": 0.85,
          "rationale": "High semantic match...",
          "completed": true,
          "rating": 5
        }
      ]
    }
  ],
  "created_at": "2025-12-03T..."
}
```

#### `ratings`
```javascript
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "course_id": "64abc...",
  "roadmap_id": ObjectId,
  "rating": 5,
  "completed": true,
  "timestamp": "2025-12-03T...",
  "note": ""
}
```

## 🎯 Recommendation Algorithm

### Scoring Factors (Weighted)

The system computes a final score for each course using 6 factors:

```python
final_score = (
    0.45 * semantic_similarity +  # Cosine similarity of embeddings
    0.15 * tag_overlap +          # Skills/interests match
    0.10 * difficulty_match +     # Appropriate challenge level
    0.15 * quality_rating +       # Bayesian average of reviews
    0.05 * popularity +           # Community preference
    0.10 * time_fit               # Fits available hours
)
```

#### 1. Semantic Similarity (45%)
Uses sentence-transformers to embed course content and user query, then computes cosine similarity.

#### 2. Tag Overlap (15%)
```python
overlap = len(user_tags ∩ course_tags)
score = overlap / max(len(user_tags), 1)
```

#### 3. Difficulty Match (10%)
- Courses at or below user level: **1.0**
- Courses above user level: **penalized** (0.7 for +1 level, 0.4 for +2)

#### 4. Quality Rating (15%)
Bayesian average to handle courses with few ratings:
```python
bayesian_avg = (R * n + m * v) / (n + v)
# R = avg_rating, n = rating_count
# m = global_avg (3.5), v = prior_weight (5)
```

#### 5. Popularity (5%)
Log-normalized to prevent outliers from dominating:
```python
score = log(1 + popularity) / log(1 + max_popularity)
```

#### 6. Time Fit (10%)
Favors courses that fit within available study time:
```python
available_hours = hours_per_week * 8 weeks * 0.6
time_fit = 1 - min(1, duration / available_hours)
```

### Sequencing Logic

After scoring, courses are organized into 3 stages:

1. **Beginner**: Top-scored courses with `difficulty == "beginner"`
2. **Advanced**: Top-scored `intermediate` and `advanced` courses
3. **Projects**: Courses with `is_project == true` or `course_type == "project"`

If no projects are found, a synthetic capstone is created based on top advanced courses.

## 🔧 Utility Scripts

### Backup Database
```bash
./scripts/backup_db.sh
```
Creates timestamped backup in `./backup/`, keeps last 5 backups.

### Recompute Embeddings
```bash
# Recompute all embeddings
python3 backend/embedding.py --force

# Only compute missing embeddings
python3 backend/embedding.py
```

### Insert Sample Courses
```bash
python3 insert_dummy_courses.py
```

## 📊 API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/users` | Create user |
| GET | `/api/users/{user_id}` | Get user profile |
| POST | `/api/users/{user_id}/profile` | Update profile |
| POST | `/api/generate` | Generate learning path |
| POST | `/api/roadmaps` | Save roadmap |
| GET | `/api/roadmaps?user_id=...` | List user roadmaps |
| GET | `/api/roadmaps/{id}` | Get roadmap detail |
| POST | `/api/roadmaps/{id}/complete` | Mark course complete + rate |
| POST | `/api/feedback` | Submit feedback |
| POST | `/api/reload_embeddings?token=...` | Reload embeddings (admin) |
| GET | `/api/stats` | Platform statistics |

## 🧪 Testing

### Automated Testing
```bash
# Health check
curl http://localhost:8000/health

# Stats
curl http://localhost:8000/api/stats
```

### Manual Testing Flow
1. Create profile → Generate path → Save roadmap
2. Mark course complete → Submit rating
3. Verify course `avg_rating` updated in database
4. Generate new path → Verify updated ratings reflected in quality scores

### Expected Behavior
- New users start with empty profiles
- Generated paths show courses sorted by relevance
- Each course displays: title, difficulty, duration, tags, score, rationale
- Completing a course with rating updates:
  - Roadmap (course.completed = true, course.rating = X)
  - Ratings collection (new rating document)
  - Courses collection (incremental avg_rating update)

## 🎨 Frontend Features

### Profile Page
- Skills tag input (press Enter to add)
- Skill level dropdown
- Hours/week numeric input
- Language selector
- Saves to localStorage for persistence

### Generator Page
- Multi-field input (skills, goal, interests)
- Project-based preference checkbox
- Real-time path generation
- Staged roadmap display with scores
- Save roadmap functionality

### Roadmaps Page
- List of all saved roadmaps
- Click to view details
- Shows creation date and query

### Roadmap Detail Page
- Complete roadmap view with all stages
- Checkbox to mark courses complete
- Rating modal (1-5 stars)
- Real-time updates after rating

## 🔒 Security Notes

> [!WARNING]
> This is a **prototype** using naive localStorage-based user persistence. For production:
> - Implement proper authentication (OAuth, JWT)
> - Add user input validation and sanitization
> - Secure admin endpoints with robust token management
> - Add rate limiting
> - Implement HTTPS

## 🛠️ Development

### Adding New Courses
1. Add courses to `courses_dummy.json`
2. Run `python3 insert_dummy_courses.py`
3. Compute embeddings: `python3 backend/embedding.py`
4. Reload in backend: Call `/api/reload_embeddings?token=...`

### Modifying Scoring Weights
Edit `DEFAULT_WEIGHTS` in `backend/recommender.py`:
```python
DEFAULT_WEIGHTS = {
    'sim': 0.45,
    'tag': 0.15,
    'diff': 0.10,
    'qual': 0.15,
    'pop': 0.05,
    'time': 0.10
}
```

### Customizing Sequencing
Edit `sequence_into_stages()` in `backend/recommender.py` to adjust:
- Number of courses per stage
- Stage definitions
- Capstone generation logic

## 📝 License

This project is for educational and prototyping purposes.

## 🙋 Support

For issues or questions:
1. Check MongoDB connection in `.env`
2. Verify embeddings computed: `curl http://localhost:8000/health`
3. Check browser console for frontend errors
4. Review backend logs for API errors

---

**Built with**: FastAPI, MongoDB, Sentence Transformers, Vanilla JavaScript

**Version**: 2.0

**Last Updated**: December 2025
