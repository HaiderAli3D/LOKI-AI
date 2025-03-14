// Progress Tracking Widgets for OCR A-Level Computer Science AI Tutor

// Global variables
let currentDate = new Date();
let streakData = [];
let topicProgressData = [];
let examDates = {
    'paper1': new Date('June 11, 2025'),
    'paper2': new Date('June 18, 2025')
};

// Initialize widgets when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize and load data for all widgets
    initializeActivityCalendar();
    initializeSpacedRepetition();
    initializeExamCountdown();
    
    // Event listeners for interactive elements
    setupEventListeners();
});

// Track user activity (call this on page load and user actions)
function trackUserActivity() {
    // Send activity data to server
    fetch('/student/track-activity', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            activity_type: 'page_view',
            session_duration: 0
        })
    })
    .then(response => response.json())
    .then(data => {
        // Update streak counter if returned in response
        if (data.streak && data.streakAtRisk !== undefined) {
            updateStreakCounter(data.streak, data.streakAtRisk);
        }
    })
    .catch(error => console.error('Error tracking activity:', error));
}

// ========== WIDGET 1: ACTIVITY CALENDAR & STREAK ==========

function initializeActivityCalendar() {
    // Fetch user activity data
    fetch('/student/get-activity-data')
        .then(response => response.json())
        .then(data => {
            streakData = data.activityData;
            renderActivityCalendar(streakData);
            updateStreakCounter(data.currentStreak, data.streakAtRisk);
        })
        .catch(error => {
            console.error('Error fetching activity data:', error);
            // Fallback to empty data
            renderActivityCalendar([]);
            updateStreakCounter(0, false);
        });
}

function renderActivityCalendar(activityData) {
    const calendarContainer = document.getElementById('activity-calendar');
    if (!calendarContainer) return;
    
    // Clear existing calendar
    calendarContainer.innerHTML = '';
    
    // Get current month and year
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth();
    
    // Create month header
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                         'July', 'August', 'September', 'October', 'November', 'December'];
    const monthHeader = document.createElement('div');
    monthHeader.className = 'calendar-header';
    monthHeader.innerHTML = `
        <button id="prev-month" class="calendar-nav-btn"><i class="fas fa-chevron-left"></i></button>
        <h4>${monthNames[currentMonth]} ${currentYear}</h4>
        <button id="next-month" class="calendar-nav-btn"><i class="fas fa-chevron-right"></i></button>
    `;
    calendarContainer.appendChild(monthHeader);
    
    // Create day labels
    const dayLabels = document.createElement('div');
    dayLabels.className = 'calendar-days';
    const days = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
    days.forEach(day => {
        const dayLabel = document.createElement('div');
        dayLabel.className = 'calendar-day-label';
        dayLabel.textContent = day;
        dayLabels.appendChild(dayLabel);
    });
    calendarContainer.appendChild(dayLabels);
    
    // Create calendar grid
    const calendarGrid = document.createElement('div');
    calendarGrid.className = 'calendar-grid';
    
    // Get first day of month and number of days
    const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    
    // Add empty cells for days before the 1st of the month
    for (let i = 0; i < firstDayOfMonth; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        calendarGrid.appendChild(emptyDay);
    }
    
    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${currentYear}-${(currentMonth + 1).toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
        const dayCell = document.createElement('div');
        dayCell.className = 'calendar-day';
        dayCell.dataset.date = dateStr;
        
        // Find activity level for this day (0-4)
        let activityLevel = 0;
        const dayActivity = activityData.find(a => a.date === dateStr);
        if (dayActivity) {
            activityLevel = dayActivity.level;
        }
        
        // Check if it's today
        const isToday = day === new Date().getDate() && 
                        currentMonth === new Date().getMonth() && 
                        currentYear === new Date().getFullYear();
        
        if (isToday) {
            dayCell.classList.add('today');
        }
        
        // Add activity level class
        if (activityLevel > 0) {
            dayCell.classList.add(`activity-level-${activityLevel}`);
        }
        
        dayCell.textContent = day;
        calendarGrid.appendChild(dayCell);
    }
    
    calendarContainer.appendChild(calendarGrid);
    
    // Add event listeners for month navigation
    document.getElementById('prev-month').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        initializeActivityCalendar();
    });
    
    document.getElementById('next-month').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        initializeActivityCalendar();
    });
}

function updateStreakCounter(streak, streakAtRisk) {
    const streakCounter = document.getElementById('streak-counter');
    if (!streakCounter) return;
    
    // Update streak count
    streakCounter.innerHTML = `
        <span class="streak-icon">🔥</span>
        <span class="streak-count">${streak}-day streak</span>
    `;
    
    // Add warning if streak is at risk
    if (streakAtRisk) {
        const warningElement = document.createElement('div');
        warningElement.className = 'streak-warning';
        warningElement.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>Study today to keep your streak!</span>
        `;
        streakCounter.appendChild(warningElement);
    }
}

// ========== WIDGET 2: SPACED REPETITION REMINDERS ==========

function initializeSpacedRepetition() {
    // Fetch topic progress data
    fetch('/student/get-topic-progress')
        .then(response => response.json())
        .then(data => {
            topicProgressData = data;
            renderSpacedRepetitionReminders(topicProgressData);
        })
        .catch(error => {
            console.error('Error fetching topic progress data:', error);
            renderSpacedRepetitionReminders([]);
        });
}

function renderSpacedRepetitionReminders(topicData) {
    const reminderContainer = document.getElementById('spaced-repetition-list');
    if (!reminderContainer) return;
    
    // Clear existing reminders
    reminderContainer.innerHTML = '';
    
    // Calculate which topics need review today
    const today = new Date();
    const dueTopics = calculateDueTopics(topicData, today);
    
    if (dueTopics.length === 0) {
        // No topics due today
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'no-reminders';
        emptyMessage.innerHTML = `
            <p>🎉 No topics to review today! Great job staying on top of your studies.</p>
        `;
        reminderContainer.appendChild(emptyMessage);
        return;
    }
    
    // Sort by priority (weakest understanding first)
    dueTopics.sort((a, b) => a.proficiency - b.proficiency);
    
    // Create list of recommended topics
    dueTopics.forEach(topic => {
        const reminderItem = document.createElement('div');
        reminderItem.className = 'reminder-item';
        reminderItem.dataset.topicCode = topic.topicCode;
        
        // Create proficiency indicator
        let proficiencyStars = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= topic.proficiency) {
                proficiencyStars += '<span class="star filled">★</span>';
            } else {
                proficiencyStars += '<span class="star">☆</span>';
            }
        }
        
        // Calculate days since last study
        const lastStudied = new Date(topic.lastStudied);
        const daysSince = Math.floor((today - lastStudied) / (1000 * 60 * 60 * 24));
        
        // Determine urgency class based on days overdue
        let urgencyClass = 'normal';
        if (daysSince > 7) {
            urgencyClass = 'high';
        } else if (daysSince > 3) {
            urgencyClass = 'medium';
        }
        
        reminderItem.innerHTML = `
            <div class="reminder-header">
                <span class="reminder-topic">${topic.topicTitle}</span>
                <div class="reminder-proficiency">${proficiencyStars}</div>
            </div>
            <div class="reminder-details">
                <span class="reminder-last-studied urgency-${urgencyClass}">Last studied ${daysSince} days ago</span>
                <button class="btn btn-sm btn-primary mark-reviewed-btn" 
                        data-topic-code="${topic.topicCode}">
                    Mark as Reviewed
                </button>
            </div>
        `;
        
        reminderContainer.appendChild(reminderItem);
    });
    
    // Add event listeners to mark as reviewed buttons
    const reviewButtons = document.querySelectorAll('.mark-reviewed-btn');
    reviewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const topicCode = this.dataset.topicCode;
            markTopicAsReviewed(topicCode);
        });
    });
}

function calculateDueTopics(topicData, today) {
    // Filter topics that are due for review
    return topicData.filter(topic => {
        // Skip topics with no last studied date
        if (!topic.lastStudied) return false;
        
        const lastStudied = new Date(topic.lastStudied);
        const daysSince = Math.floor((today - lastStudied) / (1000 * 60 * 60 * 24));
        
        // Calculate review interval based on proficiency
        let reviewInterval;
        switch (topic.proficiency) {
            case 1: reviewInterval = 1; break;  // Daily
            case 2: reviewInterval = 2; break;  // Every 2 days
            case 3: reviewInterval = 4; break;  // Every 4 days
            case 4: reviewInterval = 7; break;  // Weekly
            case 5: reviewInterval = 14; break; // Every 2 weeks
            default: reviewInterval = 3;        // Default fallback
        }
        
        // Topic is due if days since last study >= review interval
        return daysSince >= reviewInterval;
    });
}

function markTopicAsReviewed(topicCode) {
    // Send request to mark topic as reviewed
    fetch('/student/mark-topic-reviewed', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            topic_code: topicCode
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Refresh spaced repetition widget
            initializeSpacedRepetition();
            // Track this activity
            trackUserActivity();
        } else {
            console.error('Error marking topic as reviewed:', data.error);
        }
    })
    .catch(error => console.error('Error:', error));
}

// ========== WIDGET 3: EXAM COUNTDOWN ==========

function initializeExamCountdown() {
    // Update countdown timers
    updateExamCountdowns();
    
    // Set interval to update countdowns daily
    // (In a real app, you might want to do this more frequently)
    setInterval(updateExamCountdowns, 86400000); // 24 hours
}

function updateExamCountdowns() {
    const countdownContainer = document.getElementById('exam-countdown');
    if (!countdownContainer) return;
    
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Reset time to start of day
    
    // Clear existing countdowns
    countdownContainer.innerHTML = '';
    
    // Create countdown elements for each exam
    Object.entries(examDates).forEach(([exam, examDate]) => {
        const examName = exam === 'paper1' ? 'Paper 1' : 'Paper 2';
        const daysRemaining = Math.ceil((examDate - today) / (1000 * 60 * 60 * 24));
        
        // Calculate percentage of time passed (assuming 100 days exam preparation period)
        const totalPrepDays = 100; // Arbitrary prep period
        const percentagePassed = Math.min(100, Math.max(0, 100 - (daysRemaining / totalPrepDays * 100)));
        
        // Determine urgency class
        let urgencyClass = 'normal';
        if (daysRemaining <= 7) {
            urgencyClass = 'high';
        } else if (daysRemaining <= 30) {
            urgencyClass = 'medium';
        }
        
        const countdownElement = document.createElement('div');
        countdownElement.className = `exam-countdown-item urgency-${urgencyClass}`;
        
        // Format the date
        const formattedDate = examDate.toLocaleDateString('en-GB', {
            weekday: 'short',
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
        
        countdownElement.innerHTML = `
            <div class="countdown-header">
                <h4>${examName}</h4>
                <span class="exam-date">${formattedDate}</span>
            </div>
            <div class="countdown-circle-container">
                <div class="countdown-circle">
                    <div class="countdown-circle-fill" style="transform: rotate(${percentagePassed * 3.6}deg)"></div>
                    <div class="countdown-circle-center">
                        <span class="countdown-days">${daysRemaining}</span>
                        <span class="countdown-label">days left</span>
                    </div>
                </div>
            </div>
        `;
        
        countdownContainer.appendChild(countdownElement);
    });
}

// ========== UTILITY FUNCTIONS ==========

function setupEventListeners() {
    // Track activity when user interacts with page
    document.addEventListener('click', function(e) {
        // Only track certain interactions, like clicking on topic rows
        if (e.target.closest('.progress-table tr') || 
            e.target.closest('.reminder-item') || 
            e.target.closest('.btn')) {
            trackUserActivity();
        }
    });
    
    // Track initial page load
    trackUserActivity();
}
