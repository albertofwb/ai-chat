// 全局变量
let socket;
let currentCharacterId = '';
let currentSessionId = null;
const clientId = generateUUID();
const summaryModal = new bootstrap.Modal(document.getElementById('summaryModal'));

// DOM元素
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const characterSelect = document.getElementById('character-select');
const sessionsList = document.getElementById('sessions-list');
const newChatButton = document.getElementById('new-chat');
const viewSummaryButton = document.getElementById('view-summary');
const summaryContent = document.getElementById('summary-content');

// 初始化
document.addEventListener('DOMContentLoaded', init);

// 初始化函数
async function init() {
    await loadCharacters();
    await loadSessions();
    connectWebSocket();
    
    // 事件监听
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    characterSelect.addEventListener('change', selectCharacter);
    newChatButton.addEventListener('click', startNewChat);
    viewSummaryButton.addEventListener('click', showSummary);
}

// 加载角色列表
async function loadCharacters() {
    try {
        const response = await fetch('/api/characters');
        const data = await response.json();
        
        characterSelect.innerHTML = '';
        data.characters.forEach(character => {
            const option = document.createElement('option');
            option.value = character.id;
            option.textContent = character.name;
            characterSelect.appendChild(option);
        });
        
        if (data.characters.length > 0) {
            currentCharacterId = data.characters[0].id;
        }
    } catch (error) {
        console.error('加载角色失败:', error);
    }
}

// 加载会话列表
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        const data = await response.json();
        
        sessionsList.innerHTML = '';
        data.sessions.forEach(session => {
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item';
            item.dataset.sessionId = session.id;
            
            const date = new Date(session.updated_at);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${session.character_id}</h6>
                    <small>${formattedDate}</small>
                </div>
                <small>消息数: ${session.message_count}</small>
            `;
            
            item.addEventListener('click', function() {
                loadSession(session.id);
            });
            
            sessionsList.appendChild(item);
        });
    } catch (error) {
        console.error('加载会话失败:', error);
    }
}

// 连接WebSocket
function connectWebSocket() {
    socket = new WebSocket(`ws://${window.location.host}/ws/${clientId}`);
    
    socket.onopen = function(e) {
        console.log('WebSocket连接已建立');
    };
    
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleSocketMessage(data);
    };
    
    socket.onclose = function(event) {
        console.log('WebSocket连接已关闭');
        // 可以实现自动重连
        setTimeout(connectWebSocket, 3000);
    };
    
    socket.onerror = function(error) {
        console.error('WebSocket错误:', error);
    };
}

// 处理WebSocket消息
function handleSocketMessage(data) {
    const action = data.action;
    
    if (action === 'response') {
        // 移除"正在输入"指示器
        removeTypingIndicator();
        
        // 添加AI回复
        addMessage(data.message, 'bot');
        
        // 更新会话ID
        if (data.session_id) {
            currentSessionId = data.session_id;
            highlightCurrentSession();
        }
    } 
    else if (action === 'status' && data.status === 'thinking') {
        // 显示"正在输入"指示器
        showTypingIndicator();
    } 
    else if (action === 'character_changed') {
        chatMessages.innerHTML = '';
        currentCharacterId = data.character_id;
        currentSessionId = data.session_id;
        
        // 添加欢迎消息
        addMessage(`您好！我是${characterSelect.options[characterSelect.selectedIndex].text}，很高兴与您交流。`, 'bot');
    } 
    else if (action === 'session_loaded') {
        // 加载历史消息
        chatMessages.innerHTML = '';
        currentSessionId = data.session_id;
        
        // 显示历史消息
        data.history.forEach(msg => {
            if (msg.role === 'user') {
                addMessage(msg.content, 'user');
            } else if (msg.role === 'assistant') {
                addMessage(msg.content, 'bot');
            }
        });
        
        highlightCurrentSession();
    } 
    else if (action === 'history_cleared') {
        chatMessages.innerHTML = '';
        currentSessionId = data.session_id;
    } 
    else if (action === 'summary_result') {
        summaryContent.innerHTML = data.summary ? marked.parse(data.summary) : '暂无摘要';
        summaryModal.show();
    } 
    else if (action === 'error') {
        removeTypingIndicator();
        showError(data.error);
    }
}

// 发送消息
function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    addMessage(message, 'user');
    
    socket.send(JSON.stringify({
        action: 'chat',
        message: message
    }));
    
    messageInput.value = '';
}

// 添加消息到聊天区域
function addMessage(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}-message`;
    
    // 使用marked.js解析markdown
    messageElement.innerHTML = marked.parse(message);
    
    const timeElement = document.createElement('div');
    timeElement.className = 'message-time';
    timeElement.textContent = getCurrentTime();
    
    messageElement.appendChild(timeElement);
    chatMessages.appendChild(messageElement);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 选择角色
function selectCharacter() {
    const selectedCharacterId = characterSelect.value;
    if (selectedCharacterId === currentCharacterId) return;
    
    socket.send(JSON.stringify({
        action: 'select_character',
        character_id: selectedCharacterId
    }));
}

// 加载会话
function loadSession(sessionId) {
    socket.send(JSON.stringify({
        action: 'load_session',
        session_id: sessionId
    }));
}

// 开始新对话
function startNewChat() {
    socket.send(JSON.stringify({
        action: 'clear_history'
    }));
}

// 显示摘要
function showSummary() {
    if (!currentSessionId) {
        alert('请先开始一个对话');
        return;
    }
    
    summaryContent.innerHTML = '正在加载摘要...';
    
    socket.send(JSON.stringify({
        action: 'get_summary'
    }));
}

// 显示"正在输入"指示器
function showTypingIndicator() {
    // 检查是否已经存在
    if (document.querySelector('.typing-indicator')) {
        return;
    }
    
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(typingIndicator);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 移除"正在输入"指示器
function removeTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// 显示错误消息
function showError(errorMessage) {
    const errorElement = document.createElement('div');
    errorElement.className = 'alert alert-danger';
    errorElement.textContent = `错误: ${errorMessage}`;
    
    chatMessages.appendChild(errorElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // 错误消息自动消失
    setTimeout(() => {
        errorElement.remove();
    }, 5000);
}

// 高亮当前会话
function highlightCurrentSession() {
    document.querySelectorAll('#sessions-list .list-group-item').forEach(item => {
        item.classList.remove('active');
        if (parseInt(item.dataset.sessionId) === currentSessionId) {
            item.classList.add('active');
        }
    });
}

// 获取当前时间
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString();
}

// 生成UUID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
