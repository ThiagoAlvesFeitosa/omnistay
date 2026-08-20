-- Confirmar saida: tipos de pesquisa, unicidade, nota obrigatoria no checkout,
-- visao com destaque de saida vencida e excecao de encerrada com leitura humana.
-- Copia congelada do delta correspondente em docs/04-schema.sql (revisao 0017).

ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN (
        'enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
        'enviar_boas_vindas', 'classificar_mensagem',
        'responder_duvida', 'registrar_pedido_servico',
        'abrir_chamado_reclamacao', 'enviar_confirmacao_resolucao',
        'enviar_pulso', 'registrar_resposta_pulso',
        'enviar_pesquisa_saida', 'interpretar_pesquisa_saida'
    ));

CREATE UNIQUE INDEX uq_trabalho_enviar_pesquisa_saida_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_pesquisa_saida';

CREATE UNIQUE INDEX uq_trabalho_interpretar_pesquisa_saida_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'interpretar_pesquisa_saida';

ALTER TABLE avaliacao
    ADD CONSTRAINT ck_avaliacao_checkout_tem_nota
    CHECK (origem <> 'checkout' OR nota IS NOT NULL);

INSERT INTO parametro_hotel (id_hotel, chave, valor)
SELECT h.id_hotel, 'horas_atribuicao_pesquisa_saida', '24'
  FROM hotel h
 WHERE NOT EXISTS (
       SELECT 1 FROM parametro_hotel p
        WHERE p.id_hotel = h.id_hotel
          AND p.chave = 'horas_atribuicao_pesquisa_saida'
 );

COMMENT ON TABLE parametro_hotel IS
    'Configuracao operacional por propriedade. Chaves previstas: horas_ate_reenvio, '
    'horas_corte_antes_checkin, periodicidade_coleta_mercado, horas_minimas_para_pulso, '
    'duracao_sessao_recepcao_horas, duracao_sessao_staff_horas, duracao_sessao_gestor_horas, '
    'contato_responsavel_dados, tentativas_max_envio_mensagem, boas_vindas_cafe, '
    'boas_vindas_wifi, boas_vindas_checkout, horas_validade_boas_vindas, '
    'horas_destaque_chamado_aberto, horas_atribuicao_pesquisa_saida.';

DROP VIEW IF EXISTS vw_fila_do_dia;

CREATE VIEW vw_fila_do_dia AS
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

COMMENT ON VIEW vw_fila_do_dia IS
    'Alimenta a tela inicial do turno: check-in previsto ate hoje (chegadas do dia, '
    'atrasadas e hospedados). Reserva futura fica de fora. Encerrada so permanece '
    'quando pesquisa_saida_leitura_humana (excecao da F1.1: apos o checkout ainda '
    'pode haver leitura humana da pesquisa). A coluna chegada_nao_confirmada '
    'sinaliza divergencia temporal. Inclui telefone_contato, data_checkout_prevista, '
    'status_envio_coleta da mensagem de coleta, estado_cadastro (aguardando, '
    'completa, parcial, leitura_humana, sem_cadastro_previo), '
    'boas_vindas_nao_enviadas (hospedado sem recado), precisa_atendimento_humano '
    '(hospedado com mensagem de estadia encaminhada a pessoa), saida_nao_confirmada '
    '(hospedado com checkout previsto anterior a hoje) e '
    'pesquisa_saida_leitura_humana (resposta da pesquisa irreconhecivel, '
    'indisponivel, formato invalido ou prazo ausente).';
