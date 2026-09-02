import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ItemSolicitacao } from "./solicitacoes";
import { TelaAlertas } from "./TelaAlertas";

const agora = new Date("2026-08-31T15:00:00.000Z");

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function item(parcial: Partial<ItemSolicitacao> & { id_solicitacao: number; tipo: string }): ItemSolicitacao {
  return {
    id_reserva: 10 + parcial.id_solicitacao,
    descricao: "Descrição do item",
    numero_quarto: "304",
    urgencia: "media",
    janela_preferencia: null,
    status: "aberta",
    aberta_em: "2026-08-31T12:00:00.000Z",
    destaque_tempo_excedido: false,
    valor_praticado: null,
    status_lancamento: null,
    ...parcial,
  };
}

function fetchLista(itens: ItemSolicitacao[] | "erro", extras?: (url: string, init?: RequestInit) => Response | null) {
  let tentativasGet = 0;
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const extra = extras?.(url, init);
    if (extra) {
      return extra;
    }
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/solicitacoes" && metodo === "GET") {
      tentativasGet += 1;
      if (itens === "erro") {
        if (tentativasGet === 1) {
          return json({ detail: "falha" }, 500);
        }
        return json({
          itens: [item({ id_solicitacao: 9, tipo: "servico", descricao: "Toalha extra" })],
        });
      }
      return json({ itens });
    }
    return new Response(null, { status: 404 });
  });
}

function renderAlertas() {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/alertas"]}>
      <TelaAlertas agora={agora} />
    </MemoryRouter>,
  );
}

describe("TelaAlertas", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("busca a lista e mostra naturezas, tempo, Estadia e valor, sem dado cadastral", async () => {
    const itens = [
      item({
        id_solicitacao: 1,
        tipo: "reclamacao",
        descricao: "Ar-condicionado não gela",
        janela_preferencia: "depois das 16h",
        destaque_tempo_excedido: true,
        aberta_em: "2026-08-31T12:00:00.000Z",
      }),
      item({
        id_solicitacao: 2,
        tipo: "servico",
        descricao: "Toalha extra",
        numero_quarto: "210",
        aberta_em: "2026-08-31T13:00:00.000Z",
      }),
      item({
        id_solicitacao: 3,
        tipo: "consumo",
        descricao: "2 caipirinhas",
        numero_quarto: null,
        valor_praticado: "56.00",
        aberta_em: "2026-08-31T14:00:00.000Z",
      }),
    ];
    const fetchMock = fetchLista(itens);
    vi.stubGlobal("fetch", fetchMock);
    renderAlertas();

    expect(await screen.findByText("Ar-condicionado não gela")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/solicitacoes", expect.objectContaining({ credentials: "include" }));
    expect(screen.getByText("reclamação")).toBeInTheDocument();
    expect(screen.getByText("serviço")).toBeInTheDocument();
    expect(screen.getByText("consumo")).toBeInTheDocument();
    expect(screen.getByText(/há 3 h/i)).toBeInTheDocument();
    expect(screen.getByText("depois das 16h")).toBeInTheDocument();
    expect(screen.getByText(/56/)).toBeInTheDocument();
    expect(screen.getByText(/sem quarto/i)).toBeInTheDocument();

    const links = screen.getAllByRole("link", { name: "Estadia" });
    expect(links).toHaveLength(3);
    expect(links[0]).toHaveAttribute("href", expect.stringMatching(/\/ficha\/11$/));
    expect(links[2]).toHaveAttribute("href", expect.stringMatching(/\/ficha\/13$/));

    const corpo = document.body.textContent ?? "";
    expect(corpo).not.toMatch(/Marina|55119|123\.456|CPF/i);

    const linhas = screen.getAllByRole("listitem");
    expect(within(linhas[0]).getByText("Ar-condicionado não gela")).toBeInTheDocument();
    expect(within(linhas[2]).getByText("2 caipirinhas")).toBeInTheDocument();
    expect(within(linhas[0]).getByText(/tempo excessivo/i)).toBeInTheDocument();
    expect(within(linhas[1]).queryByText(/tempo excessivo/i)).not.toBeInTheDocument();
  });

  it("lista vazia não copia o recado de falha", async () => {
    vi.stubGlobal("fetch", fetchLista([]));
    renderAlertas();
    expect(await screen.findByText(/não há pendência aberta/i)).toBeInTheDocument();
    expect(screen.queryByText(/não carregou/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tentar de novo" })).not.toBeInTheDocument();
  });

  it("falha de leitura não se disfarça de lista vazia e tentar de novo recupera", async () => {
    vi.stubGlobal("fetch", fetchLista("erro"));
    renderAlertas();
    expect(await screen.findByText(/não carregou/i)).toBeInTheDocument();
    expect(screen.queryByText(/não há pendência aberta/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(await screen.findByText("Toalha extra")).toBeInTheDocument();
    expect(screen.queryByText(/não carregou/i)).not.toBeInTheDocument();
  });

  it("Resolvido faz POST e some o item; Estadia e descrição não resolvem", async () => {
    let abertos = [
      item({ id_solicitacao: 1, tipo: "reclamacao", descricao: "Ar-condicionado não gela" }),
    ];
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/solicitacoes" && metodo === "GET") {
        return json({ itens: abertos });
      }
      if (url === "/solicitacoes/1/resolucao" && metodo === "POST") {
        abertos = [];
        return json({ id_solicitacao: 1, status: "resolvida", confirmacao: "agendada" });
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderAlertas();
    expect(await screen.findByText("Ar-condicionado não gela")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Ar-condicionado não gela"));
    fireEvent.click(screen.getByRole("link", { name: "Estadia" }));
    expect(
      fetchMock.mock.calls.filter((c) => String(c[0]).includes("/resolucao")),
    ).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "Resolvido" }));
    await waitFor(() => expect(screen.queryByText("Ar-condicionado não gela")).not.toBeInTheDocument());
    const posts = fetchMock.mock.calls.filter(
      (c) => c[0] === "/solicitacoes/1/resolucao" && (c[1]?.method ?? "GET") === "POST",
    );
    expect(posts).toHaveLength(1);
    expect(posts[0][1]).toEqual(expect.objectContaining({ credentials: "include", method: "POST" }));
    expect(screen.queryByText(/tem certeza/i)).not.toBeInTheDocument();
  });

  it("409 mostra o motivo e o item permanece até o GET dizer o contrário", async () => {
    const aberto = item({ id_solicitacao: 1, tipo: "servico", descricao: "Toalha extra" });
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/solicitacoes" && metodo === "GET") {
        return json({ itens: [aberto] });
      }
      if (String(url).includes("/resolucao") && metodo === "POST") {
        return json({ detail: "Esta solicitacao ja foi resolvida." }, 409);
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderAlertas();
    expect(await screen.findByText("Toalha extra")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Resolvido" }));
    expect(await screen.findByText(/ja foi resolvida/i)).toBeInTheDocument();
    expect(screen.getByText("Toalha extra")).toBeInTheDocument();
  });
});
