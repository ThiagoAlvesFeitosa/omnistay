import { useCallback, useEffect, useState } from "react";

import { Button } from "../components/ui/button";
import {
  linhaComFalha,
  semColeta,
  temPrecoEncontrado,
  type ItemMercado,
  type VisaoMercado,
} from "./mercado";
import { pedirAutenticado } from "./sessao";
import { formatarPreco } from "./vendaveis";

type Estado = "carregando" | "ok" | "falha";

type PontoColeta = {
  id_coleta: number;
  sucesso: boolean;
  preco: number | string | null;
  nota_media: number | string | null;
  coletado_em: string;
};

function dataVisivel(valor: string): string {
  return valor.slice(0, 10);
}

function marcaLinha(item: ItemMercado): string | null {
  if (semColeta(item)) {
    return "Ainda sem coleta";
  }
  if (item.situacao === "so_falha" || (item.situacao === "desatualizado" && linhaComFalha(item))) {
    return "Coleta falhou";
  }
  if (item.situacao === "desatualizado") {
    return "Desatualizado";
  }
  if (item.situacao === "cadencia_ausente") {
    return "Cadência não configurada";
  }
  return null;
}

export function TelaMercado() {
  const [estado, setEstado] = useState<Estado>("carregando");
  const [visao, setVisao] = useState<VisaoMercado>({
    periodicidade_horas: null,
    concorrentes: [],
  });
  const [historicoDe, setHistoricoDe] = useState<number | null>(null);
  const [pontos, setPontos] = useState<PontoColeta[] | null>(null);
  const [avisoHistorico, setAvisoHistorico] = useState("");

  const carregar = useCallback(async () => {
    setEstado("carregando");
    setAvisoHistorico("");
    try {
      const resposta = await pedirAutenticado("/mercado");
      if (!resposta.ok) {
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as VisaoMercado;
      setVisao({
        periodicidade_horas: corpo.periodicidade_horas ?? null,
        concorrentes: Array.isArray(corpo.concorrentes) ? corpo.concorrentes : [],
      });
      setEstado("ok");
    } catch {
      setEstado("falha");
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  async function abrirHistorico(item: ItemMercado): Promise<void> {
    setHistoricoDe(item.id_concorrente);
    setAvisoHistorico("");
    setPontos(null);
    try {
      const resposta = await pedirAutenticado(`/mercado/concorrentes/${item.id_concorrente}`);
      if (!resposta.ok) {
        setAvisoHistorico("O histórico não carregou.");
        return;
      }
      const corpo = (await resposta.json()) as { coletas?: PontoColeta[] };
      setPontos(Array.isArray(corpo.coletas) ? corpo.coletas : []);
    } catch {
      setAvisoHistorico("O histórico não carregou.");
    }
  }

  const vazia = estado === "ok" && visao.concorrentes.length === 0;

  return (
    <main className="p-8">
      <h1 className="mb-6 border-b border-zinc-900 pb-2 text-2xl font-semibold">Mercado</h1>

      {estado === "carregando" ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : null}

      {estado === "falha" ? (
        <div className="space-y-3">
          <p role="status">A comparação não carregou.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {vazia ? <p role="status">Não há concorrente cadastrado.</p> : null}

      {estado === "ok" && visao.concorrentes.length > 0 ? (
        <ul className="space-y-3">
          {visao.concorrentes.map((item) => {
            const marca = marcaLinha(item);
            return (
              <li key={item.id_concorrente} className="rounded border border-zinc-200 bg-white p-4">
                <p className="font-medium">
                  {item.nome}
                  {item.ativo ? null : <span className="ml-2 text-sm font-normal text-zinc-500">Inativo</span>}
                </p>
                {temPrecoEncontrado(item) && item.ultimo_sucesso ? (
                  <p className="text-sm text-zinc-700">
                    <span>{formatarPreco(item.ultimo_sucesso.preco ?? 0)}</span>
                    {" · "}
                    {dataVisivel(item.ultimo_sucesso.coletado_em)}
                    {item.ultimo_sucesso.nota_media != null
                      ? ` · nota ${item.ultimo_sucesso.nota_media}`
                      : ""}
                  </p>
                ) : null}
                {marca ? <p className="text-sm text-amber-800">{marca}</p> : null}
                {item.ultima_falha && item.situacao !== "so_falha" ? (
                  <p className="text-xs text-zinc-500">
                    Falha em {dataVisivel(item.ultima_falha.coletado_em)}
                  </p>
                ) : null}
                <Button
                  type="button"
                  className="mt-2"
                  onClick={() => void abrirHistorico(item)}
                  aria-label={`Histórico de ${item.nome}`}
                >
                  Histórico
                </Button>
              </li>
            );
          })}
        </ul>
      ) : null}

      {historicoDe != null ? (
        <section className="mt-6">
          <h2 className="mb-2 text-lg font-medium">Histórico</h2>
          {avisoHistorico ? <p role="status">{avisoHistorico}</p> : null}
          {pontos
            ? pontos.map((ponto) => (
                <p key={ponto.id_coleta} className="text-sm text-zinc-700">
                  {dataVisivel(ponto.coletado_em)}
                  {ponto.sucesso ? (
                    <>
                      {" · "}
                      <span>{ponto.preco != null ? formatarPreco(ponto.preco) : "—"}</span>
                    </>
                  ) : (
                    " · Coleta falhou"
                  )}
                </p>
              ))
            : null}
        </section>
      ) : null}
    </main>
  );
}
