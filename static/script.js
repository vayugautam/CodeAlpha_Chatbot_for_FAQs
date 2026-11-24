document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatBox = document.getElementById('chatBox');
    const typingIndicator = document.getElementById('typingIndicator');
    const themeToggle = document.getElementById('themeToggle');
    const sendBtn = document.getElementById('sendBtn');

    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);

    themeToggle.addEventListener('click', () => {
        const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    });

    const escapeHTML = (value) => String(value).replace(/[&<>'"]/g, (tag) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag]));

    const scrollToBottom = () => { chatBox.scrollTop = chatBox.scrollHeight; };

    const addMessage = (message, isUser = false, sources = []) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = message;
        messageDiv.appendChild(content);

        if (!isUser && sources.length) {
            const sourcePanel = document.createElement('div');
            sourcePanel.className = 'sources-panel';
            const heading = document.createElement('div');
            heading.className = 'sources-heading';
            heading.textContent = `Retrieved sources (${sources.length})`;
            sourcePanel.appendChild(heading);

            sources.forEach((source) => {
                const item = document.createElement('div');
                item.className = 'source-item';
                const question = document.createElement('span');
                question.className = 'source-question';
                question.textContent = `[${source.id}] ${source.question}`;
                const score = document.createElement('span');
                score.className = 'source-score';
                score.textContent = `Similarity: ${Number(source.score).toFixed(3)}`;
                item.append(question, score);
                sourcePanel.appendChild(item);
            });
            messageDiv.appendChild(sourcePanel);
        }

        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageDiv.appendChild(timestamp);

        chatBox.insertBefore(messageDiv, typingIndicator);
        scrollToBottom();
    };

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const message = userInput.value.trim();
        if (!message || sendBtn.disabled) return;

        addMessage(message, true);
        userInput.value = '';
        sendBtn.disabled = true;
        typingIndicator.classList.remove('hidden');
        scrollToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'The chatbot request failed.');
            }
            addMessage(data.reply, false, data.sources || []);
        } catch (error) {
            console.error('Chat request failed:', error);
            addMessage(error.message || 'Sorry, I could not connect to the server.');
        } finally {
            typingIndicator.classList.add('hidden');
            sendBtn.disabled = false;
            userInput.focus();
        }
    });
});
