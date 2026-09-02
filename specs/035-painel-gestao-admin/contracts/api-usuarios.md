# Contrato: usuários nesta fatia

Cookie `omnistay_sessao`. Hotel só o da sessão. Operação:
`administrar_usuario` (já só gestão). Recepção e staff → `403`.

`POST /usuarios` e `DELETE /usuarios/{id}` **já existem** (F0.3).
`GET /usuarios` é **novo**. Sem `PATCH`. Sem reativar.

---

## `GET /usuarios` (novo)

Lista os funcionários da propriedade, ativos e desativados.

### Saída `200`

```json
{
  "usuarios": [
    {
      "id_usuario": 1,
      "nome": "Thiago Feitosa",
      "email": "thiago@hotel.example",
      "perfil": "gestor",
      "ativo": true
    }
  ]
}
```

Ordem: `nome`, depois `id_usuario`. Sem `senha`, sem `senha_hash`,
sem sessão. `usuarios: []` é lista vazia honesta.

---

## `POST /usuarios` (reusado)

Corpo: `nome`, `email`, `perfil` (`recepcao` · `staff` · `gestor`),
`senha` (mínimo 12). Disparado **somente** pelo controle de novo
usuário.

| Código | Efeito na tela |
| --- | --- |
| `201` | `GET /usuarios` de novo; nasce `ativo: true` |
| `409` | e-mail já cadastrado (inclusive desativado); motivo visível |
| `422` | senha curta ou perfil fora dos três; motivo visível |
| `403` | não ocorre na gestão |

A senha **não** volta no `201`.

---

## `DELETE /usuarios/{id}` (reusado)

Desativa. Não apaga. Invalida sessões daquela pessoa (já na F0.3).

| Código | Efeito na tela |
| --- | --- |
| `204` | `GET /usuarios` de novo; linha `ativo: false` |
| `409` | tentativa sobre a própria sessão; aviso; lista intacta |
| `404` | recado genérico; GET de novo |

A tela **não** oferece este controle na linha da sessão atual.

---

## Fora

- Reativar (`PATCH` / `ativo: true`)
- `GET /sessoes`, `DELETE /sessoes/{id}`
- Troca de senha de usuário existente
