# Quickstart — validar resposta da recepção

Roteiro depois de `/speckit-implement`. Contratos na pasta
`contracts/`. Modelo: [data-model.md](./data-model.md).

Sem PMS, sem WhatsApp real na suíte.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Propriedade e três perfis como no
quickstart da F0.3 / F8.1.

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k "conversa or resposta_recepcao or fila_do_dia or fidelidade"
cd frontend
npm test
```

Pytest: janela, POST grava sem enviar, visão da fila, 403/404,
worker com gateway falso. Vitest: Estadia, fila, atalhos, casca.

O teste de conformidade do esquema (`04-schema.sql` ↔ banco)
fica vermelho na `0025` até o documento ser atualizado — os dois
saem juntos.

---

## Caminho feliz (manual, opcional)

Worker no ar (`uv run python -m worker`). Simulador em
demonstração.

1. Hóspede pergunta o que o catálogo não cobre → aviso de que a
   recepção vai atender; fila do dia com distintivo.
2. Recepção abre **Estadia**: conversa no topo, ficha recolhida.
3. Envia texto livre → histórico mostra pendente, depois
   entregue; o hóspede (simulador) recebe o mesmo texto.
4. Chamado operacional, se houver, continua aberto.
5. **ver dados cadastrais** revela a ficha; copiar permanece ali.

Janela fechada: campo visível, motivo, Enviar recusado.

Staff em `/app/ficha/:id`: casca redireciona; zero GET.
