import { useCallback, useEffect, useState } from "react";

import { Button } from "../components/ui/button";
import { formatarInstanteComDecorrido, formatarMoeda } from "./apresentacao";
import { pedirAutenticado } from "./sessao";
import { rotuloNatureza, type ItemSolicitacao } from "./solicitacoes";

type Estado = "carregando" | "ok" | "falha";

type Props = {
  agora?: Date;
};

export function TelaChamados({ agora }: Props) {
  const [estado, setEstado] = useState<Estado>("carregando");
  const [itens, setItens] = useState<ItemSolicitacao[]>([]);
  const [avisoResolucao, setAvisoResolucao] = useState("");
  const [resolvendoId, setResolvendoId] = useState<number | null>(null);

  const atualizarItens = useCallback(async () => {
    try {
      const resposta = await pedirAutenticado("/solicitacoes");
      if (!resposta.ok) {
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as { itens?: ItemSolicitacao[] };
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

  async function resolver(idSolicitacao: number): Promise<void> {
    setResolvendoId(idSolicitacao);
    try {
      const resposta = await pedirAutenticado(`/solicitacoes/${idSolicitacao}/resolucao`, {
        method: "POST",
      });
      if (resposta.status === 409) {
        const corpo = (await resposta.json()) as { detail?: string };
        setAvisoResolucao(corpo.detail ?? "Não foi possível resolver.");
        await atualizarItens();
        return;
      }
      if (!resposta.ok) {
        setAvisoResolucao("Não foi possível resolver.");
        await atualizarItens();
        return;
      }
      setAvisoResolucao("");
      await atualizarItens();
    } finally {
      setResolvendoId(null);
    }
  }

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const instante = agora ?? new Date();
  const vazia = estado === "ok" && itens.length === 0;

  return (
    <main className="p-4">
      <h1 className="mb-4 text-xl font-semibold tracking-tight">Meus chamados</h1>

      {avisoResolucao ? (
        <p role="status" className="mb-4 text-sm text-red-800">
          {avisoResolucao}
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

      {vazia ? <p role="status">Não há pendência aberta.</p> : null}

      {estado === "ok" && itens.length > 0 ? (
        <ul className="space-y-3">
          {itens.map((linha) => (
            <li
              key={linha.id_solicitacao}
              className={
                linha.destaque_tempo_excedido
                  ? "rounded border border-red-200 bg-red-50 p-4"
                  : "rounded border border-zinc-200 bg-white p-4"
              }
            >
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                <span>{rotuloNatureza(linha.tipo)}</span>
                {" · "}
                {formatarInstanteComDecorrido(linha.aberta_em, instante)}
                {linha.destaque_tempo_excedido ? " · tempo excessivo" : ""}
              </p>
              <p className="mt-1 text-lg font-semibold">
                {linha.numero_quarto ? `Quarto ${linha.numero_quarto}` : "Sem quarto"}
              </p>
              <p className="text-sm">{linha.descricao}</p>
              {linha.janela_preferencia ? (
                <p className="text-sm text-zinc-600">{linha.janela_preferencia}</p>
              ) : null}
              {linha.tipo === "consumo" && linha.valor_praticado != null ? (
                <p className="text-sm">{formatarMoeda(linha.valor_praticado)}</p>
              ) : null}
              <Button
                type="button"
                className="mt-3 w-full"
                disabled={resolvendoId === linha.id_solicitacao}
                onClick={() => void resolver(linha.id_solicitacao)}
              >
                Resolvido
              </Button>
            </li>
          ))}
        </ul>
      ) : null}
    </main>
  );
}
