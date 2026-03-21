// API base URL - use relative path to work from any host
const API_URL = '/api';

// Theme toggle — apply saved preference before first paint to avoid flash
(function initTheme() {
    const saved = localStorage.getItem('theme');
    if (saved === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    }
})();

// Global state
let currentSessionId = null;

// DOM elements
let chatMessages, chatInput, sendButton, totalCourses, courseTitles;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements after page loads
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    totalCourses = document.getElementById('totalCourses');
    courseTitles = document.getElementById('courseTitles');
    
    setupEventListeners();
    setupThemeToggle();
    createNewSession();
    loadCourseStats();
});

// Theme Toggle
function setupThemeToggle() {
    const btn = document.getElementById('themeToggle');
    const html = document.documentElement;

    // Sync aria-label with current state on load
    btn.setAttribute('aria-label',
        html.getAttribute('data-theme') === 'light' ? 'Switch to dark mode' : 'Switch to light mode'
    );

    btn.addEventListener('click', () => {
        const isLight = html.getAttribute('data-theme') === 'light';
        if (isLight) {
            html.removeAttribute('data-theme');
            localStorage.setItem('theme', 'dark');
            btn.setAttribute('aria-label', 'Switch to light mode');
        } else {
            html.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            btn.setAttribute('aria-label', 'Switch to dark mode');
        }
    });
}

// Event Listeners
function setupEventListeners() {
    // Chat functionality
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    
    // New chat button
    document.getElementById('newChatBtn').addEventListener('click', () => {
        if (currentSessionId) {
            fetch(`${API_URL}/session/${currentSessionId}`, { method: 'DELETE' }).catch(() => {});
        }
        createNewSession();
    });

    // Suggested questions
    document.querySelectorAll('.suggested-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const question = e.target.getAttribute('data-question');
            chatInput.value = question;
            sendMessage();
        });
    });
}


// Chat Functions
async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    // Disable input
    chatInput.value = '';
    chatInput.disabled = true;
    sendButton.disabled = true;

    // Add user message
    addMessage(query, 'user');

    // Add loading message - create a unique container for it
    const loadingMessage = createLoadingMessage();
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                session_id: currentSessionId
            })
        });

        if (!response.ok) throw new Error('Query failed');

        const data = await response.json();
        
        // Update session ID if new
        if (!currentSessionId) {
            currentSessionId = data.session_id;
        }

        // Replace loading message with response
        loadingMessage.remove();
        addMessage(data.answer, 'assistant', data.sources);

    } catch (error) {
        // Replace loading message with error
        loadingMessage.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

function addMessage(content, type, sources = null, isWelcome = false) {
    const messageId = Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}${isWelcome ? ' welcome-message' : ''}`;
    messageDiv.id = `message-${messageId}`;
    
    // Convert markdown to HTML for assistant messages
    const displayContent = type === 'assistant' ? marked.parse(content) : escapeHtml(content);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = displayContent;
    messageDiv.appendChild(contentDiv);

    if (sources && sources.length > 0) {
        const details = document.createElement('details');
        details.className = 'sources-collapsible';

        const summary = document.createElement('summary');
        summary.className = 'sources-header';
        summary.textContent = 'Sources';
        details.appendChild(summary);

        const sourcesContent = document.createElement('div');
        sourcesContent.className = 'sources-content';

        sources.forEach(s => {
            if (s.url) {
                const a = document.createElement('a');
                a.href = s.url;
                a.textContent = s.label;
                a.target = '_blank';
                a.rel = 'noopener noreferrer';
                a.className = 'source-pill';
                sourcesContent.appendChild(a);
            } else {
                const span = document.createElement('span');
                span.className = 'source-pill';
                span.textContent = s.label;
                sourcesContent.appendChild(span);
            }
        });

        details.appendChild(sourcesContent);
        messageDiv.appendChild(details);
    }
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

// Helper function to escape HTML for user messages
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Removed removeMessage function - no longer needed since we handle loading differently

async function createNewSession() {
    currentSessionId = null;
    chatMessages.innerHTML = '';
    addMessage('Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?', 'assistant', null, true);
}

// Load course statistics
async function loadCourseStats() {
    try {
        console.log('Loading course stats...');
        const response = await fetch(`${API_URL}/courses`);
        if (!response.ok) throw new Error('Failed to load course stats');
        
        const data = await response.json();
        console.log('Course data received:', data);
        
        // Update stats in UI
        if (totalCourses) {
            totalCourses.textContent = data.total_courses;
        }
        
        // Update course titles
        if (courseTitles) {
            courseTitles.innerHTML = '';
            if (data.course_titles && data.course_titles.length > 0) {
                data.course_titles.forEach(title => {
                    const div = document.createElement('div');
                    div.className = 'course-title-item';
                    div.textContent = title;
                    courseTitles.appendChild(div);
                });
            } else {
                const span = document.createElement('span');
                span.className = 'no-courses';
                span.textContent = 'No courses available';
                courseTitles.appendChild(span);
            }
        }
        
    } catch (error) {
        console.error('Error loading course stats:', error);
        // Set default values on error
        if (totalCourses) {
            totalCourses.textContent = '0';
        }
        if (courseTitles) {
            courseTitles.innerHTML = '<span class="error">Failed to load courses</span>';
        }
    }
}