# Learnify: Project Presentation Content

## 1. Front Page
**Project Title:** Learnify - Personalized Learning Path Generator  
**Submitted By:** [Your Name]  
**Roll No:** [Your Roll No]  
**Department:** Computer Science & Engineering  
**College:** [Your College Name]  
**Date:** December 2025  

---

## 2. Introduction
**Problem Statement:**  
In the era of abundant online learning resources, learners often suffer from "choice paralysis." Finding a structured, personalized path to master a new skill (e.g., "Data Science" or "Full Stack Dev") is difficult amidst scattered courses, varying quality, and lack of clear sequencing.

**Proposed Solution:**  
**Learnify** is an intelligent recommendation system that generates personalized, staged learning roadmaps. Unlike simple keyword searches, it uses semantic understanding of the user's goals, current skills, and time availability to curate a tailored curriculum.

**Key Objectives:**  
*   To provide personalized course recommendations based on multiple factors (relevance, difficulty, quality).
*   To structure learning into logical stages (Beginner, Advanced, Projects).
*   To track user progress and adapt recommendations based on feedback.

---

## 3. Methodology
**System Architecture:**  
The project follows a modern Client-Server architecture:
*   **Frontend:** Responsive Single Page Application (SPA) built with Vanilla JavaScript, HTML5, and CSS3.
*   **Backend:** High-performance REST API built with **FastAPI** (Python).
*   **Database:** **MongoDB** for flexible storage of course metadata, user profiles, and roadmaps.

**Core Algorithm (Multi-Factor Scoring):**  
The recommendation engine scores courses based on a weighted sum of 6 factors:
1.  **Semantic Similarity (45%):** Uses **Sentence Transformers (all-MiniLM-L6-v2)** to match the semantic meaning of user goals with course content.
2.  **Tag Overlap (15%):** Matches specific technical skills (e.g., "Python", "React").
3.  **Difficulty Match (10%):** Aligns course difficulty with the user's current expertise.
4.  **Quality Rating (15%):** Uses a Bayesian average of user reviews to ensure high-quality suggestions.
5.  **Time Fit (10%):** Prioritizes courses that fit the user's weekly schedule.
6.  **Popularity (5%):** Considers community trends.

**Data Flow:**  
1.  User inputs profile & goals.
2.  Backend converts text to vector embeddings.
3.  System calculates similarity scores against the course database.
4.  Top candidates are filtered and sequenced into stages (Beginner -> Advanced -> Projects).

---

## 4. Result and Discussion
**Key Features Implemented:**  
*   **Smart Profiling:** Captures user skills, experience level, and time constraints.
*   **Dynamic Roadmaps:** Generates unique paths for queries like "Become a Data Scientist" vs "Learn Web Dev".
*   **Project-Based Learning:** Explicitly suggests hands-on projects for practical experience.
*   **Progress Tracking:** Users can mark courses as complete and rate them, influencing future recommendations.

**Performance:**  
*   **Latency:** Vector search provides sub-second response times for path generation.
*   **Relevance:** The multi-factor approach significantly outperforms simple keyword matching by understanding context (e.g., distinguishing "Java" language from "Java" coffee if context existed).

**User Interface:**  
*   Clean, minimalist design focusing on the learning content.
*   Interactive roadmap visualization with clear stage delineation.

---

## 5. Conclusion
**Summary:**  
Learnify successfully demonstrates how AI and vector embeddings can solve the curriculum curation problem. By considering personal constraints like time and skill level, it offers a superior experience to generic course directories.

**Future Scope:**  
*   **Live API Integration:** Fetch real-time courses from platforms like Udemy, Coursera, or YouTube API.
*   **Authentication:** Implement secure user accounts with OAuth.
*   **Advanced Analytics:** Dashboard for tracking learning velocity and skill acquisition graphs.
*   **Content-Based Filtering:** Analyze video transcripts for deeper content matching.

---

## 6. References
1.  **FastAPI Documentation:** https://fastapi.tiangolo.com/
2.  **Sentence Transformers:** https://www.sbert.net/
3.  **MongoDB Documentation:** https://www.mongodb.com/docs/
4.  **Recommender Systems Handbook:** Ricci, F., et al.

---

## 7. Base Paper
*   [Link to Base Paper]
*(Note: If this project is based on a specific research paper, paste the link here. Otherwise, you can cite a general paper on "Content-Based Recommendation Systems using Vector Space Models" or similar.)*
