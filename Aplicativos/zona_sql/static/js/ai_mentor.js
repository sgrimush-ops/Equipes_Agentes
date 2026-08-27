/**
 * Mentor IA (Ollama) Controller para a Zona SQL ERP Totvs Consinco.
 * Gerencia a comunicação com os endpoints de IA, chat interativo,
 * depuração de erros com 1 clique e geração de consultas em linguagem natural.
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

    // 1. Verificar Status do Ollama ao Iniciar
    checkOllamaStatus();
    setInterval(checkOllamaStatus, 30000); // Polling a cada 30s

    async function checkOllamaStatus() {
        try {
            const resp = await fetch('/api/ai/status');
            const data = await resp.json();
            if (data.online) {
                isAiOnline = true;
                if (aiStatusDot) {
                    aiStatusDot.className = 'ai-status-dot online';
                    aiStatusDot.title = `Ollama Online (${data.current_model})`;
                }
                if (aiStatusText) aiStatusText.textContent = data.current_model || 'Online';
                if (aiLatencyBadge) aiLatencyBadge.textContent = `${data.latency_ms}ms`;

                // Atualizar seletor de modelos
                if (aiModelSelect && data.models && data.models.length > 0) {
                    const currentVal = aiModelSelect.value;
                    aiModelSelect.innerHTML = '';
                    data.models.forEach(m => {
                        const opt = document.createElement('option');
                        opt.value = m;
                        opt.textContent = m;
                        if (m === data.current_model) opt.selected = true;
                        aiModelSelect.appendChild(opt);
                    });
                }
            } else {
                isAiOnline = false;
                if (aiStatusDot) {
                    aiStatusDot.className = 'ai-status-dot offline';
                    aiStatusDot.title = 'Ollama Offline';
                }
                if (aiStatusText) aiStatusText.textContent = 'Offline';
                if (aiLatencyBadge) aiLatencyBadge.textContent = 'Offline';
            }
        } catch (e) {
            isAiOnline = false;
            if (aiStatusDot) aiStatusDot.className = 'ai-status-dot offline';
            if (aiStatusText) aiStatusText.textContent = 'Offline';
        }
    }

    // 2. Abertura / Fechamento do Drawer
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

    function toggleAiDrawer(open) {
        if (!aiDrawer) return;
        if (open) {
            aiDrawer.classList.add('active');
            if (chatInput) chatInput.focus();
        } else {
            aiDrawer.classList.remove('active');
        }
    }

    // Atalho de Teclado (F2 ou Ctrl+Espaço abre o Mentor IA)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'F2' || (e.ctrlKey && e.code === 'Space')) {
            e.preventDefault();
            if (aiDrawer && aiDrawer.classList.contains('active')) {
                toggleAiDrawer(false);
            } else {
                toggleAiDrawer(true);
            }
        }
    });

    // 3. Troca de Abas do Mentor
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

    // 4. Mudança de Modelo Ativo
    if (aiModelSelect) {
        aiModelSelect.addEventListener('change', async () => {
            const selectedModel = aiModelSelect.value;
            try {
                const resp = await fetch('/api/ai/model', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model: selectedModel })
                });
                const res = await resp.json();
                if (res.success) {
                    appendSystemMessage(`Modelo do Mentor alterado para **${selectedModel}**.`);
                }
            } catch (e) {
                console.error(e);
            }
        });
    }

    // 5. Chat com o Mentor IA
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
                        <p>Estou conectado ao seu <strong>Ollama local</strong> e conheço toda a arquitetura de tabelas e regras de performance do Totvs Consinco.</p>
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
                appendChatMessage('assistant', data.response, data.extracted_sql, data.elapsed_seconds);
            } else {
                appendChatMessage('assistant', `⚠️ **Aviso:** ${data.error || 'Não foi possível obter resposta do Ollama.'}`);
            }
        } catch (err) {
            removeTypingIndicator(typingId);
            appendChatMessage('assistant', `❌ **Erro de Conexão:** Verifique se o serviço Ollama está rodando localmente.`);
        }
    }

    function appendChatMessage(role, text, extractedSql = null, elapsed = null) {
        if (!chatMessages) return;

        // Remover o card de boas-vindas se existir
        const welcome = chatMessages.querySelector('.ai-welcome-card');
        if (welcome) welcome.remove();

        const msgDiv = document.createElement('div');
        msgDiv.className = `ai-msg ${role}`;

        const avatar = role === 'user' ? '👤' : '🤖';
        const author = role === 'user' ? 'Você' : 'Mentor IA';
        const meta = elapsed ? `<span class="ai-meta">⏱️ ${elapsed}s</span>` : '';

        // Formatação simples de Markdown (negrito, código, listas)
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
        div.innerHTML = `<em>ℹ️ ${text}</em>`;
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
        div.innerHTML = `
            <div class="ai-msg-header">
                <span class="ai-msg-avatar">🤖</span>
                <span class="ai-msg-author" id="typing-author-text">Mentor IA está pensando localmente... (0s)</span>
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
                authorEl.textContent = `Mentor IA está processando localmente... (${seconds}s)`;
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

    // 6. Texto para SQL
    if (btnGenSql) {
        btnGenSql.addEventListener('click', async () => {
            const reqText = textSqlInput ? textSqlInput.value.trim() : '';
            if (!reqText) return;

            btnGenSql.disabled = true;
            btnGenSql.textContent = '⏳ Gerando SQL com IA...';
            if (textSqlOutput) textSqlOutput.innerHTML = '<div class="ai-loading-box">Consultando o modelo local...</div>';

            try {
                const resp = await fetch('/api/ai/text_to_sql', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ request: reqText })
                });
                const data = await resp.json();
                btnGenSql.disabled = false;
                btnGenSql.textContent = '🪄 Gerar SQL Consinco';

                if (data.success) {
                    const formattedExp = formatMarkdown(data.explanation);
                    textSqlOutput.innerHTML = `
                        <div class="ai-result-box">
                            <div class="ai-result-header">
                                <span>⚡ Consulta Gerada (${data.model || 'Ollama'})</span>
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
                    textSqlOutput.innerHTML = `<div class="ai-error-box">❌ ${data.error}</div>`;
                }
            } catch (e) {
                btnGenSql.disabled = false;
                btnGenSql.textContent = '🪄 Gerar SQL Consinco';
                if (textSqlOutput) textSqlOutput.innerHTML = `<div class="ai-error-box">❌ Erro ao conectar ao Ollama.</div>`;
            }
        });
    }

    // 7. Localizador de Tabelas
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
                    body: JSON.stringify({ query: query })
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
                if (findTableOutput) findTableOutput.innerHTML = `<div class="ai-error-box">❌ Erro na comunicação com Ollama.</div>`;
            }
        });
    }

    // 8. Função Global Exposta: Depuração de Erro com IA em 1 Clique
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
                appendChatMessage('assistant', data.explanation, data.fixed_sql, data.elapsed_seconds);
            } else {
                appendChatMessage('assistant', `⚠️ Não foi possível analisar o erro: ${data.error}`);
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

        // Feedback visual
        showToast('Consulta inserida no editor com sucesso!');
        toggleAiDrawer(false);
    }

    // Helper: Toast de Notificação
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
