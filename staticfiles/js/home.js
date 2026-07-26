// home.js - Trading Dashboard Interactive Features

// CSRF Token Helper
function getCsrfToken() {
    // Try to get from cookie first
    const cookieToken = getCookie('csrftoken');
    if (cookieToken) return cookieToken;
    
    // Try to get from meta tag
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    
    // Try to get from hidden input
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input) return input.value;
    
    return null;
}

// Cookie Helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Mood Selection with Gamified Response
function selectMood(mood) {
    // Get the clicked element
    const element = document.querySelector(`[data-mood="${mood}"]`);
    if (!element) return;
    
    // Remove selected class from all
    document.querySelectorAll('.mood-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // Add selected class to clicked
    element.classList.add('selected');
    
    // Play selection animation
    element.style.animation = 'selectPulse 0.5s ease';
    setTimeout(() => {
        element.style.animation = '';
    }, 500);
    
    // Get CSRF token
    const csrfToken = getCsrfToken();
    
    if (!csrfToken) {
        showNotification('Security token missing. Please refresh the page.', 'error');
        return;
    }
    
    // Save mood via AJAX
    fetch('/save-mood/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            mood: mood,
            notes: ''
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { 
                throw new Error(err.error || `HTTP error! status: ${response.status}`); 
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Store in localStorage
            localStorage.setItem('lastMoodDate', new Date().toDateString());
            localStorage.setItem('lastMoodData', JSON.stringify(data));
            
            // Hide the mood selection section
            const moodSection = document.getElementById('moodSection');
            if (moodSection) {
                moodSection.style.display = 'none';
            }
            
            // Hide the default selected card if it exists
            const selectedCard = document.getElementById('moodSelectedCard');
            if (selectedCard) {
                selectedCard.style.display = 'none';
            }
            
            // Show the persistent mood response
            showPersistentMoodResponse(data);
            updateMoodStats();
        } else {
            showNotification(data.error || 'Failed to save mood', 'error');
        }
    })
    .catch(error => {
        // Check if it's the unique constraint error
        if (error.message.includes('UNIQUE constraint failed')) {
            // User already has a mood today - just show the persistent card
            showNotification('You already logged your mood today', 'info');
            
            // Hide mood section and show persistent card
            const moodSection = document.getElementById('moodSection');
            if (moodSection) {
                moodSection.style.display = 'none';
            }
            
            // Fetch today's mood and show it
            fetchTodayMood();
        } else {
            showNotification('Failed to save mood: ' + error.message, 'error');
        }
    });
}

// Show Persistent Mood Response
function showPersistentMoodResponse(data) {
    // Create or get response container
    let responseDiv = document.getElementById('moodResponse');
    if (!responseDiv) {
        responseDiv = document.createElement('div');
        responseDiv.id = 'moodResponse';
        responseDiv.className = 'mood-response';
        
        // Insert after mood section
        const moodSection = document.getElementById('moodSection');
        if (moodSection) {
            moodSection.parentNode.insertBefore(responseDiv, moodSection.nextSibling);
        } else {
            document.querySelector('.dashboard-container').appendChild(responseDiv);
        }
    }
    
    // Get mood display name
    const moodDisplay = getMoodDisplayName(data.mood);
    
    // Create persistent response HTML
    responseDiv.innerHTML = `
        <div class="mood-selected-card" style="margin-bottom: 0; animation: slideIn 0.5s ease;">
            <div class="selected-mood-content">
                <div class="selected-mood-badge" style="border-color: ${data.color || '#6b7280'};">
                    <span class="large-emoji">${data.emoji || '😐'}</span>
                    <span class="selected-mood-name">${moodDisplay}</span>
                </div>
                
                <div class="mood-message-card" style="background: linear-gradient(135deg, ${data.color || '#6b7280'}15, transparent); border-left: 4px solid ${data.color || '#6b7280'};">
                    <p style="color: white; font-size: 16px; margin-bottom: 10px; text-align: center;">${data.message || 'Thanks for sharing your mood!'}</p>
                    <div style="display: flex; justify-content: center;">
                        <span style="background: ${data.color || '#6b7280'}20; color: ${data.color || '#6b7280'}; padding: 6px 16px; border-radius: 30px; font-weight: 500; font-size: 14px;">${data.action || 'Keep trading mindfully'}</span>
                    </div>
                </div>
                
                <!-- Streak Display -->
                <div class="streak-display">
                    <div class="streak-icon">🔥</div>
                    <div class="streak-info">
                        <span class="streak-value" id="streakValue">${data.streak || 0}</span>
                        <span class="streak-label">Day Streak</span>
                    </div>
                </div>
                
                <!-- Comeback Message -->
                <div class="comeback-message">
                    <i class="fas fa-moon"></i>
                    <p>Come back tomorrow to log your mood again!</p>
                </div>
            </div>
        </div>
    `;
    
    responseDiv.style.display = 'block';
    responseDiv.style.marginTop = '20px';
    responseDiv.style.marginBottom = '20px';
    
    // Confetti for positive moods
    if (data.mood === 'confident' || data.mood === 'energetic' || data.mood === 'focused') {
        createConfetti();
    }
}

// Helper Functions for Mood Data
function getMoodDisplayName(mood) {
    const moodNames = {
        'confident': 'Confident',
        'cautious': 'Cautious',
        'neutral': 'Neutral',
        'stressed': 'Stressed',
        'energetic': 'Energetic',
        'tired': 'Tired',
        'focused': 'Focused',
        'anxious': 'Anxious'
    };
    return moodNames[mood] || mood;
}

function getMoodEmoji(mood) {
    const emojis = {
        'confident': '😊',
        'cautious': '🤔',
        'neutral': '😐',
        'stressed': '😓',
        'energetic': '⚡',
        'tired': '😴',
        'focused': '🎯',
        'anxious': '😰'
    };
    return emojis[mood] || '😐';
}

function getMoodMessage(mood) {
    const messages = {
        'confident': 'Great! Confidence is good, but stay humble. Stick to your plan.',
        'cautious': 'Smart! Being cautious protects your capital. Consider smaller positions.',
        'neutral': 'Balanced mindset is perfect for trading. Stay focused.',
        'stressed': 'Take a break! Stressed trading leads to mistakes.',
        'energetic': 'Energy is great! Channel it into discipline, not overtrading.',
        'tired': 'Fatigue is dangerous in trading. Consider resting.',
        'focused': 'Perfect state! Your best trades come now.',
        'anxious': 'Anxiety leads to impulsive decisions. Breathe.'
    };
    return messages[mood] || 'Thanks for sharing your mood!';
}

function getMoodAction(mood) {
    const actions = {
        'confident': 'Trade normally with strict risk management',
        'cautious': 'Trade with 0.5% risk instead of 1%',
        'neutral': 'Execute your strategy as planned',
        'stressed': 'Step away from charts. Try meditation.',
        'energetic': 'Set a max of 3 trades today',
        'tired': 'Review charts only, no live trading',
        'focused': 'Look for high-probability setups',
        'anxious': 'Demo trade only today'
    };
    return actions[mood] || 'Keep trading mindfully';
}

function getMoodColor(mood) {
    const colors = {
        'confident': '#10b981',
        'cautious': '#f59e0b',
        'neutral': '#6b7280',
        'stressed': '#ef4444',
        'energetic': '#8b5cf6',
        'tired': '#3b82f6',
        'focused': '#ec4899',
        'anxious': '#f97316'
    };
    return colors[mood] || '#6b7280';
}

// Update Mood Statistics
function updateMoodStats() {
    fetch('/get-mood-stats/?days=30')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch mood stats');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update streak display if exists
                const streakValue = document.getElementById('streakValue');
                if (streakValue && data.streak) {
                    streakValue.textContent = data.streak;
                }
            }
        })
        .catch(() => {});
}

// Fetch Today's Mood
function fetchTodayMood() {
    fetch('/get-mood-stats/')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.today_mood) {
                const moodData = {
                    success: true,
                    mood: data.today_mood.mood,
                    emoji: data.today_mood.emoji || getMoodEmoji(data.today_mood.mood),
                    streak: data.streak || 0,
                    created: false,
                    message: getMoodMessage(data.today_mood.mood),
                    action: getMoodAction(data.today_mood.mood),
                    color: getMoodColor(data.today_mood.mood)
                };
                
                localStorage.setItem('lastMoodDate', new Date().toDateString());
                localStorage.setItem('lastMoodData', JSON.stringify(moodData));
                
                showPersistentMoodResponse(moodData);
            }
        })
        .catch(() => {});
}

// Check Daily Mood Reset
function checkDailyMoodReset() {
    const lastMoodDate = localStorage.getItem('lastMoodDate');
    const today = new Date().toDateString();
    const moodSection = document.getElementById('moodSection');
    const responseDiv = document.getElementById('moodResponse');
    const djangoSelectedCard = document.getElementById('moodSelectedCard');
    
    // Check server-side first
    fetch('/get-mood-stats/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.today_mood && data.today_mood.mood) {
                    // User has mood today according to server
                    if (moodSection) moodSection.style.display = 'none';
                    if (djangoSelectedCard) djangoSelectedCard.style.display = 'none';
                    
                    // Create mood data object from server response
                    const moodData = {
                        success: true,
                        mood: data.today_mood.mood,
                        emoji: data.today_mood.emoji || getMoodEmoji(data.today_mood.mood),
                        streak: data.streak || 0,
                        created: false,
                        message: getMoodMessage(data.today_mood.mood),
                        action: getMoodAction(data.today_mood.mood),
                        color: getMoodColor(data.today_mood.mood)
                    };
                    
                    // Show persistent response
                    showPersistentMoodResponse(moodData);
                    
                    // Update localStorage
                    localStorage.setItem('lastMoodDate', today);
                    localStorage.setItem('lastMoodData', JSON.stringify(moodData));
                } else {
                    // No mood today according to server
                    if (moodSection) moodSection.style.display = 'block';
                    if (responseDiv) responseDiv.style.display = 'none';
                    if (djangoSelectedCard) djangoSelectedCard.style.display = 'none';
                    localStorage.removeItem('lastMoodDate');
                    localStorage.removeItem('lastMoodData');
                }
            }
        })
        .catch(() => {
            // Fallback to localStorage check
            if (!lastMoodDate || lastMoodDate !== today) {
                if (moodSection) moodSection.style.display = 'block';
                if (responseDiv) responseDiv.style.display = 'none';
                if (djangoSelectedCard) djangoSelectedCard.style.display = 'none';
            } else {
                if (moodSection) moodSection.style.display = 'none';
                if (djangoSelectedCard) djangoSelectedCard.style.display = 'none';
                if (responseDiv) {
                    // Show stored response
                    responseDiv.style.display = 'block';
                }
            }
        });
}

// Show Notification
function showNotification(message, type = 'info') {
    // Remove any existing notification
    const existingNotification = document.getElementById('notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.id = 'notification';
    document.body.appendChild(notification);
    
    // Style notification
    notification.textContent = message;
    
    // Set color based on type
    const colors = {
        'success': '#10b981',
        'error': '#ef4444',
        'info': '#3b82f6',
        'warning': '#f59e0b'
    };
    notification.style.background = colors[type] || colors.info;
    
    // Show notification
    notification.style.opacity = '1';
    notification.style.transform = 'translateY(0)';
    
    // Hide after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(20px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 3000);
}

// Confetti Effect
function createConfetti() {
    const colors = ['#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#a855f7', '#ec4899'];
    
    for (let i = 0; i < 50; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
            confetti.style.animation = `confetti ${Math.random() * 3 + 2}s linear forwards`;
            document.body.appendChild(confetti);
            
            setTimeout(() => {
                if (confetti.parentNode) {
                    confetti.remove();
                }
            }, 5000);
        }, i * 30);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    checkDailyMoodReset();
});

// Make selectMood function globally available
window.selectMood = selectMood;