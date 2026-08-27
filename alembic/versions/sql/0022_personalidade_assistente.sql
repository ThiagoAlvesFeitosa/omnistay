-- Personalidade da assistente: coluna larga e chave vazia por hotel.
-- Copia congelada do delta em docs/04-schema.sql (revisao 0022).

ALTER TABLE parametro_hotel ALTER COLUMN valor TYPE VARCHAR(500);

COMMENT ON TABLE parametro_hotel IS
    'Configuracao operacional por propriedade. Chaves previstas: horas_ate_reenvio, '
    'horas_corte_antes_checkin, periodicidade_coleta_mercado, horas_minimas_para_pulso, '
    'duracao_sessao_recepcao_horas, duracao_sessao_staff_horas, duracao_sessao_gestor_horas, '
    'contato_responsavel_dados, tentativas_max_envio_mensagem, boas_vindas_cafe, '
    'boas_vindas_wifi, boas_vindas_checkout, horas_validade_boas_vindas, '
    'horas_destaque_chamado_aberto, horas_atribuicao_pesquisa_saida, '
    'meses_retencao_conteudo_livre, anos_retencao_ficha, '
    'personalidade_assistente.';

INSERT INTO parametro_hotel (id_hotel, chave, valor)
SELECT h.id_hotel, 'personalidade_assistente', ''
  FROM hotel h
 WHERE NOT EXISTS (
           SELECT 1 FROM parametro_hotel p
            WHERE p.id_hotel = h.id_hotel
              AND p.chave = 'personalidade_assistente'
       );
