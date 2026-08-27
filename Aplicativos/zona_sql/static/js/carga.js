/**
 * ZONA SQL - Módulo de Carga e Atualização de Tabelas (Pontos Extras / Pontas de Gôndola)
 */

class CargaTabelaManager {
    constructor(editorManager) {
        this.editor = editorManager;
        this.modal = document.getElementById('carga-modal');
        this.previewData = null;
        this.currentScripts = null;
        this.extractedRows = [];
        this.extractedColumns = [];

        this.initElements();
        this.initEvents();
        this.renderExtractQuery();
    }

    initElements() {
        this.textarea = document.getElementById('carga-raw-input');
        this.previewTableContainer = document.getElementById('carga-preview-table');
        this.previewStats = document.getElementById('carga-preview-stats');
        this.scriptCodeBlock = document.getElementById('carga-generated-sql');
        this.diffContainer = document.getElementById('carga-diff-container');
        this.monitorTraceContainer = document.getElementById('monitor-trace-results');
        
        // Elementos de Upload e Dropzone
        this.fileInput = document.getElementById('carga-file-input');
        this.dropzone = document.getElementById('carga-dropzone');
        this.fileBadge = document.getElementById('carga-file-badge');
        this.fileNameSpan = document.getElementById('carga-file-name');
        this.fileSizeSpan = document.getElementById('carga-file-size');
        this.btnRemoveFile = document.getElementById('btn-remove-file');
        this.btnUploadHeader = document.getElementById('btn-upload-file-header');
        
        // Elementos de Extração
        this.extractGridContainer = document.getElementById('extract-grid-container');
        this.extractCountBadge = document.getElementById('extract-count-badge');
        this.extractSqlPre = document.getElementById('extract-sql-code');
        this.extractPontoSelect = document.getElementById('extract-ponto-select');
        this.extractEmpSelect = document.getElementById('extract-emp-select');
        this.extractProdInput = document.getElementById('extract-prod-input');
    }

    initEvents() {
        // Abrir/Fechar Modal de Carga
        const btnOpen = document.getElementById('btn-open-carga-module');
        if (btnOpen) {
            btnOpen.addEventListener('click', () => this.openModal());
        }

        const btnClose = document.getElementById('btn-close-carga-modal');
        if (btnClose) {
            btnClose.addEventListener('click', () => this.closeModal());
        }

        // Navegação de Abas do Módulo de Carga
        document.querySelectorAll('.carga-tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetTab = e.currentTarget.getAttribute('data-ctab');
                document.querySelectorAll('.carga-tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.carga-tab-content').forEach(c => c.classList.remove('active'));

                e.currentTarget.classList.add('active');
                const targetContent = document.getElementById(targetTab);
                if (targetContent) targetContent.classList.add('active');

                if (targetTab === 'ctab-extract' && this.extractedRows.length === 0) {
                    this.runExtractQuery();
                } else if (targetTab === 'ctab-monitor') {
                    this.loadMonitorTrace();
                }
            });
        });

        // Eventos de Upload de Arquivo e Drag-and-Drop
        this.btnUploadHeader?.addEventListener('click', () => this.fileInput?.click());
        
        this.dropzone?.addEventListener('click', (e) => {
            if (e.target !== this.btnRemoveFile && !e.target.closest('#btn-remove-file')) {
                this.fileInput?.click();
            }
        });

        this.dropzone?.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropzone.classList.add('dragover');
        });

        this.dropzone?.addEventListener('dragleave', () => {
            this.dropzone?.classList.remove('dragover');
        });

        this.dropzone?.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropzone?.classList.remove('dragover');
            if (e.dataTransfer?.files?.length > 0) {
                this.handleFileSelect(e.dataTransfer.files[0]);
            }
        });

        this.fileInput?.addEventListener('change', (e) => {
            if (e.target?.files?.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });

        this.btnRemoveFile?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.clearFile();
        });

        // Eventos da Aba de Extração
        [this.extractPontoSelect, this.extractEmpSelect, this.extractProdInput].forEach(el => {
            el?.addEventListener('change', () => this.renderExtractQuery());
            el?.addEventListener('input', () => this.renderExtractQuery());
        });

        document.getElementById('btn-run-extract-query')?.addEventListener('click', () => {
            this.runExtractQuery();
        });

        document.getElementById('btn-copy-extract-query')?.addEventListener('click', () => {
            this.copyExtractQuery();
        });

        document.getElementById('btn-open-extract-editor')?.addEventListener('click', () => {
            this.openExtractInMainEditor();
        });

        document.getElementById('btn-download-txt')?.addEventListener('click', () => {
            this.downloadTxt();
        });

        document.getElementById('btn-download-csv')?.addEventListener('click', () => {
            this.downloadCsv();
        });

        document.getElementById('btn-copy-tsv')?.addEventListener('click', () => {
            this.copyTsv();
        });

        document.getElementById('btn-send-to-importer')?.addEventListener('click', () => {
            this.sendToImporter();
        });

        // Botões de Exemplo Rápido na Aba de Carga
        document.getElementById('btn-load-example-bebidas')?.addEventListener('click', () => {
            this.loadExampleBebidas();
        });

        document.getElementById('btn-load-example-checkout')?.addEventListener('click', () => {
            this.loadExampleCheckout();
        });

        document.getElementById('btn-clear-carga-input')?.addEventListener('click', () => {
            this.clearFile();
        });

        // Processar / Pré-Visualizar Dados
        document.getElementById('btn-process-carga')?.addEventListener('click', () => {
            this.processPreview();
        });

        // Alternância de Abas do Script Gerado (MERGE vs BATCH vs SELECT)
        document.querySelectorAll('.script-type-pill').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.currentTarget.getAttribute('data-script-type');
                document.querySelectorAll('.script-type-pill').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
                this.renderScriptType(type);
            });
        });

        // Ações sobre o SQL Gerado
        document.getElementById('btn-copy-generated-sql')?.addEventListener('click', () => {
            this.copyGeneratedSql();
        });

        document.getElementById('btn-open-in-editor')?.addEventListener('click', () => {
            this.openInMainEditor();
        });

        document.getElementById('btn-apply-carga-db')?.addEventListener('click', () => {
            this.applyCargaToDatabase();
        });

        document.getElementById('btn-reset-simulator-db')?.addEventListener('click', () => {
            this.resetDatabase();
        });

        // Controles do Simulador SQL Monitor
        document.getElementById('btn-refresh-monitor-trace')?.addEventListener('click', () => {
            this.loadMonitorTrace();
        });
    }

    openModal() {
        if (this.modal) {
            this.modal.classList.add('active');
            if (!this.textarea.value.trim()) {
                this.loadExampleBebidas();
            }
        }
    }

    closeModal() {
        if (this.modal) {
            this.modal.classList.remove('active');
        }
    }

    // =========================================================================
    // MÉTODOS DE EXTRAÇÃO E DOWNLOAD
    // =========================================================================

    getExtractQuerySql() {
        const ponto = parseInt(this.extractPontoSelect?.value) || 0;
        const emp = parseInt(this.extractEmpSelect?.value) || 0;
        const prod = parseInt(this.extractProdInput?.value) || 0;

        let whereClauses = ["PE.STATUS = 'A'"];
        if (ponto > 0) whereClauses.push(`PEPE.SEQPONTOEXTRA = ${ponto}`);
        if (emp > 0) whereClauses.push(`PEPE.NROEMPRESA = ${emp}`);
        if (prod > 0) whereClauses.push(`PEPE.SEQPRODUTO = ${prod}`);

        const whereSql = whereClauses.length > 0 ? `WHERE ${whereClauses.join('\n  AND ')}` : '';

        return `SELECT
    PEPE.SEQPONTOEXTRA,
    PE.DESCRICAO,
    PEPE.SEQPRODUTO,
    PROD.DESCCOMPLETA,
    PEPE.NROEMPRESA,
    PEPE.ESTQMINIMO,
    PEPE.ESTQMAXIMO,
    PEPE.DTAVIGENCIAINICIO,
    PEPE.DTAVIGENCIAFIM
FROM MRL_PONTOEXTRA PE
INNER JOIN MRL_PONTOEXTRAPRODUTO PEP
    ON PEP.SEQPONTOEXTRA = PE.SEQPONTOEXTRA
INNER JOIN MRL_PONTOEXTRAPRODUTOEMPRESA PEPE
    ON PEPE.SEQPONTOEXTRA = PEP.SEQPONTOEXTRA
   AND PEPE.SEQPRODUTO    = PEP.SEQPRODUTO
INNER JOIN MAP_PRODUTO PROD
    ON PROD.SEQPRODUTO    = PEPE.SEQPRODUTO
${whereSql}
ORDER BY PEPE.SEQPONTOEXTRA, PEPE.NROEMPRESA, PEPE.SEQPRODUTO`;
    }

    renderExtractQuery() {
        if (this.extractSqlPre) {
            this.extractSqlPre.textContent = this.getExtractQuerySql();
        }
    }

    copyExtractQuery() {
        const sql = this.getExtractQuerySql();
        navigator.clipboard.writeText(sql).then(() => {
            alert("Query de extração copiada para a área de transferência!");
        });
    }

    openExtractInMainEditor() {
        const sql = this.getExtractQuerySql();
        this.editor.setValue(sql);
        this.closeModal();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async runExtractQuery() {
        if (!this.extractGridContainer) return;

        this.extractGridContainer.innerHTML = '<div class="loading-spinner">🔍 Extraindo base atual de pontas do simulador...</div>';

        const sql = this.getExtractQuerySql();

        try {
            const resp = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql: sql, binds: {} })
            });

            const res = await resp.json();
            if (!res.success) {
                this.extractGridContainer.innerHTML = `<div class="log-entry log-error">Erro ao extrair: ${res.error}</div>`;
                return;
            }

            this.extractedColumns = res.columns || [];
            this.extractedRows = res.rows || [];

            if (this.extractCountBadge) {
                this.extractCountBadge.textContent = this.extractedRows.length;
            }

            this.renderExtractGrid(this.extractedColumns, this.extractedRows);

        } catch (err) {
            this.extractGridContainer.innerHTML = `<div class="log-entry log-error">Falha: ${err.message}</div>`;
        }
    }

    renderExtractGrid(columns, rows) {
        if (!this.extractGridContainer) return;

        if (!rows.length) {
            this.extractGridContainer.innerHTML = `
                <div class="empty-state">
                    <p>Nenhum registro encontrado para os filtros selecionados.</p>
                </div>
            `;
            return;
        }

        let html = `
            <table class="data-grid carga-grid">
                <thead>
                    <tr>
                        ${columns.map(c => `<th>${c}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
        `;

        rows.forEach(r => {
            html += '<tr>';
            r.forEach((val, idx) => {
                const colName = columns[idx];
                let formatted = val !== null ? val : '';
                
                if (colName === 'SEQPONTOEXTRA') {
                    formatted = `<span class="badge-ponto">${val}</span>`;
                } else if (colName === 'NROEMPRESA') {
                    formatted = `<span class="badge-store">${val}</span>`;
                } else if (colName === 'ESTQMINIMO' || colName === 'ESTQMAXIMO') {
                    formatted = `<strong>${val}</strong>`;
                } else if (colName === 'SITUACAO_VIGENCIA') {
                    const cls = val === 'VIGENTE' ? 'badge-insert' : 'badge-update';
                    formatted = `<span class="badge-action ${cls}">${val}</span>`;
                }
                
                html += `<td>${formatted}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        this.extractGridContainer.innerHTML = html;
    }

    downloadTxt() {
        if (!this.extractedRows.length) {
            alert("Por favor, execute a consulta primeiro para obter os dados.");
            return;
        }

        // Padrão Tab-Delimited TXT para Consinco / Excel
        let content = this.extractedColumns.join('\t') + '\r\n';
        this.extractedRows.forEach(row => {
            content += row.map(v => v !== null ? v : '').join('\t') + '\r\n';
        });

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pontas_gondola_extracao_${new Date().toISOString().slice(0,10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    downloadCsv() {
        if (!this.extractedRows.length) {
            alert("Por favor, execute a consulta primeiro para obter os dados.");
            return;
        }

        // CSV com Ponto-e-Vírgula e UTF-8 BOM para abrir direto no Excel no Brasil
        let content = '\uFEFF' + this.extractedColumns.join(';') + '\r\n';
        this.extractedRows.forEach(row => {
            content += row.map(v => {
                if (v === null) return '';
                const str = String(v);
                return str.includes(';') ? `"${str}"` : str;
            }).join(';') + '\r\n';
        });

        const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pontas_gondola_extracao_${new Date().toISOString().slice(0,10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    copyTsv() {
        if (!this.extractedRows.length) {
            alert("Nenhum dado para copiar.");
            return;
        }

        let content = this.extractedColumns.join('\t') + '\r\n';
        this.extractedRows.forEach(row => {
            content += row.map(v => v !== null ? v : '').join('\t') + '\r\n';
        });

        navigator.clipboard.writeText(content).then(() => {
            alert("Dados copiados em formato TSV! Abra o Excel e pressione Ctrl+V para colar.");
        });
    }

    sendToImporter() {
        if (!this.extractedRows.length) {
            alert("Nenhum dado extraído.");
            return;
        }

        // Envia as colunas essenciais para a aba do Importador:
        // SEQPRODUTO, NROEMPRESA, SEQPONTOEXTRA, ESTQMINIMO, ESTQMAXIMO, DTAVIGENCIAINICIO, DTAVIGENCIAFIM, QTDDIASSUGESTAO, STATUS
        const colMap = {};
        this.extractedColumns.forEach((c, idx) => {
            colMap[c.toUpperCase()] = idx;
        });

        let tsvLines = ["SEQPRODUTO\tNROEMPRESA\tSEQPONTOEXTRA\tESTQMINIMO\tESTQMAXIMO\tDTAVIGENCIAINICIO\tDTAVIGENCIAFIM\tQTDDIASSUGESTAO\tSTATUS"];
        
        this.extractedRows.forEach(r => {
            const seqprod = r[colMap['SEQPRODUTO']] || 0;
            const emp = r[colMap['NROEMPRESA']] || 0;
            const ponto = r[colMap['SEQPONTOEXTRA']] || 0;
            const min = r[colMap['ESTQMINIMO']] || 0;
            const max = r[colMap['ESTQMAXIMO']] || 0;
            const dtIni = r[colMap['DTAVIGENCIAINICIO']] || '2026-08-01';
            const dtFim = r[colMap['DTAVIGENCIAFIM']] || '2026-12-31';
            const sug = r[colMap['QTDDIASSUGESTAO']] || 0;
            const status = r[colMap['STATUS']] || 'A';

            tsvLines.push(`${seqprod}\t${emp}\t${ponto}\t${min}\t${max}\t${dtIni}\t${dtFim}\t${sug}\t${status}`);
        });

        if (this.textarea) {
            this.textarea.value = tsvLines.join('\n');
        }

        // Mudar para a aba de Carga (ctab-carga)
        document.querySelectorAll('.carga-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.carga-tab-content').forEach(c => c.classList.remove('active'));

        document.querySelector('[data-ctab="ctab-carga"]')?.classList.add('active');
        document.getElementById('ctab-carga')?.classList.add('active');

        // Disparar preview
        this.processPreview();
        alert("Dados extraídos transferidos com sucesso para a aba do Importador! Agora você pode simular a alteração dos valores.");
    }

    // =========================================================================
    // MÉTODOS DO IMPORTADOR & LABORATÓRIO DE CARGA
    // =========================================================================

    handleFileSelect(file) {
        if (!file) return;

        // Atualiza visualmente o badge do arquivo
        if (this.fileBadge && this.fileNameSpan && this.fileSizeSpan) {
            this.fileNameSpan.textContent = file.name;
            const sizeKb = (file.size / 1024).toFixed(1);
            this.fileSizeSpan.textContent = `(${sizeKb} KB)`;
            this.fileBadge.style.display = 'flex';
            const dropBody = this.dropzone?.querySelector('.dropzone-body');
            if (dropBody) dropBody.style.display = 'none';
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target.result;
            if (this.textarea) {
                this.textarea.value = text;
            }
            // Auto-valida e gera os scripts automaticamente sem precisar clicar em outro botão
            this.processPreview();
        };
        reader.readAsText(file);
    }

    clearFile() {
        if (this.fileInput) this.fileInput.value = '';
        if (this.fileBadge) this.fileBadge.style.display = 'none';
        const dropBody = this.dropzone?.querySelector('.dropzone-body');
        if (dropBody) dropBody.style.display = 'flex';
        if (this.textarea) this.textarea.value = '';
        this.clearPreview();
    }

    loadExampleBebidas() {
        const sample = `SEQPONTOEXTRA\tDESCRICAO\tSEQPRODUTO\tDESCCOMPLETA\tNROEMPRESA\tESTQMINIMO\tESTQMAXIMO\tDTAVIGENCIAINICIO\tDTAVIGENCIAFIM
101\t101 - LOJA 8 APYCE\t6725\tLAVA ROUPA OMO 7L LAVAGEM PERFEITA\t8\t100\t150\t2026-08-01\t2026-12-31
121\t121 - PONTAS FIXAS\t116\tCERV SKOL 1L\t11\t900\t1200\t2026-08-01\t2026-12-31
203\t203 - COCA\t10\tREFRIG COCA COLA PET 2L\t1\t150\t300\t2026-08-01\t2026-12-31
203\t203 - COCA\t10\tREFRIG COCA COLA PET 2L\t12\t500\t800\t2026-08-01\t2026-12-31`;

        if (this.textarea) {
            this.textarea.value = sample;
            this.processPreview();
        }
    }

    loadExampleCheckout() {
        const sample = `SEQPONTOEXTRA\tDESCRICAO\tSEQPRODUTO\tDESCCOMPLETA\tNROEMPRESA\tESTQMINIMO\tESTQMAXIMO\tDTAVIGENCIAINICIO\tDTAVIGENCIAFIM
121\t121 - PONTAS FIXAS\t144\tCERV AMSTEL LAGER LT 473ML\t11\t1800\t2800\t2026-08-01\t2026-12-31
121\t121 - PONTAS FIXAS\t193\tCERV PROVINCIA PILSEN PREM LT 473ML\t11\t1400\t1900\t2026-08-01\t2026-12-31`;

        if (this.textarea) {
            this.textarea.value = sample;
            this.processPreview();
        }
    }

    clearPreview() {
        if (this.previewTableContainer) {
            this.previewTableContainer.innerHTML = `
                <div class="empty-state">
                    <p>Cole uma planilha acima ou selecione um arquivo para <strong>Validar & Gerar Scripts SQL</strong>.</p>
                </div>
            `;
        }
        if (this.previewStats) this.previewStats.innerHTML = '';
        if (this.scriptCodeBlock) this.scriptCodeBlock.textContent = '-- O script SQL será gerado automaticamente aqui...';
        if (this.diffContainer) this.diffContainer.innerHTML = '';
    }

    async processPreview() {
        const raw = this.textarea.value.trim();
        if (!raw) {
            alert("Por favor, cole os dados da planilha antes de validar.");
            return;
        }

        const defaultPonto = parseInt(document.getElementById('carga-default-ponto')?.value) || 203;
        const defaultIni = document.getElementById('carga-default-ini')?.value || '2026-08-01';
        const defaultFim = document.getElementById('carga-default-fim')?.value || '2026-12-31';

        if (this.previewTableContainer) {
            this.previewTableContainer.innerHTML = '<div class="loading-spinner">🔍 Validando produtos e cruzando com o banco Consinco...</div>';
        }

        try {
            const resp = await fetch('/api/carga/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    raw_data: raw,
                    default_ponto: defaultPonto,
                    default_vigencia_ini: defaultIni,
                    default_vigencia_fim: defaultFim
                })
            });

            const data = await resp.json();
            if (!data.success) {
                this.previewTableContainer.innerHTML = `<div class="log-entry log-error">${data.error}</div>`;
                return;
            }

            this.previewData = data.parsed_rows;
            this.currentScripts = data.generated_scripts;

            this.renderPreviewTable(data.parsed_rows, data.summary);
            this.renderScriptType('merge');

        } catch (err) {
            this.previewTableContainer.innerHTML = `<div class="log-entry log-error">Erro ao processar dados: ${err.message}</div>`;
        }
    }

    renderPreviewTable(rows, summary) {
        if (!this.previewTableContainer) return;

        if (this.previewStats) {
            this.previewStats.innerHTML = `
                <div class="stat-pill-group">
                    <span class="stat-pill"><span class="badge-dot blue"></span> <strong>${summary.total_rows}</strong> Linhas</span>
                    <span class="stat-pill"><span class="badge-dot green"></span> <strong>${summary.total_valid}</strong> Válidas</span>
                    <span class="stat-pill"><span class="badge-dot yellow"></span> <strong>${summary.total_updates}</strong> Alterações (UPDATE)</span>
                    <span class="stat-pill"><span class="badge-dot cyan"></span> <strong>${summary.total_inserts}</strong> Inclusões (INSERT)</span>
                    ${summary.total_errors > 0 ? `<span class="stat-pill danger"><span class="badge-dot red"></span> <strong>${summary.total_errors}</strong> Erros</span>` : ''}
                </div>
            `;
        }

        let html = `
            <table class="data-grid carga-grid">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Ação</th>
                        <th>SeqProduto</th>
                        <th>Descrição do Produto</th>
                        <th>Loja</th>
                        <th>Ponto Extra</th>
                        <th>Estq Mínimo</th>
                        <th>Estq Máximo</th>
                        <th>Vigência Início</th>
                        <th>Vigência Fim</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        `;

        rows.forEach(r => {
            const actionBadge = r.action === 'UPDATE' 
                ? '<span class="badge-action badge-update">🟡 UPDATE</span>'
                : (r.action === 'INSERT' ? '<span class="badge-action badge-insert">🟢 INSERT</span>' : '<span class="badge-action badge-error">🔴 ERRO</span>');

            let minCol = `${r.estqminimo}`;
            let maxCol = `${r.estqmaximo}`;

            if (r.old_record) {
                if (r.old_record.estqminimo !== r.estqminimo) {
                    minCol = `<span class="diff-old">${r.old_record.estqminimo}</span> ➔ <span class="diff-new">${r.estqminimo}</span>`;
                }
                if (r.old_record.estqmaximo !== r.estqmaximo) {
                    maxCol = `<span class="diff-old">${r.old_record.estqmaximo}</span> ➔ <span class="diff-new">${r.estqmaximo}</span>`;
                }
            }

            html += `
                <tr class="${r.is_valid ? '' : 'row-error'}">
                    <td>${r.line_number}</td>
                    <td>${actionBadge}</td>
                    <td class="col-code">${r.seqproduto}</td>
                    <td class="col-desc">${r.desc_produto}</td>
                    <td><span class="badge-store">${r.nroempresa}</span> ${r.nome_empresa.split('-')[1] || r.nome_empresa}</td>
                    <td><span class="badge-ponto">${r.seqpontoextra}</span></td>
                    <td>${minCol}</td>
                    <td>${maxCol}</td>
                    <td>${r.dtavigenciainicio}</td>
                    <td>${r.dtavigenciafim}</td>
                    <td><span class="badge-status-val">${r.status}</span></td>
                </tr>
            `;

            if (!r.is_valid && r.errors && r.errors.length) {
                html += `
                    <tr class="row-error-msg">
                        <td colspan="11">⚠️ Erro: ${r.errors.join(' | ')}</td>
                    </tr>
                `;
            }
        });

        html += '</tbody></table>';
        this.previewTableContainer.innerHTML = html;
    }

    renderScriptType(type) {
        if (!this.currentScripts || !this.scriptCodeBlock) return;

        let code = '';
        if (type === 'merge') {
            code = this.currentScripts.merge_sql;
        } else if (type === 'batch') {
            code = this.currentScripts.batch_dml_sql;
        } else if (type === 'select') {
            code = this.currentScripts.select_check_sql;
        }

        this.scriptCodeBlock.textContent = code || '-- Nenhum script gerado.';
    }

    copyGeneratedSql() {
        if (!this.scriptCodeBlock || !this.scriptCodeBlock.textContent.trim()) {
            alert("Nenhum código para copiar.");
            return;
        }
        navigator.clipboard.writeText(this.scriptCodeBlock.textContent).then(() => {
            alert("Script SQL copiado com sucesso para a área de transferência!");
        });
    }

    openInMainEditor() {
        if (!this.scriptCodeBlock || !this.scriptCodeBlock.textContent.trim()) {
            alert("Nenhum código gerado.");
            return;
        }
        const sql = this.scriptCodeBlock.textContent;
        this.editor.setValue(sql);
        this.closeModal();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async applyCargaToDatabase() {
        if (!this.previewData || !this.previewData.length) {
            alert("Por favor, valide os dados primeiro antes de aplicar.");
            return;
        }

        const validRows = this.previewData.filter(r => r.is_valid);
        if (!validRows.length) {
            alert("Nenhuma linha válida para atualizar.");
            return;
        }

        const btnApply = document.getElementById('btn-apply-carga-db');
        if (btnApply) btnApply.disabled = true;

        try {
            const resp = await fetch('/api/carga/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rows: validRows })
            });

            const res = await resp.json();
            if (res.success) {
                this.renderDiffAuditoria(res);
                alert(`Sucesso! ${res.message}`);
                this.processPreview();
            } else {
                alert(`Erro ao aplicar carga: ${res.error}`);
            }
        } catch (err) {
            alert(`Falha de comunicação: ${err.message}`);
        } finally {
            if (btnApply) btnApply.disabled = false;
        }
    }

    renderDiffAuditoria(res) {
        if (!this.diffContainer) return;

        let html = `
            <div class="diff-header-box">
                <div class="diff-title">
                    <span>⚡ Auditoria de Atualização no Banco de Dados</span>
                    <span class="badge-success">${res.total_affected} Linhas Gravadas</span>
                </div>
                <p>Veja abaixo o comparativo exato dos valores antigos vs novos gravados no banco simulador:</p>
            </div>
            <table class="data-grid diff-grid-table">
                <thead>
                    <tr>
                        <th>Operação</th>
                        <th>Produto</th>
                        <th>Loja</th>
                        <th>Ponto Extra</th>
                        <th>Estoque Mínimo</th>
                        <th>Estoque Máximo</th>
                        <th>Vigência Início</th>
                        <th>Vigência Fim</th>
                    </tr>
                </thead>
                <tbody>
        `;

        res.diff_log.forEach(d => {
            const opBadge = d.action === 'UPDATE' ? '<span class="badge-action badge-update">ALTERADO</span>' : '<span class="badge-action badge-insert">INSERIDO</span>';
            const minDiff = d.old_min !== null && d.old_min !== d.new_min 
                ? `<span class="diff-old">${d.old_min}</span> ➔ <span class="diff-new">${d.new_min}</span>` 
                : `<span class="diff-same">${d.new_min}</span>`;
            const maxDiff = d.old_max !== null && d.old_max !== d.new_max 
                ? `<span class="diff-old">${d.old_max}</span> ➔ <span class="diff-new">${d.new_max}</span>` 
                : `<span class="diff-same">${d.new_max}</span>`;
            const iniDiff = d.old_ini && d.old_ini !== d.new_ini 
                ? `<span class="diff-old">${d.old_ini}</span> ➔ <span class="diff-new">${d.new_ini}</span>` 
                : `<span class="diff-same">${d.new_ini}</span>`;
            const fimDiff = d.old_fim && d.old_fim !== d.new_fim 
                ? `<span class="diff-old">${d.old_fim}</span> ➔ <span class="diff-new">${d.new_fim}</span>` 
                : `<span class="diff-same">${d.new_fim}</span>`;

            html += `
                <tr>
                    <td>${opBadge}</td>
                    <td><strong>${d.seqproduto}</strong> - ${d.desc_produto}</td>
                    <td><span class="badge-store">${d.nroempresa}</span> ${d.nome_empresa}</td>
                    <td><span class="badge-ponto">${d.seqpontoextra}</span></td>
                    <td>${minDiff}</td>
                    <td>${maxDiff}</td>
                    <td>${iniDiff}</td>
                    <td>${fimDiff}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        this.diffContainer.innerHTML = html;
    }

    async resetDatabase() {
        if (!confirm("Tem certeza que deseja restaurar as tabelas do simulador para o estado inicial padrão?")) {
            return;
        }

        try {
            const resp = await fetch('/api/carga/reset', { method: 'POST' });
            const res = await resp.json();
            if (res.success) {
                alert(res.message);
                this.processPreview();
                if (this.extractedRows.length > 0) {
                    this.runExtractQuery();
                }
            } else {
                alert(`Erro ao restaurar: ${res.error}`);
            }
        } catch (err) {
            alert(`Falha: ${err.message}`);
        }
    }

    async loadMonitorTrace() {
        if (!this.monitorTraceContainer) return;

        const ponto = document.getElementById('monitor-ponto-select')?.value || 203;
        const prod = document.getElementById('monitor-prod-input')?.value || 10;
        const emp = document.getElementById('monitor-emp-select')?.value || 12;

        this.monitorTraceContainer.innerHTML = '<div class="loading-spinner">🕵️ Capturando rastreamento do SQL Monitor Consinco...</div>';

        try {
            const resp = await fetch(`/api/carga/monitor_trace?ponto=${ponto}&produto=${prod}&empresa=${emp}`);
            const data = await resp.json();

            if (!data.success) {
                this.monitorTraceContainer.innerHTML = '<div class="log-entry log-error">Erro ao carregar log.</div>';
                return;
            }

            let html = `
                <div class="monitor-banner">
                    <div class="monitor-banner-title">
                        <span>📡 Monitor SQL Consinco - Rastreamento de Telas em Tempo Real</span>
                    </div>
                    <p>O ERP Totvs Consinco executa uma sequência precisa de consultas SQL nos bastidores ao abrir e carregar os Pontos Extras. Veja cada chamada detalhada abaixo:</p>
                </div>
            `;

            data.trace_blocks.forEach(b => {
                html += `
                    <div class="monitor-card">
                        <div class="monitor-card-header">
                            <div class="monitor-id-tag">${b.id}</div>
                            <div class="monitor-card-title">${b.title}</div>
                            <div class="monitor-time-tag">${b.timestamp}</div>
                        </div>
                        <div class="monitor-code-box">
                            <pre>${b.sql}</pre>
                        </div>
                        <div class="monitor-explanation">
                            💡 <strong>O que o ERP está fazendo aqui:</strong> ${b.explanation}
                        </div>
                    </div>
                `;
            });

            this.monitorTraceContainer.innerHTML = html;
        } catch (err) {
            this.monitorTraceContainer.innerHTML = `<div class="log-entry log-error">Erro ao obter trace: ${err.message}</div>`;
        }
    }
}

window.CargaTabelaManager = CargaTabelaManager;
