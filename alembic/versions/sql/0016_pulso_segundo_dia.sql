ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN (
        'enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
        'enviar_boas_vindas', 'classificar_mensagem',
        'responder_duvida', 'registrar_pedido_servico',
        'abrir_chamado_reclamacao', 'enviar_confirmacao_resolucao',
        'enviar_pulso', 'registrar_resposta_pulso'
    ));

CREATE UNIQUE INDEX uq_trabalho_enviar_pulso_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_pulso';

CREATE UNIQUE INDEX uq_trabalho_registrar_resposta_pulso_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'registrar_resposta_pulso';

INSERT INTO parametro_hotel (id_hotel, chave, valor)
SELECT h.id_hotel, 'horas_minimas_para_pulso', '24'
  FROM hotel h
 WHERE NOT EXISTS (
       SELECT 1 FROM parametro_hotel p
        WHERE p.id_hotel = h.id_hotel
          AND p.chave = 'horas_minimas_para_pulso'
 );
