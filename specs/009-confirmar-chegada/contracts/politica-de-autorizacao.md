# Contrato — política de autorização (delta da F2.2)

`app/modulos/acesso/politica.py`. A matriz é decisão pura: sem HTTP, sem banco.

---

## Operações usadas por esta fatia

| Operação | `recepcao` | `staff` | `gestor` | Situação |
| --- | --- | --- | --- | --- |
| `confirmar_fase_da_reserva` | ✅ | ❌ | ❌ | **Já existe** desde a F0.3; primeira fatia a consumir |
| `ler_fila_do_dia` | ✅ | ❌ | ❌ | Já existe |
| `alterar_texto_de_boas_vindas` | ✅ | ❌ | ❌ | **Nova** |
| `ler_texto_de_boas_vindas` | ✅ | ❌ | ✅ | **Nova** |

O par escrita/leitura repete a forma de `alterar_catalogo` / `ler_catalogo`: a recepção
mantém, a gestão consulta, o perfil operacional não alcança.

## O que estas operações alcançam

`alterar_texto_de_boas_vindas` e `ler_texto_de_boas_vindas` cobrem **exclusivamente** as
chaves `boas_vindas_cafe`, `boas_vindas_wifi` e `boas_vindas_checkout`. O alcance é garantido
pela superfície, não por convenção: a rota grava três campos nomeados, e não existe rota que
receba chave arbitrária de `parametro_hotel`.

## O que estas operações não alcançam

| Chave | Natureza | Quem deve poder mudar |
| --- | --- | --- |
| `horas_ate_reenvio` | Comportamento do sistema com o hóspede | Gestão, em fatia futura |
| `horas_corte_antes_checkin` | Comportamento | Gestão, em fatia futura |
| `tentativas_max_envio_mensagem` | Comportamento | Gestão, em fatia futura |
| `duracao_sessao_*_horas` | Segurança de acesso | Gestão, em fatia futura |
| `contato_responsavel_dados` | Texto legal da coleta | Fatia futura |
| `periodicidade_coleta_mercado` | Comportamento | Gestão, em fatia futura |

**Nenhuma operação genérica de alterar configuração da propriedade nasce nesta fatia.** Se
existisse, a recepção herdaria por acidente o poder de mudar prazo de reenvio, janela de corte
e duração de sessão — isto é, como o sistema se comporta com o hóspede e quem continua logado.

Este é o conteúdo verificável de SC-014a: depois desta fatia, a recepção continua **sem
caminho autorizado** para alterar qualquer chave de comportamento.

## Comportamento herdado que continua valendo

- Operação desconhecida é recusada. Erro de digitação não abre porta.
- `403` distingue-se de `401`: sessão inválida é `401`; perfil sem permissão é `403`.
- `id_hotel` vem da sessão e nunca do corpo ou da URL. Slot de outro hotel não é alcançável
  por nenhuma das três rotas.

## Testes exigidos no unitário da política

1. `alterar_texto_de_boas_vindas` permitido para `recepcao`, recusado para `staff` e `gestor`.
2. `ler_texto_de_boas_vindas` permitido para `recepcao` e `gestor`, recusado para `staff`.
3. `confirmar_fase_da_reserva` permanece só para `recepcao`.
4. Nenhuma operação cujo nome contenha `parametro` existe na matriz — a asserção que impede a
   permissão genérica de reaparecer por conveniência numa fatia futura.
