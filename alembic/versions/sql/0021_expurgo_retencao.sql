-- Expurgo por retencao: comprovante diario, prazos semeados.
-- Copia congelada do delta em docs/04-schema.sql (revisao 0021).

CREATE TABLE execucao_retencao (
    id_execucao              BIGSERIAL    PRIMARY KEY,
    id_hotel                 BIGINT       NOT NULL REFERENCES hotel (id_hotel),
    executado_em             TIMESTAMPTZ  NOT NULL DEFAULT now(),
    mensagens_anonimizadas   INTEGER      NOT NULL DEFAULT 0,
    comentarios_anonimizados INTEGER      NOT NULL DEFAULT 0,
    payloads_anonimizados    INTEGER      NOT NULL DEFAULT 0,
    descricoes_anonimizadas  INTEGER      NOT NULL DEFAULT 0,
    fichas_apagadas          INTEGER      NOT NULL DEFAULT 0,
    prazo_conteudo_ausente   BOOLEAN      NOT NULL DEFAULT FALSE,
    prazo_ficha_ausente      BOOLEAN      NOT NULL DEFAULT FALSE,
    CONSTRAINT ck_execucao_mensagens_nao_negativas
        CHECK (mensagens_anonimizadas >= 0),
    CONSTRAINT ck_execucao_comentarios_nao_negativos
        CHECK (comentarios_anonimizados >= 0),
    CONSTRAINT ck_execucao_payloads_nao_negativos
        CHECK (payloads_anonimizados >= 0),
    CONSTRAINT ck_execucao_descricoes_nao_negativas
        CHECK (descricoes_anonimizadas >= 0),
    CONSTRAINT ck_execucao_fichas_nao_negativas
        CHECK (fichas_apagadas >= 0)
);

COMMENT ON TABLE execucao_retencao IS
    'Comprovante de uma passagem de retencao. Uma por hotel por dia civil UTC. '
    'Nao guarda texto tratado.';

CREATE UNIQUE INDEX uq_execucao_retencao_hotel_dia
    ON execucao_retencao (
        id_hotel,
        ((executado_em AT TIME ZONE 'UTC')::date)
    );

COMMENT ON TABLE parametro_hotel IS
    'Configuracao operacional por propriedade. Chaves previstas: horas_ate_reenvio, '
    'horas_corte_antes_checkin, periodicidade_coleta_mercado, horas_minimas_para_pulso, '
    'duracao_sessao_recepcao_horas, duracao_sessao_staff_horas, duracao_sessao_gestor_horas, '
    'contato_responsavel_dados, tentativas_max_envio_mensagem, boas_vindas_cafe, '
    'boas_vindas_wifi, boas_vindas_checkout, horas_validade_boas_vindas, '
    'horas_destaque_chamado_aberto, horas_atribuicao_pesquisa_saida, '
    'meses_retencao_conteudo_livre, anos_retencao_ficha.';

INSERT INTO parametro_hotel (id_hotel, chave, valor)
SELECT h.id_hotel, 'meses_retencao_conteudo_livre', '12'
  FROM hotel h
 WHERE NOT EXISTS (
       SELECT 1 FROM parametro_hotel p
        WHERE p.id_hotel = h.id_hotel
          AND p.chave = 'meses_retencao_conteudo_livre'
 );

INSERT INTO parametro_hotel (id_hotel, chave, valor)
SELECT h.id_hotel, 'anos_retencao_ficha', '5'
  FROM hotel h
 WHERE NOT EXISTS (
       SELECT 1 FROM parametro_hotel p
        WHERE p.id_hotel = h.id_hotel
          AND p.chave = 'anos_retencao_ficha'
 );
