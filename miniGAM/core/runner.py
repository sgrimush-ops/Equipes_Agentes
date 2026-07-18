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

            # Loop de validação do grid (Fase 1 - Descendo com Seta Baixo)
            while not self.stop_event.is_set():
                if step < 12:
                    linha_visivel_idx = step
                else:
                    linha_visivel_idx = 11

                y_atual = int(linhas_y[linha_visivel_idx])
                t_lido, v_lido = self.screen_reader.ler_linha(coords, x_valor, y_atual)
                titulos_checados += 1

                if t_lido and t_lido.strip():
                    itens_lidos_tela[t_lido.strip()] = v_lido.strip()

                if step >= 12 and t_lido == ultimo_titulo and v_lido == ultimo_valor:
                    log_cb(f"[FASE 1 CONCLUÍDA] Fim da descida atingido na Linha 12 ('{t_lido}').")
                    break

                ultimo_titulo = t_lido
                ultimo_valor = v_lido

                if not t_lido or t_lido.strip() == "":
                    log_cb(f"[AVISO] Passo {step+1} (Linha {linha_visivel_idx+1} na tela): Campo Título lido vazio. Tentando avançar...")
                else:
                    is_valid, item_data, motivo = self.excel_manager.verificar_titulo(t_lido, v_lido)

                    if is_valid:
                        titulos_marcados += 1
                        resumo_temp = self.excel_manager.get_resumo()
                        val_soma = resumo_temp.get("valor_somado", 0.0)
                        val_fmt = f"{val_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        v_item_fmt = self.excel_manager.formatar_moeda_br(item_data['valor_num'])
                        log_cb(f"✅ [VALIDADO] Passo {step+1} (Linha {linha_visivel_idx+1}): Título '{t_lido}' | R$ {v_item_fmt} -> Box Marcado! [Soma Acumulada: R$ {val_fmt}]")
                        try:
                            self.mouse.position = (int(x_checkbox), y_atual)
                            time.sleep(0.05)
                            self.mouse.click(Button.left, 1)
                            time.sleep(0.15)
                            self.excel_manager.salvar_resultados()
                        except Exception as e_click:
                            log_cb(f"[ERRO CLIQUE] Falha ao clicar no checkbox da linha {linha_visivel_idx+1}: {e_click}")
                    else:
                        log_cb(f"⚠️ [PULADO] Passo {step+1} (Linha {linha_visivel_idx+1}): Título '{t_lido}' | Lida Tela R$ {v_lido} -> {motivo}")

                if self.stop_event.is_set():
                    log_cb("[PARADO] Execução interrompida pelo usuário via botão PARAR na Fase 1.")
                    status_cb("Interrompido")
                    break

                pyautogui.press('down')
                time.sleep(delay_seta)
                step += 1

                resumo = self.excel_manager.get_resumo()
                val_soma = resumo.get("valor_somado", 0.0)
                val_fmt = f"{val_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                status_cb(f"Fase 1 (Down) | Marcados: {titulos_marcados}/{resumo['total']} | Soma: R$ {val_fmt} | Linha {linha_visivel_idx+1}")

            # =========================================================================
            # FASE 2: Repassagem Subindo com Seta para Cima (UP)
            # Revisa os itens no retorno para recuperar perdas por piscada ou travamento
            # =========================================================================
            if not self.stop_event.is_set():
                log_cb("[FASE 2 INICIADA] 🔝 Retornando ao topo com Seta para Cima (UP) para re-checar títulos perdidos...")
                status_cb("Fase 2 (UP): Retornando e re-checando...")

                step_up = 0
                ultimo_titulo_up = None
                ultimo_valor_up = None

                while not self.stop_event.is_set():
                    if step_up < 11:
                        linha_visivel_idx = 11 - step_up
                    else:
                        linha_visivel_idx = 0

                    y_atual = int(linhas_y[linha_visivel_idx])
                    t_lido, v_lido = self.screen_reader.ler_linha(coords, x_valor, y_atual)
                    titulos_checados += 1

                    if t_lido and t_lido.strip():
                        itens_lidos_tela[t_lido.strip()] = v_lido.strip()

                    # Só consideramos o topo do sistema (Registro 1) quando já pressionamos UP na Linha 1 (step_up >= 12)
                    # e a informação na Linha 1 não mudou (a tabela parou de rolar para cima)
                    if step_up >= 12 and t_lido == ultimo_titulo_up and v_lido == ultimo_valor_up:
                        log_cb(f"[FASE 2 CONCLUÍDA] A informação na Linha 1 parou de rolar para cima ('{t_lido}'). Topo (Registro 1 do sistema) atingido!")
                        break

                    ultimo_titulo_up = t_lido
                    ultimo_valor_up = v_lido

                    if t_lido and t_lido.strip() != "":
                        is_valid, item_data, motivo = self.excel_manager.verificar_titulo(t_lido, v_lido)

                        if is_valid:
                            titulos_marcados += 1
                            resumo_temp = self.excel_manager.get_resumo()
                            val_soma = resumo_temp.get("valor_somado", 0.0)
                            val_fmt = f"{val_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            v_item_fmt = self.excel_manager.formatar_moeda_br(item_data['valor_num'])
                            log_cb(f"🔥 [RECUPERADO NA FASE 2] Título '{t_lido}' | R$ {v_item_fmt} -> Box Marcado! [Soma Acumulada: R$ {val_fmt}]")
                            try:
                                self.mouse.position = (int(x_checkbox), y_atual)
                                time.sleep(0.05)
                                self.mouse.click(Button.left, 1)
                                time.sleep(0.15)
                                self.excel_manager.salvar_resultados()
                            except Exception as e_click:
                                log_cb(f"[ERRO CLIQUE] Falha ao clicar no checkbox da linha {linha_visivel_idx+1}: {e_click}")
                        elif "Já validado anteriormente" in motivo:
                            # Ignora silenciosamente no log itens que já haviam sido marcados com sucesso
                            pass
                        else:
                            # Registra apenas se for uma pendência divergente ainda não resolvida
                            log_cb(f"🔍 [FASE 2 - PENDENTE] Título '{t_lido}' | Lida Tela R$ {v_lido} -> {motivo}")

                    if self.stop_event.is_set():
                        log_cb("[PARADO] Execução interrompida pelo usuário via botão PARAR na Fase 2.")
                        status_cb("Interrompido")
                        break

                    pyautogui.press('up')
                    time.sleep(delay_seta)
                    step_up += 1

                resumo = self.excel_manager.get_resumo()
                val_soma = resumo.get("valor_somado", 0.0)
                val_fmt = f"{val_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                status_cb(f"Fase 2 Concluída | Marcados: {titulos_marcados}/{resumo['total']} | Soma: R$ {val_fmt}")

            log_cb("[INFO] ===================================================")
            log_cb(f"[INFO] RESUMO FINAL GERAL: {titulos_checados} leituras na tela | {titulos_marcados} marcados com sucesso no Consinco.")
            
            # Garante o salvamento final na planilha principal
            sucesso_s, msg_s = self.excel_manager.salvar_resultados()
            if sucesso_s:
                log_cb(f"💾 [SALVO NO EXCEL] {msg_s}")
            else:
                log_cb(f"⚠️ [AVISO SALVAR] {msg_s}")

            # Gera a planilha de relatorio com itens lidos na tela que não existem no Excel
            msg_relatorio = self.excel_manager.gerar_relatorio_nao_encontrados(itens_lidos_tela)
            log_cb(f"📋 [RELATÓRIO DE LANÇAMENTOS NÃO ENCONTRADOS] {msg_relatorio}")

            if not self.stop_event.is_set():
                status_cb("Finalizado com sucesso (Fase 1 e Fase 2)")

        except Exception as e:
            log_cb(f"[ERRO FATAL] Ocorreu uma exceção inesperada durante a execução: {e}")
            status_cb("Erro durante execução")
        finally:
            self.is_running = False
            finish_cb()
