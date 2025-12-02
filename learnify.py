# Simple course-matching using TF-IDF and cosine similarity
# This code creates 10 course descriptions, converts them to TF-IDF embeddings,
# then provides a function `match_course(query, top_k=3)` to find best matching courses.
# The script demonstrates the function with an example query. Replace `example_query`
# or call `match_course` with user input in your own environment to use interactively.

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 10 example courses (name, description)
courses = [
    ("Intro to Python", "Learn Python programming basics: variables, control flow, functions, and simple data structures."),
    ("Data Science Foundations", "Introduction to data analysis, statistics, visualization, and machine learning concepts."),
    ("Web Development with React", "Build modern web applications using React, components, state management, and routing."),
    ("Intro to Machine Learning 101", "Supervised and unsupervised learning, model evaluation, and practical ML workflows."),
    ("Databases and SQL", "Relational databases, SQL queries, joins, indexing, and basic database design."),
    ("Cloud Computing Essentials", "Cloud fundamentals, deployment, containers, and basic AWS/GCP/Azure services."),
    ("Deep Learning with TensorFlow", "Neural networks, convolutional networks, sequence models, and TensorFlow/Keras basics."),
    ("Natural Language Processing", "Text processing, embeddings, sequence models, and NLP pipelines."),
    ("Frontend Styling with CSS", "Responsive design, CSS layout techniques, Flexbox, Grid, and animations."),
    ("DevOps Basics", "CI/CD pipelines, version control workflows, infrastructure as code, and monitoring."),
]

names = [c[0] for c in courses]
descriptions = [c[1] for c in courses]

# Create TF-IDF vectors (these act as our 'embeddings' for this simple demo)
vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
desc_embeddings = vectorizer.fit_transform(descriptions)  # shape: (10, vocab)

def match_course(query: str, top_k: int = 3):
    """
    Return top_k matching courses for the given query string using cosine similarity.
    Returns a pandas DataFrame with course name, description, and similarity score.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, desc_embeddings).flatten()
    idx_sorted = np.argsort(-sims)[:top_k]
    results = []
    for idx in idx_sorted:
        results.append({
            "rank": len(results)+1,
            "course_name": names[idx],
            "description": descriptions[idx],
            "score": float(sims[idx])
        })
    return pd.DataFrame(results)

# Example usage - replace this string with any user input to test
example_query = "Machine learning"
print("Query:", example_query)
top_matches = match_course(example_query, top_k=3)
print("\nBest match ->", top_matches.loc[0, "course_name"], "(score={:.4f})".format(top_matches.loc[0, "score"]))
