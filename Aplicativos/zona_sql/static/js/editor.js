/**
 * ZONA SQL - Gerenciador do Editor de Código SQL Consinco
 * Suporte a numeração de linhas, cálculo de estatísticas, atalhos de teclado,
 * limpeza rápida para nova digitação e autocomplete IntelliSense.
 */

class SqlEditorManager {
    constructor(textareaId, lineNumbersId, cursorStatId, charStatId) {
        this.textarea = document.getElementById(textareaId);
        this.lineNumbers = document.getElementById(lineNumbersId);
        this.cursorStat = document.getElementById(cursorStatId);
        this.charStat = document.getElementById(charStatId);
        this.autocomplete = null;
        
        this.initEvents();
        this.updateLineNumbers();
        this.updateStats();

        // Inicializar autocomplete se a classe estiver carregada
        if (window.SqlAutocompleteManager) {
            this.autocomplete = new window.SqlAutocompleteManager(this);
        }
    }

    initEvents() {
        // Atualizar linhas e stats na digitação
        this.textarea.addEventListener('input', () => {
            this.updateLineNumbers();
            this.updateStats();
        });

        // Sincronizar rolagem com números de linha
        this.textarea.addEventListener('scroll', () => {
            this.lineNumbers.scrollTop = this.textarea.scrollTop;
        });

        // Atualizar cursor ao clicar ou usar setas
        this.textarea.addEventListener('keyup', () => this.updateStats());
        this.textarea.addEventListener('click', () => this.updateStats());

        // Suporte a tecla TAB (inserir 4 espaços), atalho Ctrl+Enter e atalhos de limpeza
        this.textarea.addEventListener('keydown', (e) => {
            // Se o autocomplete estiver visível, deixar ele tratar Tab/Enter/Setas
            if (this.autocomplete && this.autocomplete.isVisible) {
                if (['ArrowDown', 'ArrowUp', 'Tab', 'Enter', 'Escape'].includes(e.key)) {
                    return;
                }
            }

            if (e.key === 'Tab' && !e.shiftKey && !e.ctrlKey) {
                e.preventDefault();
                const start = this.textarea.selectionStart;
                const end = this.textarea.selectionEnd;
                const value = this.textarea.value;
                this.textarea.value = value.substring(0, start) + '    ' + value.substring(end);
                this.textarea.selectionStart = this.textarea.selectionEnd = start + 4;
                this.updateLineNumbers();
                this.updateStats();
                this.textarea.dispatchEvent(new Event('input'));
            } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                const runBtn = document.getElementById('btn-run-query');
                if (runBtn) runBtn.click();
            } else if (e.altKey && (e.key === 'l' || e.key === 'L')) {
                // Atalho Alt + L para limpar editor
                e.preventDefault();
                this.clear();
            } else if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
                // Atalho Ctrl + K para limpar editor
                e.preventDefault();
                this.clear();
            }
        });
    }

    updateLineNumbers() {
        const lines = this.textarea.value.split('\n').length;
        let lineStr = '';
        for (let i = 1; i <= Math.max(lines, 1); i++) {
            lineStr += i + '<br>';
        }
        this.lineNumbers.innerHTML = lineStr;
    }

    updateStats() {
        const text = this.textarea.value;
        const selStart = this.textarea.selectionStart;
        
        // Calcular linha e coluna atual
        const textBefore = text.substring(0, selStart);
        const lines = textBefore.split('\n');
        const currentLine = lines.length;
        const currentCol = lines[lines.length - 1].length + 1;

        if (this.cursorStat) {
            this.cursorStat.textContent = `Linha ${currentLine}, Coluna ${currentCol}`;
        }
        if (this.charStat) {
            this.charStat.textContent = `${text.length} caracteres`;
        }
    }

    getValue() {
        return this.textarea.value;
    }

    setValue(val) {
        this.textarea.value = val;
        this.updateLineNumbers();
        this.updateStats();
        // Disparar evento de input para o linter
        this.textarea.dispatchEvent(new Event('input'));
    }

    clear() {
        this.textarea.value = '';
        this.updateLineNumbers();
        this.updateStats();
        this.textarea.dispatchEvent(new Event('input'));
        this.textarea.focus();
        
        if (window.showAppToast) {
            window.showAppToast('✨ Editor limpo para nova digitação!');
        }
    }

    focus() {
        this.textarea.focus();
    }

    insertTextAtCursor(text) {
        const start = this.textarea.selectionStart;
        const end = this.textarea.selectionEnd;
        const currentVal = this.textarea.value;
        this.textarea.value = currentVal.substring(0, start) + text + currentVal.substring(end);
        this.textarea.selectionStart = this.textarea.selectionEnd = start + text.length;
        this.textarea.focus();
        this.updateLineNumbers();
        this.updateStats();
        this.textarea.dispatchEvent(new Event('input'));
    }
}

window.SqlEditorManager = SqlEditorManager;
