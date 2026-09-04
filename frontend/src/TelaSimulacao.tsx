import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

import { pedirAutenticado } from "./painel/sessao";
import { BolhaConversa } from "./painel/BolhaConversa";
import { Button } from "./components/ui/button";

type ItemConversa = {
  id_reserva: number;
  status: string;
  nome_titular: string;
  telefone_contato: string;
};

type Mensagem = {
  id_mensagem: number;
  direcao: "enviada" | "recebida";
  conteudo: string;
  status_envio: string | null;
  enviada_em: string;
};

type Fio = ItemConversa & { mensagens: Mensagem[] };

function rotuloEnvio(status: string | null, direcao: string): string {
  if (direcao !== "enviada") {
    return "hóspede";
  }
  if (status === "pendente") {
    return "hotel · pendente";
  }
  if (status === "falha") {
    return "hotel · falha";
  }
  return "hotel · enviada";
}

function novoIdExterno(): string {
  return `sim:${crypto.randomUUID()}`;
}

async function lerJson(resposta: Response): Promise<unknown> {
  try {
    return await resposta.json();
  } catch {
    return null;
  }
}

function codigoDe(corpo: unknown): string | null {
  if (!corpo || typeof corpo !== "object") {
    return null;
  }
  const detalhe = (corpo as { detail?: unknown }).detail;
  if (detalhe && typeof detalhe === "object" && "codigo" in detalhe) {
    return String((detalhe as { codigo: unknown }).codigo);
  }
  return null;
}

export function TelaSimulacao() {
  const [aviso, setAviso] = useState("");
  const [conversas, setConversas] = useState<ItemConversa[]>([]);
  const [escolhida, setEscolhida] = useState<number | null>(null);
  const [fio, setFio] = useState<Fio | null>(null);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const idExterno = useRef<string | null>(null);

  function tratarRecusa(resposta: Response, corpo: unknown): boolean {
    if (resposta.status === 401) {
      return true;
    }
    if (resposta.status === 403) {
      setAviso("Perfil sem permissão para o simulador.");
      return true;
    }
    if (resposta.status === 409 && codigoDe(corpo) === "modo_real") {
      setAviso("Canal em modo real. A tela de simulação não opera.");
      return true;
    }
    return false;
  }

  async function carregarLista(): Promise<boolean> {
    const resposta = await pedirAutenticado("/simulador/conversas");
    const corpo = await lerJson(resposta);
    if (tratarRecusa(resposta, corpo)) {
      return false;
    }
    if (!resposta.ok) {
      setAviso("Não foi possível listar as conversas.");
      return false;
    }
    const dados = corpo as { conversas: ItemConversa[] };
    setConversas(dados.conversas);
    setAviso("");
    return true;
  }

  async function carregarFio(id: number): Promise<void> {
    const resposta = await pedirAutenticado(`/simulador/conversas/${id}`);
    const corpo = await lerJson(resposta);
    if (tratarRecusa(resposta, corpo)) {
      return;
    }
    if (resposta.status === 404) {
      setAviso("Conversa não encontrada nesta casa.");
      return;
    }
    if (!resposta.ok) {
      setAviso("Não foi possível ler o fio.");
      return;
    }
    setFio(corpo as Fio);
  }

  useEffect(() => {
    void carregarLista();
  }, []);

  useEffect(() => {
    if (escolhida === null) {
      return;
    }
    void carregarFio(escolhida);
    const timer = window.setInterval(() => {
      void carregarFio(escolhida);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [escolhida]);

  async function enviar(): Promise<void> {
    if (escolhida === null || !texto.trim() || enviando) {
      return;
    }
    if (!idExterno.current) {
      idExterno.current = novoIdExterno();
    }
    setEnviando(true);
    const resposta = await pedirAutenticado(`/simulador/conversas/${escolhida}/mensagens`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        texto: texto.trim(),
        id_externo: idExterno.current,
      }),
    });
    const corpo = await lerJson(resposta);
    setEnviando(false);
    if (tratarRecusa(resposta, corpo)) {
      return;
    }
    if (!resposta.ok) {
      setAviso("Não foi possível enviar o turno.");
      return;
    }
    idExterno.current = null;
    setTexto("");
    await carregarFio(escolhida);
  }

  function aoTecla(evento: KeyboardEvent<HTMLTextAreaElement>): void {
    if (evento.key !== "Enter" || evento.shiftKey) {
      return;
    }
    evento.preventDefault();
    void enviar();
  }

  return (
    <div className="p-8">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">OmniStay — simulador de conversa</h1>
        <p className="text-sm text-zinc-500">Sem WhatsApp. Sem telefone. Mesmas regras.</p>
      </header>
      {aviso ? (
        <p className="mb-4 rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm">{aviso}</p>
      ) : null}
      <div className="grid gap-6 md:grid-cols-[240px_1fr]">
        <aside>
          <h2 className="mb-3 text-sm font-medium">Reservas</h2>
          {conversas.length === 0 ? (
            <p>Nenhuma reserva nesta casa.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {conversas.map((item) => (
                <li key={item.id_reserva}>
                  <button
                    type="button"
                    className={
                      escolhida === item.id_reserva
                        ? "w-full rounded border border-zinc-900 bg-white p-3 text-left font-medium"
                        : "w-full rounded border border-zinc-200 bg-white p-3 text-left"
                    }
                    onClick={() => setEscolhida(item.id_reserva)}
                  >
                    {item.nome_titular} · {item.status}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>
        <section>
          {!escolhida || !fio ? (
            <p>Escolha uma reserva para ver a conversa.</p>
          ) : (
            <>
              <h2 className="mb-4 text-lg font-semibold">
                {fio.nome_titular} · {fio.status}
              </h2>
              <ol className="flex flex-col gap-2">
                {fio.mensagens.map((msg) => (
                  <BolhaConversa
                    key={msg.id_mensagem}
                    lado={msg.direcao === "recebida" ? "hospede" : "hotel"}
                    quando={msg.enviada_em}
                    rotulo={rotuloEnvio(msg.status_envio, msg.direcao)}
                  >
                    {msg.conteudo}
                  </BolhaConversa>
                ))}
              </ol>
              <form
                className="mt-4 flex flex-col gap-2"
                onSubmit={(evento: FormEvent) => {
                  evento.preventDefault();
                  void enviar();
                }}
              >
                <textarea
                  className="min-h-24 w-full rounded-md border border-zinc-300 bg-white p-2 text-sm"
                  value={texto}
                  onChange={(evento) => setTexto(evento.target.value)}
                  onKeyDown={aoTecla}
                  placeholder="Falar como o hóspede"
                  rows={3}
                />
                <Button type="submit" disabled={!texto.trim() || enviando}>
                  Enviar
                </Button>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
