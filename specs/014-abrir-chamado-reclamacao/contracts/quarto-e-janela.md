# Contrato: quarto, descrição e janela de preferência

Modelo: [data-model.md](../data-model.md). Serviço:
[api-de-atendimento.md](./api-de-atendimento.md).

---

## Descrição

`solicitacao.descricao` = `mensagem.conteudo` da recebida que **originou** o
chamado. Não é resumida por modelo. Não é reescrita com conhecimento geral sobre
o hotel nem convertida em taxonomia de manutenção.

Teste: a descrição gravada é igual ao texto que o hóspede enviou na origem.

A mensagem posterior que só informa o horário **não** altera `descricao`.

---

## Quarto

Reutiliza `extrair_numero_quarto(texto) -> str | None` da F3.4. Mesma tabela de
exemplos, aplicada ao texto da **origem**. Sem palavra-chave → nulo. Não
consulta reserva, PMS nem outro hotel. Chamado sem quarto **ainda** gera
confirmação e linha.

---

## Janela de preferência

Função pura `extrair_janela_preferencia(texto) -> str | None`.

| Entrada (exemplos) | Saída |
| --- | --- |
| `o ar nao gela, pode ser depois das 16h` | `depois das 16h` |
| `vazamento no banheiro as 14:30` | `14:30` |
| `ar-condicionado quebrado de manha` | `de manha` |
| `pode vir agora` | `agora` |
| `o ar nao gela` | nulo |
| `estou no 402` (sem horário) | nulo |
| texto de outra reserva / outro hotel | não se consulta; só o texto desta mensagem |

Normalização: `casefold` na busca; valor gravado é o trecho casado, até 60
caracteres. Primeiro match vence. Sem padrão → nulo. Chamado sem janela
**ainda** gera confirmação e linha, e o recado pergunta o horário.

**Proibido:** completar horário a partir de agenda da manutenção, de chamado
anterior de outra origem, de outra reserva ou de outro hóspede.

---

## Resposta posterior só de horário

Função pura `parece_resposta_de_horario(texto) -> bool`.

| Entrada | Resultado |
| --- | --- |
| `depois das 14h` | verdadeiro |
| `14h` | verdadeiro |
| `14:00` | verdadeiro |
| `de manha` | verdadeiro |
| `a noite.` | verdadeiro |
| `agora` | verdadeiro |
| `o chuveiro tambem vazou` | falso |
| `qual o wifi?` | falso |
| `o ar nao gela, 14h` | falso (mistura problema + horário) |
| ` ` | falso |

Verdadeiro → `completar_janela_se_resposta` na reclamação aberta **mais antiga
sem janela** daquela reserva (mesmo hotel). Não abre segundo chamado. Não
reenvia confirmação. Não chama LLM.

Falso → classificação normal. Nova `reclamacao_tecnica` abre chamado próprio.

Testes unitários cobrem as duas tabelas. Teste de serviço: origem sem janela →
campo nulo e pergunta no recado; origem com `depois das 16h` → campo igual e
recado **sem** pergunta; follow-up `14h` → mesmo `id_solicitacao`, janela
preenchida, zero enviada nova.
