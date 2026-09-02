import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  CAMPOS_FICHA,
  camposAusentes,
  formatarDataVisivel,
  idadeDerivada,
  montarTextoCopia,
  type CamposFicha,
  type ChaveCampoFicha,
} from "./ficha";
import { pedirAutenticado } from "./sessao";
import { TelefoneInvalido, telefoneUtilizavel } from "./telefone";

type Estado = "vazio" | "carregando" | "ok" | "falha";

export type FichaResposta = CamposFicha & {
  id_reserva: number;
  id_hospede: number;
  ficha_completa: boolean;
  status_reserva: string;
  estado_cadastro: string | null;
};

type ConsentimentoResposta = {
  id_hospede: number;
  finalidade: string;
  concedido: boolean;
  momento: string | null;
  origem: string | null;
  em: string;
};

type Rascunho = Record<ChaveCampoFicha, string>;

function hojeIso(): string {
  const hoje = new Date();
  const mes = String(hoje.getMonth() + 1).padStart(2, "0");
  const dia = String(hoje.getDate()).padStart(2, "0");
  return `${hoje.getFullYear()}-${mes}-${dia}`;
}

function valorVisivel(chave: string, valor: string): string {
  if (chave === "data_nascimento") {
    return formatarDataVisivel(valor);
  }
  if (chave === "tipo_documento") {
    return valor.toUpperCase();
  }
  return valor;
}

function rascunhoDe(ficha: FichaResposta): Rascunho {
  const rascunho = {} as Rascunho;
  for (const campo of CAMPOS_FICHA) {
    rascunho[campo.chave] = ficha[campo.chave] ?? "";
  }
  return rascunho;
}

function detalheHttp(corpo: unknown): string {
  if (corpo && typeof corpo === "object" && "detail" in corpo) {
    const detalhe = (corpo as { detail: unknown }).detail;
    if (typeof detalhe === "string") {
      return detalhe;
    }
    if (Array.isArray(detalhe) && detalhe[0] && typeof detalhe[0].msg === "string") {
      return detalhe[0].msg;
    }
  }
  return "Não foi possível gravar a ficha.";
}

function dataDoMomento(iso: string): string {
  return formatarDataVisivel(iso.slice(0, 10));
}

type Props = {
  embutida?: boolean;
};

export function TelaFicha({ embutida = false }: Props) {
  const { idReserva } = useParams();
  const [estado, setEstado] = useState<Estado>(idReserva ? "carregando" : "vazio");
  const [ficha, setFicha] = useState<FichaResposta | null>(null);
  const [editando, setEditando] = useState(false);
  const [rascunho, setRascunho] = useState<Rascunho | null>(null);
  const [avisoGravacao, setAvisoGravacao] = useState("");
  const [textoCopia, setTextoCopia] = useState<string | null>(null);
  const [consentimento, setConsentimento] = useState<ConsentimentoResposta | null>(null);

  const carregar = useCallback(async () => {
    if (!idReserva) {
      setEstado("vazio");
      setFicha(null);
      setConsentimento(null);
      return;
    }
    setEstado("carregando");
    setEditando(false);
    setTextoCopia(null);
    setAvisoGravacao("");
    try {
      const resposta = await pedirAutenticado(`/reservas/${idReserva}/ficha`);
      if (!resposta.ok) {
        setFicha(null);
        setConsentimento(null);
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as FichaResposta;
      setFicha(corpo);
      setRascunho(rascunhoDe(corpo));
      setEstado("ok");
      const doConsentimento = await pedirAutenticado(
        `/hospedes/${corpo.id_hospede}/consentimento`,
      );
      if (doConsentimento.ok) {
        setConsentimento((await doConsentimento.json()) as ConsentimentoResposta);
      } else {
        setConsentimento(null);
      }
    } catch {
      setFicha(null);
      setConsentimento(null);
      setEstado("falha");
    }
  }, [idReserva]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const ausentes = ficha ? camposAusentes(ficha) : [];
  const idade = ficha ? idadeDerivada(ficha.data_nascimento, hojeIso()) : null;

  function alterarCampo(chave: ChaveCampoFicha, valor: string): void {
    setRascunho((atual) => (atual ? { ...atual, [chave]: valor } : atual));
  }

  async function gravar(evento: FormEvent): Promise<void> {
    evento.preventDefault();
    if (!idReserva || !rascunho) {
      return;
    }
    if (!telefoneUtilizavel(rascunho.telefone)) {
      setAvisoGravacao(new TelefoneInvalido().message);
      return;
    }
    const corpo = {
      nome_completo: rascunho.nome_completo.trim(),
      profissao: rascunho.profissao.trim() || null,
      data_nascimento: rascunho.data_nascimento.trim() || null,
      tipo_documento: rascunho.tipo_documento.trim() || null,
      numero_documento: rascunho.numero_documento.trim() || null,
      endereco: rascunho.endereco.trim() || null,
      cep: rascunho.cep.trim() || null,
      cidade: rascunho.cidade.trim() || null,
      telefone: rascunho.telefone.trim(),
    };
    const resposta = await pedirAutenticado(`/reservas/${idReserva}/ficha`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });
    if (!resposta.ok) {
      let detalhe = "Não foi possível gravar a ficha.";
      try {
        detalhe = detalheHttp(await resposta.json());
      } catch {
        /* corpo ilegível */
      }
      setAvisoGravacao(detalhe);
      return;
    }
    const atualizada = (await resposta.json()) as FichaResposta;
    setFicha(atualizada);
    setRascunho(rascunhoDe(atualizada));
    setEditando(false);
    setAvisoGravacao("");
  }

  function cancelar(): void {
    if (ficha) {
      setRascunho(rascunhoDe(ficha));
    }
    setEditando(false);
    setAvisoGravacao("");
  }

  async function copiarTudo(): Promise<void> {
    if (!ficha) {
      return;
    }
    const texto = montarTextoCopia(ficha);
    try {
      await navigator.clipboard.writeText(texto);
      setTextoCopia(null);
    } catch {
      setTextoCopia(texto);
    }
  }

  async function registrarConsentimento(concedido: boolean): Promise<void> {
    if (!ficha) {
      return;
    }
    const resposta = await pedirAutenticado(
      `/hospedes/${ficha.id_hospede}/consentimento`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ concedido, origem: "painel" }),
      },
    );
    if (!resposta.ok) {
      return;
    }
    setConsentimento((await resposta.json()) as ConsentimentoResposta);
  }

  return (
    <main className={embutida ? "" : "p-8"}>
      {embutida ? null : (
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-900 pb-2">
        <h1 className="text-2xl font-semibold">Ficha do hóspede</h1>
        <Link to="/fila" className="text-sm underline">
          Fila do dia
        </Link>
      </div>
      )}

      {estado === "vazio" ? (
        <p>A ficha se abre pela fila do dia ou por Chamados e pedidos.</p>
      ) : null}

      {estado === "carregando" ? (
        <p className="text-sm text-zinc-500">Carregando a ficha…</p>
      ) : null}

      {estado === "falha" ? (
        <div className="flex flex-col items-start gap-3">
          <p role="status">Não foi possível carregar a ficha.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {estado === "ok" && ficha ? (
        <div className="flex flex-col gap-4">
          <p>
            <strong>{ficha.nome_completo}</strong>
            {` · reserva #${ficha.id_reserva} · `}
            <span>{ficha.ficha_completa ? "completa" : "parcial"}</span>
          </p>
          {ficha.estado_cadastro === "leitura_humana" ? (
            <p role="status">Esta ficha precisa de leitura humana.</p>
          ) : null}
          {ausentes.length > 0 ? <p>Falta: {ausentes.join(", ")}</p> : null}

          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={() => void copiarTudo()}>
              Copiar tudo
            </Button>
            {editando ? null : (
              <Button
                type="button"
                className="border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-100"
                onClick={() => setEditando(true)}
              >
                Editar
              </Button>
            )}
          </div>

          {textoCopia ? (
            <pre className="max-w-3xl overflow-auto whitespace-pre-wrap rounded border bg-white p-3 text-sm">
              {textoCopia}
            </pre>
          ) : null}

          {editando && rascunho ? (
            <form className="flex max-w-3xl flex-col gap-3" onSubmit={(evento) => void gravar(evento)}>
              {CAMPOS_FICHA.map((campo) => (
                <div key={campo.chave}>
                  <Label htmlFor={`ficha-${campo.chave}`}>{campo.rotulo}</Label>
                  {campo.chave === "tipo_documento" ? (
                    <select
                      id={`ficha-${campo.chave}`}
                      className="flex h-9 w-full rounded-md border border-zinc-300 bg-white px-3 py-1 text-sm"
                      value={rascunho[campo.chave]}
                      onChange={(evento) => alterarCampo(campo.chave, evento.target.value)}
                    >
                      <option value="">—</option>
                      <option value="rg">RG</option>
                      <option value="cpf">CPF</option>
                      <option value="passaporte">Passaporte</option>
                    </select>
                  ) : (
                    <Input
                      id={`ficha-${campo.chave}`}
                      type={campo.chave === "data_nascimento" ? "date" : "text"}
                      value={rascunho[campo.chave]}
                      onChange={(evento) => alterarCampo(campo.chave, evento.target.value)}
                      autoComplete="off"
                    />
                  )}
                </div>
              ))}
              {avisoGravacao ? <p role="status">{avisoGravacao}</p> : null}
              <div className="flex gap-2">
                <Button type="submit">Gravar</Button>
                <Button
                  type="button"
                  className="border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-100"
                  onClick={cancelar}
                >
                  Cancelar
                </Button>
              </div>
            </form>
          ) : (
            <dl className="grid max-w-3xl grid-cols-1 gap-3 sm:grid-cols-2">
              {CAMPOS_FICHA.map((campo) => {
                const bruto = ficha[campo.chave];
                const preenchido = bruto != null && bruto.trim() !== "";
                return (
                  <div key={campo.chave}>
                    <dt className="text-xs text-zinc-500">{campo.rotulo}</dt>
                    <dd>
                      {preenchido ? valorVisivel(campo.chave, bruto) : "—"}
                      {campo.chave === "data_nascimento" && idade != null
                        ? ` (${idade} anos)`
                        : null}
                    </dd>
                  </div>
                );
              })}
            </dl>
          )}

          <section className="max-w-3xl border-t border-zinc-200 pt-4">
            <h2 className="mb-2 text-lg font-medium">Consentimento</h2>
            {consentimento == null ? null : !consentimento.momento ? (
              <div className="flex flex-col items-start gap-2">
                <p>Nunca registrado.</p>
                <Button type="button" onClick={() => void registrarConsentimento(true)}>
                  Registrar aceite
                </Button>
              </div>
            ) : consentimento.concedido ? (
              <div className="flex flex-col items-start gap-2">
                <p>Concedido em {dataDoMomento(consentimento.momento)}</p>
                <Button type="button" onClick={() => void registrarConsentimento(false)}>
                  Revogar
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-start gap-2">
                <p>Recusado em {dataDoMomento(consentimento.momento)}</p>
                <Button type="button" onClick={() => void registrarConsentimento(true)}>
                  Registrar aceite
                </Button>
              </div>
            )}
          </section>
        </div>
      ) : null}
    </main>
  );
}
