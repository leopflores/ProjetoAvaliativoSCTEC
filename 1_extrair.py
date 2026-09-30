import gdown
import zipfile
import os
import config as config
import banco as banco
import pandas as pd

#1. EXTRAIR O ARQUIVO .ZIP DO GOOGLE DRIVE E SALVAR OS ARQUIVOS .CSV NA PASTA DE DADOS:
def baixar_e_extrair_drive(file_id, pasta_destino):
    arquivo_zip = "arquivo.zip"

    url = f"https://drive.google.com/uc?id={file_id}"

    print("Baixando...")
    gdown.download(url, arquivo_zip, quiet=False)

    print("Extraindo...")
    os.makedirs(pasta_destino, exist_ok=True)

    with zipfile.ZipFile(arquivo_zip, "r") as zip_ref:
        zip_ref.extractall(pasta_destino)

    print(f"Concluído! Arquivos extraídos em: {pasta_destino}")


baixar_e_extrair_drive(
    config.DRIVE_FILE_ID, config.PASTA_DADOS
)


#2. CRIAR DATABASE NO POSTGRESQL E TABELAS UTILIZANDO O ARQUIVO SQL:

conexao = banco.conectar()

with open("0_criar_banco.sql", "r", encoding="utf-8") as arquivo:
    query = arquivo.read()

banco.executar(conexao, query)

#3. INSERIR OS DADOS DOS DATAFRAMES NAS TABELAS RAW CORRESPONDENTES NO POSTGRESQL:

def ler_csv_em_chunks(nome_tabela):
    """
    Lê um arquivo CSV em blocos (chunks) e retorna um gerador de DataFrames.
    """
    for df in pd.read_csv(
        config.PASTA_DADOS / config.ARQUIVOS[nome_tabela]["csv"],
        sep=config.CSV_SEPARADOR,
        encoding=config.CSV_ENCODING,
        chunksize=config.TAMANHO_BLOCO,
        dtype=str
    ):
        yield df


def inserir_pagamento(conexao, df):

    sql_insert = """
        INSERT INTO raw_pagamento (
            identificador_processo_viagem,
            numero_proposta_pcdp,
            codigo_orgao_superior,
            nome_orgao_superior,
            codigo_orgao_pagador,
            nome_orgao_pagador,
            codigo_unidade_gestora_pagadora,
            nome_unidade_gestora_pagadora,
            tipo_pagamento,
            valor
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    linhas = []

    for linha in df.itertuples(index=False, name=None):
        linhas.append(linha)

    banco.inserir_em_lote(
        conexao,
        sql_insert,
        linhas
    )

def inserir_passagem(conexao, df):

    sql_insert = """
        INSERT INTO raw_passagem (
            identificador_processo_viagem,
            numero_proposta_pcdp,
            meio_transporte,
            pais_origem_ida,
            uf_origem_ida,
            cidade_origem_ida,
            pais_destino_ida,
            uf_destino_ida,
            cidade_destino_ida,
            pais_origem_volta,
            uf_origem_volta,
            cidade_origem_volta,
            pais_destino_volta,
            uf_destino_volta,
            cidade_destino_volta,
            valor_passagem,
            taxa_servico,
            data_emissao_compra,
            hora_emissao_compra
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
    """

    linhas = []

    for linha in df.itertuples(index=False, name=None):
        linhas.append(linha)

    banco.inserir_em_lote(
        conexao,
        sql_insert,
        linhas
    )

def inserir_trecho(conexao, df):

    sql_insert = """
        INSERT INTO raw_trecho (
            identificador_processo_viagem,
            numero_proposta_pcdp,
            sequencia_trecho,
            origem_data,
            origem_pais,
            origem_uf,
            origem_cidade,
            destino_data,
            destino_pais,
            destino_uf,
            destino_cidade,
            meio_transporte,
            numero_diarias,
            missao
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
    """

    linhas = []

    for linha in df.itertuples(index=False, name=None):
        linhas.append(linha)

    banco.inserir_em_lote(
        conexao,
        sql_insert,
        linhas
    )

def inserir_viagem(conexao, df):

    sql_insert = """
        INSERT INTO raw_viagem (
            identificador_processo_viagem,
            numero_proposta_pcdp,
            situacao,
            viagem_urgente,
            justificativa_urgencia_viagem,
            codigo_orgao_superior,
            nome_orgao_superior,
            codigo_orgao_solicitante,
            nome_orgao_solicitante,
            cpf_viajante,
            nome,
            cargo,
            funcao,
            descricao_funcao,
            periodo_data_inicio,
            periodo_data_fim,
            destinos,
            motivo,
            valor_diarias,
            valor_passagens,
            valor_devolucao,
            valor_outros_gastos
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s
        )
    """

    linhas = []

    for linha in df.itertuples(index=False, name=None):
        linhas.append(linha)

    banco.inserir_em_lote(
        conexao,
        sql_insert,
        linhas
    )


try:

    print("Limpando tabelas raw...")

    banco.executar(
        conexao, 
        '''
        TRUNCATE TABLE raw_pagamento;
        TRUNCATE TABLE raw_viagem;
        TRUNCATE TABLE raw_passagem;
        TRUNCATE TABLE raw_trecho;
        '''
    )

    print("Limpeza das tabelas raw concluída com sucesso!")

    print("Adicionando dados nas tabelas raw...")

    for df in ler_csv_em_chunks("pagamento"):
        inserir_pagamento(conexao, df)

    for df in ler_csv_em_chunks("passagem"):
        inserir_passagem(conexao, df)

    for df in ler_csv_em_chunks("trecho"):
        inserir_trecho(conexao, df)

    for df in ler_csv_em_chunks("viagem"):
        inserir_viagem(conexao, df)

    print("Arquivos CSV carregados com sucesso!")

except Exception as e:
    print(f"Erro durante a carga dos arquivos CSV: {e}")
    exit(1)

