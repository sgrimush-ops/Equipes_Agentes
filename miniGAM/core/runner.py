import os
import sys
import time
import json
import threading
import pyautogui
from pynput.mouse import Controller, Button
from typing import Callable, Optional
from core.excel_manager import ExcelManager
from core.screen_reader import ScreenReader
from core.calibrador_checklist import get_coords_filepath


class MiniGamRunner:
    """
    Motor de execução do Mini-GAM.
    Realiza a contagem regressiva de 5 segundos, consulta o grid do Consinco
    linha por linha (1 a 12 nos primeiros passos, depois fixo na linha 12 a cada
    seta para baixo) até que a informação da linha 12 pare de se renovar ou o
    usuário interrompa.
    """
    def __init__(self, excel_manager: ExcelManager, screen_reader: ScreenReader):
        self.excel_manager = excel_manager
        self.screen_reader = screen_reader
        self.stop_event = threading.Event()
        self.is_running = False
        self.mouse = Controller()

    def parar(self):
        """Sinaliza para interromper a execução do loop imediatamente."""
        self.stop_event.set()
        self.is_running = False

    @staticmethod
    def _atingiu_valor_total(valor_atual: float, valor_total_planilha: float, tolerancia: float = 0.02) -> bool:
        """Retorna True quando o somatório acumulado já alcançou o total esperado da planilha."""
        return valor_atual >= (valor_total_planilha - tolerancia)

    def executar(self, log_cb: Callable, status_cb: Callable, finish_cb: Callable, ask_cb: Callable = None, delay_seta: float = 0.85):
        """
        Executa a automação em uma thread separada.
        """
        if self.is_running:
            return
        self.is_running = True
        self.stop_event.clear()

        threading.Thread(
            target=self._executar_thread,
            args=(log_cb, status_cb, finish_cb, ask_cb, delay_seta),
            daemon=True
        ).start()

    def _executar_thread(self, log_cb: Callable[[str], None], status_cb: Callable[[str], None], finish_cb: Callable[[], None], ask_cb: Optional[Callable], delay_seta: float):
        try:
            # 1. Verificação de pré-requisitos
            if not self.excel_manager.df is not None:
                sucesso, msg = self.excel_manager.carregar_planilha()
                if not sucesso:
                    log_cb(f"[ERRO] {msg}")
                    status_cb("Erro ao carregar planilha")
                    self.is_running = False
                    finish_cb()
                    return

            coords_file = get_coords_filepath()
            if not os.path.exists(coords_file):
                log_cb("[ERRO] Arquivo de calibração não encontrado! Clique em 'Mapear Checklist' primeiro.")
                status_cb("Coordenadas ausentes")
                self.is_running = False
                finish_cb()
                return

            with open(coords_file, 'r', encoding='utf-8') as f:
                coords = json.load(f)

            x_titulo = coords.get("x_titulo")
            x_valor = coords.get("x_valor")
            x_checkbox = coords.get("x_checkbox")
            linhas_y = coords.get("linhas_y", [])

            has_titulo = (coords.get("x_titulo_esq") is not None and coords.get("x_titulo_dir") is not None)
            has_valor = (coords.get("x_valor_esq") is not None and coords.get("x_valor_dir") is not None)

            if not (has_titulo and has_valor and x_checkbox) or len(linhas_y) != 12:
                log_cb("[ERRO] Coordenadas sem limites esquerdo/direito da calibração de 2 cliques. Por favor, execute o 'Mapear Checklist' novamente.")
                status_cb("Calibração incompleta (Recalibre com 2 cliques)")
                self.is_running = False
                finish_cb()
                return

            if abs(linhas_y[11] - linhas_y[0]) < 80:
                log_cb(f"[ERRO CALIBRAÇÃO] A Linha 1 (Y={linhas_y[0]}) e Linha 12 (Y={linhas_y[11]}) estão muito próximas ({abs(linhas_y[11] - linhas_y[0])}px).")
                log_cb("[ERRO CALIBRAÇÃO] Clique em 'MAPEAR CHECKLIST' e clique na 1ª linha (topo da tabela) e na 12ª linha (fundo da tabela) corretamente!")
                status_cb("Erro na calibração (linhas próximas)")
                self.is_running = False
                finish_cb()
                return

            # 2. Contagem regressiva de 5 segundos
            log_cb("[INFO] ===================================================")
            log_cb("[INFO] INICIANDO MINI-GAM em 5 SEGUNDOS...")
            log_cb("[INFO] 👉 Posicione e ative o foco na tela Quitação de Título no Consinco agora!")
            for s in range(5, 0, -1):
                if self.stop_event.is_set():
                    log_cb("[PARADO] Execução cancelada pelo usuário durante contagem regressiva.")
                    status_cb("Cancelado")
                    self.is_running = False
                    finish_cb()
                    return
                status_cb(f"Aguardando {s}s para iniciar na tela...")
                log_cb(f"[CONTAGEM] {s} segundo(s)...")
                time.sleep(1.0)

            log_cb("[START] Contagem finalizada! Iniciando validação no grid Consinco.")
            status_cb("Em execução no Consinco...")

            step = 0
            ultimo_titulo = None
            ultimo_valor = None
            titulos_checados = 0
            titulos_marcados = 0
            itens_lidos_tela = {}  # {titulo_norm_ou_raw: valor_lido}
            valor_total_planilha = sum(
                item["valor_num"] for item in self.excel_manager.dados_sanitizados
                if isinstance(item.get("valor_num"), (int, float))
            )
            valor_total_planilha = round(valor_total_planilha, 2)
            log_cb(f"[INFO] Valor total da planilha: R$ {self.excel_manager.formatar_moeda_br(valor_total_planilha)}")

            # Loop de validação do grid em quatro passagens de checagem.
            # A primeira desce, a segunda sobe, a terceira desce, a quarta sobe.
            for rodada in range(1, 5):
                if self.stop_event.is_set():
                    break

                is_descendo = (rodada % 2 != 0)
                fase = f"FASE {(rodada+1)//2}-{(rodada-1)%2 + 1} ({'Descendo' if is_descendo else 'Subindo'})"
                log_cb(f"[INFO] Iniciando {fase} (rodada {rodada}/4)")
                step = 0
                historico_leituras = []

                while not self.stop_event.is_set():
                    if is_descendo:
                        tecla_scroll = 'down'
                        if step < 12:
                            linha_visivel_idx = step
                        else:
                            linha_visivel_idx = 11
                    else:
                        tecla_scroll = 'up'
                        if step < 12:
                            linha_visivel_idx = 11 - step
                        else:
                            linha_visivel_idx = 0

                    y_atual = int(linhas_y[linha_visivel_idx])
                    t_lido, v_lido = self.screen_reader.ler_linha(coords, x_valor, y_atual)
                    titulos_checados += 1

                    if t_lido and t_lido.strip() and len(t_lido.strip()) > 1:
                        itens_lidos_tela[t_lido.strip()] = v_lido.strip()

                    # Detecção inteligente de fim de grid usando histórico (resolve problema do cursor piscando)
                    historico_leituras.append((t_lido, v_lido))
                    if len(historico_leituras) > 6:
                        historico_leituras.pop(0)

                    if step >= 15:
                        repeticoes = historico_leituras.count((t_lido, v_lido))
                        # Se a mesma leitura se repetiu 4 vezes nas ultimas 6 leituras (mesmo com piscadas), chegamos ao fim
                        if repeticoes >= 4:
                            log_cb(f"[{fase} CONCLUÍDA] Fim da passagem atingido na extremidade da tabela.")
                            break

                    if not t_lido or t_lido.strip() == "":
                        log_cb(f"[AVISO] {fase} | Rodada {rodada} | Passo {step+1} (Linha {linha_visivel_idx+1} na tela): Campo Título lido vazio. Tentando avançar...")
                    else:
                        is_valid, item_data, motivo = self.excel_manager.verificar_titulo(t_lido, v_lido)

                        if is_valid:
                            titulos_marcados += 1
                            resumo_temp = self.excel_manager.get_resumo()
                            val_soma = resumo_temp.get("valor_somado", 0.0)
                            val_fmt = f"{val_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            v_item_fmt = self.excel_manager.formatar_moeda_br(item_data['valor_num'])
                            
                            if "FUZZY OK" in motivo:
                                log_cb(f"🎯 [{fase}] Rodada {rodada} | Passo {step+1}: {motivo} -> Box Marcado! [Soma Acumulada: R$ {val_fmt}]")
                            else:
                                log_cb(f"✅ [{fase}] Rodada {rodada} | Passo {step+1} (Linha {linha_visivel_idx+1}): Título '{t_lido}' | R$ {v_item_fmt} -> Box Marcado! [Soma Acumulada: R$ {val_fmt}]")
                            try:
                                self.mouse.position = (int(x_checkbox), y_atual)
                                time.sleep(0.05)
                                self.mouse.click(Button.left, 1)
                                time.sleep(0.15)
                                self.excel_manager.salvar_resultados()
                            except Exception as e_click:
                                log_cb(f"[ERRO CLIQUE] Falha ao clicar no checkbox da linha {linha_visivel_idx+1}: {e_click}")
                        else:
                            log_cb(f"⚠️ [{fase}] Rodada {rodada} | Passo {step+1} (Linha {linha_visivel_idx+1}): Título '{t_lido}' | Lida Tela R$ {v_lido} -> {motivo}")

                    if self.stop_event.is_set():
                        log_cb(f"[PARADO] Execução interrompida pelo usuário na {fase} da rodada {rodada}.")
                        status_cb("Interrompido")
                        break

                    pyautogui.press(tecla_scroll)
                    time.sleep(delay_seta)
                    step += 1

                    resumo = self.excel_manager.get_resumo()
                    val_soma = resumo.get("valor_somado", 0.0)
                    val_fmt = f"{val_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    status_cb(f"{fase} | Rodada {rodada}/4 | Marcados: {titulos_marcados}/{resumo['total']} | Soma: R$ {val_fmt} | Linha {linha_visivel_idx+1}")

                    if self._atingiu_valor_total(val_soma, valor_total_planilha):
                        log_cb(f"[INFO] Soma acumulada de R$ {val_fmt} atingiu o valor total da planilha ({self.excel_manager.formatar_moeda_br(valor_total_planilha)}). Encerrando a execução.")
                        break

                if self.stop_event.is_set() or self._atingiu_valor_total(self.excel_manager.get_resumo().get("valor_somado", 0.0), valor_total_planilha):
                    break

                if rodada < 4 and ask_cb and not self.stop_event.is_set():
                    if not self._atingiu_valor_total(self.excel_manager.get_resumo().get("valor_somado", 0.0), valor_total_planilha):
                        continuar = ask_cb(rodada)
                        if not continuar:
                            log_cb(f"[PARADO] Execução finalizada pelo usuário após a rodada {rodada}.")
                            break

            log_cb("[INFO] ===================================================")
            log_cb(f"[INFO] RESUMO FINAL GERAL: {titulos_checados} leituras na tela | {titulos_marcados} marcados com sucesso no Consinco.")
            
            sucesso_s, msg_s = self.excel_manager.salvar_resultados()
            if sucesso_s:
                log_cb(f"💾 [SALVO NO EXCEL] {msg_s}")
            else:
                log_cb(f"⚠️ [AVISO SALVAR] {msg_s}")

            msg_relatorio = self.excel_manager.gerar_relatorio_nao_encontrados(itens_lidos_tela)
            log_cb(f"📋 [RELATÓRIO DE LANÇAMENTOS NÃO ENCONTRADOS] {msg_relatorio}")

            if not self.stop_event.is_set():
                status_cb("Finalizado com sucesso (Fase 1 e Fase 2)")

        except Exception as e:
            log_cb(f"[ERRO FATAL] Ocorreu uma exceção inesperada durante a execução: {e}")
            status_cb("Erro durante execução")
            self.is_running = False
            finish_cb()

    def executar_auditoria(self, log_cb: Callable, status_cb: Callable, finish_cb: Callable, ask_audit_cb: Callable, delay_seta: float = 0.85):
        """Inicia o modo Auditoria em uma thread separada."""
        if self.is_running:
            return
        self.is_running = True
        self.stop_event.clear()
        
        threading.Thread(
            target=self._executar_auditoria_thread,
            args=(log_cb, status_cb, finish_cb, ask_audit_cb, delay_seta),
            daemon=True
        ).start()

    def _executar_auditoria_thread(self, log_cb: Callable, status_cb: Callable, finish_cb: Callable, ask_audit_cb: Callable, delay_seta: float):
        try:
            path_coords = get_coords_filepath()
            with open(path_coords, 'r', encoding='utf-8') as f:
                coords = json.load(f)
            
            linhas_y = coords.get("linhas_y", [])
            x_checkbox = coords.get("x_checkbox")
            if not linhas_y or not x_checkbox:
                log_cb("[ERRO] Coordenadas incompletas para auditoria.")
                return

            log_cb("[START] Modo Auditoria Iniciado! Contagem 5s...")
            for i in range(5, 0, -1):
                if self.stop_event.is_set(): return
                status_cb(f"Iniciando em {i}s...")
                time.sleep(1)

            log_cb("[INFO] Descendo o grid para auditoria...")
            status_cb("Auditando...")

            step = 0
            historico_leituras = []
            
            while not self.stop_event.is_set():
                if step < 12:
                    linha_visivel_idx = step
                else:
                    linha_visivel_idx = 11

                y_atual = int(linhas_y[linha_visivel_idx])
                
                # Lê título, valor e checkbox
                t_lido, v_lido = self.screen_reader.ler_linha(coords, y_linha=y_atual)
                is_marked = self.screen_reader.is_checkbox_marcado(int(x_checkbox), y_atual)
                
                if t_lido and t_lido.strip() and len(t_lido.strip()) > 1:
                    historico_leituras.append((t_lido, v_lido))
                    if len(historico_leituras) > 6:
                        historico_leituras.pop(0)

                if step >= 15 and historico_leituras.count((t_lido, v_lido)) >= 4:
                    log_cb("[INFO] Fim da tabela alcançado.")
                    break

                if is_marked and t_lido and t_lido.strip() != "":
                    # Verifica se o item deveria estar marcado
                    t_norm = self.excel_manager.normalize_titulo(t_lido)
                    v_num = self.excel_manager._parse_numeric_value(v_lido)
                    
                    item_correto = False
                    for item in self.excel_manager.dados_sanitizados:
                        if item["titulo_norm"] == t_norm and abs(item["valor_num"] - v_num) <= 0.02:
                            item_correto = True
                            break
                    
                    if not item_correto:
                        # Busca difusa (Fuzzy) em caso de pequenos erros de OCR
                        import difflib
                        candidatos_fuzzy = [
                            item for item in self.excel_manager.dados_sanitizados
                            if abs(item["valor_num"] - v_num) <= 0.02
                        ]
                        for item in candidatos_fuzzy:
                            if difflib.SequenceMatcher(None, t_norm, item["titulo_norm"]).ratio() >= 0.7:
                                item_correto = True
                                break

                    if not item_correto:
                        log_cb(f"⚠️ [ANOMALIA] Item '{t_lido}' (R$ {v_lido}) está MARCADO indevidamente!")
                        manter = ask_audit_cb(t_lido, v_lido)
                        if not manter:
                            log_cb(f"🔨 Desmarcando '{t_lido}'...")
                            self.mouse.position = (int(x_checkbox), y_atual)
                            time.sleep(0.05)
                            self.mouse.click(Button.left, 1)
                            time.sleep(0.15)
                        else:
                            log_cb(f"👍 Mantido marcado pelo usuário: '{t_lido}'")

                pyautogui.press('down')
                time.sleep(delay_seta)
                step += 1

            if not self.stop_event.is_set():
                status_cb("Auditoria Concluída")
                log_cb("✅ [INFO] Auditoria Concluída com sucesso!")
        except Exception as e:
            log_cb(f"[ERRO FATAL] Ocorreu uma exceção inesperada na auditoria: {e}")
            status_cb("Erro na auditoria")
        finally:
            self.is_running = False
            finish_cb()
