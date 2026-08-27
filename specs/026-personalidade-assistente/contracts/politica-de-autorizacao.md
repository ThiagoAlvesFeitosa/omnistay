# Contrato — política de autorização (delta da F7.2)

`app/modulos/acesso/politica.py`. A matriz é decisão pura: sem HTTP, sem banco.

---

## Operações novas

| Operação | `recepcao` | `staff` | `gestor` |
| --- | --- | --- | --- |
| `ler_personalidade_assistente` | ✅ | ❌ | ✅ |
| `alterar_personalidade_assistente` | ❌ | ❌ | ✅ |

O par inverte os slots de boas-vindas: lá a recepção grava e a gestão
lê; aqui a gestão grava (comportamento + superfície de injeção) e a
recepção lê.

## Alcance

As duas operações cobrem **exclusivamente** a chave
`personalidade_assistente`. A superfície é nomeada (`/propriedade/personalidade`);
não existe rota de chave arbitrária.

`alterar_texto_de_boas_vindas` **permanece** só recepção e **não**
alcança o tom. `alterar_catalogo` não alcança o tom.

## O que não nasce

Nenhuma operação cujo nome contenha `parametro`. A asserção
`test_nenhuma_operacao_da_matriz_contem_parametro_no_nome` continua
verdadeira.

## Comportamento herdado

- Operação desconhecida é recusada
- `403` ≠ `401`
- `id_hotel` da sessão; hotel B não lê nem grava o tom de A

## Testes exigidos no unitário da política

1. `alterar_personalidade_assistente` só `gestor`
2. `ler_personalidade_assistente` para `recepcao` e `gestor`; recusado
   para `staff`
3. `alterar_texto_de_boas_vindas` continua só `recepcao`
4. Nenhuma operação contém `parametro` no nome
5. Matriz completa bate com `OPERACOES_ESPERADAS` (as duas chaves
   novas entram na tabela do teste)
