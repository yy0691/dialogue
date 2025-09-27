document.addEventListener('DOMContentLoaded', () => {
    const dialogueHistory = document.getElementById('dialogue-history');
    const optionsContainer = document.getElementById('options-container');
    const systemPrompt = document.getElementById('system-prompt');
    const chapterName = document.getElementById('chapter-name');
    const stageSelector = document.getElementById('stage-selector');
    const sessionIdDisplay = document.getElementById('session-id-display');
    const sessionsBtn = document.getElementById('sessions-btn');
    const sessionInfo = document.getElementById('session-info');
    
    // API配置相关元素
    const apiConfigBtn = document.getElementById('api-config-btn');
    const apiConfigModal = document.getElementById('api-config-modal');
    const apiModalClose = document.getElementById('api-modal-close');
    const currentApiDisplay = document.getElementById('current-api-display');
    const apiStatus = document.getElementById('api-status');
    const newApiKeyInput = document.getElementById('new-api-key');
    const toggleApiVisibility = document.getElementById('toggle-api-visibility');
    const presetApiKeys = document.getElementById('preset-api-keys');
    const addPresetKey = document.getElementById('add-preset-key');
    const testApiKey = document.getElementById('test-api-key');
    const saveApiKey = document.getElementById('save-api-key');
    const apiTestResult = document.getElementById('api-test-result');
    
    // 系统反馈相关元素
    const systemFeedbackContainer = document.getElementById('system-feedback-container');
    const feedbackCloseBtn = document.getElementById('feedback-close-btn');
    const feedbackIntent = document.getElementById('feedback-intent');
    const feedbackText = document.getElementById('feedback-text');
    const feedbackSuggestion = document.getElementById('feedback-suggestion');

    let currentNodeInfo = null;

    let currentSessionId = null;

    // API配置管理
    let currentApiKey = localStorage.getItem('currentApiKey') || '';
    let presetKeys = JSON.parse(localStorage.getItem('presetApiKeys') || '[]');

    // 页面加载时自动开始对话
    startDialogue('M1-01');
    
    // 初始化API配置显示
    updateApiDisplay();

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

    // 显示系统反馈
    function displaySystemFeedback(systemFeedback) {
        if (!systemFeedback) return;
        
        // 意图类型的中文映射
        const intentMap = {
            'GOAL_ACHIEVED': '目标达成 ✅',
            'PARTIAL_ACHIEVEMENT': '部分达成 ⚠️',
            'RAPPORT_BUILDING': '关系建立 🤝',
            'OFF_TOPIC': '偏离主题 ❌'
        };
        
        // 更新反馈内容
        feedbackIntent.textContent = intentMap[systemFeedback.intent] || systemFeedback.intent;
        feedbackText.textContent = systemFeedback.feedback || '正在分析...';
        feedbackSuggestion.textContent = systemFeedback.suggestion || '请根据情况灵活调整策略';
        
        // 根据意图类型设置不同的样式
        feedbackIntent.className = 'feedback-intent';
        if (systemFeedback.intent === 'GOAL_ACHIEVED') {
            feedbackIntent.classList.add('intent-success');
        } else if (systemFeedback.intent === 'PARTIAL_ACHIEVEMENT') {
            feedbackIntent.classList.add('intent-warning');
        } else if (systemFeedback.intent === 'OFF_TOPIC') {
            feedbackIntent.classList.add('intent-danger');
        } else {
            feedbackIntent.classList.add('intent-info');
        }
        
        // 右侧面板中的反馈容器始终显示，只需要添加更新动画
        systemFeedbackContainer.style.opacity = '0.8';
        setTimeout(() => {
            systemFeedbackContainer.style.transition = 'opacity 0.3s ease';
            systemFeedbackContainer.style.opacity = '1';
        }, 10);
    }

    // 隐藏系统反馈（在右侧面板中不需要隐藏，只是重置内容）
    function hideSystemFeedback() {
        // 重置为默认内容
        feedbackIntent.textContent = '等待分析...';
        feedbackText.textContent = '请先进行对话，系统将为您提供实时的指导建议。';
        feedbackSuggestion.textContent = '根据咨询者的回复，选择合适的后续问题。';
        feedbackIntent.className = 'feedback-intent intent-info';
    }

    // 关闭按钮事件（在右侧面板中不显示关闭按钮）
    if (feedbackCloseBtn) {
        feedbackCloseBtn.addEventListener('click', hideSystemFeedback);
    }

    // 阶段切换事件
    stageSelector.addEventListener('change', (e) => {
        const selectedNodeId = e.target.value;
        console.log('切换到阶段:', selectedNodeId);
        startDialogue(selectedNodeId);
    });

    // 开始对话函数
    async function startDialogue(nodeId = 'M1-01') {
        try {
            const response = await fetch('/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ node_id: nodeId })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.resuming) {
                // 恢复现有阶段的对话历史
                console.log('恢复阶段对话历史');
                dialogueHistory.innerHTML = '';
                
                // 重新显示历史对话
                data.history.forEach(item => {
                    addMessage(item.speaker, item.dialogue);
                });
            } else {
                // 新阶段，清空历史并显示初始消息
                console.log('开始新阶段');
                dialogueHistory.innerHTML = '';
                addMessage(data.speaker, data.dialogue);
            }

            // 更新节点信息和选项
            currentNodeInfo = data.node_info;
            chapterName.textContent = currentNodeInfo.goal || '对话模拟';
            
            if (currentNodeInfo.id.toUpperCase() === 'END') {
                optionsContainer.innerHTML = '<div class="system-prompt">对话已结束。</div>';
            } else {
                displayOptions(currentNodeInfo.options || []);
            }

        } catch (error) {
            console.error('启动对话失败:', error);
            addMessage('系统', `启动对话失败: ${error.message}`);
        }
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

            // 显示系统反馈（如果有的话）
            console.log('收到的完整响应数据:', data);  // 调试信息
            if (data.system_feedback) {
                console.log('准备显示系统反馈:', data.system_feedback);
                displaySystemFeedback(data.system_feedback);
                console.log('系统反馈显示完成');
            } else {
                console.log('没有收到系统反馈数据');
            }

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
        // 使用流式传输
        generateClientResponseStream();
    }

    async function generateClientResponseStream() {
        try {
            const response = await fetch('/generate_client_response_stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            // 创建流式消息容器
            let streamingMessage = null;
            let currentText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.type === 'start') {
                                // 开始流式显示
                                streamingMessage = createStreamingMessage(data.speaker);
                                currentText = '';
                            } else if (data.type === 'chunk') {
                                // 添加文本块
                                currentText += data.text;
                                updateStreamingMessage(streamingMessage, currentText);
                            } else if (data.type === 'complete') {
                                // 完成流式传输
                                finalizeStreamingMessage(streamingMessage, data.full_text);
                                
                                // 更新节点信息
                                currentNodeInfo = data.node_info;
                                chapterName.textContent = currentNodeInfo.goal || '对话模拟';
                                
                                if (currentNodeInfo.id.toUpperCase() === 'END') {
                                    optionsContainer.innerHTML = '<div class="system-prompt">对话已结束。</div>';
                                } else {
                                    displayOptions(currentNodeInfo.options);
                                }
                            } else if (data.type === 'error') {
                                addMessage('系统', `错误: ${data.message}`);
                                showLoading(false);
                            }
                        } catch (e) {
                            console.error('解析SSE数据失败:', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('流式传输失败:', error);
            addMessage('系统', `网络错误: ${error.message}`);
            showLoading(false);
        }
    }

    function createStreamingMessage(speaker) {
        const messageWrapper = document.createElement('div');
        const speakerLabel = document.createElement('div');
        const messageBubble = document.createElement('div');

        speakerLabel.textContent = speaker;
        speakerLabel.className = 'speaker-label';

        messageBubble.className = 'message-bubble streaming';
        messageBubble.classList.add('client');
        messageWrapper.style.display = 'flex';
        messageWrapper.style.flexDirection = 'column';
        messageWrapper.style.alignItems = 'flex-end';

        // 添加光标
        const cursor = document.createElement('span');
        cursor.className = 'typing-cursor';
        cursor.textContent = '|';
        messageBubble.appendChild(cursor);

        messageWrapper.appendChild(speakerLabel);
        messageWrapper.appendChild(messageBubble);
        dialogueHistory.appendChild(messageWrapper);
        dialogueHistory.scrollTop = dialogueHistory.scrollHeight;

        return { wrapper: messageWrapper, bubble: messageBubble, cursor: cursor };
    }

    function updateStreamingMessage(streamingMessage, text) {
        if (streamingMessage && streamingMessage.bubble) {
            streamingMessage.bubble.innerHTML = text + '<span class="typing-cursor">|</span>';
            dialogueHistory.scrollTop = dialogueHistory.scrollHeight;
        }
    }

    function finalizeStreamingMessage(streamingMessage, finalText) {
        if (streamingMessage && streamingMessage.bubble) {
            streamingMessage.bubble.textContent = finalText;
            streamingMessage.bubble.classList.remove('streaming');
        }
    }

    // API配置事件监听器
    apiConfigBtn.addEventListener('click', () => {
        apiConfigModal.style.display = 'flex';
        loadPresetKeys();
    });

    apiModalClose.addEventListener('click', () => {
        apiConfigModal.style.display = 'none';
    });

    // 点击模态框背景关闭
    apiConfigModal.addEventListener('click', (e) => {
        if (e.target === apiConfigModal) {
            apiConfigModal.style.display = 'none';
        }
    });

    // 切换API密钥可见性
    toggleApiVisibility.addEventListener('click', () => {
        const input = newApiKeyInput;
        if (input.type === 'password') {
            input.type = 'text';
            toggleApiVisibility.textContent = '🙈';
        } else {
            input.type = 'password';
            toggleApiVisibility.textContent = '👁️';
        }
    });

    // 添加到预设
    addPresetKey.addEventListener('click', () => {
        const apiKey = newApiKeyInput.value.trim();
        if (apiKey && !presetKeys.includes(apiKey)) {
            presetKeys.push(apiKey);
            localStorage.setItem('presetApiKeys', JSON.stringify(presetKeys));
            loadPresetKeys();
            newApiKeyInput.value = '';
        }
    });

    // 测试API密钥
    testApiKey.addEventListener('click', async () => {
        const apiKey = newApiKeyInput.value.trim();
        if (!apiKey) {
            showTestResult('请输入API密钥', false);
            return;
        }
        
        testApiKey.disabled = true;
        testApiKey.textContent = '测试中...';
        
        try {
            const result = await testApiConnection(apiKey);
            showTestResult(result.message, result.success);
        } catch (error) {
            showTestResult(`测试失败: ${error.message}`, false);
        } finally {
            testApiKey.disabled = false;
            testApiKey.textContent = '测试连接';
        }
    });

    // 保存并使用API密钥
    saveApiKey.addEventListener('click', async () => {
        const apiKey = newApiKeyInput.value.trim();
        if (apiKey) {
            try {
                // 设置到后端会话
                const response = await fetch('/set_api_key', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_key: apiKey })
                });
                
                const result = await response.json();
                if (result.success) {
                    currentApiKey = apiKey;
                    localStorage.setItem('currentApiKey', apiKey);
                    updateApiDisplay();
                    apiConfigModal.style.display = 'none';
                    showTestResult('API密钥已保存并激活', true);
                } else {
                    showTestResult(`保存失败: ${result.message}`, false);
                }
            } catch (error) {
                showTestResult(`保存失败: ${error.message}`, false);
            }
        }
    });

    // 会话管理功能
    sessionsBtn.addEventListener('click', () => {
        window.location.href = '/sessions';
    });

    function updateSessionInfo(sessionId) {
        if (sessionId) {
            currentSessionId = sessionId;
            sessionIdDisplay.textContent = `会话: ${sessionId.substring(0, 8)}...`;
            sessionInfo.style.display = 'block';
        } else {
            currentSessionId = null;
            sessionInfo.style.display = 'none';
        }
    }

    async function start() {
        showLoading(true);
        
        // 检查URL参数中是否有session_id
        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('session_id');
        
        const requestBody = sessionId ? { session_id: sessionId } : {};
        
        const response = await fetch('/start', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        const data = await response.json();

        addMessage(data.speaker, data.dialogue);
        currentNodeInfo = data.node_info;
        chapterName.textContent = currentNodeInfo.goal || '对话模拟';
        
        // 更新会话信息显示
        if (data.session_id) {
            updateSessionInfo(data.session_id);
        }
        
        // 如果是恢复会话，显示历史记录
        if (data.resuming && data.history) {
            // 清空当前显示
            dialogueHistory.innerHTML = '';
            // 显示历史记录
            data.history.forEach(msg => {
                addMessage(msg.speaker, msg.dialogue);
            });
        } else {
            // Immediately generate the first client response
            generateClientResponse();
        }
    }

    start();

    // API配置辅助函数
    function updateApiDisplay() {
        if (currentApiKey) {
            const maskedKey = currentApiKey.substring(0, 8) + '...' + currentApiKey.substring(currentApiKey.length - 4);
            currentApiDisplay.textContent = maskedKey;
            apiStatus.textContent = '已激活';
            apiStatus.className = 'api-status active';
        } else {
            currentApiDisplay.textContent = '未设置';
            apiStatus.textContent = '未激活';
            apiStatus.className = 'api-status inactive';
        }
    }

    function loadPresetKeys() {
        presetApiKeys.innerHTML = '';
        if (presetKeys.length === 0) {
            presetApiKeys.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">暂无预设API密钥</div>';
            return;
        }

        presetKeys.forEach((key, index) => {
            const keyItem = document.createElement('div');
            keyItem.className = 'preset-key-item';
            
            const maskedKey = key.substring(0, 8) + '...' + key.substring(key.length - 4);
            const isActive = key === currentApiKey;
            
            keyItem.innerHTML = `
                <span style="color: ${isActive ? '#007bff' : '#333'}; font-weight: ${isActive ? 'bold' : 'normal'}">
                    ${maskedKey} ${isActive ? '(当前使用)' : ''}
                </span>
                <div class="preset-key-actions">
                    <button class="use-key-btn" onclick="usePresetKey('${key}')">使用</button>
                    <button class="delete-key-btn" onclick="deletePresetKey(${index})">删除</button>
                </div>
            `;
            
            presetApiKeys.appendChild(keyItem);
        });
    }

    function showTestResult(message, success) {
        apiTestResult.textContent = message;
        apiTestResult.className = `test-result ${success ? 'success' : 'error'}`;
        apiTestResult.style.display = 'block';
        
        setTimeout(() => {
            apiTestResult.style.display = 'none';
        }, 5000);
    }

    async function testApiConnection(apiKey) {
        try {
            const response = await fetch('/test_api_key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey })
            });

            const data = await response.json();
            return data;
        } catch (error) {
            return { success: false, message: '网络错误或服务器无响应' };
        }
    }

    // 全局函数供HTML调用
    window.usePresetKey = async function(key) {
        try {
            // 设置到后端会话
            const response = await fetch('/set_api_key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: key })
            });
            
            const result = await response.json();
            if (result.success) {
                currentApiKey = key;
                localStorage.setItem('currentApiKey', key);
                updateApiDisplay();
                loadPresetKeys();
                showTestResult('API密钥已切换', true);
            } else {
                showTestResult(`切换失败: ${result.message}`, false);
            }
        } catch (error) {
            showTestResult(`切换失败: ${error.message}`, false);
        }
    };

    window.deletePresetKey = function(index) {
        if (confirm('确定要删除这个API密钥吗？')) {
            presetKeys.splice(index, 1);
            localStorage.setItem('presetApiKeys', JSON.stringify(presetKeys));
            loadPresetKeys();
        }
    };
});
