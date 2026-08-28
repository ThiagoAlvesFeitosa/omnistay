# Contrato — política de autorização (delta)

`app/modulos/acesso/politica.py`. A matriz **não ganha operação nova**.

---

## Operações desta fatia

| Operação | `recepcao` | `staff` | `gestor` | Situação |
| --- | --- | --- | --- | --- |
| `alterar_texto_de_boas_vindas` | ✅ | ❌ | ❌ | Já existe; passa a cobrir `boas_vindas_convite` |
| `ler_texto_de_boas_vindas` | ✅ | ❌ | ✅ | Já existe; a leitura inclui o convite |
| `confirmar_fase_da_reserva` | ✅ | ❌ | ❌ | Intocada |
| `ler_fila_do_dia` | ✅ | ❌ | ❌ | Intocada |

Nenhuma operação da matriz contém a substring `parametro`.

---

## Alcance da gravação

`alterar_texto_de_boas_vindas` alcança **somente** as quatro chaves:

- `boas_vindas_cafe`
- `boas_vindas_wifi`
- `boas_vindas_checkout`
- `boas_vindas_convite`

Não alcança `horas_validade_boas_vindas`, prazos, durações,
`personalidade_assistente` nem o aviso de assistente virtual.

---

## Testes (os que já existem continuam; acresce o convite)

1. Recepção PUT com os quatro → `200`; GET devolve o convite
2. Gestão GET → `200`; PUT → `403`; valor anterior intacto
3. Staff GET e PUT → `403`
4. Recepção continua sem caminho para alterar prazo ou personalidade
5. Hotel B não lê nem grava convite do hotel A
