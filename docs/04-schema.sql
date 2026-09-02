-- =====================================================================
-- OmniStay — Hub Conversacional para Hotelaria
-- Artefato 4: script de criacao do esquema
--
-- SGBD: PostgreSQL 16
-- Autor: Thiago Alves Feitosa — Sistemas de Informacao (FIAP)
-- Versao: 1.0 — 06/08/2026
--
-- Ordem de criacao respeita as dependencias de chave estrangeira.
-- Comentarios COMMENT ON registram a classificacao LGPD de cada campo
-- sensivel, de modo que a informacao viva no banco e nao apenas no doc.
--
-- O controle de transacao e de quem aplica este arquivo, e por isso nao ha
-- BEGIN/COMMIT aqui: um COMMIT no meio fecharia a transacao da migracao
-- antes do registro de versao, deixando o banco em estado parcial.
--   Aplicacao manual:  psql --single-transaction -f docs/04-schema.sql
--   Aplicacao pelo Alembic: a revisao ja executa dentro de uma transacao.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Dominio da propriedade
-- ---------------------------------------------------------------------

CREATE TABLE hotel (
    id_hotel            BIGSERIAL    PRIMARY KEY,
    nome                VARCHAR(120) NOT NULL,
    telefone_whatsapp   VARCHAR(20)  NOT NULL,
    criado_em           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE hotel IS
    'Propriedade hoteleira. Presente desde o MVP para viabilizar multi-tenant sem migracao futura.';


CREATE TABLE usuario (
    id_usuario   BIGSERIAL    PRIMARY KEY,
    id_hotel     BIGINT       NOT NULL REFERENCES hotel (id_hotel),
    nome         VARCHAR(120) NOT NULL,
    email        VARCHAR(160) NOT NULL UNIQUE,
    senha_hash   VARCHAR(255) NOT NULL,
    perfil       VARCHAR(20)  NOT NULL,
    ativo        BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_usuario_perfil
        CHECK (perfil IN ('recepcao', 'staff', 'gestor'))
);

COMMENT ON COLUMN usuario.nome IS 'LGPD: dado pessoal (DP).';
COMMENT ON COLUMN usuario.email IS 'LGPD: dado pessoal (DP).';
COMMENT ON COLUMN usuario.senha_hash IS
    'LGPD: dado pessoal sensivel (DPS). Armazenar somente hash; nunca a senha em claro.';

CREATE INDEX ix_usuario_hotel ON usuario (id_hotel) WHERE ativo;


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


CREATE TABLE parametro_hotel (
    id_parametro BIGSERIAL    PRIMARY KEY,
    id_hotel     BIGINT       NOT NULL REFERENCES hotel (id_hotel),
    chave        VARCHAR(60)  NOT NULL,
    valor        VARCHAR(500) NOT NULL,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_parametro_hotel_chave UNIQUE (id_hotel, chave)
);

COMMENT ON TABLE parametro_hotel IS
    'Configuracao operacional por propriedade. Chaves previstas: horas_ate_reenvio, '
    'horas_corte_antes_checkin, periodicidade_coleta_mercado, horas_minimas_para_pulso, '
    'duracao_sessao_recepcao_horas, duracao_sessao_staff_horas, duracao_sessao_gestor_horas, '
    'contato_responsavel_dados, tentativas_max_envio_mensagem, boas_vindas_cafe, '
    'boas_vindas_wifi, boas_vindas_checkout, boas_vindas_convite, horas_validade_boas_vindas, '
    'horas_destaque_chamado_aberto, horas_atribuicao_pesquisa_saida, '
    'meses_retencao_conteudo_livre, anos_retencao_ficha, '
    'personalidade_assistente.';


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


CREATE TABLE catalogo_item (
    id_catalogo_item BIGSERIAL    PRIMARY KEY,
    id_hotel         BIGINT       NOT NULL REFERENCES hotel (id_hotel),
    categoria        VARCHAR(40)  NOT NULL,
    titulo           VARCHAR(160) NOT NULL,
    conteudo         TEXT         NOT NULL,
    ativo            BOOLEAN      NOT NULL DEFAULT TRUE,
    atualizado_em    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_catalogo_categoria
        CHECK (categoria IN ('horario', 'cardapio', 'servico', 'programacao', 'regra'))
);

COMMENT ON TABLE catalogo_item IS
    'Fatos da propriedade. Delimita o que a resposta automatica pode afirmar: '
    'pergunta sem correspondencia aqui escala para o ramo humano.';

CREATE INDEX ix_catalogo_hotel_categoria
    ON catalogo_item (id_hotel, categoria) WHERE ativo;


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


-- ---------------------------------------------------------------------
-- 2. Hospedagem
-- ---------------------------------------------------------------------

CREATE TABLE hospede (
    id_hospede       BIGSERIAL    PRIMARY KEY,
    nome_completo    VARCHAR(160) NOT NULL,
    profissao        VARCHAR(80),
    data_nascimento  DATE,
    tipo_documento   VARCHAR(20),
    numero_documento VARCHAR(40),
    endereco         VARCHAR(200),
    cep              VARCHAR(9),
    cidade           VARCHAR(80),
    telefone         VARCHAR(20)  NOT NULL,
    criado_em        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_hospede_tipo_documento
        CHECK (tipo_documento IS NULL
               OR tipo_documento IN ('rg', 'cpf', 'passaporte')),
    CONSTRAINT ck_hospede_nascimento_passado
        CHECK (data_nascimento IS NULL OR data_nascimento < CURRENT_DATE)
);

COMMENT ON TABLE hospede IS
    'Ficha cadastral. Retencao: 5 anos apos o checkout da ultima reserva vinculada.';
COMMENT ON COLUMN hospede.data_nascimento IS
    'LGPD: DP. A idade e derivada deste campo em exibicao e NAO e persistida, '
    'para evitar inconsistencia no dia seguinte a cada aniversario.';
COMMENT ON COLUMN hospede.numero_documento IS
    'LGPD: dado pessoal sensivel (DPS). Somente campos digitados; foto do documento '
    'nao e aceita, por minimizacao de dados.';
COMMENT ON COLUMN hospede.telefone IS
    'LGPD: DP. Chave de correlacao com as mensagens do WhatsApp.';

CREATE UNIQUE INDEX uq_hospede_documento
    ON hospede (tipo_documento, numero_documento)
    WHERE tipo_documento IS NOT NULL AND numero_documento IS NOT NULL;

CREATE INDEX ix_hospede_telefone ON hospede (telefone);


CREATE TABLE reserva (
    id_reserva             BIGSERIAL   PRIMARY KEY,
    id_hotel               BIGINT      NOT NULL REFERENCES hotel (id_hotel),
    telefone_contato       VARCHAR(20) NOT NULL,
    data_checkin_prevista  DATE        NOT NULL,
    data_checkout_prevista DATE        NOT NULL,
    status                 VARCHAR(30) NOT NULL DEFAULT 'aguardando_cadastro',
    reenvio_realizado      BOOLEAN     NOT NULL DEFAULT FALSE,
    checkin_em             TIMESTAMPTZ,
    checkout_em            TIMESTAMPTZ,
    criado_em              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_reserva_status CHECK (status IN (
        'aguardando_cadastro',
        'ficha_recebida',
        'ficha_parcial',
        'sem_cadastro_previo',
        'hospedado',
        'encerrado',
        'cancelada'
    )),
    CONSTRAINT ck_reserva_datas
        CHECK (data_checkout_prevista > data_checkin_prevista),
    CONSTRAINT ck_reserva_checkout_apos_checkin
        CHECK (checkout_em IS NULL OR checkin_em IS NULL OR checkout_em >= checkin_em),
    CONSTRAINT ck_reserva_encerrada_tem_checkin
        CHECK (status <> 'encerrado' OR checkin_em IS NOT NULL)
);

COMMENT ON COLUMN reserva.telefone_contato IS
    'LGPD: DP. Fica na reserva porque e digitado antes de existir ficha de hospede.';
COMMENT ON COLUMN reserva.reenvio_realizado IS
    'Garante o reenvio UNICO da coleta de dados. Requisito explicito de nao ser intrusivo.';
COMMENT ON CONSTRAINT ck_reserva_encerrada_tem_checkin ON reserva IS
    'Nao se faz checkout de quem nao fez check-in.';

CREATE INDEX ix_reserva_hotel_status ON reserva (id_hotel, status);
CREATE INDEX ix_reserva_checkin_previsto
    ON reserva (data_checkin_prevista)
    WHERE status <> 'cancelada';
CREATE INDEX ix_reserva_telefone ON reserva (telefone_contato);


CREATE TABLE reserva_hospede (
    id_reserva_hospede BIGSERIAL PRIMARY KEY,
    id_reserva         BIGINT    NOT NULL REFERENCES reserva (id_reserva),
    id_hospede         BIGINT    NOT NULL REFERENCES hospede (id_hospede),
    titular            BOOLEAN   NOT NULL DEFAULT FALSE,
    ficha_completa     BOOLEAN   NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_reserva_hospede UNIQUE (id_reserva, id_hospede)
);

COMMENT ON TABLE reserva_hospede IS
    'Associativa 1 reserva : N hospedes. No MVP a ficha por WhatsApp e a do titular; '
    'acompanhantes sao registrados no balcao.';

CREATE UNIQUE INDEX uq_reserva_um_titular
    ON reserva_hospede (id_reserva) WHERE titular;


CREATE TABLE consentimento (
    id_consentimento BIGSERIAL   PRIMARY KEY,
    id_hospede       BIGINT      NOT NULL REFERENCES hospede (id_hospede),
    finalidade       VARCHAR(40) NOT NULL,
    concedido        BOOLEAN     NOT NULL,
    origem           VARCHAR(40) NOT NULL,
    momento          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_consentimento_finalidade
        CHECK (finalidade IN ('comunicacao_marketing')),
    CONSTRAINT ck_consentimento_origem
        CHECK (origem IN ('pesquisa_checkout', 'painel', 'solicitacao_titular'))
);

COMMENT ON TABLE consentimento IS
    'Historico de consentimento. NUNCA atualizar uma linha: revogacao e uma nova linha '
    'com concedido = FALSE. Permite demonstrar qual era o estado em qualquer data.';

CREATE INDEX ix_consentimento_hospede
    ON consentimento (id_hospede, finalidade, momento DESC);


-- ---------------------------------------------------------------------
-- 3. Conversa
-- ---------------------------------------------------------------------

CREATE TABLE mensagem (
    id_mensagem         BIGSERIAL   PRIMARY KEY,
    id_reserva          BIGINT      NOT NULL REFERENCES reserva (id_reserva),
    direcao             VARCHAR(10) NOT NULL,
    conteudo            TEXT        NOT NULL,
    id_externo          VARCHAR(80),
    intencao            VARCHAR(40),
    sentimento          VARCHAR(20),
    urgencia            VARCHAR(20),
    classificacao_bruta JSONB,
    status_envio        VARCHAR(20),
    enviada_em          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_mensagem_direcao
        CHECK (direcao IN ('recebida', 'enviada')),
    CONSTRAINT ck_mensagem_intencao CHECK (intencao IS NULL OR intencao IN (
        'duvida_geral', 'pedido_de_servico', 'reclamacao_tecnica',
        'upsell', 'solicitacao_de_checkout', 'fora_de_escopo'
    )),
    CONSTRAINT ck_mensagem_sentimento
        CHECK (sentimento IS NULL OR sentimento IN ('positivo', 'neutro', 'negativo')),
    CONSTRAINT ck_mensagem_urgencia
        CHECK (urgencia IS NULL OR urgencia IN ('baixa', 'media', 'alta')),
    CONSTRAINT ck_mensagem_status_envio CHECK (
        status_envio IS NULL
        OR status_envio IN ('pendente', 'enviada', 'entregue', 'falha')
    ),
    CONSTRAINT ck_mensagem_enviada_tem_status
        CHECK (direcao <> 'enviada' OR status_envio IS NOT NULL)
);

COMMENT ON COLUMN mensagem.conteudo IS
    'LGPD: dado pessoal em conteudo livre (DPC). Retencao de 12 meses apos o checkout: '
    'o titular pode escrever qualquer coisa, e o conteudo nao e controlavel.';
COMMENT ON COLUMN mensagem.classificacao_bruta IS
    'Saida completa do modelo de IA, para auditoria de classificacao equivocada.';
COMMENT ON COLUMN mensagem.status_envio IS
    'Torna visivel no painel a falha de entrega — como o telefone digitado errado aparece.';
COMMENT ON COLUMN mensagem.enviada_em IS
    'Instante do registro; no sucesso do envio (status enviada) e atualizado para o '
    'momento em que a mensagem saiu — t0 do silencio da coleta.';

CREATE INDEX ix_mensagem_reserva ON mensagem (id_reserva, enviada_em DESC);
CREATE INDEX ix_mensagem_classificacao
    ON mensagem USING GIN (classificacao_bruta);


CREATE TABLE trabalho (
    id_trabalho            BIGSERIAL    PRIMARY KEY,
    id_hotel               BIGINT       NOT NULL REFERENCES hotel (id_hotel),
    tipo                   VARCHAR(40)  NOT NULL,
    payload                JSONB        NOT NULL,
    status                 VARCHAR(20)  NOT NULL DEFAULT 'pendente',
    tentativas             INTEGER      NOT NULL DEFAULT 0,
    proxima_tentativa_em   TIMESTAMPTZ,
    erro_ultima_tentativa  TEXT,
    processando_desde      TIMESTAMPTZ,
    criado_em              TIMESTAMPTZ  NOT NULL DEFAULT now(),
    atualizado_em          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_trabalho_tipo CHECK (
        tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
                 'enviar_boas_vindas', 'classificar_mensagem',
                 'responder_duvida', 'registrar_pedido_servico',
                 'abrir_chamado_reclamacao', 'enviar_confirmacao_resolucao',
                 'enviar_pulso', 'registrar_resposta_pulso',
                 'enviar_pesquisa_saida', 'interpretar_pesquisa_saida',
                 'enviar_lista_pedidos_chat', 'coletar_mercado',
                 'enviar_resposta_recepcao')
    ),
    CONSTRAINT ck_trabalho_status CHECK (
        status IN ('pendente', 'processando', 'concluido', 'falha')
    )
);

COMMENT ON TABLE trabalho IS
    'Fila duravel de trabalho assincrono. A API enfileira; o worker consome com '
    'SELECT FOR UPDATE SKIP LOCKED. Payload sem dado pessoal — so identificadores.';

CREATE UNIQUE INDEX uq_trabalho_enviar_coleta_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_coleta';

CREATE UNIQUE INDEX uq_trabalho_interpretar_ficha_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'interpretar_ficha';

CREATE UNIQUE INDEX uq_trabalho_enviar_lembrete_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_lembrete';

CREATE UNIQUE INDEX uq_trabalho_enviar_boas_vindas_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_boas_vindas';

CREATE UNIQUE INDEX uq_trabalho_classificar_mensagem_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'classificar_mensagem';

CREATE UNIQUE INDEX uq_trabalho_responder_duvida_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'responder_duvida';

CREATE UNIQUE INDEX uq_trabalho_registrar_pedido_servico_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'registrar_pedido_servico';

CREATE UNIQUE INDEX uq_trabalho_abrir_chamado_reclamacao_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'abrir_chamado_reclamacao';

CREATE UNIQUE INDEX uq_trabalho_enviar_confirmacao_resolucao_solicitacao
    ON trabalho ( ((payload->>'id_solicitacao')::bigint) )
    WHERE tipo = 'enviar_confirmacao_resolucao';

CREATE UNIQUE INDEX uq_trabalho_enviar_pulso_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_pulso';

CREATE UNIQUE INDEX uq_trabalho_registrar_resposta_pulso_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'registrar_resposta_pulso';

CREATE UNIQUE INDEX uq_trabalho_enviar_pesquisa_saida_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_pesquisa_saida';

CREATE UNIQUE INDEX uq_trabalho_interpretar_pesquisa_saida_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'interpretar_pesquisa_saida';

CREATE UNIQUE INDEX uq_trabalho_enviar_lista_pedidos_chat_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_lista_pedidos_chat';

CREATE UNIQUE INDEX uq_trabalho_coletar_mercado_concorrente_aberto
    ON trabalho ( ((payload->>'id_concorrente')::bigint) )
    WHERE tipo = 'coletar_mercado'
      AND status IN ('pendente', 'processando');

CREATE UNIQUE INDEX uq_trabalho_enviar_resposta_recepcao_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'enviar_resposta_recepcao';

COMMENT ON INDEX uq_trabalho_enviar_resposta_recepcao_mensagem IS
    'Uma mensagem, um trabalho. Varias respostas por reserva sao legitimas: '
    'nao ha UNIQUE por id_reserva neste tipo (diferente de enviar_boas_vindas).';

CREATE INDEX ix_trabalho_claim
    ON trabalho (status, proxima_tentativa_em)
    WHERE status IN ('pendente', 'processando');


CREATE TABLE evento_webhook (
    id_evento   BIGSERIAL    PRIMARY KEY,
    id_externo  VARCHAR(120) NOT NULL UNIQUE,
    payload     JSONB        NOT NULL,
    recebido_em TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE evento_webhook IS
    'Controle de idempotencia. A restricao UNIQUE em id_externo e o mecanismo inteiro: '
    'o reenvio do WhatsApp falha na insercao e e descartado sem efeito colateral.';
COMMENT ON COLUMN evento_webhook.payload IS
    'LGPD: DPC. Corpo bruto do webhook, sujeito ao mesmo prazo das mensagens.';


-- ---------------------------------------------------------------------
-- 4. Atendimento
-- ---------------------------------------------------------------------

CREATE TABLE solicitacao (
    id_solicitacao         BIGSERIAL   PRIMARY KEY,
    id_reserva             BIGINT      NOT NULL REFERENCES reserva (id_reserva),
    id_mensagem_origem     BIGINT      REFERENCES mensagem (id_mensagem),
    tipo                   VARCHAR(20) NOT NULL,
    descricao              TEXT        NOT NULL,
    numero_quarto          VARCHAR(10),
    urgencia               VARCHAR(20) NOT NULL DEFAULT 'media',
    janela_preferencia     VARCHAR(60),
    status                 VARCHAR(20) NOT NULL DEFAULT 'aberta',
    id_usuario_responsavel BIGINT      REFERENCES usuario (id_usuario),
    aberta_em              TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolvida_em           TIMESTAMPTZ,
    CONSTRAINT ck_solicitacao_tipo
        CHECK (tipo IN ('reclamacao', 'servico', 'consumo')),
    CONSTRAINT ck_solicitacao_urgencia
        CHECK (urgencia IN ('baixa', 'media', 'alta')),
    CONSTRAINT ck_solicitacao_status
        CHECK (status IN ('aberta', 'em_andamento', 'resolvida', 'cancelada')),
    CONSTRAINT ck_solicitacao_resolvida_tem_data
        CHECK (status <> 'resolvida' OR resolvida_em IS NOT NULL),
    CONSTRAINT ck_solicitacao_resolvida_tem_responsavel
        CHECK (status <> 'resolvida' OR id_usuario_responsavel IS NOT NULL)
);

COMMENT ON TABLE solicitacao IS
    'Entidade unica para reclamacao, servico operacional e consumo faturavel. '
    'Os tres compartilham todos os atributos operacionais; apenas consumo tem faturamento, '
    'que fica na tabela filha e nao como coluna nulavel aqui.';
COMMENT ON COLUMN solicitacao.descricao IS 'LGPD: DPC.';
COMMENT ON COLUMN solicitacao.numero_quarto IS
    'Texto livre: o inventario de quartos vive no PMS, fora do alcance do sistema.';
COMMENT ON COLUMN solicitacao.id_mensagem_origem IS
    'Permite auditar por que um chamado foi aberto quando a classificacao da IA errar.';

CREATE INDEX ix_solicitacao_fila
    ON solicitacao (id_reserva, status, urgencia)
    WHERE status IN ('aberta', 'em_andamento');
CREATE INDEX ix_solicitacao_abertas_antigas
    ON solicitacao (aberta_em)
    WHERE status = 'aberta';
CREATE UNIQUE INDEX uq_solicitacao_mensagem_origem
    ON solicitacao (id_mensagem_origem)
    WHERE id_mensagem_origem IS NOT NULL;


CREATE TABLE consumo (
    id_solicitacao        BIGINT         PRIMARY KEY
                                         REFERENCES solicitacao (id_solicitacao),
    descricao_item        VARCHAR(160)   NOT NULL,
    valor_praticado       NUMERIC(10, 2) NOT NULL,
    status_lancamento     VARCHAR(30)    NOT NULL DEFAULT 'pendente',
    id_usuario_lancamento BIGINT         REFERENCES usuario (id_usuario),
    lancado_em            TIMESTAMPTZ,
    CONSTRAINT ck_consumo_valor_nao_negativo
        CHECK (valor_praticado >= 0),
    CONSTRAINT ck_consumo_status
        CHECK (status_lancamento IN ('pendente', 'lancado', 'dispensado')),
    CONSTRAINT ck_consumo_terminal_tem_autor
        CHECK (status_lancamento = 'pendente'
               OR (id_usuario_lancamento IS NOT NULL AND lancado_em IS NOT NULL))
);

COMMENT ON TABLE consumo IS
    'Especializacao parcial e exclusiva de solicitacao, apenas para o tipo consumo. '
    'Chave primaria compartilhada: um consumo E uma solicitacao.';
COMMENT ON COLUMN consumo.valor_praticado IS
    'Valor do momento do pedido, nao referencia a tabela de precos. Reajuste posterior '
    'nao pode alterar o historico.';
COMMENT ON COLUMN consumo.status_lancamento IS
    'Mitigacao da quarta travessia humana: o consumo so sai da fila do painel quando '
    'alguem confirma o lancamento no PMS. Sem isso o hotel presta o servico e nao cobra.';

CREATE INDEX ix_consumo_pendente_lancamento
    ON consumo (status_lancamento) WHERE status_lancamento = 'pendente';


-- ---------------------------------------------------------------------
-- 5. Feedback e mercado
-- ---------------------------------------------------------------------

CREATE TABLE avaliacao (
    id_avaliacao   BIGSERIAL   PRIMARY KEY,
    id_reserva     BIGINT      NOT NULL REFERENCES reserva (id_reserva),
    origem         VARCHAR(20) NOT NULL,
    nota           SMALLINT,
    comentario     TEXT,
    respondida_em  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_avaliacao_origem
        CHECK (origem IN ('pulso_segundo_dia', 'checkout')),
    CONSTRAINT ck_avaliacao_nota
        CHECK (nota IS NULL OR nota BETWEEN 1 AND 5),
    CONSTRAINT ck_avaliacao_checkout_tem_nota
        CHECK (origem <> 'checkout' OR nota IS NOT NULL)
);

COMMENT ON COLUMN avaliacao.comentario IS 'LGPD: DPC.';

CREATE INDEX ix_avaliacao_reserva ON avaliacao (id_reserva);
CREATE UNIQUE INDEX uq_avaliacao_reserva_origem
    ON avaliacao (id_reserva, origem);


CREATE TABLE concorrente (
    id_concorrente BIGSERIAL    PRIMARY KEY,
    id_hotel       BIGINT       NOT NULL REFERENCES hotel (id_hotel),
    nome           VARCHAR(120) NOT NULL,
    url_fonte      VARCHAR(400) NOT NULL,
    ativo          BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_concorrente_url_fonte
        CHECK (btrim(url_fonte) ~* '^https?://[^[:space:]]+$')
);

CREATE UNIQUE INDEX uq_concorrente_hotel_fonte
    ON concorrente (id_hotel, lower(btrim(url_fonte)));

CREATE INDEX ix_concorrente_hotel_ativo
    ON concorrente (id_hotel) WHERE ativo;


CREATE TABLE coleta_mercado (
    id_coleta      BIGSERIAL      PRIMARY KEY,
    id_concorrente BIGINT         NOT NULL REFERENCES concorrente (id_concorrente),
    preco          NUMERIC(10, 2),
    nota_media     NUMERIC(3, 2),
    sucesso        BOOLEAN        NOT NULL,
    coletado_em    TIMESTAMPTZ    NOT NULL DEFAULT now(),
    CONSTRAINT ck_coleta_preco_nao_negativo
        CHECK (preco IS NULL OR preco >= 0),
    CONSTRAINT ck_coleta_nota_media
        CHECK (nota_media IS NULL OR nota_media BETWEEN 0 AND 5),
    CONSTRAINT ck_coleta_sucesso_tem_dado
        CHECK (NOT sucesso OR preco IS NOT NULL OR nota_media IS NOT NULL)
);

COMMENT ON TABLE coleta_mercado IS
    'Serie temporal: cada coleta insere uma linha, jamais atualiza a anterior. '
    'O historico de preco e o produto real do processo de inteligencia de mercado.';
COMMENT ON COLUMN coleta_mercado.sucesso IS
    'Registra a falha em vez de omiti-la. Coleta falha precisa ser distinguivel de '
    'coleta que encontrou preco zero, e o painel nao pode exibir dado velho como atual.';

CREATE INDEX ix_coleta_concorrente_data
    ON coleta_mercado (id_concorrente, coletado_em DESC);


-- ---------------------------------------------------------------------
-- 6. Validacao de transicao de estado da reserva
-- ---------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_valida_transicao_reserva()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'aguardando_cadastro' AND NEW.status IN
            ('ficha_recebida', 'ficha_parcial', 'sem_cadastro_previo', 'cancelada'))
     OR (OLD.status IN ('ficha_recebida', 'ficha_parcial', 'sem_cadastro_previo')
            AND NEW.status IN ('hospedado', 'cancelada'))
     OR (OLD.status = 'ficha_parcial' AND NEW.status = 'ficha_recebida')
     OR (OLD.status = 'ficha_recebida' AND NEW.status = 'ficha_parcial')
     OR (OLD.status = 'hospedado' AND NEW.status = 'encerrado')
    ) THEN
        RAISE EXCEPTION
            'Transicao de status invalida na reserva %: % -> %',
            OLD.id_reserva, OLD.status, NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_valida_transicao_reserva
    BEFORE UPDATE OF status ON reserva
    FOR EACH ROW
    EXECUTE FUNCTION fn_valida_transicao_reserva();

COMMENT ON FUNCTION fn_valida_transicao_reserva() IS
    'Impede corrupcao do ciclo de vida da reserva por script de correcao ou importacao. '
    'Deixar a regra apenas na aplicacao nao protege o dado.';


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


-- ---------------------------------------------------------------------
-- 7. Visao de apoio: fila do dia da recepcao
-- ---------------------------------------------------------------------

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
    '(hospedado com checkout previsto anterior a hoje) e '
    'pesquisa_saida_leitura_humana (resposta da pesquisa irreconhecivel, '
    'indisponivel, formato invalido ou prazo ausente).';
