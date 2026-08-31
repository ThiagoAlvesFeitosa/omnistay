import { useCallback, useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { Button } from "../components/ui/button";
import { cn } from "../lib/utils";
import { pedirAutenticado } from "./sessao";
import { chegadaAdmiteBotao, resumirTurno, type ItemFila } from "./fila";

type Estado = "carregando" | "ok" | "falha";

export function TelaFila() {
  const local = useLocation();
  const avisoNavegacao = (local.state as { aviso?: string } | null)?.aviso;
  const [estado, setEstado] = useState<Estado>("carregando");
  const [itens, setItens] = useState<ItemFila[]>([]);

  const [avisoChegada, setAvisoChegada] = useState("");

  const atualizarItens = useCallback(async () => {
    try {
      const resposta = await pedirAutenticado("/fila-do-dia");
      if (!resposta.ok) {
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as { itens?: ItemFila[] };
      setItens(Array.isArray(corpo.itens) ? corpo.itens : []);
      setEstado("ok");
    } catch {
      setEstado("falha");
    }
  }, []);

  const carregar = useCallback(async () => {
    setEstado("carregando");
    await atualizarItens();
  }, [atualizarItens]);

  async function confirmarChegada(idReserva: number): Promise<void> {
    const resposta = await pedirAutenticado(`/reservas/${idReserva}/chegada`, {
      method: "POST",
    });
    if (resposta.status === 409) {
      const corpo = (await resposta.json()) as { detail?: string };
      setAvisoChegada(corpo.detail ?? "Não foi possível confirmar a chegada.");
      await atualizarItens();
      return;
    }
    if (!resposta.ok) {
      setAvisoChegada("Não foi possível confirmar a chegada.");
      await atualizarItens();
      return;
    }
    setAvisoChegada("");
    await atualizarItens();
  }

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const resumo = resumirTurno(itens);
  const vazia = estado === "ok" && itens.length === 0;

  return (
    <main className="p-8">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-900 pb-2">
        <h1 className="text-2xl font-semibold">Fila do dia</h1>
        <Link
          to="/reserva"
          className={cn(
            "inline-flex items-center justify-center rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800",
          )}
        >
          Nova reserva
        </Link>
      </div>

      {avisoNavegacao ? (
        <p role="status" className="mb-4 rounded border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm">
          {avisoNavegacao}
        </p>
      ) : null}

      {avisoChegada ? (
        <p role="status" className="mb-4 rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm">
          {avisoChegada}
        </p>
      ) : null}

      {estado === "ok" ? (
        <p className="mb-4 text-sm text-zinc-600">
          <span>{resumo.hoje} hoje sem confirmar</span>
          {" · "}
          <span>{resumo.hospedados} hospedados</span>
          {" · "}
          <span>{resumo.vencidas} entrada vencida</span>
        </p>
      ) : null}

      {estado === "carregando" ? (
        <p className="text-sm text-zinc-500">Carregando a fila…</p>
      ) : null}

      {estado === "falha" ? (
        <div className="flex flex-col items-start gap-3">
          <p role="status">Não foi possível carregar a fila.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {vazia ? <p>Ninguém no turno hoje.</p> : null}

      {estado === "ok" && itens.length > 0 ? (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2">Hóspede</th>
              <th>Entrada</th>
              <th>Saída</th>
              <th>Situação</th>
              <th>Ficha</th>
              <th className="text-right">Ação</th>
            </tr>
          </thead>
          <tbody>
            {itens.map((linha) => (
              <tr key={linha.id_reserva} className="border-b">
                <td className="py-2">
                  <strong>{linha.nome}</strong>
                  <br />
                  <span className="text-zinc-500">{linha.telefone_contato}</span>
                </td>
                <td>{linha.data_checkin_prevista}</td>
                <td>{linha.data_checkout_prevista}</td>
                <td>
                  {rotuloSituacao(linha.status)}
                  {linha.chegada_nao_confirmada ? (
                    <span className="ml-2 rounded bg-red-100 px-1.5 py-0.5 text-red-800">
                      não confirmada
                    </span>
                  ) : null}
                  {linha.boas_vindas_nao_enviadas ? (
                    <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-amber-900">
                      recado não enviado
                    </span>
                  ) : null}
                </td>
                <td>
                  {linha.estado_cadastro === "parcial" ? (
                    <span className="rounded bg-zinc-200 px-1.5 py-0.5">parcial</span>
                  ) : (
                    (linha.estado_cadastro ?? "—")
                  )}
                </td>
                <td className="text-right">
                  {chegadaAdmiteBotao(linha.status) ? (
                    <Button type="button" onClick={() => void confirmarChegada(linha.id_reserva)}>
                      Confirmar chegada
                    </Button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </main>
  );
}

function rotuloSituacao(status: string): string {
  switch (status) {
    case "aguardando_cadastro":
      return "aguardando cadastro";
    case "ficha_recebida":
      return "ficha recebida";
    case "ficha_parcial":
      return "ficha parcial";
    case "sem_cadastro_previo":
      return "chegará sem cadastro prévio";
    case "hospedado":
      return "hospedado";
    default:
      return status;
  }
}
