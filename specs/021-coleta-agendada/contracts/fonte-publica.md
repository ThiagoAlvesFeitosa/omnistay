# Contrato: porta `FontePublica`

O domínio de mercado **não** abre URL. Toda visita passa por esta porta.
Falso na suíte; HTTP real só no adaptador, com fixture nos testes do
adaptador — nunca contra fonte viva.

Modelo: [data-model.md](../data-model.md). Decisões: [research.md](../research.md).

---

## Identidade

Toda chamada à fonte (diretiva ou conteúdo) identifica o coletor como
**OmniStay**, de forma reconhecível, **sem** imitar navegador de pessoa
física. O falso guarda o último identificador para o teste da FR-010.

---

## `consultar_diretiva(url_fonte) -> DiretivaAcesso`

Lê a diretiva de acesso **publicada** pela fonte (o mecanismo que o próprio
sítio oferece a coletores). Não interpreta contrato jurídico em linguagem
natural.

| Valor | Significado | O domínio faz |
| --- | --- | --- |
| `permite` | Diretiva lida e compreensível **autoriza** aquele endereço | Pode chamar `coletar_publico` |
| `recusa` | Diretiva lida **proíbe** aquele endereço | Não recolhe conteúdo; coleta falha; log `diretiva_recusada` |
| `ausente` | Sem corpo, timeout, ilegível, ou não autoriza de forma compreensível | Não recolhe; coleta falha; log `diretiva_ausente` |

`ausente` **não** é permissão ampla. Divergência consciente do default
histórico de `robots.txt` (arquivo faltando = “pode tudo”).

O domínio **nunca** chama `coletar_publico` depois de `recusa` ou `ausente`.

---

## `coletar_publico(url_fonte) -> ResultadoPublico`

Só depois de `permite`. Só o que a fonte exibe **sem** autenticação.

| Campo | Conteúdo |
| --- | --- |
| `desfecho` | `encontrado` · `sem_dado` · `indisponivel` · `exige_autenticacao` |
| `preco` | Número público ≥ 0, ou nulo |
| `nota_media` | Agregada 0–5, ou nula |

Regras:

- `encontrado` exige preço e/ou nota. É o único desfecho que vira
  `sucesso = true`.
- `sem_dado`: página pública sem preço/nota extraíveis sem chute.
- `indisponivel`: rede, timeout, 5xx, bloqueio.
- `exige_autenticacao`: login, captcha, desafio. Sem credencial, sem contorno.
- Nota fora de 0–5: campo nulo (não converter). Se restar preço, ainda pode
  ser `encontrado`.
- Nome, texto, foto ou identificador de avaliador **não** saem da porta.

A porta **não** recebe nem devolve HTML para o domínio persistir.

---

## O que este contrato recusa

| Tentação | Por que não |
| --- | --- |
| LLM “interpretar” a página | Spec; número inventado |
| Biblioteca HTTP/HTML nova | Artigo XI; stdlib basta no adaptador real |
| Tratar diretiva ausente como permite | Spec FR-009 |
| User-Agent de Chrome/Firefox | Spec FR-010 |
| Teste da suíte batendo em OTA real | FR-020 |
| Devolver recortes de avaliação individual | Artigo VIII |

---

## Implementações

| Classe | Onde | Uso |
| --- | --- | --- |
| Protocolo | `app/portas/fonte_publica.py` | Domínio |
| Falsa | `app/adaptadores/fonte_falsa.py` | Suíte e worker de teste |
| HTTP | `app/adaptadores/fonte_http.py` | Produção; teste de unidade com fixture |
