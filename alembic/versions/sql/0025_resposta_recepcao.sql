-- Tipo enviar_resposta_recepcao, UNIQUE por mensagem (nao por reserva) e
-- visao da fila que apaga precisa_atendimento_humano apos resposta humana.

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
        'enviar_lista_pedidos_chat', 'coletar_mercado',
        'enviar_resposta_recepcao'
    ));

CREATE UNIQUE INDEX uq_trabalho_enviar_resposta_recepcao_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'enviar_resposta_recepcao';

COMMENT ON INDEX uq_trabalho_enviar_resposta_recepcao_mensagem IS
    'Uma mensagem, um trabalho. Varias respostas por reserva sao legitimas: '
    'nao ha UNIQUE por id_reserva neste tipo (diferente de enviar_boas_vindas).';

CREATE OR REPLACE VIEW vw_fila_do_dia AS
SELECT r.id_hotel,
       r.id_reserva,
       r.data_checkin_prevista,
       r.data_checkout_prevista,
       r.telefone_contato,
       r.status,
       h.nome_completo,
       rh.ficha_completa,
       (r.data_checkin_prevista < CURRENT_DATE
        AND r.status <> 'hospedado'
        AND r.status <> 'cancelada') AS chegada_nao_confirmada,
       m.status_envio AS status_envio_coleta,
       CASE
           WHEN r.status = 'ficha_recebida' THEN 'completa'
           WHEN r.status = 'ficha_parcial' THEN 'parcial'
           WHEN r.status = 'sem_cadastro_previo' THEN 'sem_cadastro_previo'
           WHEN r.status = 'aguardando_cadastro'
                AND EXISTS (
                    SELECT 1
                      FROM mensagem mh
                     WHERE mh.id_reserva = r.id_reserva
                       AND mh.direcao = 'recebida'
                       AND mh.classificacao_bruta->>'desfecho'
                           IN ('irreconhecivel', 'falha_extrator')
                ) THEN 'leitura_humana'
           WHEN r.status = 'aguardando_cadastro' THEN 'aguardando'
           ELSE r.status
       END AS estado_cadastro,
       (r.status = 'hospedado'
        AND NOT EXISTS (
              SELECT 1 FROM trabalho t
               WHERE t.tipo = 'enviar_boas_vindas'
                 AND (t.payload->>'id_reserva')::bigint = r.id_reserva
            )) AS boas_vindas_nao_enviadas,
       (r.status = 'hospedado'
        AND EXISTS (
              SELECT 1
                FROM mensagem mh
               WHERE mh.id_reserva = r.id_reserva
                 AND mh.direcao = 'recebida'
                 AND mh.classificacao_bruta->>'tipo' = 'classificacao_intencao'
                 AND mh.classificacao_bruta->>'desfecho'
                     IN ('encaminhado_humano', 'formato_invalido', 'indisponivel',
                         'duvida_nao_coberta', 'item_ambiguo',
                         'identificacao_indisponivel')
                 AND mh.enviada_em > COALESCE(
                       (SELECT MAX(mr.enviada_em)
                          FROM mensagem mr
                         WHERE mr.id_reserva = r.id_reserva
                           AND mr.direcao = 'enviada'
                           AND mr.classificacao_bruta->>'tipo' = 'resposta_recepcao'),
                       '-infinity'::timestamptz)
            )) AS precisa_atendimento_humano,
       (r.status = 'hospedado'
        AND r.data_checkout_prevista < CURRENT_DATE) AS saida_nao_confirmada,
       EXISTS (
              SELECT 1
                FROM mensagem mh
               WHERE mh.id_reserva = r.id_reserva
                 AND mh.direcao = 'recebida'
                 AND mh.classificacao_bruta->>'tipo' = 'pesquisa_saida'
                 AND mh.classificacao_bruta->>'desfecho'
                     IN ('irreconhecivel', 'indisponivel',
                         'formato_invalido', 'prazo_ausente')
            ) AS pesquisa_saida_leitura_humana
  FROM reserva r
  LEFT JOIN reserva_hospede rh
         ON rh.id_reserva = r.id_reserva AND rh.titular
  LEFT JOIN hospede h
         ON h.id_hospede = rh.id_hospede
  LEFT JOIN LATERAL (
        SELECT msg.status_envio
          FROM mensagem msg
         WHERE msg.id_reserva = r.id_reserva
           AND msg.direcao = 'enviada'
         ORDER BY msg.enviada_em ASC, msg.id_mensagem ASC
         LIMIT 1
       ) m ON TRUE
 WHERE r.status <> 'cancelada'
   AND r.data_checkin_prevista <= CURRENT_DATE
   AND (
        r.status <> 'encerrado'
        OR EXISTS (
              SELECT 1
                FROM mensagem mh
               WHERE mh.id_reserva = r.id_reserva
                 AND mh.direcao = 'recebida'
                 AND mh.classificacao_bruta->>'tipo' = 'pesquisa_saida'
                 AND mh.classificacao_bruta->>'desfecho'
                     IN ('irreconhecivel', 'indisponivel',
                         'formato_invalido', 'prazo_ausente')
            )
       );
