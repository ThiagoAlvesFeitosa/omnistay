# Contrato — avaliação e módulo `feedback`

Modelo: [data-model.md](../data-model.md).

`feedback` governa `avaliacao`. Sem HTTP nesta fatia. Sem ciclo de import com
`conversa` (orquestração no worker/`conversa`; SQL só em `feedback`).

---

## Serviço

```python
def encerrar_pulso(
    conexao,
    *,
    id_reserva: int,
    comentario: str | None,
) -> int: ...
```

INSERT `origem='pulso_segundo_dia'`, `nota` nula, `comentario` informado.
Devolve `id_avaliacao`. Segunda chamada da mesma reserva: unicidade do banco;
tratar como já encerrado (não relança, não segundo comentário).

`encerrar_pulso_em_silencio` é o mesmo INSERT — o silêncio é a ausência de
recado no chamador, não um status diferente na tabela.

---

## Leitura para a varredura / o classificar

```python
def tem_avaliacao_de_pulso(conexao, *, id_reserva: int) -> bool: ...
```

Usada com o trabalho `enviar_pulso` para decidir “aguardando resposta”.

---

## LGPD

`comentario` é DPC. Log de `feedback` e de `conversa` registra `id_reserva`,
`id_avaliacao`, origem — **nunca** o comentário.
