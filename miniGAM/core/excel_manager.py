import os
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

class ExcelManager:
    """
    Gerenciador de dados do arquivo conferencia.xlsx.
    Seguindo as diretrizes da skill 'Carregar e Sanitizar Dados', realiza a leitura
    resiliente, sanitização de colunas e padronização de valores numéricos para
    garantir comparação exata com os dados capturados da tela Consinco.
    """
    def __init__(self, filepath: str = "conferencia.xlsx"):
        self.filepath = filepath
        self.df: Optional[pd.DataFrame] = None
        self.dados_sanitizados: List[Dict[str, Any]] = []
        self.validados: set = set()  # Conjunto de índices ou títulos já validados na execução atual

    @staticmethod
    def _parse_numeric_value(value: Any, default: float = 0.0) -> float:
        """
        Converte valores monetários/numéricos em float de forma resiliente.
        Trata formatos como '37,44', 'R$ 138,24', 37.44, '-8,25', etc.
        """
        if pd.isna(value):
            return default

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text or text.lower() in {'nan', 'none', ''}:
            return default

        # Remove símbolos monetários e espaços
        text = text.replace('R$', '').replace('r$', '').replace(' ', '').strip()
        negative = text.startswith('-')
        if negative:
            text = text[1:]

        # Identificação de separadores decimal e milhar
        if ',' in text and '.' in text:
            if text.rfind(',') > text.rfind('.'):
                text = text.replace('.', '').replace(',', '.')
            else:
                text = text.replace(',', '')
        elif ',' in text:
            text = text.replace(',', '.')
        elif text.count('.') > 1:
            integer_part, decimal_part = text.rsplit('.', 1)
            text = integer_part.replace('.', '') + '.' + decimal_part

        try:
            number = float(text)
            return -number if negative else number
        except ValueError:
            return default

    @staticmethod
    def normalize_titulo(titulo: Any) -> str:
        """
        Padroniza o campo 'Título' para comparação exata (remove espaços extras, maiúsculas).
        Ex: '9-700/1' -> '9-700/1'
            '  009-700 / 1 ' -> '9-700/1'
        """
        if pd.isna(titulo):
            return ""
        text = str(titulo).strip().upper()
        # Remove espaços extras em volta de barras ou traços
        text = text.replace(' / ', '/').replace('/ ', '/').replace(' /', '/')
        text = text.replace(' - ', '-').replace('- ', '-').replace(' -', '-')
        # Se começar com zeros à esquerda no número do título antes de traço/barra, podemos manter ou limpar
        # Mas mantendo string limpa para robustez
        return text

    def carregar_planilha(self, filepath: Optional[str] = None) -> Tuple[bool, str]:
        """
        Carrega a planilha Excel (ou CSV) e prepara a estrutura para consulta rápida.
        Retorna (sucesso, mensagem).
        """
        if filepath:
            self.filepath = filepath

        if not os.path.exists(self.filepath):
            # Tenta fallback para .csv ou .xlsx no mesmo diretório ou na pasta 'Dados/'
            dir_atual = os.path.dirname(self.filepath)
            base_nome = os.path.splitext(os.path.basename(self.filepath))[0]
            
            caminhos_alt = [
                os.path.join(dir_atual, base_nome + ".xlsx"),
                os.path.join(dir_atual, base_nome + ".csv"),
                os.path.join(dir_atual, "Dados", base_nome + ".xlsx"),
                os.path.join(dir_atual, "Dados", base_nome + ".csv")
            ]
            
            achou = False
            for c in caminhos_alt:
                if os.path.exists(c):
                    self.filepath = c
                    achou = True
                    break
                    
            if not achou:
                return False, f"Arquivo não encontrado: {self.filepath}"

        try:
            ext = os.path.splitext(self.filepath)[1].lower()
            if ext == '.csv':
                df = pd.read_csv(self.filepath, engine='python', dtype=str)
            else:
                df = pd.read_excel(self.filepath, engine='openpyxl', dtype=str)

            # Sanitização de colunas vazias / fantasmas
            df = df.dropna(how='all')
            df.columns = [str(col).strip() for col in df.columns]

            # Encontrar colunas 'Titulo' e 'Valor' de forma flexível (case insensitive)
            col_titulo = None
            col_valor = None

            for col in df.columns:
                col_lower = col.lower()
                if not col_titulo and ('titulo' in col_lower or 'título' in col_lower or 'nro' in col_lower or 'doc' in col_lower):
                    col_titulo = col
                if not col_valor and ('valor' in col_lower or 'vlr' in col_lower or 'aberto' in col_lower or 'saldo' in col_lower):
                    col_valor = col

            if not col_titulo or not col_valor:
                # Fallback: tentar por índice se tiver pelo menos 2 colunas
                if len(df.columns) >= 2:
                    if not col_titulo: col_titulo = df.columns[0]
                    if not col_valor: col_valor = df.columns[1]
                else:
                    return False, f"Não foi possível identificar colunas 'Titulo' e 'Valor' em {os.path.basename(self.filepath)}. Colunas encontradas: {list(df.columns)}"

            self.dados_sanitizados = []
            self.validados.clear()

            for idx, row in df.iterrows():
                t_raw = row.get(col_titulo, "")
                v_raw = row.get(col_valor, "")

                t_norm = self.normalize_titulo(t_raw)
                v_num = self._parse_numeric_value(v_raw)

                if t_norm:  # Apenas linhas com título preenchido
                    self.dados_sanitizados.append({
                        "id": idx,
                        "titulo_raw": str(t_raw).strip(),
                        "titulo_norm": t_norm,
                        "valor_raw": str(v_raw).strip(),
                        "valor_num": v_num,
                        "status": "pendente"
                    })

            self.df = df
            total = len(self.dados_sanitizados)
            return True, f"Planilha carregada com sucesso! {total} títulos encontrados na coluna '{col_titulo}' e '{col_valor}'."

        except Exception as e:
            return False, f"Erro ao ler arquivo {os.path.basename(self.filepath)}: {str(e)}"

    def verificar_titulo(self, titulo_tela: str, valor_tela: Any, tolerancia: float = 0.02) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Verifica se o título lido da tela existe na planilha e se o valor coincide.
        
        Args:
            titulo_tela: Texto lido na coluna Título do Consinco
            valor_tela: Texto ou float lido na coluna Valor em Aberto do Consinco
            tolerancia: Diferença de arredondamento aceitável (ex: R$ 0,02)
            
        Returns:
            (is_valid, item_dict, motivo_ou_status)
        """
        if not self.dados_sanitizados:
            return False, None, "Planilha não carregada."

        t_norm_tela = self.normalize_titulo(titulo_tela)
        v_num_tela = self._parse_numeric_value(valor_tela)

        if not t_norm_tela:
            return False, None, "Título lido da tela está vazio."

        # Procura pelo título na lista com correspondência exata
        candidatos = [item for item in self.dados_sanitizados if item["titulo_norm"] == t_norm_tela]

        if not candidatos:
            # Tentar busca parcial APENAS se os tamanhos forem muito próximos (evita que '336-700/1' dê match em '1336-700/1')
            candidatos_parciais = [
                item for item in self.dados_sanitizados 
                if (item["titulo_norm"] in t_norm_tela or t_norm_tela in item["titulo_norm"]) 
                and abs(len(item["titulo_norm"]) - len(t_norm_tela)) <= 1
            ]
            if not candidatos_parciais:
                return False, None, f"Título '{t_norm_tela}' não encontrado na planilha."
            candidatos = candidatos_parciais

        for item in candidatos:
            diferenca = abs(item["valor_num"] - v_num_tela)
            if diferenca <= tolerancia:
                # Match perfeito de título e valor!
                item["status"] = "validado"
                self.validados.add(item["id"])
                return True, item, f"OK: Título e Valor batem (Excel: R$ {item['valor_num']:.2f} | Tela: R$ {v_num_tela:.2f})"
            else:
                motivo = f"Divergência de valor para '{t_norm_tela}': Excel R$ {item['valor_num']:.2f} vs Tela R$ {v_num_tela:.2f}"
                return False, item, motivo

        return False, candidatos[0], f"Divergência no título ou valor para {t_norm_tela}."

    def get_resumo(self) -> Dict[str, Any]:
        """Retorna contadores de progresso e a soma financeira dos itens marcados."""
        total = len(self.dados_sanitizados)
        validados = len(self.validados)
        valor_somado = sum(
            item["valor_num"] for item in self.dados_sanitizados 
            if item["status"] == "validado" and isinstance(item.get("valor_num"), (int, float))
        )
        return {
            "total": total,
            "validados": validados,
            "pendentes": total - validados,
            "valor_somado": valor_somado
        }

    def salvar_resultados(self) -> Tuple[bool, str]:
        """
        Salva o status na coluna 'Marcado' com o texto 'ok' para todas as linhas
        que foram validadas e marcadas no Consinco.
        """
        if not hasattr(self, 'df') or self.df is None:
            return False, "Planilha original não está carregada na memória."

        try:
            # Cria a coluna 'Marcado' se ela ainda não existir
            if "Marcado" not in self.df.columns:
                self.df["Marcado"] = ""

            for item in self.dados_sanitizados:
                if item.get("status") == "validado" or item.get("id") in self.validados:
                    self.df.at[item["id"], "Marcado"] = "ok"

            ext = os.path.splitext(self.filepath)[1].lower()
            try:
                if ext == '.csv':
                    self.df.to_csv(self.filepath, sep=';', index=False, encoding='utf-8')
                else:
                    self.df.to_excel(self.filepath, index=False)
                return True, f"Planilha '{os.path.basename(self.filepath)}' atualizada: coluna 'Marcado' = 'ok'."
            except PermissionError:
                # Caso o arquivo original esteja aberto e travado pelo Microsoft Excel
                dir_atual = os.path.dirname(self.filepath)
                base_nome = os.path.splitext(os.path.basename(self.filepath))[0]
                caminho_alt = os.path.join(dir_atual, f"{base_nome}_conferido{ext}")
                if ext == '.csv':
                    self.df.to_csv(caminho_alt, sep=';', index=False, encoding='utf-8')
                else:
                    self.df.to_excel(caminho_alt, index=False)
                return True, f"Planilha salva em '{os.path.basename(caminho_alt)}' (o original estava aberto no Excel)."
        except Exception as e:
            return False, f"Erro ao salvar coluna 'Marcado' no Excel: {e}"
