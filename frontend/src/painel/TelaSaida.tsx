import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "../components/ui/button";
import { formatarMoeda } from "./apresentacao";
import { pendentesDaEstadia, type ItemConsumoPendente } from "./consumos";
import { pedirAutenticado } from "./sessao";

type Estado = "vazio" | "carregando" | "ok" | "falha" | "ausente";

type FichaResposta = {
  nome_completo: string;
  status_reserva: string;
};

type PedidoChat = {
  descricao_item: string;
  valor_praticado: string | number;
};

type PedidosResposta = {
  itens?: PedidoChat[];
  total?: number;
};

type ItemFilaDatas = {
  id_reserva: number;
  data_checkin_prevista: string;
  data_checkout_prevista: string;
};

function detalheHttp(corpo: unknown, recado: string): string {
  if (corpo && typeof corpo === "object" && "detail" in corpo) {
    const detalhe = (corpo as { detail: unknown }).detail;
    if (typeof detalhe === "string") {
      return detalhe;
    }
  }
  return recado;
}

export function TelaSaida() {
  const { idReserva } = useParams();
  const [estado, setEstado] = useState<Estado>(idReserva ? "carregando" : "vazio");
  const [ficha, setFicha] = useState<FichaResposta | null>(null);
  const [pedidos, setPedidos] = useState<PedidoChat[]>([]);
  const [total, setTotal] = useState(0);
  const [pendentes, setPendentes] = useState<ItemConsumoPendente[]>([]);
  const [datas, setDatas] = useState<ItemFilaDatas | null>(null);
  const [avisoFalha, setAvisoFalha] = useState("");
  const [avisoSaida, setAvisoSaida] = useState("");
  const [confirmando, setConfirmando] = useState(false);
  const [encerrada, setEncerrada] = useState(false);

  const carregar = useCallback(async () => {
    if (!idReserva) {
      setEstado("vazio");
      setFicha(null);
      return;
    }
    setEstado("carregando");
    setAvisoFalha("");
    setAvisoSaida("");
    try {
      const [daFicha, dosPedidos, dosPendentes, daFila] = await Promise.all([
        pedirAutenticado(`/reservas/${idReserva}/ficha`),
        pedirAutenticado(`/reservas/${idReserva}/pedidos-feitos-pelo-chat`),
        pedirAutenticado("/consumos/pendentes"),
        pedirAutenticado("/fila-do-dia"),
      ]);
      if (daFicha.status === 404 || dosPedidos.status === 404) {
        let recado = "Não foi possível carregar a saída.";
        try {
          recado = detalheHttp(await (daFicha.status === 404 ? daFicha : dosPedidos).json(), recado);
        } catch {
          /* corpo ilegível */
        }
        setFicha(null);
        setPedidos([]);
        setAvisoFalha(recado);
        setEstado("ausente");
        return;
      }
      if (!daFicha.ok || !dosPedidos.ok || !dosPendentes.ok) {
        setFicha(null);
        setPedidos([]);
        setEstado("falha");
        return;
      }
      const corpoFicha = (await daFicha.json()) as FichaResposta;
      const corpoPedidos = (await dosPedidos.json()) as PedidosResposta;
      const corpoPendentes = (await dosPendentes.json()) as { itens?: ItemConsumoPendente[] };
      setFicha(corpoFicha);
      setPedidos(Array.isArray(corpoPedidos.itens) ? corpoPedidos.itens : []);
      setTotal(typeof corpoPedidos.total === "number" ? corpoPedidos.total : 0);
      setPendentes(Array.isArray(corpoPendentes.itens) ? corpoPendentes.itens : []);
      if (daFila.ok) {
        const corpoFila = (await daFila.json()) as { itens?: ItemFilaDatas[] };
        const daEstadia = (corpoFila.itens ?? []).find(
          (linha) => String(linha.id_reserva) === String(idReserva),
        );
        setDatas(daEstadia ?? null);
      } else {
        setDatas(null);
      }
      setEstado("ok");
    } catch {
      setFicha(null);
      setPedidos([]);
      setEstado("falha");
    }
  }, [idReserva]);

  useEffect(() => {
    setEncerrada(false);
    void carregar();
  }, [carregar]);

  async function confirmarSaida(): Promise<void> {
    if (!idReserva) {
      return;
    }
    setConfirmando(true);
    try {
      const resposta = await pedirAutenticado(`/reservas/${idReserva}/saida`, {
        method: "POST",
      });
      if (resposta.status === 409) {
        const corpo = (await resposta.json()) as { detail?: string };
        setAvisoSaida(corpo.detail ?? "Não foi possível confirmar a saída.");
        return;
      }
      if (!resposta.ok) {
        setAvisoSaida("Não foi possível confirmar a saída.");
        return;
      }
      setAvisoSaida("");
      setEncerrada(true);
    } finally {
      setConfirmando(false);
    }
  }

  const idNumerico = Number(idReserva);
  const pendentesEstadia = Number.isFinite(idNumerico)
    ? pendentesDaEstadia(pendentes, idNumerico)
    : [];
  const quarto = pendentesEstadia.find((linha) => linha.numero_quarto)?.numero_quarto;
  const statusAtual = encerrada ? "encerrado" : ficha?.status_reserva;
  const podeConfirmar = estado === "ok" && statusAtual === "hospedado";

  return (
    <main className="p-8">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-900 pb-2">
        <h1 className="text-2xl font-semibold">Saída do hóspede</h1>
        <Link to="/fila" className="text-sm underline">
          Fila do dia
        </Link>
      </div>

      {estado === "vazio" ? <p>A saída se abre pela fila do dia.</p> : null}

      {estado === "carregando" ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : null}

      {estado === "falha" ? (
        <div className="flex flex-col items-start gap-3">
          <p role="status">A saída não carregou.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {estado === "ausente" ? <p role="status">{avisoFalha}</p> : null}

      {avisoSaida ? (
        <p role="status" className="mb-4 text-sm text-red-800">
          {avisoSaida}
        </p>
      ) : null}

      {estado === "ok" && ficha ? (
        <div className="flex flex-col gap-4">
          <p>
            <strong>{ficha.nome_completo}</strong>
            {quarto ? ` · Quarto ${quarto}` : ""}
            {datas
              ? ` · ${datas.data_checkin_prevista} a ${datas.data_checkout_prevista}`
              : ""}
          </p>

          {pendentesEstadia.length > 0 ? (
            <p role="status">
              Há consumo pendente de lançamento nesta estadia.{" "}
              <Link to="/consumos" className="underline">
                Consumos a lançar
              </Link>
            </p>
          ) : null}

          <section>
            <h2 className="mb-2 text-lg font-medium">Pedidos feitos pelo chat</h2>
            {pedidos.length === 0 ? (
              <p>Nenhum pedido feito pelo chat.</p>
            ) : (
              <ul className="space-y-2">
                {pedidos.map((linha, indice) => (
                  <li key={`${linha.descricao_item}-${indice}`}>
                    <span>{linha.descricao_item}</span>
                    {" · "}
                    {formatarMoeda(linha.valor_praticado)}
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-2 text-sm text-zinc-600">Total {formatarMoeda(total)}</p>
          </section>

          {podeConfirmar ? (
            <Button
              type="button"
              disabled={confirmando}
              onClick={() => void confirmarSaida()}
            >
              Confirmar saída
            </Button>
          ) : null}
        </div>
      ) : null}
    </main>
  );
}
