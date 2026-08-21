/**
 * ZONA SQL - Mentor de IA e Guardião de Regras Consinco em Tempo Real
 */

class ConsincoMentor {
    constructor(editorManager) {
        this.editor = editorManager;
        this.alertsContainer = document.getElementById('linter-alerts');
        this.explainContainer = document.getElementById('explain-container');
        this.debounceTimer = null;

        this.initEvents();
    }

    initEvents() {
        // Monitorar digitação no editor com debounce
        this.editor.textarea.addEventListener('input', () => {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.runLinter();
            }, 350);
        });

        // Botão Limpar SQL para Consinco
        document.getElementById('btn-clean-sql').addEventListener('click', () => {
            this.cleanSqlForConsinco();
        });

        // Botão Explicar Query
        document.getElementById('btn-explain-sql').addEventListener('click', () => {
            this.explainCurrentQuery();
        });
    }

    async runLinter() {
        const sql = this.editor.getValue().trim();
        if (!sql) {
            this.renderSuccessAlert("Pronto para digitar", "Comece a escrever sua query para receber validações do Consinco em tempo real.");
            return;
        }

        try {
            const resp = await fetch('/api/lint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql })
            });
            const data = await resp.json();
            this.renderAlerts(data.alerts || []);
        } catch (err) {
            console.error("Erro ao rodar linter:", err);
        }
    }

    renderAlerts(alerts) {
        if (!alerts || alerts.length === 0) {
            this.renderSuccessAlert("Tudo Certo!", "Nenhuma infração de regras do Consinco ou riscos de ORA-* detectados.");
            return;
        }

        let html = '';
        alerts.forEach((a, idx) => {
            const cardClass = a.type === 'danger' ? 'alert-danger' : (a.type === 'warning' ? 'alert-warning' : 'alert-info');
            const icon = a.type === 'danger' ? '⚠️' : (a.type === 'warning' ? '⚡' : 'ℹ️');

            html += `
                <div class="alert-card ${cardClass}">
                    <div class="alert-icon">${icon}</div>
                    <div class="alert-body">
                        <strong>${a.rule}</strong>
                        <p>${a.message}</p>
                        ${a.suggestion ? `<div class="alert-suggestion">💡 ${a.suggestion}</div>` : ''}
                    </div>
                </div>
            `;
        });

        this.alertsContainer.innerHTML = html;
    }

    renderSuccessAlert(title, message) {
        this.alertsContainer.innerHTML = `
            <div class="alert-card alert-success">
                <div class="alert-icon">✓</div>
                <div class="alert-body">
                    <strong>${title}</strong>
                    <p>${message}</p>
                </div>
            </div>
        `;
    }

    async cleanSqlForConsinco() {
        const sql = this.editor.getValue();
        if (!sql.trim()) return;

        try {
            const resp = await fetch('/api/clean_sql', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql })
            });
            const data = await resp.json();
            if (data.cleaned_sql) {
                this.editor.setValue(data.cleaned_sql);
                this.showToast("SQL limpo e pronto para colar no SGI Consinco!");
            }
        } catch (err) {
            console.error("Erro ao limpar SQL:", err);
        }
    }

    async explainCurrentQuery() {
        const sql = this.editor.getValue().trim();
        if (!sql) {
            alert("Digite uma consulta no editor primeiro.");
            return;
        }

        // Ativar aba do Mentor à direita
        document.querySelector('.sidebar-right [data-tab="tab-explain"]').click();
        this.explainContainer.innerHTML = '<div class="loading-spinner">✨ Analisando estrutura da consulta...</div>';

        try {
            const resp = await fetch('/api/explain', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql })
            });
            const data = await resp.json();
            this.renderExplanation(data.explanation);
        } catch (err) {
            this.explainContainer.innerHTML = `<div class="log-entry log-error">Erro ao analisar consulta: ${err.message}</div>`;
        }
    }

    renderExplanation(exp) {
        if (!exp) return;

        let html = '';

        // 1. Tabelas e Relacionamentos
        html += `
            <div class="explain-card">
                <h4>📁 Tabelas Envolvidas (${exp.tabelas.length})</h4>
                <ul class="explain-list">
                    ${exp.tabelas.map(t => `<li><strong>${t.tabela}:</strong> ${t.funcao}</li>`).join('')}
                </ul>
            </div>
        `;

        // 2. Agregações e Cálculos
        if (exp.agregacoes && exp.agregacoes.length > 0) {
            html += `
                <div class="explain-card">
                    <h4>🔢 Agregações e Cálculos</h4>
                    <ul class="explain-list">
                        ${exp.agregacoes.map(a => `<li>${a}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // 3. Filtros Ativos
        if (exp.filtros && exp.filtros.length > 0) {
            html += `
                <div class="explain-card">
                    <h4>🎯 Filtros e Regras de Negócio</h4>
                    <ul class="explain-list">
                        ${exp.filtros.map(f => `<li>${f}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // 4. Dica de Otimização e Performance
        html += `
            <div class="explain-card">
                <h4>💡 Diagnóstico de Arquitetura</h4>
                <p style="font-size: 0.76rem; color: #9ca3af; line-height: 1.4;">
                    ${exp.has_cte ? 'A consulta utiliza CTE (With), garantindo isolamento de lógicas repetitivas.' : 'Consulta direta padrão. Caso precise de múltiplos UNION ALL, isole os blocos pesados em CTEs com /*+ MATERIALIZE */.'}
                </p>
            </div>
        `;

        this.explainContainer.innerHTML = html;
    }

    showToast(msg) {
        const logContainer = document.getElementById('logs-container');
        if (logContainer) {
            const entry = document.createElement('div');
            entry.className = 'log-entry log-info';
            entry.textContent = `[MENTOR] ${msg}`;
            logContainer.appendChild(entry);
        }
    }
}

window.ConsincoMentor = ConsincoMentor;
