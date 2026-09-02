# Contrato: política de autorização (delta)

Matriz em `app/modulos/acesso/politica.py`. Teste puro da matriz
ganha as duas chaves.

| Operação | `recepcao` | `staff` | `gestor` |
| --- | :---: | :---: | :---: |
| `ler_conversa_da_estadia` | sim | não | não |
| `enviar_resposta_recepcao` | sim | não | não |
| `ler_ficha_de_hospede` | sim (intacto) | não | não |
| `ler_fila_do_dia` | sim (intacto) | não | não |

HTTP: `403` no perfil recusado, `404` na reserva alheia (não
vaza existência de conversa de outro hotel com `403` vs `404`
diferente da ficha — **mesmo recado genérico da ficha**).
