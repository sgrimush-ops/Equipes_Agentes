/**
 * ZONA SQL - Gerenciador do Editor de Código SQL
 */

class SqlEditorManager {
    constructor(textareaId, lineNumbersId, cursorStatId, charStatId) {
        this.textarea = document.getElementById(textareaId);
        this.lineNumbers = document.getElementById(lineNumbersId);
        this.cursorStat = document.getElementById(cursorStatId);
        this.charStat = document.getElementById(charStatId);
        
        this.initEvents();
        this.updateLineNumbers();
        this.updateStats();
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

        // Suporte a tecla TAB (inserir 4 espaços) e atalho Ctrl+Enter
        this.textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = this.textarea.selectionStart;
                const end = this.textarea.selectionEnd;
                const value = this.textarea.value;
                this.textarea.value = value.substring(0, start) + '    ' + value.substring(end);
                this.textarea.selectionStart = this.textarea.selectionEnd = start + 4;
                this.updateLineNumbers();
                this.updateStats();
            } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('btn-run-query').click();
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
