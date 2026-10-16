# Research: Cada hóspede pertence a um hotel

## 1. Onde mora o dono

**Decision**: Coluna `hospede.id_hotel BIGINT NOT NULL REFERENCES
hotel (id_hotel)`. `inserir_hospede` recebe o hotel da reserva que
está nascendo. `hospede_do_hotel` passa a ler `hospede.id_hotel`,
não o JOIN com `reserva_hospede`. Consultas de ficha já filtram
`reserva.id_hotel`; acrescentam `h.id_hotel = r.id_hotel`.

**Rationale**: Artigo XIV e ADR-009. O vínculo reserva→hóspede é
filho, não pai: hoje o hóspede só “chega” ao hotel pelo outro
sentido, e por isso o teste estrutural o reprova. Consentimento e
mensagem **não** ganham coluna (clarificação Q2).

**Alternatives considered**: Duplicar `id_hotel` em consentimento —
Artigo XI, e o pai já terá dono. Escopo só na aplicação, sem
coluna — viola Artigo IX e o teste estrutural.

## 2. Unicidade

**Decision**: Dropar `uq_hospede_documento` e recriar parcial em
`(id_hotel, tipo_documento, numero_documento) WHERE tipo e número
NOT NULL`. Mesmo recorte de hoje (sem documento = sem unicidade).
`0001` congelado; a troca é a revisão `0028`.

**Rationale**: FR-002 e FR-003. Dois hotéis, mesmo CPF: permitido.
Mesma casa: UNIQUE no banco, não só no serviço (Artigo IX).

**Alternatives considered**: UNIQUE global intacto — continua o
defeito de 18/09 entre clientes. UNIQUE só na aplicação — script
de correção fura. Incluir telefone no UNIQUE — F9.4, fora.

## 3. Aviso 409 no balcão

**Decision**: `DocumentoEmUso` carrega `nome` e `id_reserva` de
**uma** reserva titular **deste** hotel deste hóspede (a de maior
`id_reserva` que não esteja cancelada; se só canceladas, a de
maior id). Router `409` com `detail` objeto:

```json
{
  "codigo": "documento_em_uso",
  "recado": "Documento já cadastrado para Ana.",
  "nome": "Ana",
  "id_reserva": 12
}
```

Sem número de documento. A tela mostra o recado e um `Link` para
`/ficha/{id_reserva}` — o mesmo caminho da fila. Só recepção (já é
a operação `alterar_ficha_de_hospede`). Staff/gestão continuam
`403` sem nome. Hotel B nunca entra na busca.

**Rationale**: Clarificação Q1. `detail` string não dá `id_reserva`
sem parse frágil. Outros `409` do produto continuam string; só
este fica objeto. `detalheHttp` na ficha trata objeto com `recado`.

**Alternatives considered**: Só o nome — duas Marias, sem caminho.
Abrir a ficha sozinho — tira a pessoa da tela que ela estava
editando. Incluir o documento mascarado — recusado na
clarificação.

## 4. Migração 0028

**Decision**: Função pura `planejar_hospede_por_hotel` (ids de
hóspede, ids de reserva por hotel, contagem de hotéis) devolve:

| Grupo | Efeito |
| --- | --- |
| Reservas de um só hotel | `UPDATE` `id_hotel` |
| Reservas de dois ou mais | conserva a linha no hotel de menor `id_hotel`; **copia** ficha para os outros; `reserva_hospede` das reservas desses hotéis aponta para a cópia; consentimento **não** se copia |
| Sem reserva, um hotel no banco | `UPDATE` para esse hotel |
| Sem reserva, dois ou mais hotéis | ids em `orfaos`; **não** atribui |

Alembic: coluna anulável → DML → se `orfaos` não vazio, log
`hospede_migracao_orfao n=%s ids=%s` (warning, nunca documento) e
**abortar** a revisão → senão NOT NULL + índice novo. Log de
cópias não precisa listar cada id (ruído); órfãos sim.

**Rationale**: Clarificação Q3 + Artigo IX. Abortar impede esquema
com `id_hotel` nulo. Demo tem um hotel: órfãos entram nele. Cópias
respeitam “um cadastro por hotel” e “aceite não se herda”.

**Alternatives considered**: Deixar NULL nos órfãos — fura FR-001.
Apagar órfão — FR-007. Atribuir ao hotel 1 sempre — mistura
controlador. Copiar consentimento — a outra casa não registrou.

## 5. Teste estrutural (Artigo XIV)

**Decision**: Walker em `testes/suporte/artigo_xiv.py`. Para cada
tabela em `public` (exceto exceções nomeadas): tem coluna
`id_hotel` **ou** tem FK **NOT NULL** para uma tabela que já
satisfez a regra (recursivo; só o sentido filho→pai). Ser
referenciado não conta — é por isso que `hospede` hoje falha
(só `reserva_hospede` aponta para ele).

Exceções, no próprio teste, com motivo:

| Tabela | Motivo |
| --- | --- |
| `alembic_version` | Versionamento, não domínio |
| `evento_webhook` | Idempotência do canal (`id_externo`); o hotel entra no processamento |

Dois testes de integração: esquema **antes** da `0028` (ou walker
com inventário sem a coluna) lista `hospede`; `head` não lista.
Tabela nova sem dono falha o `head`.

**Rationale**: Clarificação Q2. Não exige `id_hotel` em mensagem
nem consentimento. Pega regressão futura.

**Alternatives considered**: Varredura de linhas — a clarificação
pediu estrutura. Exigir coluna em toda tabela — explode o
esquema.

## 6. Consentimento e expurgo

**Decision**: `hospede_do_hotel` pela coluna. `apagar_fichas_vencidas`
só apaga `hospede` com `id_hotel` da passagem. Relógio de checkout
continua o da F6.1, agora sem atravessar cadastro de outra casa.

**Rationale**: FR-006. Hoje o JOIN por reserva já limita; a coluna
é a garantia quando o vínculo for estranho.

**Alternatives considered**: Expurgar pelo JOIN antigo só — um
hóspede partido na migração ficaria certo, mas um cadastro
órfão atribuído ao hotel único precisa da coluna.

## 7. Coleta (WhatsApp)

**Decision**: UNIQUE por hotel vale. Esta fatia **não** cria
pendência F9.5. Colisão na consolidação continua recusa de
integridade; o worker não morre (F9.1). Sem recado nomeado no
canal (o hóspede não deve ver o nome de outro).

**Rationale**: Escopo da spec. Nomear no WhatsApp vazaria
identidade.

**Alternatives considered**: Gravar a ficha sem documento já nesta
fatia — é o coração da F9.5.
