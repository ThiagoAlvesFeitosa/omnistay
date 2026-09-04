import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { formatarInstante } from "./apresentacao";
import { TelaRetencao } from "./TelaRetencao";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function fetchRetencao(corpo: unknown | "erro") {
  let tentativas = 0;
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/retencao" && metodo === "GET") {
      tentativas += 1;
      if (corpo === "erro" && tentativas === 1) {
        return json({ detail: "falha" }, 500);
      }
      return json(
        corpo === "erro"
          ? { execucoes: [], meses_retencao_conteudo_livre: null, anos_retencao_ficha: null }
          : corpo,
      );
    }
    return new Response(null, { status: 404 });
  });
}

function renderRetencao() {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/retencao"]}>
      <TelaRetencao />
    </MemoryRouter>,
  );
}

describe("TelaRetencao", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("mostra prazos, execuções com zero e não dispara expurgo", async () => {
    const fetchMock = fetchRetencao({
      meses_retencao_conteudo_livre: 12,
      anos_retencao_ficha: 5,
      execucoes: [
        {
          id_execucao: 1,
          executado_em: "2026-09-01T12:00:00Z",
          mensagens_anonimizadas: 2,
          comentarios_anonimizados: 0,
          payloads_anonimizados: 1,
          descricoes_anonimizadas: 0,
          fichas_apagadas: 0,
          prazo_conteudo_ausente: false,
          prazo_ficha_ausente: false,
        },
      ],
    });
    vi.stubGlobal("fetch", fetchMock);
    renderRetencao();

    expect(await screen.findByRole("heading", { name: "Retenção de dados" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/retencao",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText(formatarInstante("2026-09-01T12:00:00Z"))).toBeInTheDocument();
    expect(screen.queryByText(/2026-09-01/)).not.toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /expurgar/i })).not.toBeInTheDocument();
    expect(screen.queryByText("Marina")).not.toBeInTheDocument();
  });

  it("prazo null não vira 12 ou 5; vazio honesto ≠ falha", async () => {
    vi.stubGlobal(
      "fetch",
      fetchRetencao({
        meses_retencao_conteudo_livre: null,
        anos_retencao_ficha: null,
        execucoes: [],
      }),
    );
    renderRetencao();
    expect(await screen.findAllByText("Prazo não configurado")).toHaveLength(2);
    expect(screen.getByText(/ainda não houve/i)).toBeInTheDocument();
    expect(screen.queryByText(/não carreg/i)).not.toBeInTheDocument();
  });

  it("GET 500 não finge lista vazia", async () => {
    vi.stubGlobal("fetch", fetchRetencao("erro"));
    renderRetencao();
    expect(await screen.findByText(/não carreg/i)).toBeInTheDocument();
    expect(screen.queryByText(/ainda não houve/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(await screen.findByText(/ainda não houve/i)).toBeInTheDocument();
  });
});
