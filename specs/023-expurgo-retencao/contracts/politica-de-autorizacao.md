# Contrato: política de autorização — F6.1

Estende a matriz vigente. Acrescenta **uma** operação nova e a liga ao
GET do comprovante. Não acrescenta operação de disparo nem de alteração
de prazo.

A política continua decisão pura: perfil × operação, sem HTTP e sem banco.
Isolamento por hotel é ortogonal (`id_hotel` da sessão).

---

## Operações desta fatia

| Operação | `recepcao` | `staff` | `gestor` | Rotas |
| --- | :---: | :---: | :---: | --- |
| `ler_retencao` | ❌ | ❌ | ✅ | `GET /retencao` |

Não reutilizar:

| Operação existente | Por que não |
| --- | --- |
| `ler_indicadores` | A recepção lê contagem de chegadas; aqui ela é recusada |
| `ler_dado_cadastral_de_hospede` | Recepção vê ficha viva; comprovante é cumprimento da gestão |
| `ler_consentimento` | Recepção e gestão leem consentimento vigente; não é o diário de expurgo |
| `ler_mercado` | Outro depósito; não misturar |

Não nasce `disparar_retencao` nem `alterar_retencao`. Escrita HTTP é
método inexistente (`405`), não recusa de uma operação da matriz.

A passagem do worker **não** autentica perfil; opera com `id_hotel` da
linha, como as outras varreduras.

---

## Regras

- Só a gestão da **própria** propriedade lê o comprovante.
- Recepção: `403`. Retenção não é fila do dia.
- Perfil operacional: `403`. Não é chamado atribuído.
- Gestão lê só o hotel da sessão. Comprovante de outro hotel não aparece
  (filtro; não há id na URL para vazar existência).
- Gestão **não** dispara, apaga nem corrige linha de `execucao_retencao`.

---

## Recusa visível

| Situação | Resposta |
| --- | --- |
| Sem sessão válida | `401` |
| Sessão válida, perfil sem permissão | `403` |
| Qualquer escrita / disparo | `405` |

---

## Relação com “gestão somente leitura”

A FR-019 da F0.3 recusa a gestão em reserva, hóspede, solicitação, consumo
e avaliação. Esta fatia **não** abre essas escritas. O comprovante é
consulta de cumprimento, não edição de ficha.

---

## Fora desta fatia

- Tela React
- Recepção lendo o comprovante “por curiosidade”
- Disparo manual
- Edição de `meses_retencao_conteudo_livre` / `anos_retencao_ficha` pelo
  painel
