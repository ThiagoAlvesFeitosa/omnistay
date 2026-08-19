CREATE TABLE item_vendavel (
    id_item_vendavel BIGSERIAL    PRIMARY KEY,
    id_hotel         BIGINT       NOT NULL REFERENCES hotel (id_hotel),
    nome             VARCHAR(160) NOT NULL,
    preco_atual      NUMERIC(10, 2) NOT NULL,
    ativo            BOOLEAN      NOT NULL DEFAULT TRUE,
    atualizado_em    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_item_vendavel_preco_nao_negativo
        CHECK (preco_atual >= 0)
);

COMMENT ON TABLE item_vendavel IS
    'Cadastro de item cobrado da propriedade. Fonte do preco vigente; consumo guarda '
    'retrato, sem FK para esta tabela.';
COMMENT ON COLUMN item_vendavel.preco_atual IS
    'Preco vigente. Nao entra no prompt de identificacao; o dominio le depois.';

CREATE INDEX ix_item_vendavel_hotel_ativo
    ON item_vendavel (id_hotel) WHERE ativo;

CREATE UNIQUE INDEX uq_item_vendavel_hotel_nome_ativo
    ON item_vendavel (id_hotel, lower(nome)) WHERE ativo;


ALTER TABLE consumo DROP CONSTRAINT IF EXISTS ck_consumo_lancado_tem_autor;
ALTER TABLE consumo ADD CONSTRAINT ck_consumo_terminal_tem_autor
    CHECK (status_lancamento = 'pendente'
           OR (id_usuario_lancamento IS NOT NULL AND lancado_em IS NOT NULL));


CREATE OR REPLACE FUNCTION fn_consumo_pai_tipo_consumo()
RETURNS TRIGGER AS $$
DECLARE
    tipo_pai VARCHAR(20);
BEGIN
    SELECT tipo INTO tipo_pai
      FROM solicitacao
     WHERE id_solicitacao = NEW.id_solicitacao;
    IF tipo_pai IS DISTINCT FROM 'consumo' THEN
        RAISE EXCEPTION
            'consumo exige solicitacao tipo consumo (id_solicitacao %)',
            NEW.id_solicitacao;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_consumo_pai_tipo_consumo
    BEFORE INSERT OR UPDATE ON consumo
    FOR EACH ROW
    EXECUTE FUNCTION fn_consumo_pai_tipo_consumo();

COMMENT ON FUNCTION fn_consumo_pai_tipo_consumo() IS
    'Especializacao exclusiva: linha em consumo so existe se o pai for tipo consumo.';


CREATE OR REPLACE FUNCTION fn_solicitacao_consumo_tem_filho()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tipo = 'consumo' AND NOT EXISTS (
        SELECT 1 FROM consumo WHERE id_solicitacao = NEW.id_solicitacao
    ) THEN
        RAISE EXCEPTION
            'solicitacao tipo consumo exige linha em consumo (id_solicitacao %)',
            NEW.id_solicitacao;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER tg_solicitacao_consumo_tem_filho
    AFTER INSERT ON solicitacao
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    WHEN (NEW.tipo = 'consumo')
    EXECUTE FUNCTION fn_solicitacao_consumo_tem_filho();

COMMENT ON FUNCTION fn_solicitacao_consumo_tem_filho() IS
    'Tipo consumo precisa do filho ao commit. INSERT pai+filho na mesma transacao e aceito.';


CREATE OR REPLACE FUNCTION fn_valida_transicao_lancamento()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.status_lancamento <> 'pendente' THEN
            RAISE EXCEPTION
                'consumo % deve nascer pendente, nao %',
                NEW.id_solicitacao, NEW.status_lancamento;
        END IF;
        RETURN NEW;
    END IF;

    IF OLD.status_lancamento = NEW.status_lancamento THEN
        RETURN NEW;
    END IF;

    IF NOT (
        OLD.status_lancamento = 'pendente'
        AND NEW.status_lancamento IN ('lancado', 'dispensado')
    ) THEN
        RAISE EXCEPTION
            'Transicao de lancamento invalida no consumo %: % -> %',
            NEW.id_solicitacao, OLD.status_lancamento, NEW.status_lancamento;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_valida_transicao_lancamento
    BEFORE INSERT OR UPDATE OF status_lancamento ON consumo
    FOR EACH ROW
    EXECUTE FUNCTION fn_valida_transicao_lancamento();

COMMENT ON FUNCTION fn_valida_transicao_lancamento() IS
    'Nasce pendente. So admite pendente para lancado ou dispensado. Terminal nao reabre.';


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
            )) AS precisa_atendimento_humano
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
 WHERE r.status NOT IN ('encerrado', 'cancelada')
   AND r.data_checkin_prevista <= CURRENT_DATE;

COMMENT ON VIEW vw_fila_do_dia IS
    'Alimenta a tela inicial do turno: check-in previsto ate hoje (chegadas do dia, '
    'atrasadas e hospedados). Reserva futura fica de fora. A coluna '
    'chegada_nao_confirmada sinaliza divergencia temporal. Inclui telefone_contato, '
    'data_checkout_prevista, status_envio_coleta da mensagem de coleta, '
    'estado_cadastro (aguardando, completa, parcial, leitura_humana, '
    'sem_cadastro_previo), boas_vindas_nao_enviadas (hospedado sem recado) e '
    'precisa_atendimento_humano (hospedado com mensagem de estadia encaminhada a '
    'pessoa: classificador falhou, intencao sem ramo proprio, duvida nao coberta '
    'pelo catalogo, item vendavel ambiguo ou identificacao indisponivel).';
