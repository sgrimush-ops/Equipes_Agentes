import pandas as pd
import pyautogui
import time
import sys
import json
import os

# Configuração de segurança
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

class OrderProcessorSupply:
    def __init__(self):
        self.coords = self.load_coordinates()

    def load_coordinates(self):
        if not os.path.exists('coords/coords.json'):
            return None
        with open('coords/coords.json', 'r') as f:
            return json.load(f)

    def run(self, update_callback=None, stop_event=None, pause_event=None, store_id=None):
        """
        Executa a automação para Supply lendo digitar.csv.
        """
        if not self.coords:
            if update_callback:
                update_callback({'error': "Arquivo 'coords/coords.json' não encontrado. Calibre primeiro."})
            else:
                print("Arquivo 'coords/coords.json' não encontrado. Calibre primeiro.")
            return

        pos_cd_abastecedor = self.coords.get('cd_abastecedor')
        pos_nova_linha = self.coords.get('nova_linha')
        
        if not pos_cd_abastecedor or not pos_nova_linha:
            msg = "As posições (CD abastecedor e nova_linha) não foram encontradas no 'coords/coords.json'. Calibre novamente!"
            if update_callback: update_callback({'error': msg})
            else: print(msg)
            return
        
        try:
            # Carregar dados
            df = pd.read_csv('bd_saida/digitar.csv', sep=';', encoding='utf-8-sig', dtype=str)
            
            col_codigo = 'CODIGO_CONSINCO'
            if 'CODIGO_CONSINCO' not in df.columns:
                msg = "Coluna 'CODIGO_CONSINCO' não encontrada na planilha 'digitar.csv'."
                if update_callback: update_callback({'error': msg})
                else: print(msg)
                return
            
            if 'descricao' not in df.columns:
                df['descricao'] = ''

            # Checks columns
            if 'CODIGO_EMPRESA' not in df.columns:
                msg = "Coluna 'CODIGO_EMPRESA' não encontrada na planilha 'digitar.csv'."
                if update_callback: update_callback({'error': msg})
                else: print(msg)
                return

            if 'Pedir' not in df.columns:
                msg = "Coluna 'Pedir' não encontrada na planilha 'digitar.csv'."
                if update_callback: update_callback({'error': msg})
                else: print(msg)
                return

            # Converter para numérico e filtrar o que será pedido > 0
            df['pedir_num'] = pd.to_numeric(df['Pedir'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            valid_rows = df[df['pedir_num'] > 0]
            total_items = len(valid_rows)

            if total_items == 0:
                msg = "Nenhum item com quantidade a pedir maior que zero encontrado."
                if update_callback: update_callback({'error': msg})
                else: print(msg)
                return

            if update_callback:
                update_callback({'status': 'Iniciando...', 'total': total_items})
            
            if not update_callback: 
                print("Iniciando em 5 segundos... Mude para o navegador/sistema!")
                time.sleep(5)
            else:
                time.sleep(2)
            
            if stop_event and stop_event.is_set(): return

            items_processed = 0
            unique_stores = valid_rows['CODIGO_EMPRESA'].unique()

            for current_store in unique_stores:
                if stop_event and stop_event.is_set(): return
                
                store_rows = valid_rows[valid_rows['CODIGO_EMPRESA'] == current_store]
                total_items_store = len(store_rows)

                str_store = str(current_store).replace('.0', '')
                if update_callback: update_callback({'status': f'Mapeando CD Abastecedor p/ Loja {str_store}'})
                
                # Usa pynput para sincronizar a escala exata da calibração e evitar desvio para Monitor 2
                from pynput.mouse import Controller, Button
                mouse_ctrl = Controller()

                # 1º Mapeamento - Sequência do CD Abastecedor
                mouse_ctrl.position = (pos_cd_abastecedor[0], pos_cd_abastecedor[1])
                time.sleep(0.1)
                mouse_ctrl.click(Button.left, 1)
                time.sleep(3.0)
                pyautogui.write('015')
                time.sleep(0.2)
                pyautogui.press('tab')
                time.sleep(0.2)
                pyautogui.press('enter') # exibe msg na tela que precisamos teclar enter
                time.sleep(0.5)
                
                # na sequencia precisamos de 6 tab, para chegar na empresa de faturamento; digitar nesse campo 015
                for _ in range(6): pyautogui.press('tab')
                time.sleep(0.2)
                pyautogui.write('015')
                time.sleep(0.2)
                
                # após mais 6 tab, selecionar o comprador padrão (SUPPLY)
                for _ in range(6): pyautogui.press('tab')
                time.sleep(0.5)
                
                # Verificação inteligente: se já for SUPPLY, não mexe
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.3)
                
                import pyperclip
                try:
                    c_comprador = pyperclip.paste().strip().upper()
                except:
                    c_comprador = ""

                if "SUPPLY" not in c_comprador:
                    # Campo restrito no ERP (não aceita digitação letra a letra). Usando paste seguro com intervalos ampliados.
                    import pyperclip
                    pyperclip.copy("SUPPLY")
                    time.sleep(0.2)
                    pyautogui.press('backspace')
                    time.sleep(0.1)
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(1.0) # Mais tempo para o ERP validar o colar antes do TAB
                    pyautogui.press('tab')
                else:
                    # Se já for SUPPLY, apenas um TAB para garantir o foco
                    pyautogui.press('tab')
                time.sleep(0.3)
                
                # agora teclar 4 tab para chegar em Tipo de pedido (ajustado pelo tab extra acima), 2 vezes "seta baixo"
                for _ in range(4): 
                    pyautogui.press('tab')
                    time.sleep(0.15) # Evita o bipe de saturação de teclado
                pyautogui.press('down', presses=2)
                time.sleep(0.2)

                if stop_event and stop_event.is_set(): return
                
                # 2º Mapeamento de click sera para criar uma nova linha
                mouse_ctrl.position = (pos_nova_linha[0], pos_nova_linha[1])
                time.sleep(0.1)
                mouse_ctrl.click(Button.left, 1)
                time.sleep(1.0)

                items_processed_store = 0

                # Iterar pelas linhas válidas DESTA LOJA
                for index, row in store_rows.iterrows():
                    if stop_event and stop_event.is_set():
                        if update_callback:
                            update_callback({'status': 'Parado pelo usuário.', 'finished': True})
                        return

                    # Verifica Pausa
                    if pause_event and pause_event.is_set():
                        if update_callback: update_callback({'status': 'PAUSADO'})
                        while pause_event.is_set():
                            if stop_event and stop_event.is_set(): return
                            time.sleep(0.5)
                        if update_callback: update_callback({'status': 'Processando'})

                    loja_id_raw = str(row.get('CODIGO_EMPRESA', '')).strip().replace('.0', '')
                    loja_id = loja_id_raw.zfill(3) if loja_id_raw.isdigit() else loja_id_raw
                    qtd_val = row['pedir_num']
                    # formatar para tentar remover decimais inúteis
                    if qtd_val.is_integer():
                        qtd = str(int(qtd_val))
                    else:
                        qtd = str(qtd_val).replace('.', ',')

                    codigo = str(row.get(col_codigo, '')).strip().replace('.0', '')
                    descricao = str(row.get('descricao', "Sem descrição")).strip()
                    
                    if not codigo or str(codigo).lower() == 'nan':
                        continue
                        
                    faltam = total_items - (items_processed + 1)
                    # Log de progresso
                    msg = f"Item {items_processed+1}/{total_items} (Faltam {faltam}): Loja {loja_id}, Cod {codigo}, Qtd {qtd} - {descricao}"
                    if update_callback:
                        update_callback({
                            'status': f'Processando Loja {loja_id}',
                            'current_index': items_processed + 1,
                            'total': total_items,
                            'code': codigo,
                            'qty': qtd,
                            'desc': descricao,
                            'log': msg
                        })
                    else:
                        print(msg)
                    
                    # Digitação na nova linha: abre para digitar o primeiro código
                    time.sleep(0.2)
                    pyautogui.write(codigo)
                    time.sleep(0.2)
                    
                    # após 2 TAB chegaremos no local para digitar a quantidade
                    pyautogui.press('tab', presses=2)
                    time.sleep(0.2)
                    pyautogui.write(qtd)
                    time.sleep(0.2)
                    
                    # após mais um tab vamos digitar o numero da loja de 3 dígitos
                    pyautogui.press('tab')
                    time.sleep(0.2)
                    
                    # Otimização de tempo: digitar o sufixo diretamente ao invés de usar as setas
                    pyautogui.write(f"{loja_id}-BAKLIZI")
                    time.sleep(0.2)
                    
                    if items_processed_store + 1 == total_items_store:
                        pyautogui.press('tab')
                    else:
                        pyautogui.press('enter')
                    
                    time.sleep(0.5)
                    
                    items_processed_store += 1
                    items_processed += 1
                
                # Ao finalizar a loja, teclar F3 para concluir
                time.sleep(1.0)
                pyautogui.press('f3')
                
                if update_callback: update_callback({'status': f'Aguardando 10 segundos (Loja {str_store})...'})
                for _ in range(10):
                    if stop_event and stop_event.is_set(): return
                    time.sleep(1)
                
                # ========= VERIFICAÇÃO FINAL APÓS SALVAR =========
                # Limpar clipboard com pyperclip (mais seguro que shell/subprocess)
                import pyperclip
                try:
                    pyperclip.copy("")
                except Exception:
                    pass
                
                # Clica na coordenada calibrada (com Pynput) para focar e fugir da armadilha de DPI de monitores distantes
                pos_comprador = self.coords.get("posicao_comprador")
                if not pos_comprador: pos_comprador = [1920, 767]
                
                mouse_ctrl.position = (pos_comprador[0], pos_comprador[1])
                time.sleep(0.2)
                mouse_ctrl.click(Button.left, 1)
                
                time.sleep(0.5)
                # Garante seleção total do combo e cópia
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.4)
                
                comprador_atual = ""
                try:
                    comprador_atual = pyperclip.paste().strip().upper()
                except Exception:
                    pass
                
                precisa_f4 = False
                if not comprador_atual:
                    pass # Se ler falhou, não faz ajuste as cegas
                elif "SUPPLY" in comprador_atual:
                    pass  # Tudo certo
                elif "WETER" in comprador_atual or "WERTER" in comprador_atual:
                    pyautogui.press('up')
                    precisa_f4 = True
                elif "SANDRO" in comprador_atual:
                    pyautogui.press('down')
                    precisa_f4 = True
                    
                if precisa_f4:
                    if update_callback: update_callback({'status': f'Salvando ajuste de comprador (F4)...'})
                    time.sleep(1.0)
                    pyautogui.press('f4')
                    time.sleep(2.0)
                # =================================================

                # Limpar a tela para a próxima loja
                pyautogui.press('f2')
                time.sleep(1.0)
                    
            pyautogui.press('f10')
            
            final_msg = "Todos pedidos digitados."
            if update_callback:
                update_callback({'status': 'Concluído', 'finished': True, 'log': final_msg})
            else:
                print(f"\n=== {final_msg} ===")
                pyautogui.alert(final_msg)

        except FileNotFoundError:
            err = "Arquivo 'bd_saida/digitar.csv' não encontrado."
            if update_callback: update_callback({'error': err})
            else: print(f"Erro: {err}")
        except Exception as e:
            err = f"Erro inesperado: {e}"
            if update_callback: update_callback({'error': err})
            else: print(err)

def main():
    processor = OrderProcessorSupply()
    
    print("=== Robô de Digitação Supply (Modo Automático) ===")
    if not processor.coords:
        print("Execute 'calibrar.py' primeiro.")
        return

    confirm = input("Digite 's' para iniciar ou 'n' para sair: ")
    if confirm.lower() != 's':
        return

    try:
        processor.run()
    finally:
        input("\nPressione Enter para fechar...")

if __name__ == "__main__":
    main()
