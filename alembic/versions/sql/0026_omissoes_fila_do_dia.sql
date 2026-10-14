-- Omissoes de trabalho em falha definitiva na vw_fila_do_dia.

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
            ) AS pesquisa_saida_leitura_humana,
       CASE
           WHEN r.status = 'encerrado' THEN '[]'::json
           ELSE COALESCE(
               (
                   SELECT json_agg(
                              json_build_object('tipo', falhas.tipo, 'n', falhas.n)
                              ORDER BY falhas.tipo
                          )
                     FROM (
                          SELECT t.tipo, COUNT(*)::int AS n
                            FROM trabalho t
                           WHERE t.id_hotel = r.id_hotel
                             AND t.status = 'falha'
                             AND t.payload ? 'id_reserva'
                             AND (t.payload->>'id_reserva')::bigint = r.id_reserva
                           GROUP BY t.tipo
                     ) falhas
               ),
               '[]'::json
           )
       END AS omissoes_brutas
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

COMMENT ON VIEW vw_fila_do_dia IS
    'Alimenta a tela inicial do turno: check-in previsto ate hoje (chegadas do dia, '
    'atrasadas e hospedados). Reserva futura fica de fora. Encerrada so permanece '
    'quando pesquisa_saida_leitura_humana (excecao da F1.1: apos o checkout ainda '
    'pode haver leitura humana da pesquisa). A coluna chegada_nao_confirmada '
    'sinaliza divergencia temporal. Inclui telefone_contato, data_checkout_prevista, '
    'status_envio_coleta da mensagem de coleta, estado_cadastro (aguardando, '
    'completa, parcial, leitura_humana, sem_cadastro_previo), '
    'boas_vindas_nao_enviadas (hospedado sem recado), precisa_atendimento_humano '
    '(hospedado com encaminhamento humano posterior a ultima resposta_recepcao), '
    'saida_nao_confirmada '
    '(hospedado com checkout previsto anterior a hoje), '
    'pesquisa_saida_leitura_humana (resposta da pesquisa irreconhecivel, '
    'indisponivel, formato invalido ou prazo ausente) e omissoes_brutas '
    '(JSON de trabalhos em falha definitiva ligados a id_reserva; vazio se '
    'encerrado ou se so houver coleta de mercado).';
