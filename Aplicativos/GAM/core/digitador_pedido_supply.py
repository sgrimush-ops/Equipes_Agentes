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
                
                # 1º Mapeamento - Sequência do CD Abastecedor
                pyautogui.click(pos_cd_abastecedor)
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
                
                # após mais 6 tab, selecionar o comprador "SUPPLY"
                for _ in range(6): pyautogui.press('tab')
                time.sleep(0.2)
                pyautogui.write('S')
                time.sleep(1.0)
                pyautogui.press('down')
                time.sleep(0.1)
                
                # agora teclar 5 tab para chegar em Tipo de pedido, 2 vezes "seta baixo"
                for _ in range(5): pyautogui.press('tab')
                time.sleep(0.2)
                pyautogui.press('down', presses=2)
                time.sleep(0.2)

                if stop_event and stop_event.is_set(): return
                
                # 2º Mapeamento de click sera para criar uma nova linha
                pyautogui.click(pos_nova_linha)
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
                        
                    # Log de progresso
                    msg = f"Item {items_processed+1}/{total_items}: Loja {loja_id}, Cod {codigo}, Qtd {qtd} - {descricao}"
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
                    
                    # Formatar loja se for apenas número e precisar (usualmente loja 15 pode precisar de zero à esquerda ou não,
                    # mantemos o texto original se possível. O padrão de outras macros não colocava zfill se não fosse pedido.
                    # A pedido anterior a 'loja_id' era digitada diretamente.)
                    pyautogui.write(loja_id)
                    time.sleep(0.8) # aguardar carregar box
                    
                    # quando aparecer no box selecionar a loja via seqüência de teclado
                    pyautogui.press('down')
                    time.sleep(0.1)
                    pyautogui.press('up')
                    time.sleep(0.1)
                    
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
