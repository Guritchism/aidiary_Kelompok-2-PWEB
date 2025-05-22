// Chat functionality
function sendMessage(emoji = null) {
    const messageInput = document.getElementById('message');
    const chatbox = document.getElementById('chatbox');
    
    // Gunakan emoji jika diberikan, jika tidak ambil dari input
    const userMessage = emoji || messageInput.value.trim();
    if (!userMessage) return;

    appendMessage('user', userMessage);
    messageInput.value = '';

    // Determine chat_id from URL path
    let chatId = window.location.pathname.split('/').pop();
    
    // Handle case where we might not have a valid chat_id in the URL
    if (!chatId || chatId === 'chat') {
        // If we're on the main chat page without a specific chat_id
        // Create a new chat first
        fetch("/new_chat", { method: "POST" })
            .then(response => response.json())
            .then(data => {
                if (data.id) {
                    console.log('Created new chat with ID:', data.id);
                    chatId = data.id;
                    sendMessageToServer(userMessage, chatId);
                }
            })
            .catch(error => {
                console.error('Error creating new chat:', error);
                appendMessage('assistant', 'Maaf, terjadi kesalahan saat memproses pesan Anda.');
            });
    } else {
        // We have a valid chat_id, proceed with sending the message
        sendMessageToServer(userMessage, chatId);
    }
}

// Helper function to send messages to server
function sendMessageToServer(userMessage, chatId) {
    fetch('/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `message=${encodeURIComponent(userMessage)}&chat_id=${encodeURIComponent(chatId)}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.assistant) {
            appendMessage('assistant', data.assistant);
        } else {
            appendMessage('assistant', 'Maaf, terjadi kesalahan dalam memproses respon.');
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        appendMessage('assistant', 'Maaf, terjadi kesalahan saat mengirim pesan Anda.');
    });
}

function appendMessage(sender, text) {
    const chatbox = document.getElementById('chatbox');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    messageDiv.innerHTML = `<div class="chat-bubble">${formatMessage(text)}</div>`;
    chatbox.appendChild(messageDiv);
    chatbox.scrollTop = chatbox.scrollHeight;
}

function formatMessage(text) {
    // Heading: ### Text → <h3>Text</h3>
    text = text.replace(/^### (.*)$/gm, '<h3>$1</h3>');

    // Inline code: `code`
    text = text.replace(/`([^`\n]+)`/g, '<code>$1</code>');

    // Bold: **text**
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic: *text*
    text = text.replace(/\*(.*?)\*\*/g, '<em>$1</em>');

    // Line breaks
    return text.replace(/\n/g, '<br>');
}

// Optional: Escape HTML in code blocks
function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function handleKey(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
}

// New chat functionality
function createNewChat() {
    fetch("/new_chat", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.id && data.name) {
                window.location.href = `/chat/${data.id}`;
            }
        });
}

// Logout functionality
function logout() {
    window.location.href = "/logout";
}

// Sidebar functionality
function checkWindowSize() {
    const sidebar = document.getElementById('chatbot-sidebar');
    if (sidebar) {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('sidebar-hidden');
        } else {
            sidebar.classList.remove('sidebar-hidden');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize orbital animations
    const orbits = document.querySelectorAll('.orbital');
    if (orbits.length > 0) {
        orbits.forEach((orbit, index) => {
            // Small delay to ensure CSS animations are applied properly
            setTimeout(() => {
                orbit.style.animationPlayState = 'running';
            }, 100 * index);
        });
    }    // Initialize sidebar elements
    const toggleBtn = document.getElementById('toggle-sidebar');
    const sidebar = document.getElementById('chatbot-sidebar');
    
    if (toggleBtn && sidebar) {
        // Check screen size on load and set initial state
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('active');
        } else {
            sidebar.classList.add('active');
        }
        
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            sidebar.classList.toggle('sidebar-hidden');
            
            // Change icon based on sidebar state
            if (sidebar.classList.contains('active')) {
                toggleBtn.innerHTML = '<i class="fas fa-times"></i>';
            } else {
                toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
            }
        });
    }
    
    // Add event listener to new chat button
    const newChatButton = document.getElementById('new-chat');
    if (newChatButton) {
        newChatButton.addEventListener('click', createNewChat);
    }
      // Add event listener to toggle sidebar button
    const toggleSidebarButton = document.getElementById('toggle-sidebar');
    if (toggleSidebarButton) {
        toggleSidebarButton.addEventListener('click', function() {
            const sidebar = document.getElementById('chatbot-sidebar');
            sidebar.classList.toggle('sidebar-hidden');
        });
    }
    
    // Add event listeners for chat functionality
    const sendButton = document.querySelector('#user-input button');
    if (sendButton) {
        sendButton.addEventListener('click', function() {
            sendMessage();
        });
    }
    
    const messageInput = document.getElementById('message');
    if (messageInput) {
        messageInput.addEventListener('keydown', function(event) {
            handleKey(event);
        });
    }
      // Add event listeners for emoji buttons
    const emojiButtons = document.querySelectorAll('.emoji-buttons-inside button');
    if (emojiButtons && emojiButtons.length > 0) {
        emojiButtons.forEach(button => {
            button.addEventListener('click', function() {
                const emoji = this.getAttribute('data-emoji') || this.textContent;
                sendMessage(emoji);
            });
        });
    }
      // Add logout button event listener
    const logoutButton = document.getElementById('logout-btn');
    if (logoutButton) {
        logoutButton.addEventListener('click', function() {
            logout();
        });
    }
    
    // Add mood tracker button event listener
    const moodTrackerButton = document.getElementById('mood-tracker-btn');
    if (moodTrackerButton) {
        moodTrackerButton.addEventListener('click', function() {
            window.location.href = '/mood-tracker';
        });
    }
    
    // Run window size check
    checkWindowSize();
    
    // Existing code for dynamic texts
    const texts = document.querySelectorAll('.dynamic-text');
    if (texts && texts.length > 0) { // Check if elements exist
        let currentIndex = 0;
        const displayDuration = 4000; // 4 seconds

        // Make sure the first text is visible on page load
        if (texts[0]) {
            texts[0].classList.add('visible');
        }

        function cycleTexts() {
            if (texts[currentIndex]) {
                texts[currentIndex].classList.remove('visible');
                texts[currentIndex].classList.add('exiting');
            }

            currentIndex = (currentIndex + 1) % texts.length;

            setTimeout(() => {
                document.querySelectorAll('.exiting').forEach(text => {
                    text.classList.remove('exiting');
                });
            }, 800);

            if (texts[currentIndex]) {
                texts[currentIndex].classList.add('visible');
            }
            
            setTimeout(cycleTexts, displayDuration);
        }

        if (texts.length > 1) { // Only cycle if there's more than one text
             setTimeout(cycleTexts, displayDuration);
        }
    }

    // Feature Tabs
    const featureTabs = document.querySelectorAll('.feature-tab');
    const featureCards = document.querySelectorAll('.feature-card');

    if (featureTabs && featureTabs.length > 0 && featureCards && featureCards.length > 0) {
        featureTabs.forEach(tab => {
            tab.addEventListener('click', function () {
                const targetId = this.getAttribute('data-target');

                featureTabs.forEach(t => t.classList.remove('active'));
                featureCards.forEach(c => c.classList.remove('active'));

                this.classList.add('active');
                const targetCard = document.getElementById(targetId);
                if (targetCard) {
                    targetCard.classList.add('active');
                    targetCard.style.animation = 'none';
                    setTimeout(() => {
                        targetCard.style.animation = 'scaleUp 0.3s ease forwards';
                    }, 10);
                }
            });
        });
    }

    function switchTab(newTabIndex) {
        const currentCard = document.querySelector('.feature-card.active');
        if (currentCard) {
            currentCard.classList.add('exit');
            currentCard.classList.remove('active');
            
            setTimeout(() => {
                currentCard.classList.remove('exit');
                
                const allFeatureCards = document.querySelectorAll('.feature-card');
                if (allFeatureCards && allFeatureCards[newTabIndex]) {
                    const newCard = allFeatureCards[newTabIndex];
                    newCard.classList.add('enter');
                    
                    setTimeout(() => {
                        newCard.classList.add('active');
                        newCard.classList.remove('enter');
                    }, 50);
                }
            }, 300);
        }
    }

    // FAQ Accordion
    const faqQuestions = document.querySelectorAll('.faq-question');
    if (faqQuestions && faqQuestions.length > 0) {
        faqQuestions.forEach(question => {
            question.addEventListener('click', function () {
                this.classList.toggle('active');
                const answer = this.nextElementSibling;
                if (answer) {
                    answer.classList.toggle('active');
                }
            });
        });
    }

    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (loginForm) {
        loginForm.reset();
    }
    if (registerForm) {
        registerForm.reset();
    }

    const loginButton = document.getElementById('login-button');
    const tryButton = document.getElementById('try-button');
    const loginOverlay = document.getElementById('login-overlay');
    const loginClose = document.getElementById('login-close');
    const registerOverlay = document.getElementById('register-overlay');
    const registerClose = document.getElementById('register-close');
    const openRegister = document.getElementById('open-register');
    const openLogin = document.getElementById('open-login');

    function openLoginModal() {
        if (loginOverlay) loginOverlay.classList.add('active');
        if (registerOverlay) registerOverlay.classList.remove('active');
        document.body.style.overflow = 'hidden';
    }

    function openRegisterModal() {
        if (registerOverlay) registerOverlay.classList.add('active');
        if (loginOverlay) loginOverlay.classList.remove('active');
        document.body.style.overflow = 'hidden';
    }

    if (loginButton) loginButton.addEventListener('click', openLoginModal);
    if (tryButton) tryButton.addEventListener('click', openLoginModal);
    
    if (openRegister) openRegister.addEventListener('click', function (e) {
        e.preventDefault();
        openRegisterModal();
    });
    if (openLogin) openLogin.addEventListener('click', function (e) {
        e.preventDefault();
        openLoginModal();
    });

    if (loginClose) {
        loginClose.addEventListener('click', function () {
            if (loginOverlay) loginOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    if (registerClose) {
        registerClose.addEventListener('click', function () {
            if (registerOverlay) registerOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    if (loginOverlay) {
        loginOverlay.addEventListener('click', function (e) {
            if (e.target === loginOverlay) {
                loginOverlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }

    if (registerOverlay) {
        registerOverlay.addEventListener('click', function (e) {
            if (e.target === registerOverlay) {
                registerOverlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }

    const elementsToObserve = document.querySelectorAll('.fade-in-on-scroll');
    if (elementsToObserve && elementsToObserve.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.3 });

        elementsToObserve.forEach(element => {
            observer.observe(element);
        });
    }

    // Enhanced animation for brain image
    console.log("Brain animation initializing...");
    const brainImages = document.querySelectorAll('.brain-img');
    
    // Insert the CSS animations if not already present
    if (!document.querySelector('#brain-animations')) {
        const styleElement = document.createElement('style');
        styleElement.id = 'brain-animations';
        styleElement.textContent = `
            @keyframes wobble {
                0% { transform: translateX(0) rotate(0); }
                15% { transform: translateX(-10px) rotate(-5deg); }
                30% { transform: translateX(8px) rotate(5deg); }
                45% { transform: translateX(-6px) rotate(-3deg); }
                60% { transform: translateX(4px) rotate(2deg); }
                75% { transform: translateX(-2px) rotate(-1deg); }
                100% { transform: translateX(0) rotate(0); }
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            
            .glow-effect {
                animation: glow 2s ease-in-out infinite !important;
            }
            
            @keyframes glow {
                0% { filter: drop-shadow(0 0 5px rgba(106, 142, 241, 0.3)); }
                50% { filter: drop-shadow(0 0 15px rgba(106, 142, 241, 0.8)); }
                100% { filter: drop-shadow(0 0 5px rgba(106, 142, 241, 0.3)); }
            }
        `;
        document.head.appendChild(styleElement);
        console.log("Added brain animation styles");
    }
    
    let clickCount = 0;
    const specialMessages = [
        "👋 Hello there!",
        "🧠 I'm your AI companion!",
        "😊 How are you feeling today?",
        "✨ Ready for some reflection?",
        "🌈 Every thought matters!"
    ];
    
    brainImages.forEach(brain => {
        console.log("Setting up animation for brain image");
        
        // Add hover effect for subtle pulse animation
        brain.addEventListener('mouseenter', function() {
            if (!this.classList.contains('glow-effect')) {
                this.style.animation = 'pulse 1.5s ease-in-out infinite';
            }
        });
        
        brain.addEventListener('mouseleave', function() {
            // Restore original animation if not currently wobbling or glowing
            if (!this.classList.contains('wobbling') && !this.classList.contains('glow-effect')) {
                const isInChat = document.querySelector('.chat-header') ? true : false;
                this.style.animation = isInChat ? 'float-small 4s ease-in-out infinite' : 'float 8s ease-in-out infinite';
            }
        });
        
        // Add click event for fun effects
        brain.addEventListener('click', function() {
            clickCount++;
            this.classList.add('wobbling');
            
            // Remove any existing tooltip
            const existingTooltip = document.querySelector('.brain-tooltip');
            if (existingTooltip) {
                existingTooltip.remove();
            }
            
            // Temporarily pause the floating animation
            const originalAnimation = this.style.animation;
            this.style.animation = 'none';
            
            // Force reflow
            this.offsetHeight;
            
            // Add a wobble animation
            this.style.animation = 'wobble 0.8s ease-in-out';
            
            // Show a fun message tooltip after 3 clicks
            if (clickCount % 3 === 0) {
                const randomMessage = specialMessages[Math.floor(Math.random() * specialMessages.length)];
                
                // Create tooltip
                const tooltip = document.createElement('div');
                tooltip.className = 'brain-tooltip';
                tooltip.textContent = randomMessage;
                tooltip.style.cssText = `
                    position: absolute;
                    background: white;
                    padding: 8px 15px;
                    border-radius: 20px;
                    font-size: 14px;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                    z-index: 1000;
                    opacity: 0;
                    transition: opacity 0.3s ease, transform 0.3s ease;
                    transform: translateY(10px);
                    top: -40px;
                    left: 50%;
                    transform: translateX(-50%);
                `;
                
                // Add tooltip to parent container instead of brain itself
                const parentElement = this.parentElement;
                parentElement.style.position = 'relative';
                parentElement.appendChild(tooltip);
                
                // Show tooltip with animation
                setTimeout(() => {
                    tooltip.style.opacity = '1';
                    tooltip.style.transform = 'translateY(0) translateX(-50%)';
                }, 100);
                
                // Remove tooltip after 3 seconds
                setTimeout(() => {
                    tooltip.style.opacity = '0';
                    tooltip.style.transform = 'translateY(-10px) translateX(-50%)';
                    
                    setTimeout(() => {
                        tooltip.remove();
                    }, 300);
                }, 3000);
                
                // Add special glow effect
                this.classList.add('glow-effect');
                
                // Remove glow effect after a few seconds
                setTimeout(() => {
                    this.classList.remove('glow-effect');
                    this.classList.remove('wobbling');
                    this.style.animation = originalAnimation;
                }, 5000);
            } else {
                // After wobble, restore the original floating animation
                setTimeout(() => {
                    this.classList.remove('wobbling');
                    const isInChat = document.querySelector('.chat-header') ? true : false;
                    this.style.animation = isInChat ? 'float-small 4s ease-in-out infinite' : 'float 8s ease-in-out infinite';
                }, 800);
            }
        });
    });

    // Khusus untuk memastikan animasi orbital berjalan
    console.log("Orbital animations initializing...");
    
    // Ambil semua elemen orbital
    const orbitalElements = document.querySelectorAll('.orbital');
    console.log(`Found ${orbitalElements.length} orbital elements`);
    
    // Tambahkan CSS yang dibutuhkan untuk animasi
    if (!document.querySelector('#orbital-animations')) {
        const styleElement = document.createElement('style');
        styleElement.id = 'orbital-animations';
        styleElement.textContent = `
            .orbital-highlight {
                border-color: rgba(106, 142, 241, 0.8) !important;
                box-shadow: 0 0 10px rgba(106, 142, 241, 0.4);
            }
        `;
        document.head.appendChild(styleElement);
    }
    
    // Pastikan animasi berjalan untuk setiap orbital
    orbitalElements.forEach((orbital, index) => {
        // Reset animasi
        orbital.style.animation = 'none';
        
        // Force reflow
        orbital.offsetHeight;
        
        // Set animasi kembali dengan style yang dipakai di aidiary lama
        setTimeout(() => {
            if (index === 0) {
                orbital.style.animation = 'rotate 15s linear infinite';
            } else if (index === 1) {
                orbital.style.animation = 'rotate 25s linear infinite';
                orbital.style.transform = 'translate(-50%, -50%) rotate(30deg)';
            } else if (index === 2) {
                orbital.style.animation = 'rotate 20s linear infinite';
                orbital.style.transform = 'translate(-50%, -50%) rotate(60deg)';
            }
            console.log(`Orbital ${index} animation started with transform: ${orbital.style.transform}`);
        }, 50 * index);
          // Add hover effects for interactive feel
        orbital.addEventListener('mouseenter', function() {
            this.classList.add('orbital-highlight');
            
            // Slow down animation slightly on hover
            const currentAnimation = this.style.animation;
            if (currentAnimation && currentAnimation.includes('rotate')) {
                const durationMatch = currentAnimation.match(/rotate\s+(\d+)s/);
                if (durationMatch && durationMatch[1]) {
                    const duration = parseInt(durationMatch[1]);
                    this.style.animation = `rotate ${duration * 1.5}s linear infinite`;
                }
            }
        });
        
        // Add click effect to reverse rotation direction for a few seconds
        orbital.addEventListener('click', function() {
            const isReversed = this.style.animation.includes('reverse');
            const currentAnimation = this.style.animation;
            
            if (currentAnimation && currentAnimation.includes('rotate')) {
                const durationMatch = currentAnimation.match(/rotate\s+(\d+)s/);
                if (durationMatch && durationMatch[1]) {
                    const duration = parseInt(durationMatch[1]);
                    
                    // Toggle direction
                    if (isReversed) {
                        this.style.animation = `rotate ${duration}s linear infinite`;
                    } else {
                        this.style.animation = `rotate ${duration}s linear infinite reverse`;
                    }
                    
                    // Flash effect
                    this.style.borderColor = 'rgba(106, 142, 241, 0.9)';
                    this.style.boxShadow = '0 0 15px rgba(106, 142, 241, 0.6)';
                    
                    // Reset after a short delay
                    setTimeout(() => {
                        this.style.borderColor = '';
                        this.style.boxShadow = '';
                    }, 800);
                }
            }
        });
        
        orbital.addEventListener('mouseleave', function() {
            this.classList.remove('orbital-highlight');
            
            // Restore normal speed
            setTimeout(() => {
                if (index === 0) {
                    orbital.style.animation = 'rotate 15s linear infinite';
                } else if (index === 1) {
                    orbital.style.animation = 'rotate 25s linear infinite';
                } else if (index === 2) {
                    orbital.style.animation = 'rotate 20s linear infinite';
                }
            }, 50);
        });
    });
});