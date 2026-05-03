# ⚡ Learnify - 1-Page Quick Reference

## 30-Second Pitch
"Personalized learning recommendation system using **semantic search + multi-factor scoring**. Users create profile (skills, hours/week), state goal (full-stack dev?), and get ranked courses in 3 stages: Beginner → Advanced → Projects. Backend combines 6 factors (55% semantic similarity, 15% quality, 10% difficulty, etc.) to score courses. Tech: FastAPI + MongoDB + Sentence Transformers + Vanilla JS."

---

## Architecture at a Glance
```
Browser (localStorage) → FastAPI (async) → MongoDB (4 collections) + Sentence Transformers (in-memory)
```

---

## The 6 Scoring Factors (Weights)
```
0.55 Semantic Similarity    (goal-text → 384-dim embedding → cosine sim with courses)
0.15 Quality Rating         (Bayesian avg: (R×n + m×5) / (n+5) → robust to few ratings)
0.10 Difficulty Match       (user_level ≥ course_level → 1.0, else penalty)
0.10 Tag Overlap            (len(user_tags ∩ course_tags) / len(user_tags))
0.05 Popularity             (log(1+pop) / log(1+max_pop) → prevents outliers dominating)
0.05 Time Fit               (1 - min(1, duration / available_hours))
```

---

## Bayesian Rating Formula (Key Insight)
```
Rating = (actual_rating × count + global_avg × prior) / (count + prior)

Example:
- New: (5 × 1 + 3.5 × 5) / (1 + 5) = 3.92  ← pulled down from 5.0
- Old:  (4.8 × 100 + 3.5 × 5) / (100 + 5) = 4.79  ← stable
```
**Why**: Prevents manipulation, handles low-review courses

---

## API Endpoints (13 Total)
```
POST   /api/users                      Create user
GET    /api/users/{id}                 Get profile
POST   /api/generate                   Generate path
POST   /api/roadmaps                   Save roadmap
GET    /api/roadmaps?user_id=...       List user's roadmaps
POST   /api/roadmaps/{id}/complete     Mark complete + rate
GET    /health                         Healthcheck
```

---

## Tech Stack & Why
| Component | Tech | Why |
|-----------|------|-----|
| Backend API | FastAPI | Fast, async, auto-docs |
| Database | MongoDB | Flexible schema, document-oriented |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) | 384-dim, local, fast, free |
| Similarity | scikit-learn cosine_similarity | Simple, O(ND) efficient |
| Frontend | Vanilla JS + HTML/CSS | No build, localStorage persistence |

---

## Key Design Decisions

✅ **Pre-compute embeddings in MongoDB**
- Loaded into memory at startup
- Query time: O(1) embedding lookup + O(ND) similarity = fast

✅ **Bayesian ratings**
- Protects against low-review gaming
- Used by Netflix, Amazon

✅ **3-stage sequencing**
- Beginner → Advanced → Projects
- Aligns with Bloom's taxonomy

✅ **Vanilla JS + localStorage**
- No auth needed (prototype)
- Simple, no build step

---

## Common Questions & Answers

**Q: Why 55% for semantic similarity?**
A: Equal weights (16.7%) gave generic results. Goal-alignment is most important. Tuned via user feedback.

**Q: How handle cold-start (new users)?**
A: Profile-based (not history-based). Skills + goals + hours/week → relevant courses immediately.

**Q: Complexity of path generation?**
A: O(N log N) ≈ 10ms for 1000 courses (embed goal → score all → sort → sequence)

**Q: How scale to 1M courses?**
A: Vector DB (Pinecone) for embeddings. Two-stage: BM25 filter 100K → re-rank top 1K semantically.

**Q: Why not GPT-4 embeddings?**
A: Cost + latency. Sentence Transformers local = free + 10ms, perfect for production.

---

## Limitations (Be Honest)
- No collaborative filtering (user similarity)
- No automated freshness/outdated course detection
- No diversity penalty (can get filter bubble)
- localStorage = not production-ready

---

## Talking Points (Show Depth)
- "Bayesian averaging is same math as A/B testing confidence intervals"
- "Pre-computed embeddings = trading storage for speed"
- "Staged learning follows educational psychology (foundation before application)"
- "Semantic similarity at 55% because goal-alignment matters most for learning"

---

## If You Get Stuck
✅ "That's a great question. I didn't implement that, but I'd approach it by..."
✅ "Currently we handle it like X, but for production I'd definitely add..."
❌ Don't say "I don't know" or make up details

---

## Numbers to Remember
- **13** REST endpoints
- **6** scoring factors
- **4** MongoDB collections
- **384** embedding dimensions
- **0.55** weight for semantic similarity
- **~10ms** generation time for 1000 courses
- **5** prior weight for Bayesian rating

---

**You've got this! 🚀**
