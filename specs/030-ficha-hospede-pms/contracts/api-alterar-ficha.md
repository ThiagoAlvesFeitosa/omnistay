# Contrato: `PUT /reservas/{id_reserva}/ficha`

Única rota HTTP **nova** desta fatia. Operação já existente:
`alterar_ficha_de_hospede` (só `recepcao`).

Autenticação e hotel: iguais ao GET da ficha. Sem `id_hotel` no corpo.

---

## Corpo

Os nove campos. Sem `idade`, sem `email`, sem `status`.

```json
{
  "nome_completo": "Marina Duarte Fonseca",
  "profissao": "Gerente de contas",
  "data_nascimento": "1992-03-14",
  "tipo_documento": "cpf",
  "numero_documento": "12345678900",
  "endereco": "Rua das Acácias, 220",
  "cep": "04567000",
  "cidade": "São Paulo",
  "telefone": "11987654321"
}
```

| Campo | Obrigatório no PUT | Ausência |
| --- | :---: | --- |
| `nome_completo` | sim (não vazio) | `422` |
| `telefone` | sim (brasileiro com DDD) | `422` |
| Demais | não | `null` ou omitido / string vazia → NULL |

Datas ISO `YYYY-MM-DD`. CEP: oito dígitos (hífen na entrada é
aceitável; persiste só dígitos, como a coleta). Tipo: `rg` \| `cpf`
\| `passaporte`.

A tela envia o estado atual do formulário (os nove), não um patch
campo a campo.

---

## Resposta `200`

O mesmo JSON do GET (`FichaTitularResposta`), já com
`ficha_completa`, `status_reserva` e `estado_cadastro` atualizados.

Zero item novo na fila de `trabalho`. Zero mensagem ao hóspede.

---

## Efeito no ciclo de vida

Ver [data-model.md](../data-model.md). Resumo:

- Nove utilizáveis + `ficha_parcial` → `ficha_recebida` +
  `ficha_completa = true`
- Falta campo + `ficha_recebida` → `ficha_parcial` + flag falsa
- `hospedado` / `sem_cadastro_previo` / `encerrado` / `cancelada`:
  campos e flag; **status intacto**

Gatilho: revisão `0024` admite só o vai-e-vem parcial ↔ recebida
além das transições já existentes.

---

## Erros

| Código | Quando | Efeito |
| --- | --- | --- |
| `401` | Sem sessão | Casca |
| `403` | Staff / gestão | Sem gravação |
| `404` | Reserva inexistente ou outro hotel | Recado genérico; sem confirmar existência |
| `422` | Formato (nascimento, tipo, CEP, telefone, nome vazio) | Nada daquele valor persistido; detalhe nomeia o campo, sem eco desnecessário do documento |
| `409` | Documento (tipo+número) já de outro hóspede | Não funde fichas |

Corrida: último `PUT` visível no GET seguinte. Sem mescla campo a
campo.

---

## O que esta rota não faz

- Enfileirar coleta, boas-vindas, pesquisa
- Alterar `reserva.telefone_contato`
- Confirmar chegada ou saída
- Aceitar arquivo / foto
- Gravar idade
