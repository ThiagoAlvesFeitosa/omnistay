# Contrato: superfície — Recado de boas-vindas

Fonte: `TelaBoasVindas` em `/app/boas-vindas`.
Gestão: leitura dos quatro campos, sem **Salvar**.
Recepção: edita e salva. Staff: casca redireciona.

Recepção e gestão no computador. Sem layout de mão.

---

## Recado de boas-vindas (`/app/boas-vindas`)

Título **Recado de boas-vindas**.

**Quatro campos**, rótulos congelados, uma linha cada:

| Rótulo | Campo da API |
| --- | --- |
| Café da manhã | `cafe` |
| Wi-fi | `wifi` |
| Horário de saída | `checkout` |
| Convite | `convite` |

Não há como acrescentar, remover ou renomear campo. Aviso de
assistente virtual **não** é campo. Sem prévia com nome de
hóspede.

**Salvar** (só recepção): um gesto, os quatro valores. Não dispara
recado ao hóspede.

`200`: os inputs passam a mostrar o corpo devolvido (após `strip`
no servidor).

`422`: aviso com o `detail` da API (motivo e qual campo, sem
repetir o texto recusado). Os valores **já carregados**
permanecem. Não afirma “enviado”.

A tela **não** duplica a regra de formato (quebra de linha,
tabulação, mais de quatro espaços seguidos). A recusa visível é a
da gravação.

**Falha de leitura**: painel permanece; declara que não carregou;
**Tentar de novo**. Não mostra quatro campos vazios como se fossem
o recado da casa.

**Carregando**: título visível; não tratar campos vazios como
configuração até o `200`.

---

## O que não aparece

- Confirmar chegada
- Personalidade da assistente
- Quinto campo
- Destino para staff
