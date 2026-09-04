# Contrato: autorização (inalterada)

Esta fatia **não** acrescenta operação na matriz e **não** abre tela
que o perfil já não podia usar.

Sessão: `POST /sessoes`, `GET /sessoes/atual`, `DELETE /sessoes/atual`
como na F8.1, com o campo extra documentado em
[sessao-nome-da-casa.md](./sessao-nome-da-casa.md).

`ler_nome_hotel` não é operação de painel: é leitura interna de
`propriedade` a pedido de `acesso`, no mesmo `id_hotel` da sessão.

Gestão em catálogo / vendáveis / recado continua somente leitura na
casca. Equipe continua sem destino de ficha ou conversa. Staff/gestão
não passam a chamar `GET/POST` de conversa da Estadia.
