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

   // Create chat button
    const chatButton = document.createElement('button');
    chatButton.innerHTML = 'Chat Now';  // Professional text label
    chatButton.style.cssText = `
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: none;
        background: linear-gradient(135deg, #6a11cb, #2575fc);
        color: white;
        font-size: 14px;
        font-weight: bold;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(0,0,0,0.15);
        transition: all 0.3s ease-in-out;
        padding: 8px;
        text-transform: uppercase;
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
        width: 380px;
        height: 550px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.2);
        overflow: hidden;
        border: 2px solid #2575fc;
    `;

    // Add iframe to chat window
    const chatIframe = document.createElement('iframe');
    chatIframe.src = 'http://localhost:8501';  // Your Streamlit app URL
    chatIframe.style.cssText = `
        width: 100%;
        height: 100%;
        border: none;
        border-radius: 15px;
    `;

    // Add elements to page
    chatWindow.appendChild(chatIframe);
    widgetContainer.appendChild(chatButton);
    widgetContainer.appendChild(chatWindow);
    document.body.appendChild(widgetContainer);

    // Toggle chat window
    chatButton.onclick = function() {
        const isVisible = chatWindow.style.display === 'block';
        chatWindow.style.display = isVisible ? 'none' : 'block';
    };
})();
