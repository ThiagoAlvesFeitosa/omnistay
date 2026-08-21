-- Coleta agendada: tipo coletar_mercado, unicidade do trabalho aberto e
-- semente da periodicidade. Copia congelada do delta em docs/04-schema.sql
-- (revisao 0020).

ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN (
        'enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
        'enviar_boas_vindas', 'classificar_mensagem',
        'responder_duvida', 'registrar_pedido_servico',
        'abrir_chamado_reclamacao', 'enviar_confirmacao_resolucao',
        'enviar_pulso', 'registrar_resposta_pulso',
        'enviar_pesquisa_saida', 'interpretar_pesquisa_saida',
        'enviar_lista_pedidos_chat', 'coletar_mercado'
    ));

CREATE UNIQUE INDEX uq_trabalho_coletar_mercado_concorrente_aberto
    ON trabalho ( ((payload->>'id_concorrente')::bigint) )
    WHERE tipo = 'coletar_mercado'
      AND status IN ('pendente', 'processando');

INSERT INTO parametro_hotel (id_hotel, chave, valor)
SELECT h.id_hotel, 'periodicidade_coleta_mercado', '24'
  FROM hotel h
 WHERE NOT EXISTS (
       SELECT 1 FROM parametro_hotel p
        WHERE p.id_hotel = h.id_hotel
          AND p.chave = 'periodicidade_coleta_mercado'
 );
