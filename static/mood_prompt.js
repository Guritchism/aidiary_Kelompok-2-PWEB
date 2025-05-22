function selectMood(value) {
    document.querySelectorAll('.mood-option').forEach(option => {
        option.classList.remove('selected');
    });
    document.querySelector(`.mood-option[data-value="${value}"]`).classList.add('selected');
    document.getElementById('selected-mood').value = value;
}

function saveMood() {
    const mood = document.getElementById('selected-mood').value;
    if (!mood || isNaN(parseInt(mood)) || parseInt(mood) < 1 || parseInt(mood) > 5) {
        alert('Silakan pilih suasana hati terlebih dahulu.');
        return;
    }

    const note = document.getElementById('mood-note').value;
    const today = new Date().toISOString().split('T')[0]; // Format YYYY-MM-DD
    
    const formData = new FormData();
    formData.append('date', today);
    formData.append('mood', mood);
    formData.append('note', note);
    
    // Add loading state
    const submitBtn = document.querySelector('.mood-submit');
    const originalText = submitBtn.innerText;
    submitBtn.innerText = 'Menyimpan...';
    submitBtn.disabled = true;
    
    fetch('/save_mood', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        submitBtn.innerText = originalText;
        submitBtn.disabled = false;

        if (data.success) {
            closeMoodPrompt();
            alert('Terima kasih! Suasana hatimu telah dicatat.');
        } else {
            alert('Gagal menyimpan: ' + (data.error || 'Terjadi kesalahan'));
        }
    })
    .catch(error => {
        submitBtn.innerText = originalText;
        submitBtn.disabled = false;
        console.error('Error:', error);
        alert('Terjadi kesalahan saat menyimpan data.');
    });
}

function closeMoodPrompt() {
    document.getElementById('mood-prompt-overlay').style.display = 'none';
    // Set cookie to remember user's choice not to answer mood today
    document.cookie = "mood_prompt_closed=true; path=/; max-age=86400"; // 24 hours
}

// Check if the mood prompt should be displayed when page is loaded
document.addEventListener('DOMContentLoaded', function() {
    const moodPromptOverlay = document.getElementById('mood-prompt-overlay');
    if (!moodPromptOverlay) return;

    console.log('Checking mood prompt status...');
    
    // Add event listeners for mood options
    const moodOptions = document.querySelectorAll('.mood-option');
    moodOptions.forEach(option => {
        option.addEventListener('click', function() {
            const value = this.getAttribute('data-value');
            selectMood(parseInt(value));
        });
    });
    
    // Add event listener for save mood button
    const saveButton = document.querySelector('.mood-submit');
    if (saveButton) {
        saveButton.addEventListener('click', saveMood);
    }
    
    // Add event listener for close button
    const closeButton = document.querySelector('.mood-later');
    if (closeButton) {
        closeButton.addEventListener('click', closeMoodPrompt);
    }
      // First check server-side variable
    if (typeof window.showMoodPrompt !== 'undefined' && window.showMoodPrompt && !document.cookie.includes('mood_prompt_closed=true')) {
        console.log('Showing mood prompt based on server variable');
        selectMood(3); // Default to neutral mood
        moodPromptOverlay.style.display = 'flex';
    } else {
        // Double-check with the server if the variable isn't defined or is false
        fetch('/check_mood_status')
            .then(response => response.json())
            .then(data => {
                console.log('Mood status response:', data);
                if (data.loggedIn && !data.hasMoodToday && !document.cookie.includes('mood_prompt_closed=true')) {
                    console.log('Showing mood prompt based on API response');
                    selectMood(3);
                    moodPromptOverlay.style.display = 'flex';
                }
            })
            .catch(error => {
                console.error('Error checking mood status:', error);
            });
    }
});
