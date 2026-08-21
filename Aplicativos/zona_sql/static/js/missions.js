/**
 * ZONA SQL - Gerenciador de Missões e Desafios Práticos Consinco
 */

class MissionsManager {
    constructor(editorManager) {
        this.editor = editorManager;
        this.container = document.getElementById('missions-list');
        this.missions = [];

        this.loadMissions();
    }

    async loadMissions() {
        try {
            const resp = await fetch('/api/missions');
            const data = await resp.json();
            this.missions = data.missions || [];
            this.renderMissions();
        } catch (err) {
            console.error("Erro ao carregar missões:", err);
            this.container.innerHTML = '<div class="log-entry log-error">Erro ao carregar desafios.</div>';
        }
    }

    renderMissions() {
        if (!this.missions.length) {
            this.container.innerHTML = '<p class="text-muted">Nenhum desafio encontrado.</p>';
            return;
        }

        let html = '';
        this.missions.forEach((m) => {
            const diffClass = m.difficulty.toLowerCase() === 'iniciante' ? 'diff-iniciante' : (m.difficulty.toLowerCase() === 'intermediario' ? 'diff-intermediario' : 'diff-avancado');

            html += `
                <div class="mission-card" id="mission-card-${m.id}">
                    <div class="mission-badge-row">
                        <span class="mission-difficulty ${diffClass}">${m.difficulty}</span>
                        <span class="tbl-count-badge">${m.category}</span>
                    </div>
                    <div class="mission-title">${m.title}</div>
                    <div class="mission-desc">${m.description}</div>
                    <div class="alert-suggestion" style="margin-bottom: 8px;">💡 Dica: ${m.hint}</div>
                    <div class="mission-buttons">
                        <button class="btn btn-outline btn-load-mission" data-id="${m.id}" style="padding: 4px 8px; font-size: 0.72rem;">
                            📥 Carregar Exemplo
                        </button>
                        <button class="btn btn-primary btn-verify-mission" data-id="${m.id}" style="padding: 4px 8px; font-size: 0.72rem;">
                            ✓ Verificar Minha Query
                        </button>
                    </div>
                    <div class="mission-feedback" id="feedback-mission-${m.id}" style="margin-top: 6px; display: none;"></div>
                </div>
            `;
        });

        this.container.innerHTML = html;
        this.initCardEvents();
    }

    initCardEvents() {
        // Carregar exemplo no editor
        this.container.querySelectorAll('.btn-load-mission').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = parseInt(e.currentTarget.getAttribute('data-id'));
                const mission = this.missions.find(m => m.id === id);
                if (mission && mission.starter_sql) {
                    this.editor.setValue(mission.starter_sql);
                    // Rolar para topo do editor
                    this.editor.textarea.focus();
                }
            });
        });

        // Verificar query do usuário
        this.container.querySelectorAll('.btn-verify-mission').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = parseInt(e.currentTarget.getAttribute('data-id'));
                const fbDiv = document.getElementById(`feedback-mission-${id}`);
                const currentSql = this.editor.getValue();

                fbDiv.style.display = 'block';
                fbDiv.innerHTML = '<span style="color: #93c5fd; font-size: 0.75rem;">⏳ Testando consulta...</span>';

                try {
                    const resp = await fetch('/api/mission/verify', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mission_id: id, sql: currentSql })
                    });
                    const res = await resp.json();

                    if (res.passed) {
                        fbDiv.innerHTML = `
                            <div class="alert-card alert-success" style="padding: 6px 8px; font-size: 0.74rem;">
                                <div class="alert-icon">🎉</div>
                                <div class="alert-body">
                                    <strong>Missão Concluída!</strong>
                                    <p>${res.message}</p>
                                </div>
                            </div>
                        `;
                    } else {
                        fbDiv.innerHTML = `
                            <div class="alert-card alert-warning" style="padding: 6px 8px; font-size: 0.74rem;">
                                <div class="alert-icon">⚠️</div>
                                <div class="alert-body">
                                    <strong>Quase lá!</strong>
                                    <p>${res.message}</p>
                                </div>
                            </div>
                        `;
                    }
                } catch (err) {
                    fbDiv.innerHTML = `<span style="color: #f87171; font-size: 0.75rem;">Erro ao verificar: ${err.message}</span>`;
                }
            });
        });
    }
}

window.MissionsManager = MissionsManager;
