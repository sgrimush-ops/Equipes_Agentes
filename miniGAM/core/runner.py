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

    def executar(self, log_cb: Callable, status_cb: Callable, finish_cb: Callable, ask_cb: Callable = None, ask_divergencia_cb: Callable = None, update_consinco_cb: Callable = None, delay_seta: float = 0.85):
        """
        Executa a automação em uma thread separada.
        """
        if self.is_running:
            return
        self.is_running = True
        self.stop_event.clear()

        threading.Thread(
            target=self._executar_thread,
            args=(log_cb, status_cb, finish_cb, ask_cb, ask_divergencia_cb, update_consinco_cb, delay_seta),
            daemon=True
        ).start()

    def _executar_thread(self, log_cb: Callable[[str], None], status_cb: Callable[[str], None], finish_cb: Callable[[], None], ask_cb: Optional[Callable], ask_divergencia_cb: Optional[Callable], update_consinco_cb: Optional[Callable], delay_seta: float):
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
            x_total_esq = coords.get("x_total_esq")
            x_total_dir = coords.get("x_total_dir")
            y_total = coords.get("y_total")
            linhas_y = coords.get("linhas_y", [])

            has_titulo = (coords.get("x_titulo_esq") is not None and coords.get("x_titulo_dir") is not None)
            has_vlr_lateral = (coords.get("x_vlr_lateral") is not None)
            has_total_check = (x_total_esq is not None and x_total_dir is not None and y_total is not None)

            if not (has_titulo and has_vlr_lateral and x_checkbox and has_total_check) or len(linhas_y) != 12:
                log_cb("[ERRO] Coordenadas sem limites esquerdo/direito ou faltando Vlr Pagar Lateral. Por favor, execute o 'Mapear Checklist' novamente.")
                status_cb("Calibração incompleta (Recalibre com novo passo 2)")
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
                    t_lido, _ = self.screen_reader.ler_linha(coords, None, y_atual)
                    
                    # Leitura segura via Clipboard no campo Vlr Pagar/Rec
                    v_lido = self.screen_reader.ler_celula_clipboard(coords["x_vlr_lateral"], coords["y_vlr_lateral"], delay_copia=0.15)
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

                                # --- NOVO: LER TOTAL DO CONSINCO E VERIFICAR DIVERGÊNCIA ---
                                if has_total_check:
                                    time.sleep(0.3) # Espera a soma atualizar na tela do Consinco
                                    try:
                                        v_cons_str = self.screen_reader.ler_celula_ocr(
                                            x_total_esq, y_total,
                                            largura=(x_total_dir - x_total_esq),
                                            altura=24,
                                            left_override=x_total_esq,
                                            num_only=True
                                        )
                                        v_cons = self.excel_manager._parse_numeric_value(v_cons_str)
                                        if update_consinco_cb:
                                            update_consinco_cb(v_cons)

                                        if v_cons > 0 and abs(val_soma - v_cons) > 0.05:
                                            log_cb(f"⚠️ [DIVERGÊNCIA] Soma GAM: R$ {val_fmt} | Total Consinco lido: {v_cons_str}")
                                            if ask_divergencia_cb:
                                                continuar = ask_divergencia_cb(val_soma, v_cons)
                                                if not continuar:
                                                    self.stop_event.set()
                                                    log_cb("[PARADO] Execução interrompida por divergência de totais.")
                                                    status_cb("Interrompido por Divergência")
                                                    break
                                    except Exception as e_ocr_total:
                                        log_cb(f"[AVISO] Falha ao ler Total Pagar/Rec: {e_ocr_total}")

                            except Exception as e_click:
                                log_cb(f"[ERRO CLIQUE] Falha ao clicar no checkbox da linha {linha_visivel_idx+1}: {e_click}")
                        else:
                            # Restaura foco no grid clicando na célula de Título para poder usar a seta (pois o foco ficou no campo lateral)
                            x_t = coords.get("x_titulo_esq", coords.get("x_titulo", x_checkbox - 100))
                            self.mouse.position = (int(x_t), y_atual)
                            time.sleep(0.05)
                            self.mouse.click(Button.left, 1)
                            time.sleep(0.05)
                            log_cb(f"❌ [{fase}] Rodada {rodada} | Passo {step+1}: Título '{t_lido}' | R$ {v_lido} -> {motivo}")

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

