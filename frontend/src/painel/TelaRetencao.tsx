import { useCallback, useEffect, useState } from "react";

import { Button } from "../components/ui/button";
import { prazoVisivel } from "./retencao";
import { pedirAutenticado } from "./sessao";

type Estado = "carregando" | "ok" | "falha";

type Execucao = {
  id_execucao: number;
  executado_em: string;
  mensagens_anonimizadas: number;
  comentarios_anonimizados: number;
  payloads_anonimizados: number;
  descricoes_anonimizadas: number;
  fichas_apagadas: number;
};

type PainelRetencao = {
  meses_retencao_conteudo_livre: number | null;
  anos_retencao_ficha: number | null;
  execucoes: Execucao[];
};

function dataVisivel(valor: string): string {
  return valor.slice(0, 10);
}

export function TelaRetencao() {
  const [estado, setEstado] = useState<Estado>("carregando");
  const [painel, setPainel] = useState<PainelRetencao>({
    meses_retencao_conteudo_livre: null,
    anos_retencao_ficha: null,
    execucoes: [],
  });

  const carregar = useCallback(async () => {
    setEstado("carregando");
    try {
      const resposta = await pedirAutenticado("/retencao");
      if (!resposta.ok) {
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as Partial<PainelRetencao>;
      setPainel({
        meses_retencao_conteudo_livre:
          typeof corpo.meses_retencao_conteudo_livre === "number"
            ? corpo.meses_retencao_conteudo_livre
            : null,
        anos_retencao_ficha:
          typeof corpo.anos_retencao_ficha === "number" ? corpo.anos_retencao_ficha : null,
        execucoes: Array.isArray(corpo.execucoes) ? corpo.execucoes : [],
      });
      setEstado("ok");
    } catch {
      setEstado("falha");
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  return (
    <main className="p-8">
      <h1 className="mb-6 border-b border-zinc-900 pb-2 text-2xl font-semibold">
        Retenção de dados
      </h1>

      {estado === "carregando" ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : null}

      {estado === "falha" ? (
        <div className="space-y-3">
          <p role="status">O comprovante não carregou.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {estado === "ok" ? (
        <>
          <p className="mb-1 text-sm">
            Conteúdo de conversa: <span>{prazoVisivel(painel.meses_retencao_conteudo_livre)}</span>
            {typeof painel.meses_retencao_conteudo_livre === "number" ? " meses" : ""}
          </p>
          <p className="mb-6 text-sm">
            Ficha após a saída: <span>{prazoVisivel(painel.anos_retencao_ficha)}</span>
            {typeof painel.anos_retencao_ficha === "number" ? " anos" : ""}
          </p>
          {painel.execucoes.length === 0 ? (
            <p role="status">Ainda não houve passagem de retenção.</p>
          ) : (
            <ul className="space-y-3">
              {painel.execucoes.map((item) => (
                <li key={item.id_execucao} className="rounded border border-zinc-200 bg-white p-4">
                  <p className="font-medium">{dataVisivel(item.executado_em)}</p>
                  <p className="text-sm text-zinc-600">
                    Mensagens <span>{item.mensagens_anonimizadas}</span> · Comentários{" "}
                    {item.comentarios_anonimizados} · Payloads {item.payloads_anonimizados} ·
                    Descrições {item.descricoes_anonimizadas} · Fichas {item.fichas_apagadas}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </>
      ) : null}
    </main>
  );
}
