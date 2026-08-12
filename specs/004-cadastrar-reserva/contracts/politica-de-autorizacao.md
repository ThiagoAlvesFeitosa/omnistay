# Contrato: política de autorização (delta F1.1)

A matriz completa vive no código (`app/modulos/acesso/politica.py`) e foi introduzida na F0.3.
Esta fatia **acrescenta uma operação** (`ler_fila_do_dia`) e **liga três operações a rotas
reais**.

Documento-base da F0.3: [`specs/003-autenticacao-perfis/contracts/politica-de-autorizacao.md`](../../003-autenticacao-perfis/contracts/politica-de-autorizacao.md).

---

## Operações exercitadas agora

| Operação | `recepcao` | `staff` | `gestor` | Rota |
| --- | :---: | :---: | :---: | --- |
| `alterar_reserva` | ✅ | ❌ | ❌ | `POST /reservas` |
| `ler_fila_do_dia` | ✅ | ❌ | ❌ | `GET /fila-do-dia` (**nova** na matriz) |
| `ler_indicadores` | ✅ | ❌ | ✅ | `GET /indicadores/chegadas-do-dia` (já existia) |

`ler_fila_do_dia` existe porque a fila expõe nome e telefone do turno — só a recepção.

`ler_indicadores` na contagem existe porque a gestão precisa do **número** de chegadas para
dimensionar equipe, sem receber quem são. A lista nominada e a contagem **não compartilham
rota**: o dado cadastral não pode trafegar até o cliente da gestão “para o frontend filtrar”.

---

## Regras que os testes devem travar

1. `recepcao` → `alterar_reserva`, `ler_fila_do_dia` e `ler_indicadores` permitidos.
2. `gestor` → `ler_indicadores` permitido; `alterar_reserva` e `ler_fila_do_dia` recusados.
3. `staff` → as três recusadas.
4. Operação desconhecida continua recusada (comportamento já existente da política).
5. Resposta de `GET /indicadores/chegadas-do-dia` contém só a quantidade — asserção de contrato,
   não só de status HTTP.

A varredura de rotas protegidas da F0.3 passa a incluir as três rotas novas: sem cookie → `401`.
