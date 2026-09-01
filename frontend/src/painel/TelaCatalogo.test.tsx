import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ItemCatalogo } from "./catalogo";
import { TelaCatalogo } from "./TelaCatalogo";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function item(parcial: Partial<ItemCatalogo> & { id_catalogo_item: number }): ItemCatalogo {
  return {
    categoria: "horario",
    titulo: "Café da manhã",
    conteudo: "Das 7h às 10h no salão.",
    ativo: true,
    ...parcial,
  };
}

function fetchCatalogo(
  iniciais: ItemCatalogo[] | "erro",
  extras?: (url: string, init?: RequestInit) => Response | null,
) {
  let itens: ItemCatalogo[] = iniciais === "erro" ? [] : [...iniciais];
  let tentativasGet = 0;
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const extra = extras?.(url, init);
    if (extra) {
      return extra;
    }
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/catalogo" && metodo === "GET") {
      tentativasGet += 1;
      if (iniciais === "erro" && tentativasGet === 1) {
        return json({ detail: "falha" }, 500);
      }
      return json({ itens });
    }
    if (url === "/catalogo" && metodo === "POST") {
      const corpo = JSON.parse(String(init?.body ?? "{}")) as Partial<ItemCatalogo>;
      const criado = item({
        id_catalogo_item: 99,
        categoria: (corpo.categoria as ItemCatalogo["categoria"]) ?? "horario",
        titulo: corpo.titulo ?? "",
        conteudo: corpo.conteudo ?? "",
        ativo: true,
      });
      itens = [...itens, criado];
      return json(criado, 201);
    }
    if (metodo === "PATCH" && /^\/catalogo\/\d+$/.test(url)) {
      const id = Number(url.split("/").pop());
      const corpo = JSON.parse(String(init?.body ?? "{}")) as Partial<ItemCatalogo>;
      itens = itens.map((linha) =>
        linha.id_catalogo_item === id ? { ...linha, ...corpo } : linha,
      );
      const atual = itens.find((linha) => linha.id_catalogo_item === id);
      return json(atual ?? {});
    }
    return new Response(null, { status: 404 });
  });
}

function renderCatalogo(somenteLeitura = false) {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/catalogo"]}>
      <TelaCatalogo somenteLeitura={somenteLeitura} />
    </MemoryRouter>,
  );
}

describe("TelaCatalogo", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("lista por aba com título, conteúdo, situação e sem apagar", async () => {
    const itens = [
      item({ id_catalogo_item: 1, categoria: "horario", titulo: "Café da manhã" }),
      item({
        id_catalogo_item: 2,
        categoria: "horario",
        titulo: "Sauna",
        conteudo: "Em reforma.",
        ativo: false,
      }),
      item({
        id_catalogo_item: 3,
        categoria: "cardapio",
        titulo: "Feijoada",
        conteudo: "Sábados.",
      }),
    ];
    const fetchMock = fetchCatalogo(itens);
    vi.stubGlobal("fetch", fetchMock);
    renderCatalogo();

    expect(await screen.findByRole("heading", { name: "Catálogo" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/catalogo",
      expect.objectContaining({ credentials: "include" }),
    );
    for (const rotulo of ["Horários", "Cardápio", "Serviços", "Programação", "Regras"]) {
      expect(screen.getByRole("tab", { name: rotulo })).toBeInTheDocument();
    }
    expect(screen.getByText("Café da manhã")).toBeInTheDocument();
    expect(screen.getByText("Das 7h às 10h no salão.")).toBeInTheDocument();
    expect(screen.getByText("Sauna")).toBeInTheDocument();
    expect(screen.queryByText("Feijoada")).not.toBeInTheDocument();
    expect(screen.getByText(/1 ativos · 1 desativados/)).toBeInTheDocument();

    const ativo = screen.getByText("Café da manhã").closest("tr");
    expect(ativo).not.toBeNull();
    expect(within(ativo as HTMLElement).getByRole("button", { name: "Editar" })).toBeInTheDocument();
    expect(within(ativo as HTMLElement).getByRole("button", { name: "Desativar" })).toBeInTheDocument();
    expect(within(ativo as HTMLElement).queryByRole("button", { name: "Reativar" })).not.toBeInTheDocument();

    const inativo = screen.getByText("Sauna").closest("tr");
    expect(inativo).not.toBeNull();
    expect(within(inativo as HTMLElement).getByRole("button", { name: "Reativar" })).toBeInTheDocument();
    expect(within(inativo as HTMLElement).queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apagar" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Cardápio" }));
    expect(screen.getByText("Feijoada")).toBeInTheDocument();
    expect(screen.queryByText("Café da manhã")).not.toBeInTheDocument();
  });

  it("cria na aba visível, edita sem categoria, desativa e recusa clique na linha", async () => {
    const fetchMock = fetchCatalogo([
      item({ id_catalogo_item: 1, categoria: "cardapio", titulo: "Suco" }),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    renderCatalogo();

    fireEvent.click(await screen.findByRole("tab", { name: "Cardápio" }));
    fireEvent.click(screen.getByRole("button", { name: "+ Novo item" }));
    fireEvent.change(screen.getByLabelText("Título"), { target: { value: "Torta" } });
    fireEvent.change(screen.getByLabelText("Conteúdo"), { target: { value: "À tarde." } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      const post = fetchMock.mock.calls.find(
        (chamada) => chamada[0] === "/catalogo" && (chamada[1]?.method ?? "GET") === "POST",
      );
      expect(post).toBeDefined();
      expect(JSON.parse(String(post?.[1]?.body))).toEqual({
        categoria: "cardapio",
        titulo: "Torta",
        conteudo: "À tarde.",
      });
    });
    expect(await screen.findByText("Torta")).toBeInTheDocument();

    fireEvent.click(within(screen.getByText("Suco").closest("tr") as HTMLElement).getByRole("button", { name: "Editar" }));
    fireEvent.change(screen.getByLabelText("Título"), { target: { value: "Suco de laranja" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      const patch = fetchMock.mock.calls.find(
        (chamada) =>
          String(chamada[0]) === "/catalogo/1" && (chamada[1]?.method ?? "") === "PATCH",
      );
      expect(patch).toBeDefined();
      const corpo = JSON.parse(String(patch?.[1]?.body)) as Record<string, unknown>;
      expect(corpo).toEqual({ titulo: "Suco de laranja", conteudo: "Das 7h às 10h no salão." });
      expect(corpo).not.toHaveProperty("categoria");
    });

    fireEvent.click(
      within(screen.getByText("Suco de laranja").closest("tr") as HTMLElement).getByRole(
        "button",
        { name: "Desativar" },
      ),
    );
    await waitFor(() => {
      const patch = fetchMock.mock.calls.find(
        (chamada) =>
          String(chamada[0]) === "/catalogo/1" &&
          (chamada[1]?.method ?? "") === "PATCH" &&
          String(chamada[1]?.body).includes('"ativo":false'),
      );
      expect(patch).toBeDefined();
    });

    const antes = fetchMock.mock.calls.length;
    fireEvent.click(screen.getByText("Suco de laranja"));
    expect(fetchMock.mock.calls.length).toBe(antes);
  });

  it("lista vazia é distinta de falha", async () => {
    const fetchMock = fetchCatalogo([]);
    vi.stubGlobal("fetch", fetchMock);
    const visao = renderCatalogo();

    expect(await screen.findByText("Não há item nesta categoria.")).toBeInTheDocument();
    expect(screen.queryByText("A lista não carregou.")).not.toBeInTheDocument();
    visao.unmount();

    const falha = fetchCatalogo("erro");
    vi.stubGlobal("fetch", falha);
    renderCatalogo();
    expect(await screen.findByText("A lista não carregou.")).toBeInTheDocument();
    expect(screen.queryByText("Não há item nesta categoria.")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(await screen.findByText("Não há item nesta categoria.")).toBeInTheDocument();
  });

  it("mostra o detalhe do 422 no POST e não inventa o item", async () => {
    const fetchMock = fetchCatalogo([], (url, init) => {
      if (url === "/catalogo" && (init?.method ?? "GET") === "POST") {
        return json({ detail: "Informe o titulo." }, 422);
      }
      return null;
    });
    vi.stubGlobal("fetch", fetchMock);
    renderCatalogo();
    fireEvent.click(await screen.findByRole("button", { name: "+ Novo item" }));
    fireEvent.change(screen.getByLabelText("Título"), { target: { value: "   " } });
    fireEvent.change(screen.getByLabelText("Conteúdo"), { target: { value: "texto" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
    expect(await screen.findByText("Informe o titulo.")).toBeInTheDocument();
    expect(screen.queryByRole("cell", { name: "   " })).not.toBeInTheDocument();
  });

  it("desativar mantém o item na lista e não chama DELETE nem catálogo ativo", async () => {
    const fetchMock = fetchCatalogo([
      item({ id_catalogo_item: 1, categoria: "horario", titulo: "Café da manhã" }),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    renderCatalogo();

    fireEvent.click(await screen.findByRole("button", { name: "Desativar" }));
    expect(await screen.findByRole("button", { name: "Reativar" })).toBeInTheDocument();
    const linha = screen.getByText("Café da manhã").closest("tr") as HTMLElement;
    expect(within(linha).getByText("desativado")).toBeInTheDocument();

    expect(
      fetchMock.mock.calls.some((chamada) => (chamada[1]?.method ?? "").toUpperCase() === "DELETE"),
    ).toBe(false);
    expect(fetchMock.mock.calls.some((chamada) => String(chamada[0]) === "/catalogo/ativo")).toBe(
      false,
    );
  });
});
