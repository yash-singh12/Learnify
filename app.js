/**
 * Learnify Frontend Application
 * Multi-page SPA with user profile management, path generation, and roadmap tracking
 */

const API_URL = 'http://localhost:8000';
const LS_USER_ID = 'learnify_user_id';

// User skills array
let userSkills = [];

// Current roadmap ID for rating
let currentRoadmapId = null;
let currentCourseForRating = null;

// ============ INITIALIZATION ============

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    handleRouting();
});

function initializeApp() {
    // Check if user exists
    const userId = localStorage.getItem(LS_USER_ID);

    if (userId) {
        // Load user profile
        loadUserProfile(userId);
    } else {
        // Show profile page for new users
        navigateTo('profile');
    }

    // Handle hash changes for routing
    window.addEventListener('hashchange', handleRouting);
}

function setupEventListeners() {
    // Profile page
    document.getElementById('skill-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addSkill();
        }
    });

    document.getElementById('save-profile-btn').addEventListener('click', saveProfile);

    // Generate page
    document.getElementById('generate-btn').addEventListener('click', generatePath);

    // Back button
    document.getElementById('back-to-roadmaps').addEventListener('click', () => {
        navigateTo('roadmaps');
    });
}

// ============ ROUTING ============

function handleRouting() {
    const hash = window.location.hash.slice(1) || 'profile';
    const [page, id] = hash.split('/');

    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

    // Show active page
    const pageElement = document.getElementById(`${page}-page`);
    if (pageElement) {
        pageElement.classList.add('active');
    }

    // Highlight active nav link
    const activeLink = document.querySelector(`a[href="#${page}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }

    // Handle specific pages
    if (page === 'roadmaps' && !id) {
        loadRoadmaps();
    } else if (page === 'roadmap-detail' && id) {
        loadRoadmapDetail(id);
    }
}

function navigateTo(page, subPath = '') {
    const path = subPath ? `${page}/${subPath}` : page;
    window.location.hash = path;
}

// ============ USER PROFILE ============

async function loadUserProfile(userId) {
    try {
        const response = await fetch(`${API_URL}/api/users/${userId}`);
        if (!response.ok) {
            console.error('Failed to load user profile');
            return;
        }

        const user = await response.json();

        // Populate form
        document.getElementById('username').value = user.username || '';
        document.getElementById('email').value = user.email || '';
        document.getElementById('skill-level').value = user.skill_level || 'beginner';
        document.getElementById('hours-per-week').value = user.hours_per_week || 10;
        document.getElementById('preferred-language').value = user.preferred_language || 'English';

        // Load skills
        userSkills = user.skills || [];
        renderSkillsTags();

    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

function addSkill() {
    const input = document.getElementById('skill-input');
    const skill = input.value.trim();

    if (skill && !userSkills.includes(skill)) {
        userSkills.push(skill);
        renderSkillsTags();
        input.value = '';
    }
}

function removeSkill(skill) {
    userSkills = userSkills.filter(s => s !== skill);
    renderSkillsTags();
}

function renderSkillsTags() {
    const container = document.getElementById('skills-tags');
    container.innerHTML = userSkills.map(skill => `
        <div class="tag">
            <span>${escapeHtml(skill)}</span>
            <span class="remove" onclick="removeSkill('${escapeHtml(skill)}')">&times;</span>
        </div>
    `).join('');
}

async function saveProfile() {
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const skillLevel = document.getElementById('skill-level').value;
    const hoursPerWeek = parseInt(document.getElementById('hours-per-week').value);
    const preferredLanguage = document.getElementById('preferred-language').value;

    if (!username || !email) {
        showAlert('Please fill in username and email', 'error');
        return;
    }

    const btn = document.getElementById('save-profile-btn');
    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
        const userId = localStorage.getItem(LS_USER_ID);

        if (userId) {
            // Update existing profile
            const response = await fetch(`${API_URL}/api/users/${userId}/profile`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    skills: userSkills,
                    skill_level: skillLevel,
                    hours_per_week: hoursPerWeek,
                    preferred_language: preferredLanguage
                })
            });

            if (!response.ok) throw new Error('Failed to update profile');

            showAlert('Profile updated successfully!', 'success');

        } else {
            // Create new user
            const response = await fetch(`${API_URL}/api/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username,
                    email,
                    skills: userSkills,
                    skill_level: skillLevel,
                    hours_per_week: hoursPerWeek,
                    preferred_language: preferredLanguage
                })
            });

            if (!response.ok) throw new Error('Failed to create user');

            const data = await response.json();
            localStorage.setItem(LS_USER_ID, data.user_id);

            showAlert('Profile created successfully!', 'success');
        }

        setTimeout(() => navigateTo('generate'), 1500);

    } catch (error) {
        console.error('Error saving profile:', error);
        showAlert('Failed to save profile', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Save Profile';
    }
}

// ============ PATH GENERATION ============

async function generatePath() {
    const userId = localStorage.getItem(LS_USER_ID);

    if (!userId) {
        showAlert('Please create your profile first', 'error');
        navigateTo('profile');
        return;
    }

    const skillText = document.getElementById('skill-text').value.trim();
    const goalText = document.getElementById('goal-text').value.trim();
    const interestsText = document.getElementById('interests-text').value.trim();
    const projectBased = document.getElementById('project-based').checked;

    if (!skillText && !goalText && !interestsText) {
        showAlert('Please provide at least one search criterion', 'error');
        return;
    }

    const interests = interestsText ? interestsText.split(',').map(i => i.trim()) : [];

    const btn = document.getElementById('generate-btn');
    const resultsContainer = document.getElementById('results-container');

    btn.disabled = true;
    btn.textContent = 'Generating...';
    resultsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>Analyzing your goals and finding the best courses...</p></div>';

    try {
        const response = await fetch(`${API_URL}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                skill_text: skillText,
                goal_text: goalText,
                interests: interests,
                project_based: projectBased
            })
        });

        if (!response.ok) throw new Error('Failed to generate path');

        const data = await response.json();
        renderGeneratedPath(data);

    } catch (error) {
        console.error('Error generating path:', error);
        resultsContainer.innerHTML = '<div class="alert alert-error">Failed to generate path. Please try again.</div>';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate Learning Path';
    }
}

function renderGeneratedPath(data) {
    const container = document.getElementById('results-container');

    let html = `
        <div class="alert alert-success">
            ✅ Generated personalized path based on: "${escapeHtml(data.query)}"
        </div>
        <button onclick="saveCurrentRoadmap()" style="margin-bottom: 2rem;">💾 Save this Roadmap</button>
    `;

    // Store data for saving
    window.currentGeneratedPath = data;

    // Render stages
    data.stages.forEach(stage => {
        if (stage.courses.length === 0) return;

        html += `
            <div class="stage">
                <div class="stage-header">
                    <h3>${escapeHtml(stage.name)}</h3>
                    <p>${escapeHtml(stage.description)}</p>
                </div>
                <div class="course-list">
                    ${stage.courses.map(course => renderCourseCard(course)).join('')}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function renderCourseCard(course, roadmapId = null) {
    const isCompleted = course.completed || false;
    const rating = course.rating || null;

    return `
        <div class="course-card">
            <div class="course-header">
                <div class="course-title">${escapeHtml(course.title)}</div>
                <div class="course-score">Score: ${course.final_score ? course.final_score.toFixed(2) : 'N/A'}</div>
            </div>
            <div class="course-meta">
                <span>📊 ${escapeHtml(course.difficulty || 'N/A')}</span>
                <span>⏱️ ${course.duration_hours || '?'}h</span>
                ${course.language ? `<span>🌐 ${escapeHtml(course.language)}</span>` : ''}
                ${course.is_project ? '<span>🚀 Project</span>' : ''}
            </div>
            <div class="course-description">${escapeHtml(course.description || 'No description available')}</div>
            ${course.rationale ? `<div class="course-rationale">💡 ${escapeHtml(course.rationale)}</div>` : ''}
            ${roadmapId ? `
                <div class="course-actions">
                    <label class="checkbox-label">
                        <input type="checkbox" ${isCompleted ? 'checked' : ''} 
                               onchange="toggleCourseCompletion('${roadmapId}', '${course.course_id || course.id}', '${escapeHtml(course.title)}', this.checked)">
                        <span>Mark as Complete</span>
                    </label>
                    ${rating ? `<span>Your rating: ${'⭐'.repeat(rating)}</span>` : ''}
                </div>
            ` : ''}
        </div>
    `;
}

async function saveCurrentRoadmap() {
    const userId = localStorage.getItem(LS_USER_ID);
    if (!userId || !window.currentGeneratedPath) {
        showAlert('No path to save', 'error');
        return;
    }

    const title = prompt('Enter a title for this roadmap:');
    if (!title) return;

    const data = window.currentGeneratedPath;

    try {
        // Prepare stages with course metadata
        const stages = data.stages.map(stage => ({
            name: stage.name,
            description: stage.description,
            courses: stage.courses.map(course => ({
                course_id: course.id,
                title: course.title,
                score: course.final_score,
                rationale: course.rationale,
                completed: false,
                rating: null
            }))
        }));

        const response = await fetch(`${API_URL}/api/roadmaps`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                title: title,
                query: data.query,
                meta: {
                    project_based: document.getElementById('project-based').checked
                },
                stages: stages
            })
        });

        if (!response.ok) throw new Error('Failed to save roadmap');

        const result = await response.json();
        showAlert('Roadmap saved successfully!', 'success');

        setTimeout(() => navigateTo('roadmaps'), 1500);

    } catch (error) {
        console.error('Error saving roadmap:', error);
        showAlert('Failed to save roadmap', 'error');
    }
}

// ============ ROADMAPS LIST ============

async function loadRoadmaps() {
    const userId = localStorage.getItem(LS_USER_ID);
    if (!userId) {
        document.getElementById('roadmaps-list').innerHTML = '<div class="alert alert-info">Please create your profile first.</div>';
        return;
    }

    const container = document.getElementById('roadmaps-list');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading your roadmaps...</p></div>';

    try {
        const response = await fetch(`${API_URL}/api/roadmaps?user_id=${userId}`);
        if (!response.ok) throw new Error('Failed to load roadmaps');

        const data = await response.json();

        if (data.roadmaps.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>📚 No saved roadmaps yet</p>
                    <p>Generate your first learning path and save it!</p>
                    <button onclick="navigateTo('generate')" style="margin-top: 1rem;">Generate Path</button>
                </div>
            `;
            return;
        }

        container.innerHTML = data.roadmaps.map(roadmap => `
            <div class="roadmap-item" onclick="navigateTo('roadmap-detail', '${roadmap.id}')">
                <div class="roadmap-title">${escapeHtml(roadmap.title)}</div>
                <div class="roadmap-meta">
                    <div>📝 Query: ${escapeHtml(roadmap.query)}</div>
                    <div>📅 Created: ${new Date(roadmap.created_at).toLocaleDateString()}</div>
                    <div>📊 Stages: ${roadmap.stages.length}</div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading roadmaps:', error);
        container.innerHTML = '<div class="alert alert-error">Failed to load roadmaps</div>';
    }
}

// ============ ROADMAP DETAIL ============

async function loadRoadmapDetail(roadmapId) {
    currentRoadmapId = roadmapId;
    const container = document.getElementById('roadmap-detail-content');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading roadmap details...</p></div>';

    try {
        const response = await fetch(`${API_URL}/api/roadmaps/${roadmapId}`);
        if (!response.ok) throw new Error('Failed to load roadmap');

        const roadmap = await response.json();

        let html = `
            <h2>${escapeHtml(roadmap.title)}</h2>
            <div class="alert alert-info">
                <strong>Query:</strong> ${escapeHtml(roadmap.query)}<br>
                <strong>Created:</strong> ${new Date(roadmap.created_at).toLocaleDateString()}
            </div>
        `;

        roadmap.stages.forEach(stage => {
            if (stage.courses.length === 0) return;

            html += `
                <div class="stage">
                    <div class="stage-header">
                        <h3>${escapeHtml(stage.name)}</h3>
                        ${stage.description ? `<p>${escapeHtml(stage.description)}</p>` : ''}
                    </div>
                    <div class="course-list">
                        ${stage.courses.map(course => renderCourseCard(course, roadmapId)).join('')}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

    } catch (error) {
        console.error('Error loading roadmap detail:', error);
        container.innerHTML = '<div class="alert alert-error">Failed to load roadmap details</div>';
    }
}

async function toggleCourseCompletion(roadmapId, courseId, courseTitle, isChecked) {
    if (!isChecked) {
        // User unchecked - just update without rating
        await markComplete(roadmapId, courseId, null);
        return;
    }

    // Show rating modal
    currentCourseForRating = { roadmapId, courseId, courseTitle };
    document.getElementById('rating-course-title').textContent = courseTitle;
    document.getElementById('rating-modal').classList.add('active');
}

function closeRatingModal() {
    document.getElementById('rating-modal').classList.remove('active');
    currentCourseForRating = null;
}

async function submitRating() {
    if (!currentCourseForRating) return;

    const rating = parseInt(document.getElementById('rating-select').value);
    const { roadmapId, courseId } = currentCourseForRating;

    closeRatingModal();

    await markComplete(roadmapId, courseId, rating);
}

async function markComplete(roadmapId, courseId, rating) {
    try {
        const response = await fetch(`${API_URL}/api/roadmaps/${roadmapId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_id: courseId,
                rating: rating
            })
        });

        if (!response.ok) throw new Error('Failed to mark complete');

        showAlert(rating ? `Course completed with ${rating} stars!` : 'Course updated', 'success');

        // Reload roadmap detail
        setTimeout(() => loadRoadmapDetail(roadmapId), 1000);

    } catch (error) {
        console.error('Error marking complete:', error);
        showAlert('Failed to update course status', 'error');
    }
}

// ============ UTILITIES ============

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    const container = document.querySelector('.page.active');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        setTimeout(() => alertDiv.remove(), 3000);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
