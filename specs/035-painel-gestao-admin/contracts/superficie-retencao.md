# Contrato: superfície — Retenção de dados

Destino `/app/retencao`. Título **Retenção de dados**. Só gestão.
Computador. Sem `compacto`. Só leitura.

Um `GET /retencao` ao montar.

---

## Topo

Prazos vigentes: ficha após a saída (`anos_retencao_ficha`) e
conteúdo de conversa (`meses_retencao_conteudo_livre`). Se o
campo vier `null`, texto de prazo não configurado — **não** 5
nem 12 inventados.

Sem controle para editar prazo. Sem **expurgar agora**.

---

## Execuções

Cada linha: quando (`executado_em`); espécies e quantidades já
gravadas (mensagens, comentários, payloads, descrições, fichas);
quantidade pode ser zero.

Sem nome, telefone, documento, mensagem ou comentário de hóspede.

`execucoes: []`: ainda não houve passagem — distinto de falha.

---

## Falha

GET 5xx: falha ao ler; não fingir “nada a expurgar” nem lista
vazia.
