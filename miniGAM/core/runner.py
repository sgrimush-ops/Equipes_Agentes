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

    def executar(self, log_cb: Callable[[str], None], status_cb: Callable[[str], None], finish_cb: Callable[[], None], delay_seta: float = 0.45):
        """
        Executa a automação em uma thread separada.
        """
        self.stop_event.clear()
        self.is_running = True

        threading.Thread(
            target=self._executar_thread,
            args=(log_cb, status_cb, finish_cb, delay_seta),
            daemon=True
        ).start()

    def _executar_thread(self, log_cb: Callable[[str], None], status_cb: Callable[[str], None], finish_cb: Callable[[], None], delay_seta: float):
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

            if not all([x_titulo, x_valor, x_checkbox]) or len(linhas_y) != 12:
                log_cb("[ERRO] Coordenadas incompletas. Por favor, execute o 'Mapear Checklist' novamente.")
                status_cb("Calibração incompleta")
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

            # Loop de validação do grid
            while not self.stop_event.is_set():
                # Determina em qual das 12 linhas visíveis estamos atuando
                if step < 12:
                    linha_visivel_idx = step  # de 0 a 11 (Linha 1 a Linha 12 na tela)
                else:
                    # Após clicar 11 setas para baixo (chegar no step 11 que é a linha 12),
                    # a partir do step 12 todas as novas verificações acontecem na linha 12 (índice 11)
                    linha_visivel_idx = 11

                y_atual = int(linhas_y[linha_visivel_idx])

                # Leitura da linha (Título e Valor em Aberto)
                t_lido, v_lido = self.screen_reader.ler_linha(x_titulo, x_valor, y_atual)
                titulos_checados += 1

                # Se já passamos das 12 linhas e a informação lida for idéntica à última lida na linha 12,
                # significa que a tabela não rolou mais (fim da lista/tabela)
                if step >= 12 and t_lido == ultimo_titulo and v_lido == ultimo_valor:
                    log_cb(f"[CONCLUÍDO] A informação na linha 12 parou de se renovar ('{t_lido}'). Fim da consulta da tabela atingido!")
                    status_cb("Consulta finalizada (fim da tabela)")
                    break

                ultimo_titulo = t_lido
                ultimo_valor = v_lido

                if not t_lido or t_lido.strip() == "":
                    log_cb(f"[AVISO] Passo {step+1} (Linha {linha_visivel_idx+1} na tela): Campo Título lido vazio. Tentando avançar...")
                else:
                    # Validação com a tabela Excel
                    is_valid, item_data, motivo = self.excel_manager.verificar_titulo(t_lido, v_lido)

                    if is_valid:
                        titulos_marcados += 1
                        resumo_temp = self.excel_manager.get_resumo()
                        val_soma = resumo_temp.get("valor_somado", 0.0)
                        val_fmt = f"{val_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        log_cb(f"✅ [VALIDADO] Passo {step+1} (Linha {linha_visivel_idx+1}): Título '{t_lido}' | R$ {item_data['valor_num']:.2f} -> Box Marcado! [Soma Acumulada: R$ {val_fmt}]")
                        # Clica no checkbox correspondente na coordenada (x_checkbox, y_atual)
                        try:
                            self.mouse.position = (int(x_checkbox), y_atual)
                            time.sleep(0.05)
                            self.mouse.click(Button.left, 1)
                            time.sleep(0.15)
                            # Salva progressivamente a marcação no Excel
                            self.excel_manager.salvar_resultados()
                        except Exception as e_click:
                            log_cb(f"[ERRO CLIQUE] Falha ao clicar no checkbox da linha {linha_visivel_idx+1}: {e_click}")
                    else:
                        log_cb(f"⚠️ [PULADO] Passo {step+1} (Linha {linha_visivel_idx+1}): Título '{t_lido}' | Lida Tela R$ {v_lido} -> {motivo}")

                if self.stop_event.is_set():
                    log_cb("[PARADO] Execução interrompida pelo usuário via botão PARAR.")
                    status_cb("Interrompido")
                    break

                # Pressiona Seta para Baixo para ir para o próximo item
                pyautogui.press('down')
                time.sleep(delay_seta)
                step += 1

                # Atualiza progresso na barra / status
                resumo = self.excel_manager.get_resumo()
                val_soma = resumo.get("valor_somado", 0.0)
                val_fmt = f"{val_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                status_cb(f"Passo {step} | Marcados: {titulos_marcados}/{resumo['total']} | Soma: R$ {val_fmt} | Tela Linha {linha_visivel_idx+1}")

            log_cb("[INFO] ===================================================")
            log_cb(f"[INFO] RESUMO FINAL: {titulos_checados} itens inspecionados na tela | {titulos_marcados} marcados com sucesso no Consinco.")
            
            # Garante o salvamento final e informa no log
            sucesso_s, msg_s = self.excel_manager.salvar_resultados()
            if sucesso_s:
                log_cb(f"💾 [SALVO NO EXCEL] {msg_s}")
            else:
                log_cb(f"⚠️ [AVISO SALVAR] {msg_s}")

            if not self.stop_event.is_set():
                status_cb("Finalizado com sucesso")

        except Exception as e:
            log_cb(f"[ERRO FATAL] Ocorreu uma exceção inesperada durante a execução: {e}")
            status_cb("Erro durante execução")
        finally:
            self.is_running = False
            finish_cb()
