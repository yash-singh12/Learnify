"""
Enhanced recommendation engine with multi-factor scoring and sequencing.
Implements semantic similarity, tag overlap, difficulty matching, 
quality (Bayesian avg), popularity, and time-fit scoring.
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Optional
import re

# Default scoring weights
DEFAULT_WEIGHTS = {
    'sim': 0.55,      # Semantic similarity (increased for goal focus)
    'tag': 0.10,      # Tag overlap (reduced, can be noisy)
    'diff': 0.10,     # Difficulty match
    'qual': 0.15,     # Quality (Bayesian rating)
    'pop': 0.05,      # Popularity
    'time': 0.05      # Time fit (reduced)
}

DIFFICULTY_RANK = {
    "beginner": 0,
    "intermediate": 1,
    "advanced": 2
}

def extract_tags_from_text(text: str) -> List[str]:
    """Extract potential tags/keywords from text."""
    # Simple keyword extraction - split on spaces and clean
    words = re.findall(r'\b\w+\b', text.lower())
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'i', 'want', 'learn', 'learning', 'become'}
    tags = [w for w in words if w not in stop_words and len(w) > 2]
    return tags

def compute_goal_relevance(goal_text: str, interests: List[str], course: dict) -> bool:
    """Check if course is relevant to user's goal and interests."""
    if not goal_text and not interests:
        return True  # No filtering if no goal specified
    
    # Extract goal keywords
    goal_keywords = set(extract_tags_from_text(goal_text))
    interest_keywords = set()
    for interest in interests:
        interest_keywords.update(extract_tags_from_text(interest))
    
    all_goal_keywords = goal_keywords | interest_keywords
    
    if not all_goal_keywords:
        return True
    
    # Check course title, description, and tags
    course_text = f"{course.get('title', '')} {course.get('description', '')}"
    course_keywords = set(extract_tags_from_text(course_text))
    course_tags = set([tag.lower() for tag in course.get('tags', [])])
    
    all_course_keywords = course_keywords | course_tags
    
    # Course is relevant if it shares at least 1 keyword with goal
    overlap = all_goal_keywords & all_course_keywords
    return len(overlap) > 0

def compute_tag_overlap_score(user_tags: List[str], course_tags: List[str]) -> float:
    """Compute tag overlap score."""
    if not user_tags or not course_tags:
        return 0.0
    
    user_set = set(user_tags)
    course_set = set(course_tags)
    overlap = len(user_set & course_set)
    
    # Normalize by user tags (what they're looking for)
    score = overlap / max(len(user_set), 1)
    return min(score, 1.0)

def compute_difficulty_match(user_level: str, course_difficulty: str) -> float:
    """
    Compute difficulty match score.
    Courses at or below user level get 1.0.
    Courses above user level get penalized.
    """
    user_rank = DIFFICULTY_RANK.get(user_level, 0)
    course_rank = DIFFICULTY_RANK.get(course_difficulty, 1)
    
    if course_rank <= user_rank:
        return 1.0
    else:
        # Penalize courses above user level
        penalty = 0.3 * (course_rank - user_rank)
        return max(0.3, 1.0 - penalty)

def compute_bayesian_quality(course: dict, global_avg: float, prior_weight: int = 5) -> float:
    """
    Compute Bayesian average rating.
    Formula: (R*n + m*v) / (n + v)
    where R = avg_rating, n = rating_count, m = global_avg, v = prior_weight
    """
    R = course.get('avg_rating', 0)
    n = course.get('rating_count', 0)
    m = global_avg
    v = prior_weight
    
    bayesian_avg = (R * n + m * v) / (n + v)
    
    # Normalize to 0-1 (assuming 5-star scale)
    return bayesian_avg / 5.0

def compute_popularity_score(popularity: int, max_popularity: int) -> float:
    """Compute normalized popularity score using log scale."""
    if max_popularity == 0:
        return 0.0
    
    # Log normalization to prevent outliers from dominating
    log_pop = np.log(1 + popularity)
    log_max = np.log(1 + max_popularity)
    
    return log_pop / log_max if log_max > 0 else 0.0

def compute_time_fit_score(duration_hours: int, hours_per_week: int, target_weeks: int = 8) -> float:
    """
    Compute time fit score.
    Favors courses that fit within available time (with 60% utilization assumption).
    """
    if hours_per_week <= 0:
        return 0.5  # neutral score if no hours specified
    
    available_hours = hours_per_week * target_weeks * 0.6  # 60% utilization
    
    if available_hours == 0:
        return 0.5
    
    # Score decreases as duration exceeds available time
    ratio = duration_hours / available_hours
    time_fit = 1.0 - min(1.0, ratio)
    
    return max(0.0, time_fit)

def compute_multi_factor_scores(
    user_emb: np.ndarray,
    user_data: dict,
    courses: List[dict],
    course_embeddings: np.ndarray,
    global_stats: dict,
    query_text: str = "",
    weights: dict = None,
    request_data: dict = None
) -> List[dict]:
    """
    Compute multi-factor scores for all courses.
    Returns list of courses with scores and factors.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    # Extract user tags from query and user skills
    user_tags = extract_tags_from_text(query_text)
    if user_data.get('skills'):
        user_tags.extend(user_data['skills'])
    user_tags = list(set(user_tags))  # deduplicate
    
    user_level = user_data.get('skill_level', 'beginner')
    hours_per_week = user_data.get('hours_per_week', 10)
    preferred_language = user_data.get('preferred_language', '').lower()
    
    global_avg_rating = global_stats.get('global_avg_rating', 3.5)
    max_popularity = global_stats.get('max_popularity', 100)
    
    # Extract goal and interests for relevance filtering
    goal_text = request_data.get('goal_text', '') if request_data else ''
    interests = request_data.get('interests', []) if request_data else []
    
    # Compute semantic similarity for all courses
    sim_scores = cosine_similarity(user_emb, course_embeddings)[0]
    
    scored_courses = []
    
    for idx, course in enumerate(courses):
        # Filter by language if specified
        if preferred_language and course.get('language', '').lower() != preferred_language:
            continue
        
        # Filter by goal relevance
        if not compute_goal_relevance(goal_text, interests, course):
            continue
        
        # Factor 1: Semantic Similarity
        sim_score = float(sim_scores[idx])
        
        # Factor 2: Tag Overlap
        course_tags = course.get('tags', [])
        tag_score = compute_tag_overlap_score(user_tags, course_tags)
        
        # Factor 3: Difficulty Match
        diff_score = compute_difficulty_match(user_level, course.get('difficulty', 'beginner'))
        
        # Factor 4: Quality (Bayesian Average)
        qual_score = compute_bayesian_quality(course, global_avg_rating)
        
        # Factor 5: Popularity
        pop_score = compute_popularity_score(course.get('popularity', 0), max_popularity)
        
        # Factor 6: Time Fit
        time_score = compute_time_fit_score(course.get('duration_hours', 10), hours_per_week)
        
        # Compute final weighted score
        final_score = (
            weights['sim'] * sim_score +
            weights['tag'] * tag_score +
            weights['diff'] * diff_score +
            weights['qual'] * qual_score +
            weights['pop'] * pop_score +
            weights['time'] * time_score
        )
        
        # Store all factors for rationale generation
        factors = {
            'sim': sim_score,
            'tag': tag_score,
            'diff': diff_score,
            'qual': qual_score,
            'pop': pop_score,
            'time': time_score
        }
        
        scored_course = {
            **course,
            'final_score': final_score,
            'factors': factors
        }
        
        scored_courses.append(scored_course)
    
    return scored_courses

def generate_rationale(course: dict, factors: dict) -> str:
    """Generate human-readable rationale for why course was recommended."""
    parts = []
    
    # Semantic similarity
    if factors['sim'] > 0.7:
        parts.append(f"High semantic match ({factors['sim']:.2f})")
    elif factors['sim'] > 0.5:
        parts.append(f"Good semantic match ({factors['sim']:.2f})")
    
    # Tag overlap
    if factors['tag'] > 0.5:
        parts.append("Strong tag overlap")
    elif factors['tag'] > 0.3:
        parts.append("Moderate tag overlap")
    
    # Difficulty
    difficulty = course.get('difficulty', 'beginner')
    if factors['diff'] >= 1.0:
        parts.append(f"Difficulty fits your {difficulty} level")
    elif factors['diff'] < 0.7:
        parts.append(f"Advanced ({difficulty}) - challenging content")
    
    # Quality
    avg_rating = course.get('avg_rating', 0)
    rating_count = course.get('rating_count', 0)
    if avg_rating > 0:
        parts.append(f"Rating: {avg_rating:.1f}/5 ({rating_count} reviews)")
    
    # Popularity
    if factors['pop'] > 0.7:
        parts.append("Highly popular")
    
    # Time fit
    duration = course.get('duration_hours', 0)
    if factors['time'] > 0.7:
        parts.append(f"Good time fit ({duration}h)")
    elif duration > 0:
        parts.append(f"Duration: {duration}h")
    
    return "; ".join(parts) if parts else "Recommended based on your interests"

def deduplicate_courses(courses: List[dict], similarity_threshold: int = 30) -> List[dict]:
    """Remove courses with very similar titles."""
    seen_titles = set()
    unique_courses = []
    
    for course in courses:
        title = course.get('title', '')
        # Use first N characters as similarity key
        title_key = title.lower()[:similarity_threshold]
        
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_courses.append(course)
    
    return unique_courses

def sequence_into_stages(
    scored_courses: List[dict],
    top_n: int = 15,
    project_based_preference: bool = False
) -> List[dict]:
    """
    Sequence courses into three stages: Beginner, Advanced, Projects.
    Returns list of stage dicts with courses.
    """
    # Sort by final score descending
    sorted_courses = sorted(scored_courses, key=lambda x: x['final_score'], reverse=True)
    
    # Deduplicate similar titles
    unique_courses = deduplicate_courses(sorted_courses)
    
    # Pick top N
    top_courses = unique_courses[:top_n]
    
    # Add rationale to each course
    for course in top_courses:
        course['rationale'] = generate_rationale(course, course['factors'])
        # Clean up factors from response (keep only in rationale)
        del course['factors']
    
    # Partition into stages
    # First, identify project courses
    project_courses = [c for c in top_courses if c.get('is_project') or c.get('course_type') == 'project']
    project_course_ids = {c.get('id') for c in project_courses}
    
    # Exclude project courses from beginner and advanced sections
    beginner_courses = [c for c in top_courses if c.get('difficulty') == 'beginner' and c.get('id') not in project_course_ids]
    advanced_courses = [c for c in top_courses if c.get('difficulty') in ['intermediate', 'advanced'] and c.get('id') not in project_course_ids]
    
    # If project-based preference, boost project courses in advanced stage
    if project_based_preference and not project_courses:
        # Create a capstone suggestion
        if advanced_courses:
            top_advanced = advanced_courses[0]
            project_courses = [{
                'id': 'capstone_suggestion',
                'title': f"Capstone: {top_advanced.get('title', 'Advanced')} Project",
                'description': f"Apply your knowledge from {top_advanced.get('title', 'courses')} by building a real-world project. This hands-on capstone will solidify your understanding and create portfolio work.",
                'tags': top_advanced.get('tags', []) + ['project', 'capstone'],
                'difficulty': 'advanced',
                'duration_hours': 40,
                'is_project': True,
                'course_type': 'project',
                'final_score': top_advanced.get('final_score', 0.7) * 0.9,
                'rationale': 'Synthesized project to apply your learning',
                'source_url': '#',
                'language': top_advanced.get('language', 'English')
            }]
    
    stages = [
        {
            "name": "Beginner",
            "description": "Foundation courses to build core skills",
            "courses": beginner_courses[:5]
        },
        {
            "name": "Advanced",
            "description": "Intermediate and advanced courses to deepen expertise",
            "courses": advanced_courses[:7]
        }
    ]
    
    # Only add Projects stage if user selected project-based preference
    if project_based_preference and project_courses:
        stages.append({
            "name": "Projects",
            "description": "Hands-on projects to apply your knowledge",
            "courses": project_courses[:3]
        })
    
    return stages

def build_user_query_text(request_data: dict, user_data: dict) -> str:
    """Build query text with goal prioritization (3x goal, 2x interests, 1x skills)."""
    parts = []
    
    # PRIORITY 1: Goal (repeat 3x for higher weight in embedding)
    goal_text = request_data.get('goal_text', '').strip()
    if goal_text:
        parts.extend([goal_text] * 3)
    
    # PRIORITY 2: Interests (repeat 2x)
    if request_data.get('interests'):
        interest_str = " ".join(request_data['interests'])
        parts.extend([interest_str] * 2)
    
    # PRIORITY 3: Current skills (1x only, for context)
    skill_text = request_data.get('skill_text', '').strip()
    if skill_text:
        parts.append(skill_text)
    
    # Add language preference
    if request_data.get('language'):
        parts.append(request_data['language'])
    elif user_data.get('preferred_language'):
        parts.append(user_data['preferred_language'])
    
    # Add project preference
    if request_data.get('project_based'):
        parts.append("project-based hands-on")
    
    query_text = " ".join([p for p in parts if p])
    return query_text

def build_display_query_text(request_data: dict, user_data: dict) -> str:
    """Build clean display query text without repetitions for showing to user."""
    parts = []
    
    # Current skills
    skill_text = request_data.get('skill_text', '').strip()
    if skill_text:
        parts.append(skill_text)
    
    # Goal (only once for display)
    goal_text = request_data.get('goal_text', '').strip()
    if goal_text:
        parts.append(goal_text)
    
    # Interests
    if request_data.get('interests'):
        interest_str = ", ".join(request_data['interests'])
        parts.append(interest_str)
    
    # Language
    if request_data.get('language'):
        parts.append(request_data['language'])
    elif user_data.get('preferred_language'):
        parts.append(user_data['preferred_language'])
    
    # Project preference
    if request_data.get('project_based'):
        parts.append("project-based")
    
    return ", ".join([p for p in parts if p])
