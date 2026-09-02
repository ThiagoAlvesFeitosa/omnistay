import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelaMercado } from "./TelaMercado";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const visao = {
  periodicidade_horas: 24,
  concorrentes: [
    {
      id_concorrente: 1,
      nome: "Hotel Atlântico",
      ativo: true,
      situacao: "atual",
      ultimo_sucesso: {
        preco: 180,
        nota_media: 8.2,
        coletado_em: "2026-09-01T10:00:00Z",
      },
      ultima_falha: null,
    },
    {
      id_concorrente: 2,
      nome: "Pousada Mar",
      ativo: true,
      situacao: "desatualizado",
      ultimo_sucesso: {
        preco: 150,
        nota_media: 7.1,
        coletado_em: "2026-08-20T10:00:00Z",
      },
      ultima_falha: { coletado_em: "2026-09-01T08:00:00Z" },
    },
    {
      id_concorrente: 3,
      nome: "Só falha",
      ativo: true,
      situacao: "so_falha",
      ultimo_sucesso: null,
      ultima_falha: { coletado_em: "2026-09-01T09:00:00Z" },
    },
    {
      id_concorrente: 4,
      nome: "Sem coleta",
      ativo: true,
      situacao: "sem_coleta",
      ultimo_sucesso: null,
      ultima_falha: null,
    },
    {
      id_concorrente: 5,
      nome: "Zero datado",
      ativo: false,
      situacao: "atual",
      ultimo_sucesso: {
        preco: 0,
        nota_media: null,
        coletado_em: "2026-09-01T11:00:00Z",
      },
      ultima_falha: null,
    },
  ],
};

function fetchMercado(opcoes?: { historico?: unknown; historicoStatus?: number }) {
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/mercado" && metodo === "GET") {
      return json(visao);
    }
    if (url === "/mercado/concorrentes/1" && metodo === "GET") {
      if (opcoes?.historicoStatus === 404) {
        return json({ detail: "Nao encontrado." }, 404);
      }
      return json(
        opcoes?.historico ?? {
          id_concorrente: 1,
          nome: "Hotel Atlântico",
          ativo: true,
          coletas: [
            {
              id_coleta: 10,
              sucesso: true,
              preco: 170,
              nota_media: 8.0,
              coletado_em: "2026-08-30T10:00:00Z",
            },
            {
              id_coleta: 11,
              sucesso: false,
              preco: null,
              nota_media: null,
              coletado_em: "2026-08-31T10:00:00Z",
            },
            {
              id_coleta: 12,
              sucesso: true,
              preco: 180,
              nota_media: 8.2,
              coletado_em: "2026-09-01T10:00:00Z",
            },
          ],
        },
      );
    }
    return new Response(null, { status: 404 });
  });
}

function renderMercado() {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/mercado"]}>
      <TelaMercado />
    </MemoryRouter>,
  );
}

describe("TelaMercado", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("lista nome, preço datado, falha visível e sem tarifa da casa", async () => {
    const fetchMock = fetchMercado();
    vi.stubGlobal("fetch", fetchMock);
    renderMercado();

    expect(await screen.findByRole("heading", { name: "Mercado" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/mercado",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(screen.getByText("Hotel Atlântico")).toBeInTheDocument();
    expect(screen.getByText("180.00")).toBeInTheDocument();
    expect(screen.getAllByText(/2026-09-01/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Pousada Mar")).toBeInTheDocument();
    expect(screen.getByText("150.00")).toBeInTheDocument();
    expect(screen.getByText(/2026-08-20/)).toBeInTheDocument();
    expect(screen.getAllByText(/Coleta falhou/).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Ainda sem coleta")).toBeInTheDocument();
    expect(screen.getByText("0.00")).toBeInTheDocument();
    expect(screen.queryByText(/^você$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/tarifa da casa/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /novo concorrente/i })).not.toBeInTheDocument();

    const escritas = fetchMock.mock.calls.filter((chamada) => {
      const metodo = (chamada[1]?.method ?? "GET").toUpperCase();
      return metodo === "POST" || metodo === "PATCH";
    });
    expect(escritas).toHaveLength(0);
    expect(
      fetchMock.mock.calls.some((chamada) => String(chamada[0]).includes("/mercado/concorrentes/")),
    ).toBe(false);
  });

  it("histórico só no clique, falha intercalada sem preço 0 e 404 preserva a visão", async () => {
    const fetchMock = fetchMercado();
    vi.stubGlobal("fetch", fetchMock);
    const primeira = renderMercado();
    expect(await screen.findByText("Hotel Atlântico")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Histórico de Hotel Atlântico" }));
    expect(await screen.findByText("170.00")).toBeInTheDocument();
    expect(screen.getByText(/2026-08-31/)).toBeInTheDocument();
    const zerosDoHistorico = screen.queryAllByText("0.00");
    expect(zerosDoHistorico).toHaveLength(1);

    const historico = fetchMock.mock.calls.filter(
      (chamada) => chamada[0] === "/mercado/concorrentes/1",
    );
    expect(historico).toHaveLength(1);
    expect(historico[0][1]).toEqual(expect.objectContaining({ credentials: "include" }));
    primeira.unmount();

    const fetch404 = fetchMercado({ historicoStatus: 404 });
    vi.stubGlobal("fetch", fetch404);
    renderMercado();
    expect(await screen.findByText("Hotel Atlântico")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Histórico de Hotel Atlântico" }));
    expect(await screen.findByText(/não carreg/i)).toBeInTheDocument();
    expect(screen.getByText("Hotel Atlântico")).toBeInTheDocument();
    expect(screen.getByText("180.00")).toBeInTheDocument();
  });
});
