# Contrato: superfície da equipe — Meus chamados

Fonte: `TelaChamados` em `/app/chamados` (casa do perfil
operacional). Casca compacta da F8.1: sem menu no cabeçalho; Sair
visível; sessão longa no mesmo aparelho.

Feita para tela de telefone: cartões, um botão por item, sem tabela
de computador, sem rolagem horizontal para achar a ação.

---

## Meus chamados (`/app/chamados`)

Título **Meus chamados**.

**Lista** — os mesmos itens do `GET /solicitacoes`, mesma ordem
(mais antigos primeiro), as três naturezas. Por cartão:

- natureza distinguível
- tempo decorrido
- quarto quando conhecido (ou ausência perceptível)
- descrição
- urgência
- janela de preferência, se houver
- valor praticado, se consumo
- destaque de tempo excessivo só quando `destaque_tempo_excedido`
- **exatamente um** `<button>` **Resolvido**

**Proibido na tela inteira:** nome, telefone, documento, endereço,
CEP, cidade, data de nascimento, profissão, **Ver ficha**, `Link`
para `/ficha/…`, `id_reserva` visível, lançar/dispensar, “extrato”,
“conta”.

Clicar descrição, quarto ou natureza **não** resolve e **não**
navega.

**Resolvido** — um clique; sem diálogo; sem campo de recado. Botão
daquele cartão indisponível até o `POST` voltar.

**Lista vazia** e **falha de leitura**: os mesmos estados distintos
da recepção (vazio explícito × não carregou + tentar de novo).
Título permanece. Compacto permanece.

**Carregando**: título visível; não fingir lista vazia.

**Recarregar** com sessão válida: continua nesta tela, novo `GET`,
sem pedir e-mail/senha (casca).

---

## O que não aparece

- Chamados e pedidos da recepção
- Fila do dia, ficha, simulador
- Abas, atribuído, canal, resolvidos do dia
- Destino `chamados` para recepção ou gestão (casca já redireciona)
