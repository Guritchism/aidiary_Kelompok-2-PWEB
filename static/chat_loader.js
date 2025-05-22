// Handle chat selection and history loading
function setupChatSelection() {
    // Get all chat selection links
    const chatLinks = document.querySelectorAll('.chat-item a');
    
    if (chatLinks && chatLinks.length > 0) {
        chatLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // We don't need to preventDefault since we want the link to navigate
                
                // Here we could add visual feedback like animation
                const allChats = document.querySelectorAll('.chat-item');
                allChats.forEach(l => l.classList.remove('active'));
                this.parentElement.classList.add('active');
                
                // The actual navigation will happen via the href attribute
                // and the server will load the correct chat
                  // If we're on mobile, close the sidebar after selection
                const sidebar = document.getElementById('chatbot-sidebar');
                if (window.innerWidth <= 768 && sidebar) {
                    sidebar.classList.add('sidebar-hidden');
                    const toggleBtn = document.getElementById('toggle-sidebar');
                    if (toggleBtn) {
                        toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
                    }
                }
            });
        });
    }
}

// Helper function to load messages into chat
function loadChatMessages(messages) {
    const chatbox = document.getElementById('chatbox');
    if (!chatbox || !messages) return;
    
    // Clear existing messages
    chatbox.innerHTML = '';
    
    // Add each message
    messages.forEach(message => {
        appendMessage(message.role, message.content);
    });
    
    // Scroll to the bottom
    chatbox.scrollTop = chatbox.scrollHeight;
}

// Function to initialize the chat page
function initializeChatPage() {
    // Setup chat selection
    setupChatSelection();
    
    // Setup new chat button
    setupNewChatButton();
      
    // Load selected chat messages if available
    const selectedChatData = document.getElementById('selected-chat-data');
    if (selectedChatData) {
        try {
            const chatData = JSON.parse(selectedChatData.textContent);
            if (chatData && chatData.messages) {
                loadChatMessages(chatData.messages);
                  // Highlight the active chat in the sidebar
                const activeChatId = chatData.id;
                if (activeChatId) {
                    const chatItems = document.querySelectorAll('.chat-item');
                    chatItems.forEach(item => {
                        const link = item.querySelector('a');
                        if (link && link.getAttribute('href').includes(activeChatId)) {
                            item.classList.add('active');
                        } else {
                            item.classList.remove('active');
                        }
                    });
                }
            }
        } catch (e) {
            console.error('Error loading chat data:', e);
        }
    }
}

// Function to set up the new chat button
function setupNewChatButton() {
    const newChatButton = document.getElementById('new-chat');
    if (newChatButton) {
        newChatButton.addEventListener('click', function() {
            createNewChat();
        });
    }
}

// Function to create a new chat
function createNewChat() {
    fetch("/new_chat", { method: "POST" })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.id && data.name) {
                // Add the new chat to the sidebar immediately
                addChatToSidebar(data.id, data.name, true);
                
                // Navigate to the new chat
                window.location.href = `/chat/${data.id}`;
            }
        })
        .catch(error => {
            console.error('Error creating new chat:', error);
        });
}

// Function to add a new chat to the sidebar
function addChatToSidebar(chatId, chatName, active = false) {
    const chatList = document.getElementById('chat-list');
    if (!chatList) return;
    
    // Create a new list item
    const listItem = document.createElement('li');
    listItem.className = `chat-item ${active ? 'active' : ''}`;
    
    // Create the link
    const link = document.createElement('a');
    link.href = `/chat/${chatId}`;
    link.textContent = chatName;
    
    // Append link to list item
    listItem.appendChild(link);
    
    // Append list item to chat list
    chatList.appendChild(listItem);
    
    // Add event listener to the new chat item
    link.addEventListener('click', function(e) {
        // Visual feedback
        const allChats = document.querySelectorAll('.chat-item');
        allChats.forEach(l => l.classList.remove('active'));
        listItem.classList.add('active');
        
        // If we're on mobile, close the sidebar after selection
        const sidebar = document.getElementById('chatbot-sidebar');
        if (window.innerWidth <= 768 && sidebar) {
            sidebar.classList.add('sidebar-hidden');
            const toggleBtn = document.getElementById('toggle-sidebar');
            if (toggleBtn) {
                toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
            }
        }
    });
}

// Function to append a message to the chat box
function appendMessage(sender, text) {
    const chatbox = document.getElementById('chatbox');
    if (!chatbox) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    messageDiv.innerHTML = `<div class="chat-bubble">${formatMessage(text)}</div>`;
    chatbox.appendChild(messageDiv);
    chatbox.scrollTop = chatbox.scrollHeight;
}

// Format message text with markdown-like syntax
function formatMessage(text) {
    // Heading: ### Text → <h3>Text</h3>
    text = text.replace(/^### (.*)$/gm, '<h3>$1</h3>');

    // Inline code: `code`
    text = text.replace(/`([^`\n]+)`/g, '<code>$1</code>');

    // Bold: **text**
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic: *text*
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Line breaks
    return text.replace(/\n/g, '<br>');
}

// Call this on document load
document.addEventListener('DOMContentLoaded', () => {
    // Other initialization code
    // ...
    
    // Initialize chat page
    initializeChatPage();
});
