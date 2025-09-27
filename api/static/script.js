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
    const apiProviderSelect = document.getElementById('api-provider-select');
    const geminiConfig = document.getElementById('gemini-config');
    const siliconflowConfig = document.getElementById('siliconflow-config');
    const customConfig = document.getElementById('custom-config');
    const geminiApiKey = document.getElementById('gemini-api-key');
    const siliconflowApiKey = document.getElementById('siliconflow-api-key');
    const siliconflowUrl = document.getElementById('siliconflow-url');
    const siliconflowModel = document.getElementById('siliconflow-model');
    const siliconflowCustomModel = document.getElementById('siliconflow-custom-model');
    const customApiKey = document.getElementById('custom-api-key');
    const customUrl = document.getElementById('custom-url');
    const customModel = document.getElementById('custom-model');
    const customModelName = document.getElementById('custom-model-name');
    const customProviderName = document.getElementById('custom-provider-name');
    const toggleGeminiVisibility = document.getElementById('toggle-gemini-visibility');
    const toggleSiliconflowVisibility = document.getElementById('toggle-siliconflow-visibility');
    const toggleCustomVisibility = document.getElementById('toggle-custom-visibility');
    const presetApiKeys = document.getElementById('preset-api-keys');
    const addPresetKey = document.getElementById('add-preset-key');
    const testApiKey = document.getElementById('test-api-key');
    const saveApiKey = document.getElementById('save-api-key');
    const apiTestResult = document.getElementById('api-test-result');
    
    // 系统反馈相关元素
    const systemFeedbackContainer = document.getElementById('system-feedback-container');
    const feedbackToggleBtn = document.getElementById('feedback-toggle-btn');
    const feedbackIntent = document.getElementById('feedback-intent');
    const feedbackText = document.getElementById('feedback-text');
    const feedbackSuggestion = document.getElementById('feedback-suggestion');
    const feedbackSections = document.querySelector('.feedback-sections');
    const feedbackPlaceholder = document.querySelector('.feedback-placeholder');

    let currentNodeInfo = null;

    let currentSessionId = null;

    // API配置管理
    let currentApiConfig = JSON.parse(localStorage.getItem('currentApiConfig') || '{}');
    let presetConfigs = JSON.parse(localStorage.getItem('presetApiConfigs') || '[]');
    let availableProviders = {};

    // 页面加载时自动开始对话
    startDialogue('M1-01');
    
    // 初始化API配置显示
    updateApiDisplay();
    
    // 初始化API提供商信息
    initializeApiProviders();

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
            messageWrapper.style.alignItems = 'flex-end';
        } else {
            messageBubble.classList.add('client');
            messageWrapper.style.display = 'flex';
            messageWrapper.style.flexDirection = 'column';
            messageWrapper.style.alignItems = 'flex-start';
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
        
        // 隐藏占位符，显示反馈内容
        if (feedbackPlaceholder) {
            feedbackPlaceholder.style.display = 'none';
        }
        if (feedbackSections) {
            feedbackSections.style.display = 'block';
        }
        
        // 添加淡入动画
        feedbackSections.style.opacity = '0';
        setTimeout(() => {
            feedbackSections.style.transition = 'opacity 0.3s ease-in';
            feedbackSections.style.opacity = '1';
        }, 100);
        
        // 显示反馈容器
        systemFeedbackContainer.style.display = 'block';
        
        // 添加淡入动画
        systemFeedbackContainer.style.opacity = '0';
        systemFeedbackContainer.style.transform = 'translateY(20px)';
        setTimeout(() => {
            systemFeedbackContainer.style.transition = 'all 0.3s ease';
            systemFeedbackContainer.style.opacity = '1';
            systemFeedbackContainer.style.transform = 'translateY(0)';
        }, 10);
    }

    // 隐藏系统反馈
    function hideSystemFeedback() {
        systemFeedbackContainer.style.transition = 'all 0.3s ease';
        systemFeedbackContainer.style.opacity = '0';
        systemFeedbackContainer.style.transform = 'translateY(20px)';
        setTimeout(() => {
            systemFeedbackContainer.style.display = 'none';
        }, 300);
    }

    // 系统反馈切换按钮事件
    if (feedbackToggleBtn) {
        feedbackToggleBtn.addEventListener('click', () => {
            const feedbackPanel = document.querySelector('.feedback-panel');
            if (feedbackPanel.style.display === 'none') {
                feedbackPanel.style.display = 'flex';
                feedbackToggleBtn.textContent = '📌';
            } else {
                feedbackPanel.style.display = 'none';
                feedbackToggleBtn.textContent = '📋';
            }
        });
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
        
        // 检查是否需要触发咨询者回复
        if (currentNodeInfo.trigger_client_response) {
            // Now, trigger AI client's response
            generateClientResponse();
        } else {
            // 显示选项
            displayOptions(currentNodeInfo.options || []);
        }
    }

    async function generateClientResponse() {
        // 暂时禁用流式传输，使用普通API调用
        generateClientResponseNormal();
    }

    async function generateClientResponseNormal() {
        try {
            const response = await fetch('/generate_client_response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                addMessage('系统', `错误: ${data.error}`);
                showLoading(false);
                return;
            }

            // 添加AI回复到对话历史
            addMessage(data.speaker, data.dialogue);

            // 更新节点信息
            currentNodeInfo = data.node_info;
            chapterName.textContent = currentNodeInfo.goal || '对话模拟';

            if (currentNodeInfo.id.toUpperCase() === 'END') {
                optionsContainer.innerHTML = '<div class="system-prompt">对话已结束。</div>';
            } else {
                displayOptions(currentNodeInfo.options);
            }

        } catch (error) {
            console.error('生成回复失败:', error);
            addMessage('系统', `网络错误: ${error.message}`);
            showLoading(false);
        }
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
        messageWrapper.style.alignItems = 'flex-start';

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

    // 初始化API提供商信息
    async function initializeApiProviders() {
        try {
            const response = await fetch('/get_api_providers');
            const data = await response.json();
            if (data.success) {
                availableProviders = data.providers;
                updateProviderSelect();
            }
        } catch (error) {
            console.error('获取API提供商信息失败:', error);
        }
    }

    // API配置事件监听器
    apiConfigBtn.addEventListener('click', async () => {
        apiConfigModal.style.display = 'flex';
        await initializeApiProviders();
        loadPresetConfigs();
        updateCurrentConfigDisplay();
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

    // API提供商选择变化
    apiProviderSelect.addEventListener('change', () => {
        const selectedProvider = apiProviderSelect.value;
        showProviderConfig(selectedProvider);
    });

    // 切换API密钥可见性
    toggleGeminiVisibility.addEventListener('click', () => {
        togglePasswordVisibility(geminiApiKey, toggleGeminiVisibility);
    });

    toggleSiliconflowVisibility.addEventListener('click', () => {
        togglePasswordVisibility(siliconflowApiKey, toggleSiliconflowVisibility);
    });

    toggleCustomVisibility.addEventListener('click', () => {
        togglePasswordVisibility(customApiKey, toggleCustomVisibility);
    });

    // 自定义模型选择变化
    customModel.addEventListener('change', () => {
        if (customModel.value === 'custom') {
            customModelName.style.display = 'block';
            customModelName.focus();
        } else {
            customModelName.style.display = 'none';
        }
    });

    // 添加到预设
    addPresetKey.addEventListener('click', () => {
        const config = getCurrentProviderConfig();
        if (config && config.api_key) {
            const configKey = `${config.provider}_${config.api_key.substring(0, 8)}`;
            const existingIndex = presetConfigs.findIndex(c => 
                c.provider === config.provider && c.api_key === config.api_key
            );
            
            if (existingIndex === -1) {
                presetConfigs.push(config);
                localStorage.setItem('presetApiConfigs', JSON.stringify(presetConfigs));
                loadPresetConfigs();
                showTestResult('配置已添加到预设', true);
            } else {
                showTestResult('该配置已存在于预设中', false);
            }
        }
    });

    // 测试API连接
    testApiKey.addEventListener('click', async () => {
        const config = getCurrentProviderConfig();
        if (!config || !config.api_key) {
            showTestResult('请输入API密钥', false);
            return;
        }
        
        // 验证自定义URL格式
        if (config.provider === 'custom' && config.custom_config.base_url) {
            if (!validateApiUrl(config.custom_config.base_url)) {
                showTestResult('API地址格式无效，请输入有效的HTTP/HTTPS地址', false);
                return;
            }
        }
        
        testApiKey.disabled = true;
        testApiKey.textContent = '测试中...';
        
        try {
            const result = await testApiConnection(config);
            showTestResult(result.message, result.success);
        } catch (error) {
            showTestResult(`测试失败: ${error.message}`, false);
        } finally {
            testApiKey.disabled = false;
            testApiKey.textContent = '测试连接';
        }
    });

    // 保存并使用API配置
    saveApiKey.addEventListener('click', async () => {
        const config = getCurrentProviderConfig();
        if (!config || !config.api_key) {
            showTestResult('请输入API密钥', false);
            return;
        }
        
        try {
            const response = await fetch('/set_api_key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    api_key: config.api_key,
                    provider: config.provider,
                    custom_config: config.custom_config || {}
                })
            });
            
            const result = await response.json();
            if (result.success) {
                currentApiConfig = config;
                localStorage.setItem('currentApiConfig', JSON.stringify(config));
                updateApiDisplay();
                apiConfigModal.style.display = 'none';
                showTestResult('API配置已保存并激活', true);
            } else {
                showTestResult(`保存失败: ${result.message}`, false);
            }
        } catch (error) {
            showTestResult(`保存失败: ${error.message}`, false);
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
        if (currentApiConfig && currentApiConfig.api_key) {
            const maskedKey = currentApiConfig.api_key.substring(0, 8) + '...' + currentApiConfig.api_key.substring(currentApiConfig.api_key.length - 4);
            const providerName = availableProviders[currentApiConfig.provider]?.name || currentApiConfig.provider;
            currentApiDisplay.textContent = `${providerName}: ${maskedKey}`;
            apiStatus.textContent = '已激活';
            apiStatus.className = 'api-status active';
        } else {
            currentApiDisplay.textContent = '未设置';
            apiStatus.textContent = '未激活';
            apiStatus.className = 'api-status inactive';
        }
    }

    function updateProviderSelect() {
        apiProviderSelect.innerHTML = '';
        Object.keys(availableProviders).forEach(provider => {
            const option = document.createElement('option');
            option.value = provider;
            option.textContent = availableProviders[provider].name;
            apiProviderSelect.appendChild(option);
        });
        
        // 设置当前选择
        if (currentApiConfig.provider) {
            apiProviderSelect.value = currentApiConfig.provider;
        }
        showProviderConfig(apiProviderSelect.value);
    }

    function showProviderConfig(provider) {
        // 隐藏所有配置区域
        geminiConfig.style.display = 'none';
        siliconflowConfig.style.display = 'none';
        customConfig.style.display = 'none';
        
        // 显示选中的配置区域
        if (provider === 'gemini') {
            geminiConfig.style.display = 'block';
        } else if (provider === 'siliconflow') {
            siliconflowConfig.style.display = 'block';
        } else if (provider === 'custom') {
            customConfig.style.display = 'block';
        }
    }

    function updateCurrentConfigDisplay() {
        if (currentApiConfig.provider) {
            apiProviderSelect.value = currentApiConfig.provider;
            showProviderConfig(currentApiConfig.provider);
            
            if (currentApiConfig.provider === 'gemini') {
                geminiApiKey.value = currentApiConfig.api_key || '';
            } else if (currentApiConfig.provider === 'siliconflow') {
                siliconflowApiKey.value = currentApiConfig.api_key || '';
                if (currentApiConfig.custom_config) {
                    siliconflowUrl.value = currentApiConfig.custom_config.base_url || 'https://api.siliconflow.cn/v1';
                    siliconflowModel.value = currentApiConfig.custom_config.model || 'qwen/Qwen2.5-7B-Instruct';
                    siliconflowCustomModel.value = currentApiConfig.custom_config.custom_model || '';
                }
            } else if (currentApiConfig.provider === 'custom') {
                customApiKey.value = currentApiConfig.api_key || '';
                if (currentApiConfig.custom_config) {
                    customUrl.value = currentApiConfig.custom_config.base_url || 'https://api.openai.com/v1';
                    const modelValue = currentApiConfig.custom_config.model || 'gpt-3.5-turbo';
                    
                    // 检查是否是预设模型
                    const isPresetModel = Array.from(customModel.options).some(option => option.value === modelValue);
                    if (isPresetModel) {
                        customModel.value = modelValue;
                        customModelName.style.display = 'none';
                    } else {
                        customModel.value = 'custom';
                        customModelName.value = modelValue;
                        customModelName.style.display = 'block';
                    }
                    
                    customProviderName.value = currentApiConfig.custom_config.provider_name || '';
                }
            }
        }
    }

    function getCurrentProviderConfig() {
        const provider = apiProviderSelect.value;
        let config = {
            provider: provider,
            api_key: '',
            custom_config: {}
        };

        if (provider === 'gemini') {
            config.api_key = geminiApiKey.value.trim();
        } else if (provider === 'siliconflow') {
            config.api_key = siliconflowApiKey.value.trim();
            config.custom_config = {
                base_url: siliconflowUrl.value.trim() || 'https://api.siliconflow.cn/v1',
                model: siliconflowCustomModel.value.trim() || siliconflowModel.value
            };
        } else if (provider === 'custom') {
            config.api_key = customApiKey.value.trim();
            const modelValue = customModel.value === 'custom' ? customModelName.value.trim() : customModel.value;
            let baseUrl = customUrl.value.trim() || 'https://api.openai.com/v1';
            
            // 验证和修正URL格式
            if (baseUrl && !baseUrl.startsWith('http')) {
                baseUrl = 'https://' + baseUrl;
            }
            
            config.custom_config = {
                base_url: baseUrl,
                model: modelValue || 'gpt-3.5-turbo',
                provider_name: customProviderName.value.trim() || '自定义供应商'
            };
        }

        return config.api_key ? config : null;
    }
    
    // URL验证函数
    function validateApiUrl(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
        } catch (e) {
            return false;
        }
    }

    function togglePasswordVisibility(input, button) {
        if (input.type === 'password') {
            input.type = 'text';
            button.textContent = '🙈';
        } else {
            input.type = 'password';
            button.textContent = '👁️';
        }
    }

    function loadPresetConfigs() {
        presetApiKeys.innerHTML = '';
        if (presetConfigs.length === 0) {
            presetApiKeys.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">暂无预设API配置</div>';
            return;
        }

        presetConfigs.forEach((config, index) => {
            const configItem = document.createElement('div');
            configItem.className = 'preset-key-item';
            
            const maskedKey = config.api_key.substring(0, 8) + '...' + config.api_key.substring(config.api_key.length - 4);
            let providerName = availableProviders[config.provider]?.name || config.provider;
            
            // 如果是自定义供应商，使用用户设置的名称
            if (config.provider === 'custom' && config.custom_config?.provider_name) {
                providerName = config.custom_config.provider_name;
            }
            
            const isActive = currentApiConfig.provider === config.provider && currentApiConfig.api_key === config.api_key;
            
            configItem.innerHTML = `
                <div class="preset-key-info">
                    <div class="preset-key-provider">${providerName}</div>
                    <div class="preset-key-display" style="color: ${isActive ? '#007bff' : '#333'}; font-weight: ${isActive ? 'bold' : 'normal'}">
                        ${maskedKey} ${isActive ? '(当前使用)' : ''}
                    </div>
                </div>
                <div class="preset-key-actions">
                    <button class="use-key-btn" onclick="usePresetConfig(${index})">使用</button>
                    <button class="delete-key-btn" onclick="deletePresetConfig(${index})">删除</button>
                </div>
            `;
            
            presetApiKeys.appendChild(configItem);
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

    async function testApiConnection(config) {
        try {
            // 首先进行调试检查
            const debugResponse = await fetch('/debug_api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    api_key: config.api_key,
                    provider: config.provider,
                    custom_config: config.custom_config || {}
                })
            });
            
            const debugData = await debugResponse.json();
            console.log('API调试信息:', debugData);
            
            // 检查是否缺少依赖
            if (config.provider !== 'gemini' && debugData.debug_info && !debugData.debug_info.openai_available) {
                return { 
                    success: false, 
                    message: '缺少OpenAI库依赖，请运行: pip install openai' 
                };
            }
            
            // 进行实际的API测试
            const response = await fetch('/test_api_key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    api_key: config.api_key,
                    provider: config.provider,
                    custom_config: config.custom_config || {}
                })
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API测试错误:', error);
            return { success: false, message: '网络错误或服务器无响应' };
        }
    }

    // 全局函数供HTML调用
    window.usePresetConfig = async function(index) {
        const config = presetConfigs[index];
        if (!config) return;
        
        try {
            const response = await fetch('/set_api_key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    api_key: config.api_key,
                    provider: config.provider,
                    custom_config: config.custom_config || {}
                })
            });
            
            const result = await response.json();
            if (result.success) {
                currentApiConfig = config;
                localStorage.setItem('currentApiConfig', JSON.stringify(config));
                updateApiDisplay();
                loadPresetConfigs();
                updateCurrentConfigDisplay();
                showTestResult('API配置已切换', true);
            } else {
                showTestResult(`切换失败: ${result.message}`, false);
            }
        } catch (error) {
            showTestResult(`切换失败: ${error.message}`, false);
        }
    };

    window.deletePresetConfig = function(index) {
        if (confirm('确定要删除这个API配置吗？')) {
            presetConfigs.splice(index, 1);
            localStorage.setItem('presetApiConfigs', JSON.stringify(presetConfigs));
            loadPresetConfigs();
        }
    };
});
