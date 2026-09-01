/**
 * Mentor IA (Google Gemini Flash & Ollama) Controller para a Zona SQL ERP Totvs Consinco.
 * Gerencia a comunicação de alta velocidade com a nuvem (Gemini Flash) e local (Ollama),
 * chat interativo, depuração de erros com 1 clique e geração de consultas em linguagem natural.
 */

document.addEventListener('DOMContentLoaded', () => {
    initAiMentor();
});

function initAiMentor() {
    // Elementos DOM principais
    const btnOpenMentor = document.getElementById('btn-open-ai-mentor');
    const btnCloseMentor = document.getElementById('btn-close-ai-drawer');
    const aiDrawer = document.getElementById('ai-mentor-drawer');
    const aiStatusDot = document.querySelector('.ai-status-dot');
    const aiStatusText = document.getElementById('ai-status-text');
    const aiModelSelect = document.getElementById('ai-model-select');
    const aiLatencyBadge = document.getElementById('ai-latency-badge');
    const aiWelcomeText = document.getElementById('ai-welcome-text');

    // Modal de Configuração do Gemini
    const btnOpenGeminiConfig = document.getElementById('btn-open-gemini-config');
    const geminiModal = document.getElementById('gemini-config-modal');
    const btnCloseGeminiModal = document.getElementById('btn-close-gemini-modal');
    const inputGeminiKey = document.getElementById('input-gemini-key');
    const btnToggleKeyVis = document.getElementById('btn-toggle-key-visibility');
    const selectGeminiModalModel = document.getElementById('select-gemini-modal-model');
    const btnTestGeminiKey = document.getElementById('btn-test-gemini-key');
    const btnSaveGeminiKey = document.getElementById('btn-save-gemini-key');
    const geminiTestResult = document.getElementById('gemini-test-result');

    // Abas do Drawer
    const aiNavTabs = document.querySelectorAll('.ai-nav-tab');
    const aiTabPanes = document.querySelectorAll('.ai-tab-pane');

    // Chat
    const chatMessages = document.getElementById('ai-chat-messages');
    const chatInput = document.getElementById('ai-chat-input');
    const btnSendChat = document.getElementById('btn-ai-chat-send');
    const btnClearChat = document.getElementById('btn-ai-chat-clear');
    const chatChips = document.querySelectorAll('.ai-prompt-chip');

    // Text to SQL
    const textSqlInput = document.getElementById('ai-textsql-input');
    const btnGenSql = document.getElementById('btn-ai-generate-sql');
    const textSqlOutput = document.getElementById('ai-textsql-output');

    // Localizador de Tabelas
    const findTableInput = document.getElementById('ai-findtable-input');
    const btnFindTable = document.getElementById('btn-ai-findtable');
    const findTableOutput = document.getElementById('ai-findtable-output');

    // Histórico de Conversa em Memória
    let chatHistory = [];
    let isAiOnline = false;
    let hasGeminiKey = false;
    let currentProvider = 'gemini';

    // 1. Verificar Status de IA ao Iniciar
    checkAiStatus();
    setInterval(checkAiStatus, 25000); // Polling a cada 25s

    async function checkAiStatus() {
        try {
            const resp = await fetch('/api/ai/status');
            const data = await resp.json();
            
            hasGeminiKey = data.has_gemini_key;
            currentProvider = data.provider || 'gemini';

            if (data.online) {
                isAiOnline = true;
                if (aiStatusDot) {
                    aiStatusDot.className = 'ai-status-dot online';
                    aiStatusDot.title = `Mentor Ativo: ${data.current_model} (${currentProvider === 'gemini' ? 'Nuvem Gemini Flash' : 'Ollama Local'})`;
                }
                
                if (aiStatusText) {
                    if (currentProvider === 'gemini') {
                        aiStatusText.textContent = 'Gemini Flash';
                    } else {
                        aiStatusText.textContent = data.current_model || 'Ollama';
                    }
                }

                if (aiLatencyBadge) {
                    if (currentProvider === 'gemini') {
                        aiLatencyBadge.className = 'badge-latency badge-gemini';
                        aiLatencyBadge.textContent = `⚡ Flash (${data.latency_ms}ms)`;
                    } else {
                        aiLatencyBadge.className = 'badge-latency badge-ollama';
                        aiLatencyBadge.textContent = `🖥️ Local (${data.latency_ms}ms)`;
                    }
                }

                if (aiWelcomeText) {
                    if (currentProvider === 'gemini') {
                        aiWelcomeText.innerHTML = 'Estou conectado ao <strong>Google Gemini Flash</strong> de alta velocidade e conheço toda a arquitetura de tabelas e regras de performance do Totvs Consinco.';
                    } else {
                        aiWelcomeText.innerHTML = 'Estou conectado ao seu <strong>Ollama local</strong> e conheço toda a arquitetura de tabelas e regras de performance do Totvs Consinco.';
                    }
                }

                // Atualizar seletor de modelos
                updateModelDropdown(data);
            } else {
                isAiOnline = false;
                if (aiStatusDot) {
                    aiStatusDot.className = 'ai-status-dot offline';
                    aiStatusDot.title = 'Mentor Offline (Sem chave Gemini ou Ollama offline)';
                }
                if (aiStatusText) aiStatusText.textContent = 'Offline';
                if (aiLatencyBadge) {
                    aiLatencyBadge.className = 'badge-latency';
                    aiLatencyBadge.textContent = 'Offline';
                }
                updateModelDropdown(data);
            }
        } catch (e) {
            isAiOnline = false;
            if (aiStatusDot) aiStatusDot.className = 'ai-status-dot offline';
            if (aiStatusText) aiStatusText.textContent = 'Offline';
        }
    }

    function updateModelDropdown(data) {
        if (!aiModelSelect) return;
        const currentVal = data.current_model || 'gemini-2.5-flash';
        
        let html = '';
        
        // Grupo Gemini Flash
        html += '<optgroup label="⚡ Google Gemini (Nuvem Ultrarrápida < 1s)">';
        const geminiModels = data.gemini_models || ['gemini-2.5-flash', 'gemini-3.5-flash'];
        geminiModels.forEach(m => {
            const isSelected = m === currentVal ? 'selected' : '';
            const keyHint = !data.has_gemini_key ? ' [🔑 Inserir Chave]' : ' (Ativo ⚡)';
            html += `<option value="${m}" ${isSelected}>⚡ ${m}${keyHint}</option>`;
        });
        html += '</optgroup>';

        // Grupo Ollama Local
        if (data.ollama_models && data.ollama_models.length > 0) {
            html += '<optgroup label="🖥️ Ollama (Local - Mais Lento)">';
            data.ollama_models.filter(m => !m.toLowerCase().includes('hermes')).forEach(m => {
                const isSelected = m === currentVal ? 'selected' : '';
                html += `<option value="${m}" ${isSelected}>🖥️ ${m}</option>`;
            });
            html += '</optgroup>';
        } else {
            html += '<optgroup label="🖥️ Ollama (Local)">';
            html += '<option value="qwen2.5-coder:1.5b">🖥️ qwen2.5-coder:1.5b</option>';
            html += '<option value="gemma4:latest">🖥️ gemma4:latest</option>';
            html += '</optgroup>';
        }

        aiModelSelect.innerHTML = html;
    }

    // 2. Modal de Configuração do Gemini
    if (btnOpenGeminiConfig) {
        btnOpenGeminiConfig.addEventListener('click', openGeminiModal);
    }

    if (btnCloseGeminiModal) {
        btnCloseGeminiModal.addEventListener('click', closeGeminiModal);
    }

    if (geminiModal) {
        geminiModal.addEventListener('click', (e) => {
            if (e.target === geminiModal) closeGeminiModal();
        });
    }

    if (btnToggleKeyVis && inputGeminiKey) {
        btnToggleKeyVis.addEventListener('click', () => {
            if (inputGeminiKey.type === 'password') {
                inputGeminiKey.type = 'text';
                btnToggleKeyVis.textContent = '🙈';
            } else {
                inputGeminiKey.type = 'password';
                btnToggleKeyVis.textContent = '👁️';
            }
        });
    }

    async function openGeminiModal() {
        if (!geminiModal) return;
        geminiModal.classList.add('active');
        if (geminiTestResult) geminiTestResult.style.display = 'none';

        // Carregar config atual
        try {
            const resp = await fetch('/api/ai/config');
            const cfg = await resp.json();
            if (cfg.has_gemini_key && inputGeminiKey) {
                inputGeminiKey.placeholder = `Chave configurada (${cfg.masked_key}). Digite para alterar.`;
            }
            if (cfg.current_model && selectGeminiModalModel) {
                selectGeminiModalModel.value = cfg.current_model.startsWith('gemini') ? cfg.current_model : 'gemini-2.5-flash';
            }
        } catch (e) {
            console.error(e);
        }
        if (inputGeminiKey) inputGeminiKey.focus();
    }

    function closeGeminiModal() {
        if (geminiModal) geminiModal.classList.remove('active');
    }

    // Testar Chave Gemini
    if (btnTestGeminiKey) {
        btnTestGeminiKey.addEventListener('click', async () => {
            const keyVal = inputGeminiKey ? inputGeminiKey.value.trim() : '';
            const modelVal = selectGeminiModalModel ? selectGeminiModalModel.value : 'gemini-2.5-flash';

            btnTestGeminiKey.disabled = true;
            btnTestGeminiKey.textContent = '⏳ Testando...';
            if (geminiTestResult) {
                geminiTestResult.style.display = 'block';
                geminiTestResult.className = 'gemini-test-result testing';
                geminiTestResult.innerHTML = '⚡ Enviando requisição de teste para o Google Gemini Flash...';
            }

            try {
                const resp = await fetch('/api/ai/test_gemini', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ gemini_api_key: keyVal, model: modelVal })
                });
                const data = await resp.json();
                btnTestGeminiKey.disabled = false;
                btnTestGeminiKey.textContent = '🧪 Testar Conexão';

                if (data.success) {
                    geminiTestResult.className = 'gemini-test-result success';
                    geminiTestResult.innerHTML = `✅ <strong>Conexão bem-sucedida!</strong> Respondido pelo <code>${data.model}</code> em <strong>${data.latency_ms} ms</strong>.`;
                } else {
                    geminiTestResult.className = 'gemini-test-result error';
                    geminiTestResult.innerHTML = `❌ <strong>Falha na validação:</strong> ${data.error || 'Verifique se a chave de API é válida.'}`;
                }
            } catch (err) {
                btnTestGeminiKey.disabled = false;
                btnTestGeminiKey.textContent = '🧪 Testar Conexão';
                if (geminiTestResult) {
                    geminiTestResult.className = 'gemini-test-result error';
                    geminiTestResult.innerHTML = `❌ Erro de rede: ${err.message}`;
                }
            }
        });
    }

    // Salvar Chave Gemini
    if (btnSaveGeminiKey) {
        btnSaveGeminiKey.addEventListener('click', async () => {
            const keyVal = inputGeminiKey ? inputGeminiKey.value.trim() : '';
            const modelVal = selectGeminiModalModel ? selectGeminiModalModel.value : 'gemini-2.5-flash';

            btnSaveGeminiKey.disabled = true;
            btnSaveGeminiKey.textContent = '⏳ Salvando...';

            try {
                const resp = await fetch('/api/ai/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ gemini_api_key: keyVal, model: modelVal })
                });
                const data = await resp.json();
                btnSaveGeminiKey.disabled = false;
                btnSaveGeminiKey.textContent = '💾 Salvar e Ativar Flash';

                if (data.success) {
                    showToast(`⚡ Gemini Flash ativado com sucesso! (${modelVal})`);
                    closeGeminiModal();
                    checkAiStatus();
                    appendSystemMessage(`🚀 **Google Gemini Flash (${modelVal})** ativado com sucesso! Suas dúvidas e consultas agora respondem em velocidade máxima.`);
                } else {
                    alert(`Erro ao salvar: ${data.error || 'Não foi possível salvar.'}`);
                }
            } catch (err) {
                btnSaveGeminiKey.disabled = false;
                btnSaveGeminiKey.textContent = '💾 Salvar e Ativar Flash';
                alert(`Erro: ${err.message}`);
            }
        });
    }

    // 3. Abertura / Fechamento do Drawer
    if (btnOpenMentor) {
        btnOpenMentor.addEventListener('click', () => {
            toggleAiDrawer(true);
        });
    }

    if (btnCloseMentor) {
        btnCloseMentor.addEventListener('click', () => {
            toggleAiDrawer(false);
        });
    }

    const aiDrawerBackdrop = document.getElementById('ai-drawer-backdrop');

    function toggleAiDrawer(forceOpen) {
        if (!aiDrawer) return;
        const shouldOpen = (forceOpen !== undefined) ? Boolean(forceOpen) : !aiDrawer.classList.contains('active');
        if (shouldOpen) {
            aiDrawer.classList.add('active');
            if (aiDrawerBackdrop) aiDrawerBackdrop.classList.add('active');
            if (chatInput) chatInput.focus();
        } else {
            aiDrawer.classList.remove('active');
            if (aiDrawerBackdrop) aiDrawerBackdrop.classList.remove('active');
        }
    }
    window.toggleAiDrawer = toggleAiDrawer;

    // Botão de Abrir no Cabeçalho Superior
    if (btnOpenMentor) {
        btnOpenMentor.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleAiDrawer();
        });
    }

    // Botão ✕ de Fechar no Topo do Drawer
    if (btnCloseMentor) {
        btnCloseMentor.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleAiDrawer(false);
        });
    }

    // Clique no Backdrop Translúcido fecha o Drawer imediatamente
    if (aiDrawerBackdrop) {
        aiDrawerBackdrop.addEventListener('click', () => {
            toggleAiDrawer(false);
        });
    }

    // Atalhos de Teclado (F2 ou Esc)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (geminiModal && geminiModal.classList.contains('active')) {
                closeGeminiModal();
            } else if (aiDrawer && aiDrawer.classList.contains('active')) {
                toggleAiDrawer(false);
            }
        } else if (e.key === 'F2') {
            e.preventDefault();
            toggleAiDrawer();
        }
    });

    // Fechar ao clicar fora do Drawer
    document.addEventListener('mousedown', (e) => {
        if (aiDrawer && aiDrawer.classList.contains('active')) {
            const isClickInsideDrawer = aiDrawer.contains(e.target);
            const isClickOnOpenBtn = btnOpenMentor && btnOpenMentor.contains(e.target);
            const isClickOnGeminiModal = geminiModal && geminiModal.contains(e.target);
            const isClickOnDebugBtn = e.target.closest && e.target.closest('#btn-ai-explain-error');
            
            if (!isClickInsideDrawer && !isClickOnOpenBtn && !isClickOnGeminiModal && !isClickOnDebugBtn) {
                toggleAiDrawer(false);
            }
        }
    });

    // 4. Troca de Abas do Mentor
    aiNavTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            aiNavTabs.forEach(t => t.classList.remove('active'));
            aiTabPanes.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const targetId = tab.getAttribute('data-target');
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add('active');
        });
    });

    // 5. Mudança de Modelo Ativo no Dropdown
    if (aiModelSelect) {
        aiModelSelect.addEventListener('change', async () => {
            const selectedModel = aiModelSelect.value;

            // Se for modelo Gemini e não tiver chave, abrir modal
            if (selectedModel.startsWith('gemini') && !hasGeminiKey) {
                openGeminiModal();
                if (selectGeminiModalModel) selectGeminiModalModel.value = selectedModel;
                return;
            }

            try {
                const resp = await fetch('/api/ai/model', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model: selectedModel })
                });
                const res = await resp.json();
                if (res.success) {
                    const isGem = selectedModel.startsWith('gemini');
                    const badgeTxt = isGem ? '⚡ Google Gemini Flash (Ultrarrápido)' : '🖥️ Ollama Local';
                    appendSystemMessage(`Modelo do Mentor alterado para **${selectedModel}** (${badgeTxt}).`);
                    checkAiStatus();
                } else {
                    if (selectedModel.startsWith('gemini')) {
                        openGeminiModal();
                    }
                }
            } catch (e) {
                console.error(e);
            }
        });
    }

    // 6. Chat com o Mentor IA
    if (btnSendChat) {
        btnSendChat.addEventListener('click', sendUserChatMessage);
    }

    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendUserChatMessage();
            }
        });
    }

    if (btnClearChat) {
        btnClearChat.addEventListener('click', () => {
            chatHistory = [];
            if (chatMessages) {
                chatMessages.innerHTML = `
                    <div class="ai-welcome-card">
                        <div class="ai-welcome-icon">🤖</div>
                        <h4>Olá! Eu sou o seu Mentor IA de SQL Consinco.</h4>
                        <p>${currentProvider === 'gemini' ? 'Estou conectado ao <strong>Google Gemini Flash</strong> de alta velocidade' : 'Estou conectado ao seu <strong>Ollama local</strong>'} e conheço toda a arquitetura de tabelas e regras de performance do Totvs Consinco.</p>
                        <p>Pergunte-me qualquer dúvida, peça para criar consultas ou corrigir erros!</p>
                    </div>
                `;
            }
        });
    }

    // Chips de perguntas rápidas
    chatChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const promptText = chip.getAttribute('data-prompt') || chip.textContent;
            if (chatInput) chatInput.value = promptText;
            sendUserChatMessage();
        });
    });

    async function sendUserChatMessage() {
        const text = chatInput ? chatInput.value.trim() : '';
        if (!text) return;

        // Limpar input
        if (chatInput) chatInput.value = '';

        // Obter SQL atual do editor principal se houver
        let currentSql = '';
        if (window.editor) {
            currentSql = window.editor.getValue();
        } else {
            const ta = document.getElementById('sql-editor');
            if (ta) currentSql = ta.value;
        }

        // Adicionar mensagem do usuário na tela
        appendChatMessage('user', text);

        // Adicionar indicador de digitando
        const typingId = appendTypingIndicator();

        try {
            const resp = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    current_sql: currentSql,
                    history: chatHistory,
                    model: aiModelSelect ? aiModelSelect.value : undefined
                })
            });

            removeTypingIndicator(typingId);
            const data = await resp.json();

            if (data.success) {
                chatHistory.push({ role: 'user', content: text });
                chatHistory.push({ role: 'assistant', content: data.response });
                appendChatMessage('assistant', data.response, data.extracted_sql, data.elapsed_seconds, data.provider);
            } else {
                if (data.error && data.error.includes('Chave de API do Gemini não configurada')) {
                    appendChatMessage('assistant', `🔑 **Chave Necessária:** Para usar o **Gemini Flash**, clique no ícone da chave 🔑 no topo para colar sua chave gratuita do Google AI Studio.`);
                    openGeminiModal();
                } else {
                    appendChatMessage('assistant', `⚠️ **Aviso:** ${data.error || 'Não foi possível obter resposta do Mentor.'}`);
                }
            }
        } catch (err) {
            removeTypingIndicator(typingId);
            appendChatMessage('assistant', `❌ **Erro de Comunicação:** Falha ao contatar o servidor local.`);
        }
    }

    function appendChatMessage(role, text, extractedSql = null, elapsed = null, provider = null) {
        if (!chatMessages) return;

        // Remover o card de boas-vindas se existir
        const welcome = chatMessages.querySelector('.ai-welcome-card');
        if (welcome) welcome.remove();

        const msgDiv = document.createElement('div');
        msgDiv.className = `ai-msg ${role}`;

        const avatar = role === 'user' ? '👤' : (provider === 'gemini' ? '⚡' : '🤖');
        const author = role === 'user' ? 'Você' : (provider === 'gemini' ? 'Mentor Gemini Flash' : 'Mentor IA');
        const meta = elapsed ? `<span class="ai-meta">⏱️ ${elapsed}s</span>` : '';

        // Formatação simples de Markdown
        const formattedText = formatMarkdown(text);

        let sqlActionHtml = '';
        if (extractedSql && role === 'assistant') {
            sqlActionHtml = `
                <div class="ai-sql-card">
                    <div class="ai-sql-header">
                        <span>⚡ SQL Sugerido pelo Mentor</span>
                        <div class="ai-sql-actions">
                            <button class="btn-xs btn-outline btn-copy-ai-sql" data-sql="${encodeURIComponent(extractedSql)}">📋 Copiar</button>
                            <button class="btn-xs btn-primary btn-apply-ai-sql" data-sql="${encodeURIComponent(extractedSql)}">▶️ Inserir no Editor</button>
                        </div>
                    </div>
                    <pre><code>${escapeHtml(extractedSql)}</code></pre>
                </div>
            `;
        }

        msgDiv.innerHTML = `
            <div class="ai-msg-header">
                <span class="ai-msg-avatar">${avatar}</span>
                <span class="ai-msg-author">${author}</span>
                ${meta}
            </div>
            <div class="ai-msg-body">${formattedText}</div>
            ${sqlActionHtml}
        `;

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Bind dos botões de ação do SQL
        const btnApply = msgDiv.querySelector('.btn-apply-ai-sql');
        if (btnApply) {
            btnApply.addEventListener('click', () => {
                const sqlToApply = decodeURIComponent(btnApply.getAttribute('data-sql'));
                applySqlToEditor(sqlToApply);
            });
        }

        const btnCopy = msgDiv.querySelector('.btn-copy-ai-sql');
        if (btnCopy) {
            btnCopy.addEventListener('click', () => {
                const sqlToCopy = decodeURIComponent(btnCopy.getAttribute('data-sql'));
                navigator.clipboard.writeText(sqlToCopy);
                btnCopy.textContent = '✅ Copiado!';
                setTimeout(() => btnCopy.textContent = '📋 Copiar', 2000);
            });
        }
    }

    function appendSystemMessage(text) {
        if (!chatMessages) return;
        const div = document.createElement('div');
        div.className = 'ai-sys-msg';
        div.innerHTML = `<em>ℹ️ ${formatMarkdown(text)}</em>`;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    let typingTimerInterval = null;

    function appendTypingIndicator() {
        const id = 'typing-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'ai-msg assistant ai-typing';
        let seconds = 0;
        const isGem = aiModelSelect && aiModelSelect.value.startsWith('gemini');
        const providerName = isGem ? 'Gemini Flash' : 'Ollama Local';

        div.innerHTML = `
            <div class="ai-msg-header">
                <span class="ai-msg-avatar">${isGem ? '⚡' : '🤖'}</span>
                <span class="ai-msg-author" id="typing-author-text">Mentor ${providerName} está processando... (0s)</span>
            </div>
            <div class="ai-typing-dots">
                <span></span><span></span><span></span>
            </div>
        `;
        if (chatMessages) {
            chatMessages.appendChild(div);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        if (typingTimerInterval) clearInterval(typingTimerInterval);
        typingTimerInterval = setInterval(() => {
            seconds++;
            const authorEl = document.getElementById('typing-author-text');
            if (authorEl) {
                authorEl.textContent = `Mentor ${providerName} está processando... (${seconds}s)`;
            }
        }, 1000);

        return id;
    }

    function removeTypingIndicator(id) {
        if (typingTimerInterval) {
            clearInterval(typingTimerInterval);
            typingTimerInterval = null;
        }
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // 7. Texto para SQL
    if (btnGenSql) {
        btnGenSql.addEventListener('click', async () => {
            const reqText = textSqlInput ? textSqlInput.value.trim() : '';
            if (!reqText) return;

            const isGem = aiModelSelect && aiModelSelect.value.startsWith('gemini');
            btnGenSql.disabled = true;
            btnGenSql.textContent = '⏳ Gerando SQL com IA...';
            if (textSqlOutput) textSqlOutput.innerHTML = `<div class="ai-loading-box">Consultando ${isGem ? 'Google Gemini Flash' : 'modelo local'}...</div>`;

            try {
                const resp = await fetch('/api/ai/text_to_sql', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        request: reqText,
                        model: aiModelSelect ? aiModelSelect.value : undefined
                    })
                });
                const data = await resp.json();
                btnGenSql.disabled = false;
                btnGenSql.textContent = '🪄 Gerar SQL Consinco';

                if (data.success) {
                    const formattedExp = formatMarkdown(data.explanation);
                    textSqlOutput.innerHTML = `
                        <div class="ai-result-box">
                            <div class="ai-result-header">
                                <span>⚡ Consulta Gerada (${data.model || 'Gemini Flash'}) [${data.elapsed_seconds}s]</span>
                                <div class="ai-sql-actions">
                                    <button id="btn-copy-gen-sql" class="btn-xs btn-outline">📋 Copiar</button>
                                    <button id="btn-apply-gen-sql" class="btn-xs btn-primary">▶️ Inserir no Editor</button>
                                </div>
                            </div>
                            <pre class="code-preview-block"><code>${escapeHtml(data.generated_sql)}</code></pre>
                            <div class="ai-explanation-box">
                                <h5>📖 Explicação da Lógica:</h5>
                                ${formattedExp}
                            </div>
                        </div>
                    `;

                    document.getElementById('btn-apply-gen-sql')?.addEventListener('click', () => {
                        applySqlToEditor(data.generated_sql);
                    });

                    document.getElementById('btn-copy-gen-sql')?.addEventListener('click', () => {
                        navigator.clipboard.writeText(data.generated_sql);
                        const b = document.getElementById('btn-copy-gen-sql');
                        if (b) {
                            b.textContent = '✅ Copiado!';
                            setTimeout(() => b.textContent = '📋 Copiar', 2000);
                        }
                    });
                } else {
                    if (data.error && data.error.includes('Chave de API')) {
                        openGeminiModal();
                    }
                    textSqlOutput.innerHTML = `<div class="ai-error-box">❌ ${data.error}</div>`;
                }
            } catch (e) {
                btnGenSql.disabled = false;
                btnGenSql.textContent = '🪄 Gerar SQL Consinco';
                if (textSqlOutput) textSqlOutput.innerHTML = `<div class="ai-error-box">❌ Erro ao processar requisição.</div>`;
            }
        });
    }

    // 8. Localizador de Tabelas
    if (btnFindTable) {
        btnFindTable.addEventListener('click', async () => {
            const query = findTableInput ? findTableInput.value.trim() : '';
            if (!query) return;

            btnFindTable.disabled = true;
            btnFindTable.textContent = '⏳ Localizando...';
            if (findTableOutput) findTableOutput.innerHTML = '<div class="ai-loading-box">Buscando na arquitetura Consinco...</div>';

            try {
                const resp = await fetch('/api/ai/find_table', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: query,
                        model: aiModelSelect ? aiModelSelect.value : undefined
                    })
                });
                const data = await resp.json();
                btnFindTable.disabled = false;
                btnFindTable.textContent = '🔍 Onde está o Dado?';

                if (data.success) {
                    const formatted = formatMarkdown(data.answer);
                    findTableOutput.innerHTML = `
                        <div class="ai-result-box">
                            <div class="ai-explanation-box">
                                ${formatted}
                            </div>
                            ${data.sample_sql ? `
                                <div class="ai-sql-card" style="margin-top: 1rem;">
                                    <div class="ai-sql-header">
                                        <span>Exemplo Prático de Consulta</span>
                                        <button id="btn-apply-find-sql" class="btn-xs btn-primary">▶️ Inserir no Editor</button>
                                    </div>
                                    <pre><code>${escapeHtml(data.sample_sql)}</code></pre>
                                </div>
                            ` : ''}
                        </div>
                    `;

                    document.getElementById('btn-apply-find-sql')?.addEventListener('click', () => {
                        applySqlToEditor(data.sample_sql);
                    });
                } else {
                    findTableOutput.innerHTML = `<div class="ai-error-box">❌ ${data.error}</div>`;
                }
            } catch (e) {
                btnFindTable.disabled = false;
                btnFindTable.textContent = '🔍 Onde está o Dado?';
                if (findTableOutput) findTableOutput.innerHTML = `<div class="ai-error-box">❌ Erro na comunicação.</div>`;
            }
        });
    }

    // 9. Função Global Exposta: Depuração de Erro com IA em 1 Clique
    window.explainErrorWithAi = async function(sql, errorMsg, binds = {}) {
        toggleAiDrawer(true);

        // Ativar aba de chat
        const chatTabBtn = document.querySelector('.ai-nav-tab[data-target="ai-tab-chat"]');
        if (chatTabBtn) chatTabBtn.click();

        appendChatMessage('user', `Estou com erro na execução da minha query:\n\`\`\`sql\n${sql}\n\`\`\`\nErro retornado: **${errorMsg}**.\nPor favor, me explique o que causou o erro e me mostre a consulta corrigida.`);

        const typingId = appendTypingIndicator();

        try {
            const resp = await fetch('/api/ai/explain_error', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sql: sql,
                    error: errorMsg,
                    binds: binds,
                    model: aiModelSelect ? aiModelSelect.value : undefined
                })
            });

            removeTypingIndicator(typingId);
            const data = await resp.json();

            if (data.success) {
                appendChatMessage('assistant', data.explanation, data.fixed_sql, data.elapsed_seconds, data.provider);
            } else {
                if (data.requires_key || (data.error && data.error.includes('Chave da API'))) {
                    appendChatMessage('assistant', `🔑 **Ativação Necessária do Gemini Flash:** Para obter diagnósticos e correções em menos de 1 segundo, clique no ícone **🔑** no topo para colar sua chave gratuita do Google AI Studio.`);
                    openGeminiModal();
                } else {
                    appendChatMessage('assistant', `⚠️ Não foi possível analisar o erro: ${data.error}`);
                }
            }
        } catch (e) {
            removeTypingIndicator(typingId);
            appendChatMessage('assistant', `❌ Falha ao acionar depurador IA.`);
        }
    };

    // Helper: Inserir SQL no Editor
    function applySqlToEditor(sql) {
        if (window.editor) {
            window.editor.setValue(sql);
            window.editor.focus();
        } else {
            const ta = document.getElementById('sql-editor');
            if (ta) {
                ta.value = sql;
                ta.focus();
            }
        }

        showToast('Consulta inserida no editor com sucesso!');
        toggleAiDrawer(false);
    }

    // Helper: Toast de Notificação Global
    function showToast(msg) {
        const toast = document.createElement('div');
        toast.className = 'ai-toast';
        toast.textContent = msg;
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 50);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2500);
    }

    window.showAppToast = showToast;

    // Helper: Formatação de Markdown simples
    function formatMarkdown(txt) {
        if (!txt) return '';
        let s = escapeHtml(txt);

        // Bloco de código ```sql ... ```
        s = s.replace(/```(sql)?\s*([\s\S]*?)```/gi, '<pre class="code-block"><code>$2</code></pre>');
        // Código inline `code`
        s = s.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
        // Negrito **texto**
        s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        // Itálico *texto*
        s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        // Quebras de linha
        s = s.replace(/\n/g, '<br>');

        return s;
    }

    function escapeHtml(string) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(string).replace(/[&<>"']/g, m => map[m]);
    }
}
