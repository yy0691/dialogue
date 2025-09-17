document.addEventListener('DOMContentLoaded', () => {
    const dialogueHistory = document.getElementById('dialogue-history');
    const optionsContainer = document.getElementById('options-container');
    const systemPrompt = document.getElementById('system-prompt');
    const chapterName = document.getElementById('chapter-name');

    let currentNodeInfo = null;

    function addMessage(speaker, text) {
        const messageWrapper = document.createElement('div');
        const speakerLabel = document.createElement('div');
        const messageBubble = document.createElement('div');

        speakerLabel.textContent = speaker;
        speakerLabel.className = 'speaker-label';

        messageBubble.textContent = text;
        messageBubble.classList.add('message-bubble');

        if (speaker === '咨询师') {
            messageBubble.classList.add('counselor');
            messageWrapper.style.display = 'flex';
            messageWrapper.style.flexDirection = 'column';
            messageWrapper.style.alignItems = 'flex-start';
        } else {
            messageBubble.classList.add('client');
            messageWrapper.style.display = 'flex';
            messageWrapper.style.flexDirection = 'column';
            messageWrapper.style.alignItems = 'flex-end';
        }
        
        messageWrapper.appendChild(speakerLabel);
        messageWrapper.appendChild(messageBubble);
        dialogueHistory.appendChild(messageWrapper);
        dialogueHistory.scrollTop = dialogueHistory.scrollHeight;
    }

    function showLoading(isLoading) {
        optionsContainer.innerHTML = ''; // Clear previous options
        if (isLoading) {
            const loadingIndicator = document.createElement('div');
            loadingIndicator.className = 'loading-indicator';
            loadingIndicator.textContent = 'AI 正在生成回复...';
            optionsContainer.appendChild(loadingIndicator);
        }
    }

    function displayOptions(options) {
        optionsContainer.innerHTML = ''; // Clear previous content
        optionsContainer.appendChild(systemPrompt); // Add back the prompt

        options.forEach(optionText => {
            const button = document.createElement('button');
            button.className = 'option-btn';
            
            const icon = document.createElement('span');
            icon.className = 'icon';
            
            const text = document.createElement('span');
            text.textContent = optionText;
            
            button.appendChild(icon);
            button.appendChild(text);

            button.onclick = () => handleCounselorChoice(optionText);
            optionsContainer.appendChild(button);
        });

        // Add custom input option
        const customInputButton = document.createElement('button');
        customInputButton.className = 'option-btn custom-question-btn'; // Added a specific class
        const icon = document.createElement('span');
        icon.className = 'icon';
        const text = document.createElement('span');
        text.textContent = '我想问一个额外问题...'; // Changed text for clarity
        customInputButton.appendChild(icon);
        customInputButton.appendChild(text);
        customInputButton.onclick = handleCustomQuestion;
        optionsContainer.appendChild(customInputButton);
    }

    function handleCustomQuestion() {
        optionsContainer.innerHTML = ''; // Clear options
        optionsContainer.appendChild(systemPrompt);

        const container = document.createElement('div');
        container.className = 'custom-input-container';

        const input = document.createElement('input');
        input.type = 'text';
        input.id = 'custom-input';
        input.placeholder = '在此输入您想追问的问题...';

        const sendButton = document.createElement('button');
        sendButton.id = 'send-custom-btn';
        sendButton.textContent = '发送追问';
        sendButton.onclick = () => {
            const question = input.value.trim();
            if (question) {
                sendCustomQuestionToServer(question);
            }
        };
        
        input.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                sendButton.click();
            }
        });

        container.appendChild(input);
        container.appendChild(sendButton);
        optionsContainer.appendChild(container);
        input.focus();
    }

    async function sendCustomQuestionToServer(question) {
        addMessage('咨询师', question);
        showLoading(true);

        try {
            const response = await fetch('/ask_client_custom_question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                addMessage('系统', `错误: ${data.error}`);
                showLoading(false);
                return;
            }

            // Add AI's custom response to history
            addMessage(data.speaker, data.dialogue);

            // Restore the original options
            displayOptions(data.options_to_restore);

        } catch (error) {
            addMessage('系统', `网络或服务器错误: ${error.message}`);
            showLoading(false);
        }
    }

    async function handleCounselorChoice(dialogue) {
        addMessage('咨询师', dialogue);
        showLoading(true);

        const response = await fetch('/counselor_turn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dialogue: dialogue })
        });
        const data = await response.json();
        
        currentNodeInfo = data.node_info;
        chapterName.textContent = currentNodeInfo.goal || '对话模拟';
        
        // Now, trigger AI client's response
        generateClientResponse();
    }

    async function generateClientResponse() {
        const response = await fetch('/generate_client_response', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();

        if (data.error) {
            addMessage('系统', `错误: ${data.error}`);
            showLoading(false);
            return;
        }

        addMessage('咨询者', data.dialogue);
        currentNodeInfo = data.node_info;
        chapterName.textContent = currentNodeInfo.goal || '对话模拟';

        if (currentNodeInfo.id.toUpperCase() === 'END') {
            optionsContainer.innerHTML = '<div class="system-prompt">对话已结束。</div>';
        } else {
            displayOptions(currentNodeInfo.options);
        }
    }

    async function start() {
        showLoading(true);
        const response = await fetch('/start', { method: 'POST' });
        const data = await response.json();

        addMessage(data.speaker, data.dialogue);
        currentNodeInfo = data.node_info;
        chapterName.textContent = currentNodeInfo.goal || '对话模拟';
        
        // Immediately generate the first client response
        generateClientResponse();
    }

    start();
});
