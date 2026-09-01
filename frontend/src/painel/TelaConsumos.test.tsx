import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ItemConsumoPendente } from "./consumos";
import { tempoDecorrido } from "./solicitacoes";
import { TelaConsumos } from "./TelaConsumos";

const agora = new Date("2026-08-31T15:00:00.000Z");

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function item(
  parcial: Partial<ItemConsumoPendente> & { id_solicitacao: number },
): ItemConsumoPendente {
  return {
    id_reserva: 10,
    descricao: "texto livre da solicitação",
    descricao_item: "Lavanderia",
    numero_quarto: "210",
    valor_praticado: "32.00",
    status_lancamento: "pendente",
    aberta_em: "2026-08-29T15:00:00.000Z",
    resolvida_em: null,
    ...parcial,
  };
}

function fetchPendentes(
  itens: ItemConsumoPendente[] | "erro",
  extras?: (url: string, init?: RequestInit) => Response | null,
) {
  let tentativasGet = 0;
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const extra = extras?.(url, init);
    if (extra) {
      return extra;
    }
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/consumos/pendentes" && metodo === "GET") {
      tentativasGet += 1;
      if (itens === "erro") {
        if (tentativasGet === 1) {
          return json({ detail: "falha" }, 500);
        }
        return json({
          itens: [item({ id_solicitacao: 9, descricao_item: "Lavanderia recuperada" })],
        });
      }
      return json({ itens });
    }
    return new Response(null, { status: 404 });
  });
}

function renderConsumos() {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/consumos"]}>
      <TelaConsumos agora={agora} />
    </MemoryRouter>,
  );
}

describe("TelaConsumos", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("lista item, valor, tempo, Ver ficha e resumo, sem nome nem palavra proibida", async () => {
    const itens = [
      item({
        id_solicitacao: 1,
        id_reserva: 42,
        descricao_item: "Lavanderia",
        numero_quarto: "210",
        valor_praticado: "32.00",
        aberta_em: "2026-08-29T15:00:00.000Z",
      }),
      item({
        id_solicitacao: 2,
        id_reserva: 7,
        descricao_item: "Frigobar",
        numero_quarto: null,
        valor_praticado: 56,
        aberta_em: "2026-08-31T12:00:00.000Z",
      }),
    ];
    const fetchMock = fetchPendentes(itens);
    vi.stubGlobal("fetch", fetchMock);
    renderConsumos();

    expect(await screen.findByText("Lavanderia")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/consumos/pendentes",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(screen.getByText("Frigobar")).toBeInTheDocument();
    expect(screen.getByText(/Quarto 210/)).toBeInTheDocument();
    expect(screen.getByText(/sem quarto/i)).toBeInTheDocument();
    expect(screen.getByText(/32/)).toBeInTheDocument();
    expect(screen.getByText(/56/)).toBeInTheDocument();

    const linhas = screen.getAllByRole("listitem");
    expect(within(linhas[0]).getByText("Lavanderia")).toBeInTheDocument();
    expect(within(linhas[1]).getByText("Frigobar")).toBeInTheDocument();
    expect(within(linhas[0]).getByText(new RegExp(tempoDecorrido(itens[0].aberta_em, agora)))).toBeInTheDocument();
    expect(within(linhas[1]).getByText(new RegExp(tempoDecorrido(itens[1].aberta_em, agora)))).toBeInTheDocument();

    expect(screen.getByText(/2 pendentes/)).toBeInTheDocument();
    expect(screen.getByText(/88/)).toBeInTheDocument();
    expect(screen.getByText(new RegExp(`o mais antigo ${tempoDecorrido(itens[0].aberta_em, agora)}`))).toBeInTheDocument();

    const links = screen.getAllByRole("link", { name: "Ver ficha" });
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", expect.stringMatching(/\/ficha\/42$/));
    expect(links[1]).toHaveAttribute("href", expect.stringMatching(/\/ficha\/7$/));

    const corpo = (document.body.textContent ?? "").toLowerCase();
    expect(corpo).not.toMatch(/marina|55119|123\.456|cpf|extrato|\bconta\b/);
    expect(screen.queryByText("texto livre da solicitação")).not.toBeInTheDocument();
  });

  it("lista vazia não copia o recado de falha e zera o total", async () => {
    vi.stubGlobal("fetch", fetchPendentes([]));
    renderConsumos();
    expect(await screen.findByText(/não há consumo a lançar/i)).toBeInTheDocument();
    expect(screen.getByText(/0 pendentes/)).toBeInTheDocument();
    expect(screen.queryByText(/não carregou/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tentar de novo" })).not.toBeInTheDocument();
  });

  it("falha de leitura não se disfarça de lista vazia e tentar de novo recupera", async () => {
    vi.stubGlobal("fetch", fetchPendentes("erro"));
    renderConsumos();
    expect(await screen.findByText(/não carregou/i)).toBeInTheDocument();
    expect(screen.queryByText(/não há consumo a lançar/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/0 pendentes/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(await screen.findByText("Lavanderia recuperada")).toBeInTheDocument();
    expect(screen.queryByText(/não carregou/i)).not.toBeInTheDocument();
  });

  it("Marcar lançado faz POST e some o item; Ver ficha e descrição não lançam", async () => {
    let abertos = [
      item({ id_solicitacao: 1, descricao_item: "Lavanderia", valor_praticado: "32.00" }),
      item({ id_solicitacao: 2, descricao_item: "Frigobar", valor_praticado: "56.00" }),
    ];
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/consumos/pendentes" && metodo === "GET") {
        return json({ itens: abertos });
      }
      if (url === "/solicitacoes/1/lancamento" && metodo === "POST") {
        abertos = abertos.filter((linha) => linha.id_solicitacao !== 1);
        return json({ id_solicitacao: 1, status_lancamento: "lancado" });
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderConsumos();
    expect(await screen.findByText("Lavanderia")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Marcar lançado" })).toHaveLength(2);
    fireEvent.click(screen.getByText("Lavanderia"));
    fireEvent.click(screen.getAllByRole("link", { name: "Ver ficha" })[0]);
    expect(
      fetchMock.mock.calls.filter((chamada) => String(chamada[0]).includes("/lancamento")),
    ).toHaveLength(0);
    fireEvent.click(screen.getAllByRole("button", { name: "Marcar lançado" })[0]);
    await waitFor(() => expect(screen.queryByText("Lavanderia")).not.toBeInTheDocument());
    expect(screen.getByText("Frigobar")).toBeInTheDocument();
    expect(screen.getByText(/1 pendentes/)).toBeInTheDocument();
    expect(screen.getAllByText(/56/).length).toBeGreaterThan(0);
    const posts = fetchMock.mock.calls.filter(
      (chamada) =>
        chamada[0] === "/solicitacoes/1/lancamento" && (chamada[1]?.method ?? "GET") === "POST",
    );
    expect(posts).toHaveLength(1);
    expect(posts[0][1]).toEqual(expect.objectContaining({ credentials: "include", method: "POST" }));
    expect(posts[0][1]?.body).toBeUndefined();
    expect(screen.queryByText(/tem certeza/i)).not.toBeInTheDocument();
  });

  it("409 de lançamento mostra o motivo e o item permanece até o GET dizer o contrário", async () => {
    const aberto = item({ id_solicitacao: 1, descricao_item: "Lavanderia" });
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/consumos/pendentes" && metodo === "GET") {
        return json({ itens: [aberto] });
      }
      if (String(url).includes("/lancamento") && metodo === "POST") {
        return json({ detail: "Este consumo ja foi lancado." }, 409);
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderConsumos();
    expect(await screen.findByText("Lavanderia")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Marcar lançado" }));
    expect(await screen.findByText(/ja foi lancado/i)).toBeInTheDocument();
    expect(screen.getByText("Lavanderia")).toBeInTheDocument();
    expect(screen.queryByText(/sucesso/i)).not.toBeInTheDocument();
  });

  it("Dispensar faz POST distinto do lançar e some o item", async () => {
    let abertos = [
      item({ id_solicitacao: 1, descricao_item: "Lavanderia" }),
      item({ id_solicitacao: 2, descricao_item: "Frigobar" }),
    ];
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/consumos/pendentes" && metodo === "GET") {
        return json({ itens: abertos });
      }
      if (url === "/solicitacoes/1/dispensa" && metodo === "POST") {
        abertos = abertos.filter((linha) => linha.id_solicitacao !== 1);
        return json({ id_solicitacao: 1, status_lancamento: "dispensado" });
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderConsumos();
    expect(await screen.findByText("Lavanderia")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Dispensar" })).toHaveLength(2);
    fireEvent.click(screen.getAllByRole("button", { name: "Marcar lançado" })[1]);
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.filter((chamada) => String(chamada[0]).includes("/lancamento")),
      ).toHaveLength(1),
    );
    expect(
      fetchMock.mock.calls.filter((chamada) => String(chamada[0]).includes("/dispensa")),
    ).toHaveLength(0);
    fireEvent.click(screen.getAllByRole("button", { name: "Dispensar" })[0]);
    await waitFor(() => expect(screen.queryByText("Lavanderia")).not.toBeInTheDocument());
    expect(screen.getByText("Frigobar")).toBeInTheDocument();
    const posts = fetchMock.mock.calls.filter(
      (chamada) =>
        chamada[0] === "/solicitacoes/1/dispensa" && (chamada[1]?.method ?? "GET") === "POST",
    );
    expect(posts).toHaveLength(1);
    expect(posts[0][1]).toEqual(expect.objectContaining({ credentials: "include", method: "POST" }));
    expect(posts[0][1]?.body).toBeUndefined();
  });

  it("409 de dispensa mostra o motivo e o item permanece", async () => {
    const aberto = item({ id_solicitacao: 1, descricao_item: "Lavanderia" });
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/consumos/pendentes" && metodo === "GET") {
        return json({ itens: [aberto] });
      }
      if (String(url).includes("/dispensa") && metodo === "POST") {
        return json({ detail: "Este consumo ja foi dispensado." }, 409);
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderConsumos();
    expect(await screen.findByText("Lavanderia")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Dispensar" }));
    expect(await screen.findByText(/ja foi dispensado/i)).toBeInTheDocument();
    expect(screen.getByText("Lavanderia")).toBeInTheDocument();
  });
});
