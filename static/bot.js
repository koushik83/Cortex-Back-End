// bot.js - Chat Widget

class ChatWidget {
    constructor() {
        this.companyId = this.getCompanyId();
        this.serverUrl = 'https://yourbot.com'; // Change to your server URL
        this.createWidgetHTML();
        this.initializeEventListeners();
    }

    // Get company ID from script tag
    getCompanyId() {
        const script = document.currentScript;
        return script.getAttribute('data-company');
    }

    // Create chat widget HTML
    createWidgetHTML() {
        const widgetHTML = `
            <div id="chat-widget" class="chat-widget">
                <!-- Chat Button -->
                <button id="chat-button" class="chat-button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                </button>

                <!-- Chat Container -->
                <div id="chat-container" class="chat-container hidden">
                    <div class="chat-header">
                        <span>Chat Support</span>
                        <button id="close-chat">×</button>
                    </div>
                    <div id="chat-messages" class="chat-messages"></div>
                    <div class="chat-input-container">
                        <input type="text" id="chat-input" placeholder="Type your message...">
                        <button id="send-message">Send</button>
                    </div>
                </div>
            </div>
        `;

        // Add styles
        const styles = `
            .chat-widget {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                font-family: Arial, sans-serif;
            }

            .chat-button {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: #2196F3;
                color: white;
                border: none;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .chat-container {
                position: fixed;
                bottom: 100px;
                right: 20px;
                width: 300px;
                height: 400px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
            }

            .chat-header {
                padding: 15px;
                background: #2196F3;
                color: white;
                border-radius: 10px 10px 0 0;
                display: flex;
                justify-content: space-between;
            }

            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
            }

            .message {
                margin: 8px 0;
                padding: 8px 12px;
                border-radius: 15px;
                max-width: 80%;
                word-wrap: break-word;
            }

            .user-message {
                background: #E3F2FD;
                margin-left: auto;
                border-radius: 15px 15px 0 15px;
            }

            .bot-message {
                background: #F5F5F5;
                margin-right: auto;
                border-radius: 15px 15px 15px 0;
            }

            .chat-input-container {
                padding: 15px;
                display: flex;
                gap: 10px;
            }

            #chat-input {
                flex: 1;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 20px;
                outline: none;
            }

            #send-message {
                padding: 8px 15px;
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 20px;
                cursor: pointer;
            }

            .hidden {
                display: none !important;
            }
        `;

        // Add styles to document
        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);

        // Add widget HTML to document
        const div = document.createElement('div');
        div.innerHTML = widgetHTML;
        document.body.appendChild(div);
    }

    // Initialize event listeners
    initializeEventListeners() {
        const chatButton = document.getElementById('chat-button');
        const closeChat = document.getElementById('close-chat');
        const chatContainer = document.getElementById('chat-container');
        const sendButton = document.getElementById('send-message');
        const chatInput = document.getElementById('chat-input');

        // Toggle chat window
        chatButton.addEventListener('click', () => {
            chatContainer.classList.toggle('hidden');
            if (!chatContainer.classList.contains('hidden')) {
                chatInput.focus();
            }
        });

        // Close chat
        closeChat.addEventListener('click', () => {
            chatContainer.classList.add('hidden');
        });

        // Send message
        const sendMessage = async () => {
            const message = chatInput.value.trim();
            if (message) {
                this.addMessage(message, 'user');
                chatInput.value = '';
                await this.getBotResponse(message);
            }
        };

        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    // Add message to chat
    addMessage(message, sender) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Get bot response from server
    async getBotResponse(message) {
        try {
            const response = await fetch(`${this.serverUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    company_id: this.companyId
                })
            });

            const data = await response.json();
            if (data.response) {
                this.addMessage(data.response, 'bot');
            } else {
                this.addMessage('Sorry, I encountered an error.', 'bot');
            }
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('Sorry, I encountered an error.', 'bot');
        }
    }
}

// Initialize widget when script loads
window.addEventListener('load', () => {
    new ChatWidget();
});