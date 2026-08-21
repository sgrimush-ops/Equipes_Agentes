import os
import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta

def build_database():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'banco_simulador_consinco.db')
    
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Estrutura das Tabelas Centrais do Consinco
    cursor.executescript("""
    -- Cadastro de Pessoas (Fornecedores / Clientes)
    CREATE TABLE GE_PESSOA (
        SEQPESSOA INTEGER PRIMARY KEY,
        NOMERAZAO TEXT NOT NULL,
        FANTASIA TEXT,
        NROCGCCPF TEXT,
        TIPOPESSOA TEXT DEFAULT 'J',
        STATUS TEXT DEFAULT 'A',
        CIDADE TEXT DEFAULT 'PORTO ALEGRE',
        UF TEXT DEFAULT 'RS'
    );

    -- Compradores
    CREATE TABLE MAX_COMPRADOR (
        SEQCOMPRADOR INTEGER PRIMARY KEY,
        COMPRADOR TEXT NOT NULL,
        APELIDO TEXT NOT NULL,
        STATUS TEXT DEFAULT 'A',
        EMAIL TEXT
    );

    -- Empresas / Filiais da Rede
    CREATE TABLE MAX_EMPRESA (
        NROEMPRESA INTEGER PRIMARY KEY,
        NOMERAZAO TEXT NOT NULL,
        FANTASIA TEXT NOT NULL,
        NROSEGMENTOPRINC INTEGER DEFAULT 1,
        CIDADE TEXT,
        UF TEXT DEFAULT 'RS',
        STATUS TEXT DEFAULT 'A',
        TIPOEMPRESA TEXT DEFAULT 'L' -- L = Loja, C = Centro de Distribuicao
    );

    -- Famílias de Produtos (Hierarquia Tributária e Comercial)
    CREATE TABLE MAP_FAMILIA (
        SEQFAMILIA INTEGER PRIMARY KEY,
        FAMILIA TEXT NOT NULL,
        PESAVEL TEXT DEFAULT 'N',
        TIPOSTENTRADA TEXT DEFAULT 'T',
        TIPOETIQUETA TEXT DEFAULT 'P',
        ALIQUOTAICMS REAL DEFAULT 18.0
    );

    -- Categorias / Departamentos / Setores
    CREATE TABLE MAP_CATEGORIA (
        SEQCATEGORIA INTEGER PRIMARY KEY,
        CATEGORIA TEXT NOT NULL,
        TIPCATEGORIA TEXT DEFAULT 'N',
        NIVELHIERARQUIA INTEGER NOT NULL, -- 1=Depto, 2=Secao, 3=Grupo, 4=Subgrupo, 5=Classe
        CATEGORIAPAI INTEGER
    );

    -- Vínculo Família x Categoria por Divisão
    CREATE TABLE MAP_FAMDIVCATEG (
        SEQFAMILIA INTEGER,
        NRODIVISAO INTEGER DEFAULT 1,
        SEQCATEGORIA INTEGER,
        PRIMARY KEY (SEQFAMILIA, NRODIVISAO, SEQCATEGORIA)
    );

    -- Configuração Comercial da Família na Divisão
    CREATE TABLE MAP_FAMDIVISAO (
        SEQFAMILIA INTEGER,
        NRODIVISAO INTEGER DEFAULT 1,
        FINALIDADEFAMILIA TEXT DEFAULT 'R', -- 'R' = Revenda, 'U' = Uso/Consumo, 'I' = Imobilizado
        PADRAOEMBCOMPRA INTEGER DEFAULT 1,
        PADRAOEMBTRANSF INTEGER DEFAULT 1,
        SEQCOMPRADOR INTEGER,
        STATUSCOMPRA TEXT DEFAULT 'A',
        PRIMARY KEY (SEQFAMILIA, NRODIVISAO)
    );

    -- Fornecedor Principal da Família
    CREATE TABLE MAP_FAMFORNEC (
        SEQFAMILIA INTEGER,
        SEQPESSOA INTEGER,
        PRINCIPAL TEXT DEFAULT 'S',
        PRIMARY KEY (SEQFAMILIA, SEQPESSOA)
    );

    -- Embalagens da Família
    CREATE TABLE MAP_FAMEMBALAGEM (
        SEQFAMILIA INTEGER,
        QTDEMBALAGEM INTEGER,
        EMBALAGEM TEXT DEFAULT 'UN',
        PESOBRUTO REAL DEFAULT 1.0,
        PESOLIQUIDO REAL DEFAULT 1.0,
        PADRAOEMBVENDA TEXT DEFAULT 'S',
        PRIMARY KEY (SEQFAMILIA, QTDEMBALAGEM)
    );

    -- Cadastro de Produtos
    CREATE TABLE MAP_PRODUTO (
        SEQPRODUTO INTEGER PRIMARY KEY,
        DESCCOMPLETA TEXT NOT NULL,
        DESCREDUZIDA TEXT,
        SEQFAMILIA INTEGER,
        NCM TEXT DEFAULT '19059090',
        PESOLIQ REAL DEFAULT 0.5,
        PESOBRUTO REAL DEFAULT 0.52,
        DTACADASTRO TEXT,
        STATUS TEXT DEFAULT 'A'
    );

    -- Códigos de Barras (EAN / DUN)
    CREATE TABLE MAP_PRODCODIGO (
        SEQPRODUTO INTEGER,
        CODACESSO TEXT,
        TIPCODIGO TEXT, -- 'E' = EAN, 'D' = DUN/CX, 'B' = Balanca
        QTDEMBALAGEM INTEGER DEFAULT 1,
        STATUS TEXT DEFAULT 'A',
        PRIMARY KEY (SEQPRODUTO, CODACESSO)
    );

    -- Configurações, Estoques e Custos por Loja/Empresa
    CREATE TABLE MRL_PRODUTOEMPRESA (
        SEQPRODUTO INTEGER,
        NROEMPRESA INTEGER,
        STATUSCOMPRA TEXT DEFAULT 'A', -- 'A' = Ativo, 'I' = Inativo, 'S' = Suspenso
        PRCBASE REAL DEFAULT 0.0,
        ESTQLOJA REAL DEFAULT 0.0,
        ESTQDEPOSITO REAL DEFAULT 0.0,
        ESTQMINIMOLOJA REAL DEFAULT 5.0,
        ESTQMAXIMOLOJA REAL DEFAULT 50.0,
        QTDPENDPEDCOMPRA REAL DEFAULT 0.0,
        QTDRESERVADAVDA REAL DEFAULT 0.0,
        QTDRESERVADARECEB REAL DEFAULT 0.0,
        QTDRESERVADAFIXA REAL DEFAULT 0.0,
        QTDVMD REAL DEFAULT 1.5, -- Venda Media Diaria
        CMULTVLRNF REAL DEFAULT 0.0,
        CMULTIPI REAL DEFAULT 0.0,
        CMULTCREDICMS REAL DEFAULT 0.0,
        CMULTICMSST REAL DEFAULT 0.0,
        CMULTDESPNF REAL DEFAULT 0.0,
        CMULTDESPFORANF REAL DEFAULT 0.0,
        CMULTDCTOFORANF REAL DEFAULT 0.0,
        CMULTCREDPIS REAL DEFAULT 0.0,
        CMULTCREDCOFINS REAL DEFAULT 0.0,
        CMULTVLRVERBA REAL DEFAULT 0.0,
        CMULTCUSLIQUIDOEMP REAL DEFAULT 0.0,
        DTAULTENTRADA TEXT,
        DTAHORAULTENTRADA TEXT,
        DTAULTCOMPRA TEXT,
        QTDULTCOMPRA REAL DEFAULT 0.0,
        DTAULTVENDA TEXT,
        DTAULTVENDAEFETIVA TEXT,
        PRIMARY KEY (SEQPRODUTO, NROEMPRESA)
    );

    -- Preços Vigentes por Segmento
    CREATE TABLE MRL_PRODEMPSEG (
        SEQPRODUTO INTEGER,
        NROEMPRESA INTEGER,
        NROSEGMENTO INTEGER DEFAULT 1,
        QTDEMBALAGEM INTEGER DEFAULT 1,
        PRECOVALIDNORMAL REAL DEFAULT 0.0,
        PRECOVALIDPROMOC REAL DEFAULT 0.0,
        STATUSVENDA TEXT DEFAULT 'A',
        DTAINICIOPROMOC TEXT,
        DTAFIMPROMOC TEXT,
        PRIMARY KEY (SEQPRODUTO, NROEMPRESA, NROSEGMENTO, QTDEMBALAGEM)
    );

    -- Embalagem Padrão de Venda do Segmento
    CREATE TABLE MAD_FAMSEGMENTO (
        SEQFAMILIA INTEGER,
        NROSEGMENTO INTEGER DEFAULT 1,
        PADRAOEMBVENDA INTEGER DEFAULT 1,
        PRIMARY KEY (SEQFAMILIA, NROSEGMENTO)
    );

    -- Vendas Diárias Consolidadas por Produto / Empresa / Data
    CREATE TABLE MRL_PRODVENDADIA (
        SEQPRODUTO INTEGER,
        NROEMPRESA INTEGER,
        DTAVDA TEXT,
        QTDVDA REAL DEFAULT 0.0,
        PRIMARY KEY (SEQPRODUTO, NROEMPRESA, DTAVDA)
    );

    -- Custódia / Vendas Oficiais e Custo Médio Diário
    CREATE TABLE MRL_CUSTODIA (
        SEQPRODUTO INTEGER,
        NROEMPRESA INTEGER,
        DTAENTRADASAIDA TEXT,
        QTDVDA REAL DEFAULT 0.0,
        CMDIAVLRNF REAL DEFAULT 0.0,
        CMDIAIPI REAL DEFAULT 0.0,
        CMDIAICMSST REAL DEFAULT 0.0,
        CMDIADESPNF REAL DEFAULT 0.0,
        CMDIACREDICMS REAL DEFAULT 0.0,
        CMDIACREDPIS REAL DEFAULT 0.0,
        PRIMARY KEY (SEQPRODUTO, NROEMPRESA, DTAENTRADASAIDA)
    );

    -- Métricas Logísticas Gerais do CD
    CREATE TABLE MRL_PRODEMPRESAWM (
        SEQPRODUTO INTEGER,
        NROEMPRESA INTEGER,
        PALETELASTRO INTEGER DEFAULT 10,
        PALETEALTURA INTEGER DEFAULT 5,
        PALETELASTROAPANHA INTEGER DEFAULT 10,
        PALETEALTURAAPANHA INTEGER DEFAULT 5,
        PALETELASTROMIUD INTEGER DEFAULT 0,
        PRIMARY KEY (SEQPRODUTO, NROEMPRESA)
    );

    -- Métricas por Espécie de Endereço (WMS Avançado)
    CREATE TABLE MAD_ESPECIEENDERECO (
        CODESPECENDERECO INTEGER PRIMARY KEY,
        DESCRICAO TEXT NOT NULL
    );

    CREATE TABLE MAD_PRODESPENDERECO (
        SEQPRODUTO INTEGER,
        NROEMPRESA INTEGER,
        CODESPECENDERECO INTEGER,
        PALETELASTRO INTEGER DEFAULT 10,
        PALETEALTURA INTEGER DEFAULT 5,
        QTDEMBALAGEM INTEGER DEFAULT 1,
        PRIMARY KEY (SEQPRODUTO, NROEMPRESA, CODESPECENDERECO)
    );

    -- Tabela de Destino BI / Curva ABC de Vendas
    CREATE TABLE MBI_TABCDISTRIB (
        SEQCONSULTA INTEGER,
        SEQPRODUTO INTEGER,
        NROEMPRESA INTEGER,
        QUANTIDADE REAL DEFAULT 0.0,
        VLRVENDA REAL DEFAULT 0.0,
        VLRLUCRO REAL DEFAULT 0.0,
        CTOBRUTOVDA REAL DEFAULT 0.0,
        VLRCONTRIB REAL DEFAULT 0.0,
        PRIMARY KEY (SEQCONSULTA, SEQPRODUTO, NROEMPRESA)
    );

    -- Títulos Financeiros a Receber / Pagar (Verbas, Devoluções, Compra)
    CREATE TABLE FI_TITULO (
        SEQTITULO INTEGER PRIMARY KEY,
        NROEMPRESA INTEGER NOT NULL,
        SEQPESSOA INTEGER NOT NULL,
        NROTITULO TEXT NOT NULL,
        SERIETITULO TEXT DEFAULT '1',
        OBRIGACOES TEXT DEFAULT 'P', -- P = Pagar, R = Receber
        CODESPECIE TEXT DEFAULT 'DP', -- DP = Duplicata, VB = Verba, DV = Devolucao
        DTAVENCIMENTO TEXT NOT NULL,
        DTAEMISSAO TEXT NOT NULL,
        VLRLIQUIDO REAL NOT NULL,
        VLRORIGINAL REAL NOT NULL,
        VLRDESCONTO REAL DEFAULT 0.0,
        VLRJUROS REAL DEFAULT 0.0,
        VLRMULTA REAL DEFAULT 0.0,
        VLRABATIMENTO REAL DEFAULT 0.0,
        SITUACAO TEXT DEFAULT 'A', -- A = Aberto, L = Liquidado, C = Cancelado
        DTAQUITACAO TEXT
    );

    -- Vínculo Título Financeiro x Comprador
    CREATE TABLE FI_TITCOMPRADOR (
        SEQTITULO INTEGER,
        SEQCOMPRADOR INTEGER,
        PERCRATRATEIO REAL DEFAULT 100.0,
        PRIMARY KEY (SEQTITULO, SEQCOMPRADOR)
    );

    -- Baixas e Operações do Título
    CREATE TABLE FI_TITOPERACAO (
        SEQOPERACAO INTEGER PRIMARY KEY,
        SEQTITULO INTEGER NOT NULL,
        CODOPERACAO INTEGER NOT NULL, -- 6=Pago Banco, 19=Compensado, 29=Desconto
        DTAOPERACAO TEXT NOT NULL,
        VLROPERACAO REAL NOT NULL,
        COMPLHISTORICO TEXT
    );

    -- Capa do Pedido de Suprimento / Transferência
    CREATE TABLE MSU_PEDIDOSUPRIM (
        NROPEDIDOSUPRIM INTEGER PRIMARY KEY,
        NROEMPRESA INTEGER NOT NULL, -- Empresa Solicitante / Loja Destino
        SEQFORNECEDOR INTEGER NOT NULL, -- Fornecedor ou CD Origem (NROEMPRESA)
        DTAPEDIDO TEXT NOT NULL,
        DTAENTREGA TEXT,
        STATUS TEXT DEFAULT 'A', -- A = Ativo, L = Liquidado, C = Cancelado
        TIPOPEDIDO TEXT DEFAULT 'T' -- T = Transferencia, C = Compra
    );

    -- Itens a Receber no Pedido de Transferência / Compra
    CREATE TABLE MSU_PSITEMRECEBER (
        NROPEDIDOSUPRIM INTEGER,
        SEQPRODUTO INTEGER,
        QTDEMBALAGEM INTEGER DEFAULT 1,
        QTDPEDIDA REAL NOT NULL,
        QTDRECEBIDA REAL DEFAULT 0.0,
        QTDTOTTRANSITO REAL DEFAULT 0.0,
        STATUSITEM TEXT DEFAULT 'P', -- P = Pendente, A = Atendido, C = Cancelado
        DTAEXPEDICAO TEXT,
        PRIMARY KEY (NROPEDIDOSUPRIM, SEQPRODUTO)
    );

    -- Itens Expedidos
    CREATE TABLE MSU_PSITEMEXPEDIDO (
        NROPEDIDOSUPRIM INTEGER,
        SEQPRODUTO INTEGER,
        QTDEXPEDIDA REAL DEFAULT 0.0,
        NROEMPDESTINO INTEGER,
        PRIMARY KEY (NROPEDIDOSUPRIM, SEQPRODUTO)
    );

    -- Notas Fiscais
    CREATE TABLE MLF_NOTAFISCAL (
        SEQNOTAFISCAL INTEGER PRIMARY KEY,
        NUMERONF INTEGER NOT NULL,
        SERIENF TEXT DEFAULT '1',
        NROEMPRESA INTEGER NOT NULL,
        SEQPESSOA INTEGER NOT NULL,
        DTAEMISSAO TEXT NOT NULL,
        DTAENTRADA TEXT NOT NULL,
        VLRTOTALNF REAL NOT NULL,
        SITUACAO TEXT DEFAULT 'N',
        STATUSNF TEXT DEFAULT 'V',
        CODGERALOPER INTEGER DEFAULT 1102,
        NFECHAVEACESSO TEXT
    );
    """)

    # 2. Inserção de Empresas Reais da Rede
    empresas = [
        (1, 'MATRIZ / LOJA 01 - CENTRO', 'LJ 01 CENTRO', 1, 'PORTO ALEGRE', 'RS', 'A', 'L'),
        (2, 'SUPERMERCADO LOJA 02 - NORTE', 'LJ 02 NORTE', 1, 'CANOAS', 'RS', 'A', 'L'),
        (3, 'SUPERMERCADO LOJA 03 - SUL', 'LJ 03 SUL', 1, 'PORTO ALEGRE', 'RS', 'A', 'L'),
        (4, 'SUPERMERCADO LOJA 04 - LESTE', 'LJ 04 LESTE', 1, 'GRAVATAI', 'RS', 'A', 'L'),
        (5, 'SUPERMERCADO LOJA 05 - OESTE', 'LJ 05 OESTE', 1, 'NOVO HAMBURGO', 'RS', 'A', 'L'),
        (6, 'SUPERMERCADO LOJA 06 - PRAIA', 'LJ 06 PRAIA', 1, 'CAPAO DA CANOA', 'RS', 'A', 'L'),
        (7, 'SUPERMERCADO LOJA 07 - SERRA', 'LJ 07 SERRA', 1, 'CAXIAS DO SUL', 'RS', 'A', 'L'),
        (8, 'SUPERMERCADO LOJA 08 - VALE', 'LJ 08 VALE', 1, 'SAO LEOPOLDO', 'RS', 'A', 'L'),
        (11, 'SUPERMERCADO LOJA 11 - EXPRESS', 'LJ 11 EXPRESS', 1, 'PORTO ALEGRE', 'RS', 'A', 'L'),
        (12, 'SUPERMERCADO LOJA 12 - BAIRRO', 'LJ 12 BAIRRO', 1, 'VIAMAO', 'RS', 'A', 'L'),
        (13, 'SUPERMERCADO LOJA 13 - SHOPPING', 'LJ 13 SHOPPING', 1, 'CANOAS', 'RS', 'A', 'L'),
        (14, 'SUPERMERCADO LOJA 14 - PARQUE', 'LJ 14 PARQUE', 1, 'ALVORADA', 'RS', 'A', 'L'),
        (15, 'SUPERMERCADO LOJA 15 - AVENIDA', 'LJ 15 AVENIDA', 1, 'PORTO ALEGRE', 'RS', 'A', 'L'),
        (16, 'CENTRO DE DISTRIBUICAO MATRIZ CD 16', 'CD 16 PRINCIPAL', 1, 'ESTEIO', 'RS', 'A', 'C'),
        (17, 'SUPERMERCADO LOJA 17 - HIGIENOPOLIS', 'LJ 17 HIGIENOPOLIS', 1, 'PORTO ALEGRE', 'RS', 'A', 'L'),
        (18, 'SUPERMERCADO LOJA 18 - PETROPOLIS', 'LJ 18 PETROPOLIS', 1, 'PORTO ALEGRE', 'RS', 'A', 'L'),
        (50, 'CD SECOS E LOGISTICA 50', 'CD 50 SECOS', 1, 'SAPUCAIA DO SUL', 'RS', 'A', 'C'),
        (900, 'ADMINISTRATIVO CENTRAL', 'ADM CENTRAL', 1, 'PORTO ALEGRE', 'RS', 'A', 'L')
    ]
    cursor.executemany("INSERT INTO MAX_EMPRESA VALUES (?,?,?,?,?,?,?,?)", empresas)

    # 3. Inserção de Compradores Reais do Projeto
    compradores = [
        (1, 'WETER SILVA', 'WETER', 'A', 'weter@rede.com.br'),
        (2, 'SANDRO MOREIRA', 'SANDRO', 'A', 'sandro@rede.com.br'),
        (3, 'NICOLAS AUGUSTO P. BORGES', 'NICOLAS', 'A', 'nicolas@rede.com.br'),
        (4, 'SUPPLY CHAIN GESTAO', 'SUPPLY', 'A', 'supply@rede.com.br'),
        (5, 'CARLOS EDUARDO PEREIRA', 'CARLOS', 'A', 'carlos@rede.com.br'),
        (6, 'MARIANA RODRIGUES', 'MARIANA', 'A', 'mariana@rede.com.br')
    ]
    cursor.executemany("INSERT INTO MAX_COMPRADOR VALUES (?,?,?,?,?)", compradores)

    # 4. Inserção de Fornecedores Reais / Pessoas
    fornecedores = [
        (5894, 'AMBEV S.A.', 'AMBEV', '07.526.557/0001-00', 'J', 'A', 'SAO PAULO', 'SP'),
        (1042, 'COCA COLA FEMSA BRASIL', 'COCA COLA', '61.427.534/0001-45', 'J', 'A', 'PORTO ALEGRE', 'RS'),
        (2311, 'NESTLE BRASIL LTDA', 'NESTLE', '60.409.075/0001-52', 'J', 'A', 'SAO PAULO', 'SP'),
        (3405, 'JBS S/A - SEARA ALIMENTOS', 'JBS SEARA', '02.916.265/0001-00', 'J', 'A', 'ITAJAI', 'SC'),
        (4510, 'BRF S.A. - SADIA E PERDIGAO', 'BRF ALIMENTOS', '01.838.723/0001-27', 'J', 'A', 'CURITIBA', 'PR'),
        (7820, 'UNILEVER BRASIL LTDA', 'UNILEVER', '61.068.276/0001-04', 'J', 'A', 'VALINHOS', 'SP'),
        (8901, 'M. DIAS BRANCO S.A.', 'M DIAS BRANCO', '07.206.816/0001-15', 'J', 'A', 'FORTALEZA', 'CE'),
        (9140, 'PIRACANJUBA - LATICINIOS BELA VISTA', 'PIRACANJUBA', '01.077.568/0001-70', 'J', 'A', 'BELA VISTA', 'GO'),
        (6500, 'MONDELEZ BRASIL LTDA', 'MONDELEZ', '33.033.028/0001-84', 'J', 'A', 'CURITIBA', 'PR'),
        (3320, 'PROCTER & GAMBLE INDUSTRIAL', 'P&G', '01.358.196/0001-49', 'J', 'A', 'SAO PAULO', 'SP')
    ]
    cursor.executemany("INSERT INTO GE_PESSOA VALUES (?,?,?,?,?,?,?,?)", fornecedores)

    # 5. Inserção de Categorias Hierárquicas
    categorias = [
        # Nível 1 - Departamentos
        (100, 'BEBIDAS', 'N', 1, None),
        (200, 'MERCEARIA', 'N', 1, None),
        (300, 'PERECIVEIS', 'N', 1, None),
        (400, 'PERFUMARIA E LIMPEZA', 'N', 1, None),
        (500, 'PRODUTOS PET', 'N', 1, None),
        (600, 'NAO ALIMENTO', 'N', 1, None),
        (999, 'ALMOXARIFADO', 'N', 1, None), # Expurgo

        # Nível 2 - Seções
        (110, 'CERVEJAS E CHOPP', 'N', 2, 100),
        (120, 'REFRIGERANTES E AGUAS', 'N', 2, 100),
        (130, 'SUCOS E DESTILADOS', 'N', 2, 100),
        (210, 'MERCEARIA DOCE', 'N', 2, 200),
        (220, 'MERCEARIA SALGADA', 'N', 2, 200),
        (230, 'MATINAIS E GRAOS', 'N', 2, 200),
        (310, 'ACOUGUE E CARNES', 'N', 2, 300),
        (320, 'LATICINIOS E QUEIJOS', 'N', 2, 300),
        (330, 'FIAMBRERIA E EMBUTIDOS', 'N', 2, 300),
        (410, 'HIGIENE PESSOAL', 'N', 2, 400),
        (420, 'CUIDADOS COM A CASA', 'N', 2, 400),
        (510, 'RACAO E PETISCOS', 'N', 2, 500),

        # Nível 3 - Grupos
        (111, 'CERVEJA PURO MALTE', 'N', 3, 110),
        (112, 'CERVEJA PILSNER TRADICIONAL', 'N', 3, 110),
        (121, 'REFRIGERANTE COLA', 'N', 3, 120),
        (122, 'AGUA MINERAL', 'N', 3, 120),
        (211, 'CHOCOLATES E BOMBONIERE', 'N', 3, 210),
        (212, 'BISCOITOS E COOKIES', 'N', 3, 210),
        (221, 'MASSAS E MOLHOS', 'N', 3, 220),
        (222, 'ARROZ E FEIJAO', 'N', 3, 230),
        (311, 'BOVINO RESFRIADO', 'N', 3, 310),
        (312, 'AVES E CONGELADOS', 'N', 3, 310),
        (321, 'LEITE UHT', 'N', 3, 320),
        (322, 'IOGURTES', 'N', 3, 320),
        (411, 'SABONETES E SHAMPOOS', 'N', 3, 410),
        (421, 'DETERGENTES E LAVA ROUPAS', 'N', 3, 420),

        # Nível 4/5 - Subgrupos
        (1111, 'CERVEJA HEINEKEN LATA 350ML', 'N', 4, 111),
        (1112, 'CERVEJA SPATEN LONG NECK 355ML', 'N', 4, 111),
        (1211, 'COCA COLA PET 2L TRADICIONAL', 'N', 4, 121),
        (2111, 'BARRA CHOCOLATE NESTLE 90G', 'N', 4, 211),
        (2211, 'MASSA ESPAGUETE DIAS BRANCO 500G', 'N', 4, 221),
        (3111, 'PICANHA BOVINA RESFRIADA VACUO KG', 'N', 4, 311),
        (3211, 'LEITE INTEGRAL PIRACANJUBA 1L', 'N', 4, 321),
        (4111, 'SABONETE DOVE ORIGINAL 90G', 'N', 4, 411),
        (4211, 'SABAO LIQUIDO OMO LAVAGEM PERFEITA 3L', 'N', 4, 421)
    ]
    cursor.executemany("INSERT INTO MAP_CATEGORIA VALUES (?,?,?,?,?)", categorias)

    # 6. Carregar Produtos Reais dos Arquivos do Workspace se existirem
    workspace_dir = os.path.dirname(os.path.dirname(base_dir))
    sem_venda_file = os.path.join(workspace_dir, 'Aplicativos', 'sem_venda', 'sem_venda.xlsx')
    
    produtos_base = []
    if os.path.exists(sem_venda_file):
        try:
            df_sv = pd.read_excel(sem_venda_file)
            # Pegar registros únicos de produto
            df_unique = df_sv.drop_duplicates(subset=['CODIGO_PRODUTO'])
            for _, r in df_unique.head(300).iterrows():
                seqprod = int(r['CODIGO_PRODUTO'])
                desc = str(r['DESCRICAO_PRODUTO']).strip()
                depto = str(r['DEPARTAMENTO']).strip().upper()
                comp = str(r['COMPRADOR']).strip().upper()
                produtos_base.append((seqprod, desc, depto, comp))
        except Exception as e:
            print("Aviso ao ler sem_venda:", e)

    # Lista fallback de produtos realistas de varejo caso poucos sejam carregados
    fallback_produtos = [
        (3880, 'CERVEJA HEINEKEN LAGER LATA 350ML', 'BEBIDAS', 'WETER'),
        (3881, 'CERVEJA SPATEN PURO MALTE LN 355ML', 'BEBIDAS', 'WETER'),
        (3883, 'CERVEJA BRAHMA DUPLO MALTE LATA 350ML', 'BEBIDAS', 'WETER'),
        (4012, 'REFRIGERANTE COCA COLA PET 2 LITROS', 'BEBIDAS', 'WETER'),
        (4015, 'REFRIGERANTE GUARANA ANTARCTICA PET 2L', 'BEBIDAS', 'WETER'),
        (4020, 'AGUA MINERAL SEM GAS CRYSTAL 500ML', 'BEBIDAS', 'WETER'),
        (5102, 'CHOCOLATE NESTLE CLASSIC AO LEITE 90G', 'MERCEARIA', 'SANDRO'),
        (5105, 'CHOCOLATE LACTA AO LEITE BARRA 80G', 'MERCEARIA', 'SANDRO'),
        (5201, 'BISCOITO RECHEADO OREO ORIGINAL 90G', 'MERCEARIA', 'SANDRO'),
        (5310, 'ARROZ BRANCO TIO JOAO TIPO 1 5KG', 'MERCEARIA', 'NICOLAS'),
        (5320, 'FEIJAO PRETO KICALDO TIPO 1 1KG', 'MERCEARIA', 'NICOLAS'),
        (5405, 'MASSA ESPAGUETE ADRIA TRADICIONAL 500G', 'MERCEARIA', 'SANDRO'),
        (5501, 'OLEO DE SOJA LIZA PET 900ML', 'MERCEARIA', 'NICOLAS'),
        (6100, 'PICANHA BOVINA GRILL RESFRIADA KG', 'PERECIVEIS', 'SUPPLY'),
        (6150, 'FILE DE PEITO FRANGO SEARA BANDEJA 1KG', 'PERECIVEIS', 'SUPPLY'),
        (6210, 'LEITE UHT INTEGRAL PIRACANJUBA 1L', 'PERECIVEIS', 'SUPPLY'),
        (6220, 'LEITE CONDENSADO MOCOCA TETRA 395G', 'MERCEARIA', 'SANDRO'),
        (6250, 'QUEIJO MUSSARELA FATIADO PRESIDENT 150G', 'PERECIVEIS', 'SUPPLY'),
        (7100, 'SABAO EM PO OMO LAVAGEM PERFEITA 1.6KG', 'PERFUMARIA E LIMPEZA', 'CARLOS'),
        (7110, 'AMACIANTE CONCENTRADO COMFORT 1L', 'PERFUMARIA E LIMPEZA', 'CARLOS'),
        (7120, 'DETERGENTE LIQUIDO YPE MACA 500ML', 'PERFUMARIA E LIMPEZA', 'CARLOS'),
        (7200, 'SHAMPOO PANTENE RESTAURACAO 400ML', 'PERFUMARIA E LIMPEZA', 'MARIANA'),
        (7210, 'SABONETE DOVE ORIGINAL 90G', 'PERFUMARIA E LIMPEZA', 'MARIANA'),
        (7220, 'CREME DENTAL COLGATE TOTAL 12 90G', 'PERFUMARIA E LIMPEZA', 'MARIANA'),
        (8100, 'RACAO PEDIGREE CAES ADULTOS CARNE 10KG', 'PRODUTOS PET', 'CARLOS'),
        (8110, 'RACAO WHISKAS GATOS CARNE 3KG', 'PRODUTOS PET', 'CARLOS')
    ]

    for p in fallback_produtos:
        if not any(x[0] == p[0] for x in produtos_base):
            produtos_base.append(p)

    # 7. Popular Famílias, Produtos, Vínculos e Embalagens
    seq_familia = 1000
    cat_map = {
        'BEBIDAS': 100,
        'MERCEARIA': 200,
        'PERECIVEIS': 300,
        'PERFUMARIA E LIMPEZA': 400,
        'PRODUTOS PET': 500,
        'NAO ALIMENTO': 600,
        'ALMOXARIFADO': 999
    }
    comp_map = {
        'WETER': 1,
        'SANDRO': 2,
        'NICOLAS': 3,
        'SUPPLY': 4,
        'CARLOS': 5,
        'MARIANA': 6
    }
    forn_keys = [5894, 1042, 2311, 3405, 4510, 7820, 8901, 9140, 6500, 3320]

    lojas_validas = [1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 50]

    # Gerar datas recentes
    hoje = datetime(2026, 8, 21)
    
    for seqprod, desc, depto, comp_name in produtos_base:
        seq_familia += 1
        cat_id = cat_map.get(depto, 200)
        
        # Encontrar comprador id
        comp_id = 1
        for k, v in comp_map.items():
            if k in comp_name.upper():
                comp_id = v
                break

        # Família
        cursor.execute("INSERT INTO MAP_FAMILIA VALUES (?,?,?,?,?,?)",
                       (seq_familia, f"FAMILIA {desc[:30]}", 'S' if 'KG' in desc else 'N', 'T', 'P', 18.0))
        
        # Família x Categoria
        cursor.execute("INSERT INTO MAP_FAMDIVCATEG VALUES (?,?,?)", (seq_familia, 1, cat_id))
        
        # Família Divisão
        cursor.execute("INSERT INTO MAP_FAMDIVISAO VALUES (?,?,?,?,?,?,?)",
                       (seq_familia, 1, 'R', 1, 1, comp_id, 'A'))
        
        # Família Fornecedor Principal
        forn_id = random.choice(forn_keys)
        cursor.execute("INSERT INTO MAP_FAMFORNEC VALUES (?,?,?)", (seq_familia, forn_id, 'S'))

        # Embalagens (Unitária + Caixa)
        cursor.execute("INSERT INTO MAP_FAMEMBALAGEM VALUES (?,?,?,?,?,?)",
                       (seq_familia, 1, 'UN', 0.5, 0.5, 'S'))
        cursor.execute("INSERT INTO MAP_FAMEMBALAGEM VALUES (?,?,?,?,?,?)",
                       (seq_familia, 12, 'CX', 6.0, 6.0, 'N'))
        
        # Segmento
        cursor.execute("INSERT INTO MAD_FAMSEGMENTO VALUES (?,?,?)", (seq_familia, 1, 1))

        # Produto
        dta_cad = (hoje - timedelta(days=random.randint(60, 800))).strftime('%Y-%m-%d')
        cursor.execute("INSERT INTO MAP_PRODUTO VALUES (?,?,?,?,?,?,?,?,?)",
                       (seqprod, desc, desc[:20], seq_familia, '19059090', 0.5, 0.52, dta_cad, 'A'))
        
        # Códigos EAN / DUN
        ean = f"789{seqprod:09d}"
        dun = f"1789{seqprod:09d}5"
        cursor.execute("INSERT INTO MAP_PRODCODIGO VALUES (?,?,?,?,?)", (seqprod, ean, 'E', 1, 'A'))
        cursor.execute("INSERT INTO MAP_PRODCODIGO VALUES (?,?,?,?,?)", (seqprod, dun, 'D', 12, 'A'))

        # Preço base e custos realistas
        custo_nf = round(random.uniform(2.5, 45.0), 2)
        ipi = round(custo_nf * 0.05, 2)
        icms = round(custo_nf * 0.12, 2)
        pis = round(custo_nf * 0.0165, 2)
        cofins = round(custo_nf * 0.076, 2)
        custo_liquido = round(custo_nf + ipi - icms - pis - cofins, 2)
        prc_normal = round(custo_liquido * random.uniform(1.35, 1.65), 2)
        prc_promoc = round(prc_normal * 0.85, 2) if random.random() < 0.35 else 0.0

        # WMS do CD
        cursor.execute("INSERT INTO MRL_PRODEMPRESAWM VALUES (?,?,?,?,?,?,?)",
                       (seqprod, 16, 12, 6, 12, 6, 0))

        # Popular em cada Loja da Rede
        for nroemp in lojas_validas:
            is_cd = nroemp in (16, 50)
            status_compra = 'A' if random.random() > 0.08 else 'I'
            
            # Estoques
            if is_cd:
                estq_loja = 0.0
                estq_dep = float(random.randint(200, 3500))
                pend_compra = float(random.randint(0, 500))
            else:
                estq_loja = float(random.randint(0, 120)) if status_compra == 'A' else 0.0
                estq_dep = float(random.randint(0, 60))
                pend_compra = float(random.randint(0, 40))
                
            res_vda = float(random.randint(0, 5)) if estq_loja > 10 else 0.0
            res_rec = float(random.randint(0, 8)) if random.random() < 0.2 else 0.0
            res_fixa = 0.0

            dta_ult_ent = (hoje - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            dta_ult_vda = (hoje - timedelta(days=random.randint(0, 15))).strftime('%Y-%m-%d')

            cursor.execute("""
            INSERT INTO MRL_PRODUTOEMPRESA (
                SEQPRODUTO, NROEMPRESA, STATUSCOMPRA, PRCBASE,
                ESTQLOJA, ESTQDEPOSITO, ESTQMINIMOLOJA, ESTQMAXIMOLOJA, QTDPENDPEDCOMPRA,
                QTDRESERVADAVDA, QTDRESERVADARECEB, QTDRESERVADAFIXA, QTDVMD,
                CMULTVLRNF, CMULTIPI, CMULTCREDICMS, CMULTICMSST, CMULTDESPNF,
                CMULTDESPFORANF, CMULTDCTOFORANF, CMULTCREDPIS, CMULTCREDCOFINS, CMULTVLRVERBA,
                CMULTCUSLIQUIDOEMP, DTAULTENTRADA, DTAHORAULTENTRADA, DTAULTCOMPRA,
                QTDULTCOMPRA, DTAULTVENDA, DTAULTVENDAEFETIVA
            ) VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )""", (
                seqprod, nroemp, status_compra, prc_normal,
                estq_loja, estq_dep, 5.0, 50.0, pend_compra,
                res_vda, res_rec, res_fixa, 2.5,
                custo_nf, ipi, icms, 0.0, 0.0,
                0.0, 0.0, pis, cofins, 0.0,
                custo_liquido, dta_ult_ent, f"{dta_ult_ent} 08:30:00", dta_ult_ent,
                24.0, dta_ult_vda, dta_ult_vda
            ))

            # Preço no Segmento
            cursor.execute("INSERT INTO MRL_PRODEMPSEG VALUES (?,?,?,?,?,?,?,?,?)",
                           (seqprod, nroemp, 1, 1, prc_normal, prc_promoc, 'A',
                            (hoje - timedelta(days=5)).strftime('%Y-%m-%d') if prc_promoc > 0 else None,
                            (hoje + timedelta(days=10)).strftime('%Y-%m-%d') if prc_promoc > 0 else None))

            # Histórico de Vendas Diárias (últimos 7 dias)
            for d in range(7):
                dt_dia = (hoje - timedelta(days=d)).strftime('%Y-%m-%d')
                qtd_vda_dia = float(random.randint(0, 18)) if not is_cd else 0.0
                if qtd_vda_dia > 0:
                    cursor.execute("INSERT INTO MRL_PRODVENDADIA VALUES (?,?,?,?)",
                                   (seqprod, nroemp, dt_dia, qtd_vda_dia))
                    
                    # Custódia diária correspondente
                    cursor.execute("INSERT INTO MRL_CUSTODIA VALUES (?,?,?,?,?,?,?,?,?,?)",
                                   (seqprod, nroemp, dt_dia, qtd_vda_dia, custo_nf, ipi, 0.0, 0.0, icms, pis))

            # Registro Curva ABC consolidada (MBI_TABCDISTRIB)
            qtd_abc = float(random.randint(40, 500))
            vlr_abc = round(qtd_abc * prc_normal, 2)
            cto_abc = round(qtd_abc * custo_liquido, 2)
            lucro_abc = round(vlr_abc - cto_abc, 2)
            cursor.execute("INSERT INTO MBI_TABCDISTRIB VALUES (?,?,?,?,?,?,?,?)",
                           (1001, seqprod, nroemp, qtd_abc, vlr_abc, lucro_abc, cto_abc, lucro_abc))

    # 8. Inserção de Títulos Financeiros e Operações
    seq_tit = 50000
    for forn in fornecedores:
        seqforn = forn[0]
        comp_id = random.randint(1, 6)
        for t in range(5):
            seq_tit += 1
            vlr = round(random.uniform(500.0, 25000.0), 2)
            dta_venc = (hoje + timedelta(days=random.randint(-15, 45))).strftime('%Y-%m-%d')
            dta_emi = (hoje - timedelta(days=random.randint(10, 60))).strftime('%Y-%m-%d')
            esp = random.choice(['DP', 'VB', 'DV'])
            obrig = 'P' if esp == 'DP' else 'R' # Verbas e devoluções a receber
            situacao = 'L' if random.random() < 0.4 else 'A'
            dta_quit = (hoje - timedelta(days=random.randint(1, 10))).strftime('%Y-%m-%d') if situacao == 'L' else None

            cursor.execute("""
            INSERT INTO FI_TITULO VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (seq_tit, 1, seqforn, f"NF{seq_tit}", '1', obrig, esp, dta_venc, dta_emi, vlr, vlr, 0.0, 0.0, 0.0, 0.0, situacao, dta_quit))

            cursor.execute("INSERT INTO FI_TITCOMPRADOR VALUES (?,?,?)", (seq_tit, comp_id, 100.0))

            if situacao == 'L':
                cursor.execute("INSERT INTO FI_TITOPERACAO VALUES (?,?,?,?,?,?)",
                               (seq_tit * 10 + 1, seq_tit, 6, dta_quit, vlr, 'LIQUIDACAO BANCO'))

    # 9. Pedidos de Transferência em Trânsito (MSU)
    seq_ped = 800000
    for loja in [1, 2, 3, 4, 5, 7, 8, 11, 14, 18]:
        seq_ped += 1
        dta_ped = (hoje - timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d')
        cursor.execute("INSERT INTO MSU_PEDIDOSUPRIM VALUES (?,?,?,?,?,?,?)",
                       (seq_ped, loja, 16, dta_ped, dta_ped, 'A', 'T'))

        # Itens do Pedido
        amostra_prods = random.sample(produtos_base, 4)
        for prod in amostra_prods:
            seqp = prod[0]
            qtd_ped = float(random.randint(10, 50))
            qtd_transito = float(random.randint(5, 30))
            cursor.execute("INSERT INTO MSU_PSITEMRECEBER VALUES (?,?,?,?,?,?,?,?)",
                           (seq_ped, seqp, 1, qtd_ped, 0.0, qtd_transito, 'P', dta_ped))
            cursor.execute("INSERT INTO MSU_PSITEMEXPEDIDO VALUES (?,?,?,?)",
                           (seq_ped, seqp, qtd_transito, loja))

    # 10. Notas Fiscais (MLF_NOTAFISCAL)
    seq_nf = 900000
    for forn in fornecedores:
        seqforn = forn[0]
        for n in range(3):
            seq_nf += 1
            num_nf = random.randint(100000, 999999)
            dta_ent = (hoje - timedelta(days=random.randint(1, 20))).strftime('%Y-%m-%d')
            vlr_nf = round(random.uniform(3000.0, 45000.0), 2)
            chave = f"432608{forn[3].replace('.', '').replace('/', '').replace('-', '')[:14]}55001{num_nf:09d}1000000000"
            cursor.execute("INSERT INTO MLF_NOTAFISCAL VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                           (seq_nf, num_nf, '1', 16, seqforn, dta_ent, dta_ent, vlr_nf, 'N', 'V', 1102, chave))

    # 11. Integrar Dicionário Oficial de 4.515 Tabelas do Consinco
    dict_src_path = os.path.join(workspace_dir, 'Aplicativos', 'gerenciamento_sql', 'dicionario_consinco.db')
    if os.path.exists(dict_src_path):
        try:
            conn_src = sqlite3.connect(dict_src_path)
            c_src = conn_src.cursor()
            c_src.execute("SELECT NOME_TABELA, DESCRICAO_TABELA, ORDEM, NOME_COLUNA, TIPO_DADOS, DESCRICAO_COLUNA FROM colunas")
            dict_rows = c_src.fetchall()
            cursor.execute("CREATE TABLE IF NOT EXISTS colunas (NOME_TABELA TEXT, DESCRICAO_TABELA TEXT, ORDEM TEXT, NOME_COLUNA TEXT, TIPO_DADOS TEXT, DESCRICAO_COLUNA TEXT)")
            cursor.executemany("INSERT INTO colunas VALUES (?,?,?,?,?,?)", dict_rows)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_colunas_tab ON colunas(NOME_TABELA)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_colunas_col ON colunas(NOME_COLUNA)")
            conn_src.close()
            print(f"Dicionario oficial integrado com sucesso: {len(dict_rows)} colunas!")
        except Exception as e:
            print("Aviso ao integrar dicionario:", e)

    # Commit e Finalização
    conn.commit()
    
    # Validação rápida de contagem
    print("--- Banco Simulador Consinco Gerado com Sucesso! ---")
    cursor.execute("SELECT count(*) FROM MAP_PRODUTO")
    print(f"Produtos Cadastrados: {cursor.fetchone()[0]}")
    cursor.execute("SELECT count(*) FROM MRL_PRODUTOEMPRESA")
    print(f"Registros de Estoque Loja (MRL_PRODUTOEMPRESA): {cursor.fetchone()[0]}")
    cursor.execute("SELECT count(*) FROM MRL_CUSTODIA")
    print(f"Registros de Custodia/Venda: {cursor.fetchone()[0]}")
    cursor.execute("SELECT count(*) FROM FI_TITULO")
    print(f"Titulos Financeiros: {cursor.fetchone()[0]}")
    cursor.execute("SELECT count(*) FROM MSU_PEDIDOSUPRIM")
    print(f"Pedidos de Transferencia: {cursor.fetchone()[0]}")

    conn.close()

if __name__ == '__main__':
    build_database()
