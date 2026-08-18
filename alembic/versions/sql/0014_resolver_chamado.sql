-- Resolver chamado: tipo de trabalho, unicidade, transicao e autor.
-- Copia congelada do delta correspondente em docs/04-schema.sql (revisao 0014).

ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
                    'enviar_boas_vindas', 'classificar_mensagem',
                    'responder_duvida', 'registrar_pedido_servico',
                    'abrir_chamado_reclamacao', 'enviar_confirmacao_resolucao'));

CREATE UNIQUE INDEX uq_trabalho_enviar_confirmacao_resolucao_solicitacao
    ON trabalho ( ((payload->>'id_solicitacao')::bigint) )
    WHERE tipo = 'enviar_confirmacao_resolucao';

ALTER TABLE solicitacao
    ADD CONSTRAINT ck_solicitacao_resolvida_tem_responsavel
    CHECK (status <> 'resolvida' OR id_usuario_responsavel IS NOT NULL);

CREATE OR REPLACE FUNCTION fn_valida_transicao_solicitacao()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        OLD.status IN ('aberta', 'em_andamento') AND NEW.status = 'resolvida'
    ) THEN
        RAISE EXCEPTION
            'Transicao de status invalida na solicitacao %: % -> %',
            OLD.id_solicitacao, OLD.status, NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_valida_transicao_solicitacao
    BEFORE UPDATE OF status ON solicitacao
    FOR EACH ROW
    EXECUTE FUNCTION fn_valida_transicao_solicitacao();

COMMENT ON FUNCTION fn_valida_transicao_solicitacao() IS
    'Nesta fatia so admite aberta ou em_andamento para resolvida. '
    'Reabrir ou cancelar pelo banco e recusado; a aplicacao devolve 409.';
