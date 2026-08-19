# Contrato: política de autorização — F3.7

Estende a matriz vigente (F0.3 … F3.6). **Nenhuma operação nova.** Esta fatia
**liga** `lancar_consumo` às rotas de lançamento e dispensa, reusa
`ler_solicitacao_atribuida` na fila destacada, reusa `resolver_solicitacao` para
tipo `consumo`, e reusa `alterar_catalogo` / `ler_catalogo` no item vendável.

---

## Superfícies

| Superfície | recepcao | operacional (`staff`) | gestao |
| --- | --- | --- | --- |
| `POST /itens-vendaveis` e `PATCH` (`alterar_catalogo`) | cria / edita / desativa | **403** | **403** |
| `GET /itens-vendaveis` (`ler_catalogo`) | lê | **403** | lê |
| `GET /solicitacoes` (`ler_solicitacao_atribuida`) | vê abertas, inclusive consumo com valor | o mesmo, **sem ficha** | o mesmo |
| `GET /consumos/pendentes` (`ler_solicitacao_atribuida`) | fila destacada | vê (entrega), **não** lança | vê, **não** lança |
| `POST .../lancamento` e `POST .../dispensa` (`lancar_consumo`) | lança / dispensa | **403** | **403** |
| `POST .../resolucao` (`resolver_solicitacao`) | resolve o quarto, inclusive consumo | o mesmo | **403** |
| `GET /fila-do-dia` | vê flag humano se identificação falhou | recusa | recusa |
| `GET /reservas/{id}/ficha` | inalterado | recusa | recusa |

Corpos `200` **não** carregam nome, telefone, documento. `id_usuario_lancamento`
é identificador de quem clicou, não ficha de hóspede.

A sessão longa do staff só permanece aceitável porque o alcance continua:
solicitações e pendências operacionais, nunca ficha. Ver o valor a entregar não
é dado cadastral. Lançar no sistema de gestão **não** é dele — é a ponte da
recepção.

Gestão consulta pendências e itens vendáveis e **não** altera consumo nem preço.

---

## Regras

- Isolamento: `id_hotel` da sessão em todo SELECT/UPDATE (join `reserva` ou
  coluna em `item_vendavel`). Hotel B recebe lista vazia ou `404`, nunca o
  dado de A.
- `403` de gestão no POST de lançamento **não** contradiz o `200` no GET de
  pendências.
- Staff autenticado no GET de pendências **não** autoriza o POST de lançamento
  nem a ficha.
- `404` para consumo de outro hotel (e para não-consumo no POST de lançamento)
  é deliberado: não distingue “não existe” de “não é sua”.
- Conteúdo da mensagem, da confirmação e da descrição nunca em log.
- Cookie de sessão do POST de lançamento não dispara envio ao hóspede.

---

## Fora desta fatia

- Operação nova na matriz
- Staff ou gestão lançarem
- Rota autenticada de histórico da conversa
- Débito no sistema de gestão do hotel (Artigo I)
