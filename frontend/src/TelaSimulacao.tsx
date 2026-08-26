import { FormEvent, useEffect, useRef, useState, type CSSProperties } from "react";

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
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [aviso, setAviso] = useState("");
  const [precisaLogin, setPrecisaLogin] = useState(true);
  const [conversas, setConversas] = useState<ItemConversa[]>([]);
  const [escolhida, setEscolhida] = useState<number | null>(null);
  const [fio, setFio] = useState<Fio | null>(null);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const idExterno = useRef<string | null>(null);

  function tratarRecusa(resposta: Response, corpo: unknown): boolean {
    if (resposta.status === 401) {
      setPrecisaLogin(true);
      setAviso("Sessão ausente. Entre com e-mail e senha.");
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
    const resposta = await fetch("/simulador/conversas", {
      credentials: "include",
    });
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
    setPrecisaLogin(false);
    setAviso("");
    return true;
  }

  async function carregarFio(id: number): Promise<void> {
    const resposta = await fetch(`/simulador/conversas/${id}`, {
      credentials: "include",
    });
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
    if (precisaLogin || escolhida === null) {
      return;
    }
    void carregarFio(escolhida);
    const timer = window.setInterval(() => {
      void carregarFio(escolhida);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [precisaLogin, escolhida]);

  async function entrar(evento: FormEvent): Promise<void> {
    evento.preventDefault();
    const resposta = await fetch("/sessoes", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });
    if (!resposta.ok) {
      setAviso("Credenciais inválidas.");
      return;
    }
    await carregarLista();
  }

  async function enviar(): Promise<void> {
    if (escolhida === null || !texto.trim() || enviando) {
      return;
    }
    if (!idExterno.current) {
      idExterno.current = novoIdExterno();
    }
    setEnviando(true);
    const resposta = await fetch(`/simulador/conversas/${escolhida}/mensagens`, {
      method: "POST",
      credentials: "include",
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

  return (
    <div style={estilos.pagina}>
      <header style={estilos.cabecalho}>
        <strong>OmniStay — simulador de conversa</strong>
        <span style={estilos.sub}>Sem WhatsApp. Sem telefone. Mesmas regras.</span>
      </header>
      {aviso ? <p style={estilos.aviso}>{aviso}</p> : null}
      {precisaLogin ? (
        <form onSubmit={entrar} style={estilos.login}>
          <label>
            E-mail
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label>
            Senha
            <input
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          <button type="submit">Entrar</button>
        </form>
      ) : (
        <div style={estilos.grade}>
          <aside style={estilos.lista}>
            <h2>Reservas</h2>
            {conversas.length === 0 ? (
              <p>Nenhuma reserva nesta casa.</p>
            ) : (
              <ul style={estilos.ul}>
                {conversas.map((item) => (
                  <li key={item.id_reserva}>
                    <button
                      type="button"
                      style={{
                        ...estilos.item,
                        fontWeight:
                          escolhida === item.id_reserva ? 700 : 400,
                      }}
                      onClick={() => setEscolhida(item.id_reserva)}
                    >
                      {item.nome_titular} · {item.status}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </aside>
          <section style={estilos.fio}>
            {!escolhida || !fio ? (
              <p>Escolha uma reserva para ver a conversa.</p>
            ) : (
              <>
                <h2>
                  {fio.nome_titular} · {fio.status}
                </h2>
                <ol style={estilos.ul}>
                  {fio.mensagens.map((msg) => (
                    <li
                      key={msg.id_mensagem}
                      style={{
                        ...estilos.balao,
                        marginLeft: msg.direcao === "enviada" ? 0 : "20%",
                        marginRight: msg.direcao === "enviada" ? "20%" : 0,
                        background:
                          msg.direcao === "enviada" ? "#e8f1ff" : "#f3f3f3",
                      }}
                    >
                      <small>{rotuloEnvio(msg.status_envio, msg.direcao)}</small>
                      <p style={estilos.corpo}>{msg.conteudo}</p>
                    </li>
                  ))}
                </ol>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void enviar();
                  }}
                  style={estilos.composer}
                >
                  <textarea
                    value={texto}
                    onChange={(e) => setTexto(e.target.value)}
                    placeholder="Falar como o hóspede"
                    rows={3}
                  />
                  <button type="submit" disabled={!texto.trim() || enviando}>
                    Enviar
                  </button>
                </form>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

const estilos: Record<string, CSSProperties> = {
  pagina: {
    fontFamily: "Georgia, serif",
    maxWidth: 960,
    margin: "0 auto",
    padding: 16,
    color: "#1c1c1c",
  },
  cabecalho: { display: "flex", flexDirection: "column", gap: 4, marginBottom: 16 },
  sub: { color: "#555", fontSize: 14 },
  aviso: {
    background: "#fff4e5",
    border: "1px solid #e0a100",
    padding: 8,
  },
  login: { display: "flex", flexDirection: "column", gap: 12, maxWidth: 320 },
  grade: { display: "grid", gridTemplateColumns: "240px 1fr", gap: 16 },
  lista: { borderRight: "1px solid #ddd", paddingRight: 12 },
  ul: { listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 8 },
  item: {
    width: "100%",
    textAlign: "left",
    padding: 8,
    cursor: "pointer",
  },
  fio: { minHeight: 400 },
  balao: { padding: 8, borderRadius: 8 },
  corpo: { whiteSpace: "pre-wrap", margin: "4px 0 0" },
  composer: { display: "flex", flexDirection: "column", gap: 8, marginTop: 16 },
};
