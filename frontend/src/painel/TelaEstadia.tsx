import { FormEvent, KeyboardEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "../components/ui/button";
import { pedirAutenticado } from "./sessao";
import { TelaFicha } from "./TelaFicha";
import { BolhaConversa } from "./BolhaConversa";

type EstadoConversa = "vazio" | "carregando" | "ok" | "falha";

type JanelaCanal = {
  aberta: boolean;
  motivo: string | null;
};

type ItemConversa = {
  id_mensagem: number;
  direcao: string;
  origem: string;
  conteudo: string;
  status_envio: string | null;
  entrega: string | null;
  nova_tentativa: boolean | null;
  em: string | null;
};

type ConversaResposta = {
  id_reserva: number;
  janela: JanelaCanal;
  mensagens: ItemConversa[];
};

const ROTULO_ORIGEM: Record<string, string> = {
  hospede: "Hóspede",
  automatico: "Automático",
  recepcao: "Recepção",
};

const MOTIVO_JANELA: Record<string, string> = {
  nunca_escreveu: "Janela fechada: o hóspede ainda não escreveu nesta estadia.",
  sem_mensagem_recente: "Janela fechada: o hóspede não escreveu nas últimas 24 horas.",
};

function rotuloEntrega(item: ItemConversa): string | null {
  if (item.origem !== "recepcao" || !item.entrega) {
    return null;
  }
  if (item.entrega === "enviando") {
    return "enviando";
  }
  if (item.entrega === "enviada") {
    return "enviada";
  }
  if (item.entrega === "falhou") {
    return item.nova_tentativa ? "falhou · nova tentativa marcada" : "falhou";
  }
  return null;
}

export function TelaEstadia() {
  const { idReserva } = useParams();
  const [estado, setEstado] = useState<EstadoConversa>(idReserva ? "carregando" : "vazio");
  const [conversa, setConversa] = useState<ConversaResposta | null>(null);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [avisoEnvio, setAvisoEnvio] = useState("");
  const [mostrarCadastrais, setMostrarCadastrais] = useState(false);

  const carregar = useCallback(async () => {
    if (!idReserva) {
      setEstado("vazio");
      setConversa(null);
      return;
    }
    setEstado("carregando");
    setAvisoEnvio("");
    try {
      const resposta = await pedirAutenticado(`/reservas/${idReserva}/conversa`);
      if (!resposta.ok) {
        setConversa(null);
        setEstado("falha");
        return;
      }
      setConversa((await resposta.json()) as ConversaResposta);
      setEstado("ok");
    } catch {
      setConversa(null);
      setEstado("falha");
    }
  }, [idReserva]);

  useEffect(() => {
    setMostrarCadastrais(false);
    void carregar();
  }, [carregar]);

  async function enviar(evento: FormEvent): Promise<void> {
    evento.preventDefault();
    if (!idReserva || enviando) {
      return;
    }
    setEnviando(true);
    setAvisoEnvio("");
    try {
      const resposta = await pedirAutenticado(`/reservas/${idReserva}/respostas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto }),
      });
      if (!resposta.ok) {
        setAvisoEnvio("Não foi possível gravar a resposta.");
        return;
      }
      setTexto("");
      await carregar();
    } catch {
      setAvisoEnvio("Não foi possível gravar a resposta.");
    } finally {
      setEnviando(false);
    }
  }

  function impedirEnter(evento: KeyboardEvent<HTMLTextAreaElement>): void {
    if (evento.key === "Enter" && !evento.shiftKey) {
      evento.preventDefault();
    }
  }

  const janelaAberta = conversa?.janela.aberta === true;
  const motivoJanela = conversa?.janela.motivo
    ? MOTIVO_JANELA[conversa.janela.motivo] ?? "Janela fechada."
    : null;

  return (
    <main className="p-8">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-900 pb-2">
        <h1 className="text-2xl font-semibold">Estadia</h1>
        <Link to="/fila" className="text-sm underline">
          Fila do dia
        </Link>
      </div>

      {estado === "vazio" ? (
        <p>A estadia se abre pela fila do dia ou por Chamados e pedidos.</p>
      ) : null}

      {estado === "carregando" ? (
        <p className="text-sm text-zinc-500">Carregando a conversa…</p>
      ) : null}

      {estado === "falha" ? (
        <div className="flex flex-col items-start gap-3">
          <p role="status">Não foi possível carregar a conversa.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {estado === "ok" && conversa ? (
        <section className="mb-8 flex max-w-3xl flex-col gap-4">
          <ol className="flex flex-col gap-3">
            {conversa.mensagens.map((item) => (
              <BolhaConversa
                key={item.id_mensagem}
                lado={item.origem === "hospede" ? "hospede" : "hotel"}
                quando={item.em}
                rotulo={ROTULO_ORIGEM[item.origem] ?? item.origem}
                entrega={rotuloEntrega(item)}
              >
                {item.conteudo}
              </BolhaConversa>
            ))}
          </ol>

          <form className="flex flex-col gap-2" onSubmit={(evento) => void enviar(evento)}>
            {motivoJanela && !janelaAberta ? (
              <p role="status">{motivoJanela}</p>
            ) : null}
            <label htmlFor="resposta-recepcao" className="text-sm font-medium">
              Resposta ao hóspede
            </label>
            <textarea
              id="resposta-recepcao"
              className="min-h-24 w-full rounded-md border border-zinc-300 bg-white p-2 text-sm"
              value={texto}
              onChange={(evento) => setTexto(evento.target.value)}
              onKeyDown={impedirEnter}
            />
            {avisoEnvio ? <p role="status">{avisoEnvio}</p> : null}
            <Button type="submit" disabled={enviando || !janelaAberta}>
              Enviar
            </Button>
          </form>
        </section>
      ) : null}

      {idReserva ? (
        mostrarCadastrais ? (
          <TelaFicha embutida />
        ) : estado === "ok" || estado === "falha" ? (
          <Button type="button" onClick={() => setMostrarCadastrais(true)}>
            ver dados cadastrais
          </Button>
        ) : null
      ) : null}
    </main>
  );
}
