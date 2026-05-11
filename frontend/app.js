/**
 * Mumble - DJ Mixing Assistant
 * Frontend Application Logic
 */

// API Base URL
const API_BASE = '';

// State
let currentAnalysis = null;
let selectedFile = null;

// DOM Elements
const elements = {
    // Tabs
    tabBtns: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Upload
    uploadZone: document.getElementById('uploadZone'),
    fileInput: document.getElementById('fileInput'),
    filePreview: document.getElementById('filePreview'),
    fileName: document.getElementById('fileName'),
    removeFile: document.getElementById('removeFile'),
    
    // URL
    urlInput: document.getElementById('urlInput'),
    
    // Search
    songNameInput: document.getElementById('songNameInput'),
    artistInput: document.getElementById('artistInput'),
    
    // Buttons
    analyzeBtn: document.getElementById('analyzeBtn'),
    findMatchesBtn: document.getElementById('findMatchesBtn'),
    
    // Sections
    inputSection: document.getElementById('inputSection'),
    analysisSection: document.getElementById('analysisSection'),
    promptSection: document.getElementById('promptSection'),
    resultsSection: document.getElementById('resultsSection'),
    
    // Analysis Display
    trackTitle: document.getElementById('trackTitle'),
    trackSource: document.getElementById('trackSource'),
    bpmValue: document.getElementById('bpmValue'),
    keyValue: document.getElementById('keyValue'),
    energyValue: document.getElementById('energyValue'),
    moodValue: document.getElementById('moodValue'),
    compatibleKeys: document.getElementById('compatibleKeys'),
    pitchSemitoneRange: document.getElementById('pitchSemitoneRange'),
    pitchRangeReadout: document.getElementById('pitchRangeReadout'),
    includeFifths: document.getElementById('includeFifths'),
    
    // Prompt
    promptInput: document.getElementById('promptInput'),
    suggestionChips: document.querySelectorAll('.suggestion-chip'),
    
    // Results
    resultsInfo: document.getElementById('resultsInfo'),
    resultsList: document.getElementById('resultsList')
};

// Initialize
document.addEventListener('DOMContentLoaded', init);

function init() {
    setupTabs();
    setupFileUpload();
    setupButtons();
    setupSuggestions();
    setupKeyMatchingControls();
}

// ============================================
// Tab Functionality
// ============================================

function setupTabs() {
    elements.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // Update buttons
            elements.tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update content
            elements.tabContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabId}Tab`).classList.add('active');
        });
    });
}

// ============================================
// File Upload
// ============================================

function setupFileUpload() {
    // Click to upload
    elements.uploadZone.addEventListener('click', () => {
        elements.fileInput.click();
    });
    
    // File selected
    elements.fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });
    
    // Drag and drop
    elements.uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.add('dragover');
    });
    
    elements.uploadZone.addEventListener('dragleave', () => {
        elements.uploadZone.classList.remove('dragover');
    });
    
    elements.uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file && isAudioFile(file)) {
            handleFileSelect(file);
        }
    });
    
    // Remove file
    elements.removeFile.addEventListener('click', (e) => {
        e.stopPropagation();
        clearFile();
    });
}

function handleFileSelect(file) {
    if (!file) return;
    
    selectedFile = file;
    elements.fileName.textContent = file.name;
    elements.uploadZone.style.display = 'none';
    elements.filePreview.style.display = 'flex';
}

function clearFile() {
    selectedFile = null;
    elements.fileInput.value = '';
    elements.uploadZone.style.display = 'flex';
    elements.filePreview.style.display = 'none';
}

function isAudioFile(file) {
    const audioTypes = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/ogg', 'audio/mp4', 'audio/aac'];
    return audioTypes.includes(file.type) || /\.(mp3|wav|flac|ogg|m4a|aac)$/i.test(file.name);
}

// ============================================
// Buttons
// ============================================

function setupButtons() {
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    elements.findMatchesBtn.addEventListener('click', handleFindMatches);
}

function getKeyMatchingOptions() {
    const pitch = parseInt(elements.pitchSemitoneRange.value, 10);
    return {
        pitch_semitone_range: Number.isNaN(pitch) ? 1 : Math.max(0, Math.min(11, pitch)),
        include_fifths: elements.includeFifths.checked,
    };
}

function updatePitchReadout() {
    const v = parseInt(elements.pitchSemitoneRange.value, 10);
    const n = Number.isNaN(v) ? 1 : v;
    if (n === 0) {
        elements.pitchRangeReadout.textContent = 'No extra semitone shifts (same key + relative only)';
    } else {
        elements.pitchRangeReadout.textContent = `±${n} semitone${n === 1 ? '' : 's'}`;
    }
}

function setupKeyMatchingControls() {
    updatePitchReadout();
    elements.pitchSemitoneRange.addEventListener('input', () => {
        updatePitchReadout();
        refreshCompatibleKeysFromServer();
    });
    elements.includeFifths.addEventListener('change', () => {
        refreshCompatibleKeysFromServer();
    });
}

async function refreshCompatibleKeysFromServer() {
    if (!currentAnalysis || !currentAnalysis.key) return;

    const { pitch_semitone_range, include_fifths } = getKeyMatchingOptions();
    const keyParam = encodeURIComponent(currentAnalysis.key);

    try {
        const res = await fetch(
            `${API_BASE}/api/compatible-keys/${keyParam}?pitch_semitone_range=${pitch_semitone_range}&include_fifths=${include_fifths}`
        );
        const data = await res.json();
        if (!data.success || !data.compatible_keys) return;

        currentAnalysis.compatible_keys = data.compatible_keys;
        currentAnalysis.pitch_semitone_range = pitch_semitone_range;
        currentAnalysis.include_fifths = include_fifths;
        renderCompatibleKeyBadges(currentAnalysis);
    } catch (e) {
        console.warn('Could not refresh compatible keys', e);
    }
}

async function handleAnalyze() {
    const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
    
    setButtonLoading(elements.analyzeBtn, true);
    
    try {
        let result;
        
        if (activeTab === 'upload' && selectedFile) {
            result = await analyzeFile(selectedFile);
        } else if (activeTab === 'url' && elements.urlInput.value.trim()) {
            result = await analyzeUrl(elements.urlInput.value.trim());
        } else if (activeTab === 'search' && elements.songNameInput.value.trim()) {
            result = await lookupSong(
                elements.songNameInput.value.trim(),
                elements.artistInput.value.trim()
            );
        } else {
            throw new Error('Please provide a song to analyze');
        }
        
        if (result.success) {
            currentAnalysis = result.analysis;
            displayAnalysis(result.analysis);
            showSection(elements.analysisSection);
            showSection(elements.promptSection);
        } else {
            throw new Error(result.error || 'Analysis failed');
        }
    } catch (error) {
        showError(error.message);
    } finally {
        setButtonLoading(elements.analyzeBtn, false);
    }
}

async function handleFindMatches() {
    if (!currentAnalysis) {
        showError('Please analyze a song first');
        return;
    }
    
    const prompt = elements.promptInput.value.trim();
    if (!prompt) {
        showError('Please describe what kind of song you\'re looking for');
        return;
    }
    
    setButtonLoading(elements.findMatchesBtn, true);
    
    try {
        const result = await getRecommendations(currentAnalysis, prompt);
        
        if (result.success) {
            displayResults(result.recommendations, result.filters_applied);
            showSection(elements.resultsSection);
            
            // Scroll to results
            elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            throw new Error(result.error || 'Failed to get recommendations');
        }
    } catch (error) {
        showError(error.message);
    } finally {
        setButtonLoading(elements.findMatchesBtn, false);
    }
}

// ============================================
// API Calls
// ============================================

async function analyzeFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    const km = getKeyMatchingOptions();
    formData.append('pitch_semitone_range', String(km.pitch_semitone_range));
    formData.append('include_fifths', km.include_fifths ? 'true' : 'false');
    
    const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        body: formData
    });
    
    return response.json();
}

async function analyzeUrl(url) {
    const km = getKeyMatchingOptions();
    const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url, ...km })
    });
    
    return response.json();
}

async function lookupSong(songName, artist) {
    const km = getKeyMatchingOptions();
    const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ song_name: songName, artist, ...km })
    });
    
    return response.json();
}

async function getRecommendations(analysis, prompt) {
    const km = getKeyMatchingOptions();
    const response = await fetch(`${API_BASE}/api/recommend`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            analysis: { ...analysis, ...km },
            prompt,
            ...km,
        })
    });
    
    return response.json();
}

// ============================================
// Display Functions
// ============================================

function displayAnalysis(analysis) {
    // Title
    let title = 'Unknown Track';
    if (analysis.filename) {
        title = analysis.filename.replace(/\.[^/.]+$/, '');
    } else if (analysis.song_name) {
        title = analysis.song_name;
    } else if (analysis.url) {
        title = 'Analyzed Track';
    }
    
    elements.trackTitle.textContent = title;
    elements.trackSource.textContent = `Source: ${analysis.source || 'Unknown'}`;
    
    // Stats
    elements.bpmValue.textContent = analysis.bpm || '-';
    elements.keyValue.textContent = analysis.key || '-';
    elements.energyValue.textContent = analysis.energy ? `${Math.round(analysis.energy)}%` : '-';
    elements.moodValue.textContent = capitalize(analysis.mood) || '-';
    
    if (typeof analysis.pitch_semitone_range === 'number') {
        elements.pitchSemitoneRange.value = String(
            Math.max(0, Math.min(6, analysis.pitch_semitone_range))
        );
    }
    if (typeof analysis.include_fifths === 'boolean') {
        elements.includeFifths.checked = analysis.include_fifths;
    }
    updatePitchReadout();
    renderCompatibleKeyBadges(analysis);
}

function renderCompatibleKeyBadges(analysis) {
    elements.compatibleKeys.innerHTML = '';

    if (analysis.key) {
        elements.compatibleKeys.appendChild(createKeyBadge(analysis.key, true));
    }

    if (analysis.compatible_keys) {
        analysis.compatible_keys.forEach((key) => {
            if (key !== analysis.key) {
                elements.compatibleKeys.appendChild(createKeyBadge(key, false));
            }
        });
    }
}

function createKeyBadge(key, isSource) {
    const badge = document.createElement('span');
    badge.className = `key-badge${isSource ? ' source' : ''}`;
    badge.textContent = key;
    badge.title = isSource ? 'Source key' : 'Compatible for mixing';
    return badge;
}

function displayResults(recommendations, filters) {
    // Display filter info
    elements.resultsInfo.innerHTML = '';
    
    if (filters.source_key) {
        elements.resultsInfo.appendChild(createFilterTag('Source Key', filters.source_key));
    }
    if (filters.source_bpm) {
        elements.resultsInfo.appendChild(createFilterTag('BPM Range', `${Math.round(filters.source_bpm * 0.85)}-${Math.round(filters.source_bpm * 1.15)}`));
    }
    if (filters.compatible_keys && filters.compatible_keys.length > 0) {
        elements.resultsInfo.appendChild(createFilterTag('Compatible Keys', `${filters.compatible_keys.length} keys`));
    }
    if (typeof filters.pitch_semitone_range === 'number') {
        const label =
            filters.pitch_semitone_range === 0
                ? 'Pitch tolerance'
                : 'Pitch tolerance (± semitones)';
        const val =
            filters.pitch_semitone_range === 0
                ? 'none (same + relative)'
                : `±${filters.pitch_semitone_range}`;
        elements.resultsInfo.appendChild(createFilterTag(label, val));
    }
    if (typeof filters.include_fifths === 'boolean') {
        elements.resultsInfo.appendChild(
            createFilterTag('Circle of fifths', filters.include_fifths ? 'on' : 'off')
        );
    }
    
    // Display results
    elements.resultsList.innerHTML = '';
    
    if (recommendations.length === 0) {
        elements.resultsList.innerHTML = `
            <div class="no-results">
                <p>No matching songs found. Try adjusting your prompt or analyzing a different song.</p>
            </div>
        `;
        return;
    }
    
    recommendations.forEach((song, index) => {
        const card = createResultCard(song, index + 1);
        elements.resultsList.appendChild(card);
    });
}

function createFilterTag(label, value) {
    const tag = document.createElement('span');
    tag.className = 'filter-tag';
    tag.innerHTML = `${label}: <strong>${value}</strong>`;
    return tag;
}

function createResultCard(song, rank) {
    const card = document.createElement('div');
    card.className = 'result-card';
    
    const reasonsHtml = song.compatibility_reasons ? 
        song.compatibility_reasons.map(r => `<span class="reason-tag">✓ ${r}</span>`).join('') : '';
    
    const aiHtml = song.ai_recommendation ? 
        `<div class="ai-recommendation">"${song.ai_recommendation}"</div>` : '';
    
    card.innerHTML = `
        <div class="result-rank">${rank}</div>
        <div class="result-content">
            <div class="result-header">
                <div>
                    <div class="result-title">${escapeHtml(song.title)}</div>
                    <div class="result-artist">${escapeHtml(song.artist)}</div>
                </div>
                <div class="result-score">
                    <span class="score-value">${Math.round(song.compatibility_score)}</span>
                    <span class="score-label">Match</span>
                </div>
            </div>
            <div class="result-meta">
                <span class="meta-badge key">🎵 ${song.key}</span>
                <span class="meta-badge bpm">💓 ${song.bpm} BPM</span>
                <span class="meta-badge energy">⚡ ${song.energy}%</span>
                <span class="meta-badge mood">🎭 ${capitalize(song.mood)}</span>
                ${song.genre ? `<span class="meta-badge">🎸 ${song.genre}</span>` : ''}
                ${song.language ? `<span class="meta-badge">🌐 ${song.language}</span>` : ''}
            </div>
            ${reasonsHtml ? `<div class="result-reasons">${reasonsHtml}</div>` : ''}
            ${aiHtml}
        </div>
    `;
    
    return card;
}

// ============================================
// Suggestions
// ============================================

function setupSuggestions() {
    elements.suggestionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const prompt = chip.dataset.prompt;
            elements.promptInput.value = prompt;
            elements.promptInput.focus();
        });
    });
}

// ============================================
// Utility Functions
// ============================================

function setButtonLoading(button, loading) {
    const textEl = button.querySelector('.btn-text');
    const loaderEl = button.querySelector('.btn-loader');
    
    if (loading) {
        textEl.style.display = 'none';
        loaderEl.style.display = 'flex';
        button.disabled = true;
    } else {
        textEl.style.display = 'flex';
        loaderEl.style.display = 'none';
        button.disabled = false;
    }
}

function showSection(section) {
    section.style.display = 'block';
    section.classList.add('animate-in');
}

function hideSection(section) {
    section.style.display = 'none';
}

function showError(message) {
    // Simple alert for now - could be replaced with a toast notification
    alert(`Error: ${message}`);
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

