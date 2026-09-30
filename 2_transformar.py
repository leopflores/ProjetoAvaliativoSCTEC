"""
Transformações da camada RAW para a camada SILVER:

1. silver_viagem
- Converte campos de texto com 'NaN' para NULL.
- Converte datas de DD/MM/AAAA para DATE.
- Converte valores monetários para DECIMAL.
- Calcula valor_total:
  valor_diarias + valor_passagens - valor_devolucao + valor_outros_gastos.
- Calcula duracao_dias a partir de data_fim - data_inicio.

2. silver_passagem
- Converte campos de texto com 'NaN' para NULL.
- Converte valor_passagem e taxa_servico para DECIMAL.
- Converte data_emissao_compra para DATE.

3. silver_pagamento
- Converte campos de texto com 'NaN' para NULL.
- Converte valor para DECIMAL.

4. silver_trecho
- Converte sequencia_trecho para INT.
- Converte datas de origem e destino para DATE.
- Converte campos de texto com 'NaN' para NULL.
- Converte numero_diarias para DECIMAL.

Os valores numéricos ausentes permanecem como NULL, não sendo
substituídos por zero.

A ordem de carregamento respeita a integridade referencial:
silver_viagem → silver_passagem → silver_pagamento → silver_trecho.
"""


import banco

def trunca_tabelas(conexao):

    print("Iniciando truncamento das tabelas Silver...")

    sql_truncate = """
        TRUNCATE TABLE
            silver_passagem,
            silver_pagamento,
            silver_trecho,
            silver_viagem
        RESTART IDENTITY;
        """

    banco.executar(conexao, sql_truncate)
    
    print("Truncamento das tabelas Silver concluído.")

def transformar_viagem(conexao):

    print("Iniciando transformação dos dados de viagem...")

    sql_insert = """

        INSERT INTO silver_viagem (
            id_viagem,
            num_proposta,
            situacao,
            viagem_urgente,
            cod_orgao_superior,
            nome_orgao_superior,
            nome_viajante,
            cargo,
            data_inicio,
            data_fim,
            destinos,
            motivo,
            valor_diarias,
            valor_passagens,
            valor_devolucao,
            valor_outros_gastos,
            valor_total,
            duracao_dias
        )

        SELECT

            -- Identificação da viagem
            identificador_processo_viagem,

            -- Dados textuais
            NULLIF(TRIM(numero_proposta_pcdp), 'NaN'),

            NULLIF(TRIM(situacao), 'NaN'),

            NULLIF(TRIM(viagem_urgente), 'NaN'),

            NULLIF(TRIM(codigo_orgao_superior), 'NaN'),

            NULLIF(TRIM(nome_orgao_superior), 'NaN'),

            NULLIF(TRIM(nome), 'NaN'),

            NULLIF(TRIM(cargo), 'NaN'),

            -- Datas
            TO_DATE(
                periodo_data_inicio,
                'DD/MM/YYYY'
            ),

            TO_DATE(
                periodo_data_fim,
                'DD/MM/YYYY'
            ),

            -- Outros dados textuais
            NULLIF(TRIM(destinos), 'NaN'),

            NULLIF(TRIM(motivo), 'NaN'),

            -- Valores monetários
            REPLACE(
                valor_diarias,
                ',',
                '.'
            )::DECIMAL(10,2),

            REPLACE(
                valor_passagens,
                ',',
                '.'
            )::DECIMAL(10,2),

            REPLACE(
                valor_devolucao,
                ',',
                '.'
            )::DECIMAL(10,2),

            REPLACE(
                valor_outros_gastos,
                ',',
                '.'
            )::DECIMAL(10,2),

            -- Valor total
            (
                REPLACE(valor_diarias, ',', '.')::DECIMAL(10,2)
                +
                REPLACE(valor_passagens, ',', '.')::DECIMAL(10,2)
                -
                REPLACE(valor_devolucao, ',', '.')::DECIMAL(10,2)
                +
                REPLACE(valor_outros_gastos, ',', '.')::DECIMAL(10,2)
            )::DECIMAL(12,2),

            -- Duração da viagem
            TO_DATE(
                periodo_data_fim,
                'DD/MM/YYYY'
            )
            -
            TO_DATE(
                periodo_data_inicio,
                'DD/MM/YYYY'
            )

        FROM raw_viagem;
    """

    banco.executar(conexao, sql_insert)

    print("Transformação de viagem concluída.")

def transformar_passagem(conexao):

    print("Iniciando transformação dos dados de passagem...")

    sql_insert = """
        INSERT INTO silver_passagem (
            id_viagem,
            meio_transporte,
            pais_origem_ida,
            uf_origem_ida,
            cidade_origem_ida,
            pais_destino_ida,
            uf_destino_ida,
            cidade_destino_ida,
            valor_passagem,
            taxa_servico,
            data_emissao
        )

        SELECT

            -- Chave estrangeira
            identificador_processo_viagem,

            -- Dados textuais
            NULLIF(TRIM(meio_transporte), 'NaN'),

            NULLIF(TRIM(pais_origem_ida), 'NaN'),

            NULLIF(TRIM(uf_origem_ida), 'NaN'),

            NULLIF(TRIM(cidade_origem_ida), 'NaN'),

            NULLIF(TRIM(pais_destino_ida), 'NaN'),

            NULLIF(TRIM(uf_destino_ida), 'NaN'),

            NULLIF(TRIM(cidade_destino_ida), 'NaN'),

            -- Valores monetários
            REPLACE(
                valor_passagem,
                ',',
                '.'
            )::DECIMAL(10,2),

            REPLACE(
                taxa_servico,
                ',',
                '.'
            )::DECIMAL(10,2),

            -- Data
            CASE
                WHEN TRIM(data_emissao_compra) ~ '^\\d{2}/\\d{2}/\\d{4}$'
                    THEN TO_DATE(
                        TRIM(data_emissao_compra),
                        'DD/MM/YYYY'
                    )
                ELSE NULL
            END

        FROM raw_passagem;
    """

    banco.executar(conexao, sql_insert)

    print("Transformação de passagem concluída.")

def transformar_pagamento(conexao):

    print("Iniciando transformação dos dados de pagamento...")

    sql_insert = """
        INSERT INTO silver_pagamento (
            id_viagem,
            num_proposta,
            nome_orgao_pagador,
            nome_ug_pagadora,
            tipo_pagamento,
            valor
        )

        SELECT

            -- Chave estrangeira
            identificador_processo_viagem,

            -- Dados textuais
            NULLIF(TRIM(numero_proposta_pcdp), 'NaN'),

            NULLIF(TRIM(nome_orgao_pagador), 'NaN'),

            NULLIF(TRIM(nome_unidade_gestora_pagadora), 'NaN'),

            NULLIF(TRIM(tipo_pagamento), 'NaN'),

            -- Valor monetário
            REPLACE(
                valor,
                ',',
                '.'
            )::DECIMAL(10,2)

        FROM raw_pagamento;
    """

    banco.executar(conexao, sql_insert)

    print("Transformação de pagamento concluída.")

def transformar_trecho(conexao):

    print("Iniciando transformação dos dados de trecho...")

    sql_insert = """
        INSERT INTO silver_trecho (
            id_viagem,
            sequencia_trecho,
            origem_data,
            origem_uf,
            origem_cidade,
            destino_data,
            destino_uf,
            destino_cidade,
            meio_transporte,
            numero_diarias
        )

        SELECT
            identificador_processo_viagem,

            sequencia_trecho::INT,

            CASE
                WHEN TRIM(origem_data) ~ '^\\d{2}/\\d{2}/\\d{4}$'
                THEN TO_DATE(
                    TRIM(origem_data),
                    'DD/MM/YYYY'
                )
                ELSE NULL
            END,

            NULLIF(TRIM(origem_uf), 'NaN'),

            NULLIF(TRIM(origem_cidade), 'NaN'),

            CASE
                WHEN TRIM(destino_data) ~ '^\\d{2}/\\d{2}/\\d{4}$'
                THEN TO_DATE(
                    TRIM(destino_data),
                    'DD/MM/YYYY'
                )
                ELSE NULL
            END,

            NULLIF(TRIM(destino_uf), 'NaN'),

            NULLIF(TRIM(destino_cidade), 'NaN'),

            NULLIF(TRIM(meio_transporte), 'NaN'),

            REPLACE(numero_diarias, ',', '.')::DECIMAL(10,2)

        FROM raw_trecho;
    """

    banco.executar(conexao, sql_insert)

    print("Transformação de trecho concluída.")

conexao = banco.conectar()

try:

    trunca_tabelas(conexao)

    transformar_viagem(conexao)

    transformar_passagem(conexao)

    transformar_pagamento(conexao)
    
    transformar_trecho(conexao)

    print("Dados transformados com sucesso e carregados nas tabelas Silver.")

except Exception as e:
    print(f"Erro durante a transformação: {e}")
