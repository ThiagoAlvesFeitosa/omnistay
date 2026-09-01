import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "../components/ui/button";
import {
  tempoDoMaisAntigo,
  totalPendente,
  type ItemConsumoPendente,
} from "./consumos";
import { pedirAutenticado } from "./sessao";
import { tempoDecorrido } from "./solicitacoes";

type Estado = "carregando" | "ok" | "falha";

type Props = {
  agora?: Date;
};

export function TelaConsumos({ agora }: Props) {
  const [estado, setEstado] = useState<Estado>("carregando");
  const [itens, setItens] = useState<ItemConsumoPendente[]>([]);
  const [avisoAcao, setAvisoAcao] = useState("");
  const [emVooId, setEmVooId] = useState<number | null>(null);

  const atualizarItens = useCallback(async () => {
    try {
      const resposta = await pedirAutenticado("/consumos/pendentes");
      if (!resposta.ok) {
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as { itens?: ItemConsumoPendente[] };
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

  async function lancar(idSolicitacao: number): Promise<void> {
    await executarAcao(idSolicitacao, "lancamento");
  }

  async function dispensar(idSolicitacao: number): Promise<void> {
    await executarAcao(idSolicitacao, "dispensa");
  }

  async function executarAcao(
    idSolicitacao: number,
    acao: "lancamento" | "dispensa",
  ): Promise<void> {
    setEmVooId(idSolicitacao);
    try {
      const resposta = await pedirAutenticado(`/solicitacoes/${idSolicitacao}/${acao}`, {
        method: "POST",
      });
      if (resposta.status === 409) {
        const corpo = (await resposta.json()) as { detail?: string };
        setAvisoAcao(corpo.detail ?? "Não foi possível concluir.");
        await atualizarItens();
        return;
      }
      if (!resposta.ok) {
        setAvisoAcao("Não foi possível concluir.");
        await atualizarItens();
        return;
      }
      setAvisoAcao("");
      await atualizarItens();
    } finally {
      setEmVooId(null);
    }
  }

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const instante = agora ?? new Date();
  const vazia = estado === "ok" && itens.length === 0;
  const total = totalPendente(itens);
  const maisAntigo = tempoDoMaisAntigo(itens, instante);

  return (
    <main className="p-8">
      <h1 className="mb-4 border-b border-zinc-900 pb-2 text-2xl font-semibold">
        Consumos a lançar
      </h1>

      {avisoAcao ? (
        <p role="status" className="mb-4 text-sm text-red-800">
          {avisoAcao}
        </p>
      ) : null}

      {estado === "carregando" ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : null}

      {estado === "falha" ? (
        <div className="space-y-3">
          <p role="status">A lista não carregou.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {estado === "ok" ? (
        <p className="mb-4 text-sm text-zinc-600">
          {itens.length} pendentes · R$ {total}
          {maisAntigo ? ` · o mais antigo ${maisAntigo}` : ""}
        </p>
      ) : null}

      {vazia ? <p role="status">Não há consumo a lançar.</p> : null}

      {estado === "ok" && itens.length > 0 ? (
        <ul className="space-y-3">
          {itens.map((linha) => (
            <li key={linha.id_solicitacao} className="rounded border border-zinc-200 bg-white p-4">
              <p className="font-medium">{linha.descricao_item}</p>
              <p className="text-sm text-zinc-600">
                {linha.numero_quarto ? `Quarto ${linha.numero_quarto}` : "Sem quarto"}
                {" · "}
                {tempoDecorrido(linha.aberta_em, instante)}
              </p>
              <p className="text-sm">R$ {linha.valor_praticado}</p>
              <div className="mt-3 flex flex-wrap items-center gap-4">
                <Link to={`/ficha/${linha.id_reserva}`} className="text-sm underline">
                  Ver ficha
                </Link>
                <Button
                  type="button"
                  disabled={emVooId === linha.id_solicitacao}
                  onClick={() => void lancar(linha.id_solicitacao)}
                >
                  Marcar lançado
                </Button>
                <Button
                  type="button"
                  className="border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-100"
                  disabled={emVooId === linha.id_solicitacao}
                  onClick={() => void dispensar(linha.id_solicitacao)}
                >
                  Dispensar
                </Button>
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </main>
  );
}
