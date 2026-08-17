# Contrato: política de autorização — F2.1

Estende a matriz vigente. Acrescenta **uma** operação nova e **liga** a escrita do
catálogo a rotas.

A política continua decisão pura: perfil × operação, sem HTTP e sem banco. Isolamento
por hotel é ortogonal (`id_hotel` da sessão; alvo alheio → `404`).

---

## Operações desta fatia

| Operação | `recepcao` | `staff` | `gestor` | Rotas |
| --- | :---: | :---: | :---: | --- |
| `alterar_catalogo` | ✅ | ❌ | ❌ | `POST /catalogo`, `PATCH /catalogo/{id}` |
| `ler_catalogo` | ✅ | ❌ | ✅ | `GET /catalogo`, `GET /catalogo/ativo` |

`alterar_catalogo` já existia na matriz da F0.3 sem rota. `ler_catalogo` **não** existia:
sem ela, a gestão não consulta (FR-015) ou o GET reusaria a operação de escrita.

---

## Regras

- Gestão lê manutenção e catálogo ativo da **própria** propriedade; qualquer escrita →
  `403`.
- Perfil operacional: `403` em leitura e escrita. Catálogo não é chamado atribuído.
- Recepção escreve só no hotel da sessão. Id de outro hotel → `404`.
- Worker futuro (F2.2) não autentica perfil para ler a porta; opera com `id_hotel` da
  reserva. Fora desta fatia.

---

## Recusa visível

| Situação | Resposta |
| --- | --- |
| Sem sessão válida | `401` |
| Sessão válida, perfil sem permissão | `403` |
| Sessão válida, item de outro hotel ou id inexistente | `404` |

---

## Fora desta fatia

- Tela React de manutenção
- `staff` lendo catálogo para executar serviço (não pedido)
- Gestão alterando catálogo (spec confirmou a F0.3)
