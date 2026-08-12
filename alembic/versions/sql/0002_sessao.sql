-- =====================================================================
-- OmniStay — revisao 0002: sessao do painel
--
-- Copia congelada do bloco acrescentado a docs/04-schema.sql na fatia
-- F0.3. Nao editar depois de aplicado em ambiente duravel: mudanca de
-- esquema vira revisao nova.
--
-- O controle de transacao e de quem aplica, como na revisao inicial.
-- =====================================================================

CREATE TABLE sessao (
    id_sessao   BIGSERIAL   PRIMARY KEY,
    id_usuario  BIGINT      NOT NULL REFERENCES usuario (id_usuario),
    token_hash  CHAR(64)    NOT NULL UNIQUE,
    dispositivo VARCHAR(120),
    criada_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    expira_em   TIMESTAMPTZ NOT NULL,
    revogada_em TIMESTAMPTZ,
    CONSTRAINT ck_sessao_expira_depois_de_criada
        CHECK (expira_em > criada_em),
    CONSTRAINT ck_sessao_revogada_depois_de_criada
        CHECK (revogada_em IS NULL OR revogada_em >= criada_em)
);

COMMENT ON TABLE sessao IS
    'Sessao do painel, uma linha por dispositivo autenticado. Guarda o hash do token e '
    'nunca o token: vazamento desta tabela nao equivale a vazamento de acesso. '
    'O hotel da sessao e o do usuario, por juncao — duplicar a coluna permitiria '
    'divergencia que so uma chave estrangeira composta impediria.';
COMMENT ON COLUMN sessao.token_hash IS
    'Credencial de acesso. SHA-256 do token opaco; o token existe apenas no cookie do cliente.';
COMMENT ON COLUMN sessao.dispositivo IS
    'LGPD: dado pessoal (DP) de funcionario. Rotulo informado no login ou agente do cliente.';
COMMENT ON COLUMN sessao.expira_em IS
    'Fixado na criacao a partir da duracao configurada para o perfil. Alterar a '
    'configuracao afeta as sessoes seguintes, nunca as existentes.';

CREATE INDEX ix_sessao_usuario_ativas
    ON sessao (id_usuario) WHERE revogada_em IS NULL;

-- As tres chaves de duracao de sessao entram na lista de chaves previstas.
COMMENT ON TABLE parametro_hotel IS
    'Configuracao operacional por propriedade. Chaves previstas: horas_ate_reenvio, '
    'horas_corte_antes_checkin, periodicidade_coleta_mercado, horas_minimas_para_pulso, '
    'duracao_sessao_recepcao_horas, duracao_sessao_staff_horas, duracao_sessao_gestor_horas.';
