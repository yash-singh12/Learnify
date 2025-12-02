const API_URL = 'http://localhost:8000/api/generate';

document.getElementById('generate-btn').addEventListener('click', async () => {
    const btn = document.getElementById('generate-btn');
    const resultsDiv = document.getElementById('results');

    // Gather inputs
    const field1 = document.getElementById('interest-1').value.trim();
    const field2 = document.getElementById('interest-2').value.trim();
    const field3 = document.getElementById('interest-3').value.trim();

    if (!field1 && !field2 && !field3) {
        alert('Please enter at least one interest.');
        return;
    }

    // UI Loading State
    btn.disabled = true;
    btn.textContent = 'Generating...';
    resultsDiv.innerHTML = '<div class="loading">Analyzing your interests and finding best matches...</div>';

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                field1,
                field2,
                field3,
                top_k: 2
            })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Failed to fetch results');
        }

        const data = await response.json();
        renderResults(data.results);

    } catch (error) {
        console.error('Error:', error);
        resultsDiv.innerHTML = `<div class="error">Error: ${error.message}. Is the backend running?</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate Path';
    }
});

function renderResults(results) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';

    if (!results || results.length === 0) {
        resultsDiv.innerHTML = '<div class="loading">No matching courses found. Try different keywords.</div>';
        return;
    }

    const list = document.createElement('div');

    results.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = 'result-card';

        const scorePercent = (item.score * 100).toFixed(1) + '%';

        card.innerHTML = `
            <div class="result-header">
                <h3 class="result-title">${index + 1}. ${escapeHtml(item.title)}</h3>
                <span class="result-score" title="Cosine Similarity Score">Match: ${item.score.toFixed(3)}</span>
            </div>
            <p class="result-desc">${escapeHtml(item.description)}</p>
        `;
        list.appendChild(card);
    });

    resultsDiv.appendChild(list);
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
