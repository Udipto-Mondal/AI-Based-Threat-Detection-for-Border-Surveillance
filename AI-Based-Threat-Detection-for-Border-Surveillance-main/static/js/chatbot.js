document.addEventListener('DOMContentLoaded', function () {
    const fab = document.getElementById('chatbot-fab');
    const chatWidget = document.getElementById('chat-widget');
    const closeBtn = document.getElementById('close-chat');
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');

    // Toggle Chat Widget
    fab.addEventListener('click', () => {
        chatWidget.classList.toggle('hidden');
        if (!chatWidget.classList.contains('hidden')) {
            chatInput.focus();
        }
    });

    closeBtn.addEventListener('click', () => {
        chatWidget.classList.add('hidden');
    });

    // Send Message
    function sendMessage() {
        const query = chatInput.value.trim();
        if (!query) return;

        // Add User Message
        addMessage(query, 'user-message');
        chatInput.value = '';

        // Show Typing Indicator
        const typingId = addTypingIndicator();

        // Call API
        fetch('/api/chatbot/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken() // Ensure you have CSRF protection if needed
            },
            body: JSON.stringify({ query: query })
        })
            .then(response => response.json())
            .then(data => {
                removeMessage(typingId);
                addMessage(data.response, 'bot-message');
            })
            .catch(error => {
                removeMessage(typingId);
                addMessage("⚠ Connection Error. Please try again.", 'bot-message');
                console.error('Error:', error);
            });
    }

    sendBtn.addEventListener('click', sendMessage);

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Helper: Add Message to UI
    function addMessage(text, className) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', className);

        // Convert newlines to <br> for bot messages
        if (className === 'bot-message') {
            msgDiv.innerHTML = text.replace(/\n/g, '<br>');
        } else {
            msgDiv.textContent = text;
        }

        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
        return msgDiv.id = 'msg-' + Date.now();
    }

    // Helper: Typing Indicator
    function addTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.id = id;
        msgDiv.classList.add('message', 'bot-message');
        msgDiv.textContent = 'Analyzing...';
        msgDiv.style.fontStyle = 'italic';
        msgDiv.style.opacity = '0.7';
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
        return id;
    }

    // Helper: Remove Message
    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // Helper: Scroll to Bottom
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Helper: Get CSRF Token (if using Flask-WTF/SeaSurf)
    function getCsrfToken() {
        // Implementation depends on how you handle CSRF. 
        // Often stored in a meta tag or cookie.
        // For now returning null as basic Flask implementation might not enforce it strictly on API 
        // or it's handled via session cookie.
        return null;
    }
});
