import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelaVendaveis } from "./TelaVendaveis";
import type { ItemVendavel } from "./vendaveis";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function item(parcial: Partial<ItemVendavel> & { id_item_vendavel: number }): ItemVendavel {
  return {
    nome: "Água com gás",
    preco_atual: "9.00",
    ativo: true,
    ...parcial,
  };
}

function fetchVendaveis(
  iniciais: ItemVendavel[] | "erro",
  extras?: (url: string, init?: RequestInit) => Response | null,
) {
  let itens: ItemVendavel[] = iniciais === "erro" ? [] : [...iniciais];
  let tentativasGet = 0;
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const extra = extras?.(url, init);
    if (extra) {
      return extra;
    }
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/itens-vendaveis" && metodo === "GET") {
      tentativasGet += 1;
      if (iniciais === "erro" && tentativasGet === 1) {
        return json({ detail: "falha" }, 500);
      }
      return json({ itens });
    }
    if (url === "/itens-vendaveis" && metodo === "POST") {
      const corpo = JSON.parse(String(init?.body ?? "{}")) as Partial<ItemVendavel>;
      const criado = item({
        id_item_vendavel: 99,
        nome: String(corpo.nome ?? ""),
        preco_atual: corpo.preco_atual ?? 0,
        ativo: true,
      });
      itens = [...itens, criado];
      return json(criado, 201);
    }
    if (metodo === "PATCH" && /^\/itens-vendaveis\/\d+$/.test(url)) {
      const id = Number(url.split("/").pop());
      const corpo = JSON.parse(String(init?.body ?? "{}")) as Partial<ItemVendavel>;
      itens = itens.map((linha) =>
        linha.id_item_vendavel === id ? { ...linha, ...corpo } : linha,
      );
      const atual = itens.find((linha) => linha.id_item_vendavel === id);
      return json(atual ?? {});
    }
    return new Response(null, { status: 404 });
  });
}

function renderVendaveis(somenteLeitura = false) {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/vendaveis"]}>
      <TelaVendaveis somenteLeitura={somenteLeitura} />
    </MemoryRouter>,
  );
}

describe("TelaVendaveis", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("lista nome, preço próprio e situação, sem descrição nem apagar", async () => {
    const fetchMock = fetchVendaveis([
      item({ id_item_vendavel: 1, nome: "Caipirinha", preco_atual: 28 }),
      item({
        id_item_vendavel: 2,
        nome: "Cesta de frutas",
        preco_atual: "45.00",
        ativo: false,
      }),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    renderVendaveis();

    expect(await screen.findByRole("heading", { name: "Itens vendáveis" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/itens-vendaveis",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(screen.getByText("Caipirinha")).toBeInTheDocument();
    expect(screen.getByText("R$ 28,00")).toBeInTheDocument();
    expect(screen.getByText("Cesta de frutas")).toBeInTheDocument();
    expect(screen.queryByText(/descri/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: /descri/i })).not.toBeInTheDocument();

    const ativo = screen.getByText("Caipirinha").closest("tr") as HTMLElement;
    expect(within(ativo).getByRole("button", { name: "Editar" })).toBeInTheDocument();
    expect(within(ativo).getByRole("button", { name: "Desativar" })).toBeInTheDocument();
    const inativo = screen.getByText("Cesta de frutas").closest("tr") as HTMLElement;
    expect(within(inativo).getByRole("button", { name: "Reativar" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apagar" })).not.toBeInTheDocument();
  });

  it("lista vazia é distinta de falha", async () => {
    vi.stubGlobal("fetch", fetchVendaveis([]));
    const visao = renderVendaveis();
    expect(await screen.findByText("Não há item vendável.")).toBeInTheDocument();
    expect(screen.queryByText("A lista não carregou.")).not.toBeInTheDocument();
    visao.unmount();

    vi.stubGlobal("fetch", fetchVendaveis("erro"));
    renderVendaveis();
    expect(await screen.findByText("A lista não carregou.")).toBeInTheDocument();
    expect(screen.queryByText("Não há item vendável.")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(await screen.findByText("Não há item vendável.")).toBeInTheDocument();
  });

  it("cria com nome e preço separados e edita só o preço", async () => {
    const fetchMock = fetchVendaveis([item({ id_item_vendavel: 1, nome: "Água", preco_atual: "9.00" })]);
    vi.stubGlobal("fetch", fetchMock);
    renderVendaveis();

    fireEvent.click(await screen.findByRole("button", { name: "+ Novo item" }));
    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Lavanderia" } });
    fireEvent.change(screen.getByLabelText("Preço"), { target: { value: "32" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      const post = fetchMock.mock.calls.find(
        (chamada) => chamada[0] === "/itens-vendaveis" && (chamada[1]?.method ?? "") === "POST",
      );
      expect(post).toBeDefined();
      expect(JSON.parse(String(post?.[1]?.body))).toEqual({
        nome: "Lavanderia",
        preco_atual: 32,
      });
    });

    fireEvent.click(within(screen.getByText("Água").closest("tr") as HTMLElement).getByRole("button", { name: "Editar" }));
    fireEvent.change(screen.getByLabelText("Preço"), { target: { value: "11" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      const patch = fetchMock.mock.calls.find(
        (chamada) =>
          String(chamada[0]) === "/itens-vendaveis/1" && (chamada[1]?.method ?? "") === "PATCH",
      );
      expect(patch).toBeDefined();
      expect(JSON.parse(String(patch?.[1]?.body))).toEqual({ preco_atual: 11 });
    });

    const antes = fetchMock.mock.calls.length;
    fireEvent.click(screen.getByText("Água"));
    expect(fetchMock.mock.calls.length).toBe(antes);
  });

  it("mostra 409 e 422 ao salvar, sem sumir o item", async () => {
    const fetchMock = fetchVendaveis(
      [item({ id_item_vendavel: 1, nome: "Água", preco_atual: "9.00" })],
      (url, init) => {
        const metodo = (init?.method ?? "GET").toUpperCase();
        if (url === "/itens-vendaveis" && metodo === "POST") {
          return json({ detail: "Ja existe item vendavel ativo com este nome." }, 409);
        }
        if (url === "/itens-vendaveis/1" && metodo === "PATCH") {
          return json({ detail: "Preco nao pode ser negativo." }, 422);
        }
        return null;
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    renderVendaveis();

    fireEvent.click(await screen.findByRole("button", { name: "+ Novo item" }));
    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Água" } });
    fireEvent.change(screen.getByLabelText("Preço"), { target: { value: "9" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
    expect(await screen.findByText("Ja existe item vendavel ativo com este nome.")).toBeInTheDocument();
    expect(screen.getByText("Água")).toBeInTheDocument();

    fireEvent.click(within(screen.getByText("Água").closest("tr") as HTMLElement).getByRole("button", { name: "Editar" }));
    fireEvent.change(screen.getByLabelText("Preço"), { target: { value: "-1" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
    expect(await screen.findByText("Preco nao pode ser negativo.")).toBeInTheDocument();
    expect(screen.getByText("Água")).toBeInTheDocument();
  });

  it("desativar mantém o item visível e não chama DELETE nem catálogo ativo", async () => {
    const fetchMock = fetchVendaveis([item({ id_item_vendavel: 1, nome: "Água", preco_atual: "9.00" })]);
    vi.stubGlobal("fetch", fetchMock);
    renderVendaveis();

    fireEvent.click(await screen.findByRole("button", { name: "Desativar" }));
    expect(await screen.findByRole("button", { name: "Reativar" })).toBeInTheDocument();
    const linha = screen.getByText("Água").closest("tr") as HTMLElement;
    expect(within(linha).getByText("desativado")).toBeInTheDocument();

    expect(
      fetchMock.mock.calls.some((chamada) => (chamada[1]?.method ?? "").toUpperCase() === "DELETE"),
    ).toBe(false);
    expect(fetchMock.mock.calls.some((chamada) => String(chamada[0]) === "/catalogo/ativo")).toBe(
      false,
    );
  });
});
