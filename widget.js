(function() {
    // Create widget container
    const widgetContainer = document.createElement('div');
    widgetContainer.id = 'chatbot-widget-container';
    widgetContainer.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 65px;
        height: 65px;
        z-index: 9999;
    `;

    // Create chat button with an icon
    const chatButton = document.createElement('button');
    const chatIcon = document.createElement('img');
    chatIcon.src = 'https://cdn-icons-png.flaticon.com/512/906/906343.png';  // Chat bubble icon
    chatIcon.style.width = '35px';
    chatIcon.style.height = '35px';
    chatIcon.style.margin = 'auto';

    chatButton.appendChild(chatIcon);
    chatButton.style.cssText = `
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: none;
        background: linear-gradient(135deg, #6a11cb, #2575fc);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(0,0,0,0.15);
        transition: all 0.3s ease-in-out;
    `;

    // Hover effect
    chatButton.onmouseover = function() {
        chatButton.style.boxShadow = "0 6px 18px rgba(0,0,0,0.2)";
        chatButton.style.transform = "scale(1.05)";
    };
    chatButton.onmouseout = function() {
        chatButton.style.boxShadow = "0 4px 14px rgba(0,0,0,0.15)";
        chatButton.style.transform = "scale(1)";
    };

    // Create chat window
    const chatWindow = document.createElement('div');
    chatWindow.style.cssText = `
        display: none;
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 90%;
        max-width: 380px;
        height: 550px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.2);
        overflow: hidden;
        border: 2px solid #2575fc;
        transform: scale(0.9);
        opacity: 0;
        transition: transform 0.3s ease-out, opacity 0.3s ease-out;
    `;

    // Add iframe to chat window (Dynamic URL)
    const botURL = document.currentScript.getAttribute('data-bot-url') || 'http://localhost:8501';
    const chatIframe = document.createElement('iframe');
    chatIframe.src = botURL;
    chatIframe.style.cssText = `
        width: 100%;
        height: 100%;
        border: none;
        border-radius: 15px;
    `;

    // Close button
    const closeButton = document.createElement('button');
    closeButton.innerHTML = '✖';
    closeButton.style.cssText = `
        position: absolute;
        top: 10px;
        right: 15px;
        background: none;
        border: none;
        font-size: 20px;
        cursor: pointer;
    `;
    closeButton.onclick = function() {
        chatWindow.style.opacity = '0';
        chatWindow.style.transform = 'scale(0.9)';
        setTimeout(() => chatWindow.style.display = 'none', 200);
    };

    // Add elements to chat window
    chatWindow.appendChild(closeButton);
    chatWindow.appendChild(chatIframe);
    widgetContainer.appendChild(chatButton);
    widgetContainer.appendChild(chatWindow);
    document.body.appendChild(widgetContainer);

    // Toggle chat window with animation
    chatButton.onclick = function() {
        if (chatWindow.style.display === 'none' || chatWindow.style.opacity === '0') {
            chatWindow.style.display = 'block';
            setTimeout(() => {
                chatWindow.style.opacity = '1';
                chatWindow.style.transform = 'scale(1)';
            }, 100);
        } else {
            chatWindow.style.opacity = '0';
            chatWindow.style.transform = 'scale(0.9)';
            setTimeout(() => chatWindow.style.display = 'none', 200);
        }
    };
})();
