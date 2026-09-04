import { useCallback, useEffect, useState } from "react";

import { Button } from "../components/ui/button";
import { formatarMoeda } from "./apresentacao";
import { CAMPOS_INDICADORES, type IndicadoresOperacao } from "./indicadores";
import { pedirAutenticado } from "./sessao";

type Estado = "carregando" | "ok" | "falha";

const ROTULOS: Record<(typeof CAMPOS_INDICADORES)[number], string> = {
  chegadas_hoje: "Chegadas hoje",
  hospedados: "Hospedados",
  chamados_abertos: "Chamados em aberto",
  consumo_a_lancar: "Consumo a lançar",
};

const vazio: IndicadoresOperacao = {
  chegadas_hoje: 0,
  hospedados: 0,
  chamados_abertos: 0,
  consumo_a_lancar: 0,
};

function lerNumero(valor: unknown): number {
  const n = typeof valor === "number" ? valor : Number(valor);
  return Number.isFinite(n) ? n : 0;
}

export function TelaPainel() {
  const [estado, setEstado] = useState<Estado>("carregando");
  const [numeros, setNumeros] = useState<IndicadoresOperacao>(vazio);

  const carregar = useCallback(async () => {
    setEstado("carregando");
    try {
      const resposta = await pedirAutenticado("/indicadores");
      if (!resposta.ok) {
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as Partial<IndicadoresOperacao>;
      setNumeros({
        chegadas_hoje: lerNumero(corpo.chegadas_hoje),
        hospedados: lerNumero(corpo.hospedados),
        chamados_abertos: lerNumero(corpo.chamados_abertos),
        consumo_a_lancar: lerNumero(corpo.consumo_a_lancar),
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
      <h1 className="mb-6 border-b border-zinc-900 pb-2 text-2xl font-semibold">Painel</h1>

      {estado === "carregando" ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : null}

      {estado === "falha" ? (
        <div className="space-y-3">
          <p role="status">Os números não carregaram.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {estado === "ok" ? (
        <dl className="grid max-w-xl grid-cols-1 gap-4 sm:grid-cols-2">
          {CAMPOS_INDICADORES.map((campo) => (
            <div key={campo} className="rounded border border-zinc-200 bg-white p-4">
              <dt className="text-sm text-zinc-600">{ROTULOS[campo]}</dt>
              <dd className="mt-1 text-2xl font-semibold">
                {campo === "consumo_a_lancar"
                  ? formatarMoeda(numeros[campo])
                  : numeros[campo]}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
    </main>
  );
}
