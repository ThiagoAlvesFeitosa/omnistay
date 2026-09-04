import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelaPainel } from "./TelaPainel";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function fetchIndicadores(corpo: unknown | "erro") {
  let tentativas = 0;
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/indicadores" && metodo === "GET") {
      tentativas += 1;
      if (corpo === "erro" && tentativas === 1) {
        return json({ detail: "falha" }, 500);
      }
      return json(
        corpo === "erro"
          ? { chegadas_hoje: 0, hospedados: 0, chamados_abertos: 0, consumo_a_lancar: 0 }
          : corpo,
      );
    }
    return new Response(null, { status: 404 });
  });
}

function renderPainel() {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/indicadores"]}>
      <TelaPainel />
    </MemoryRouter>,
  );
}

describe("TelaPainel", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("busca GET /indicadores e mostra os quatro números", async () => {
    const fetchMock = fetchIndicadores({
      chegadas_hoje: 4,
      hospedados: 2,
      chamados_abertos: 5,
      consumo_a_lancar: 132,
    });
    vi.stubGlobal("fetch", fetchMock);
    renderPainel();

    expect(await screen.findByRole("heading", { name: "Painel" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/indicadores",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(screen.getByText("Chegadas hoje")).toBeInTheDocument();
    expect(screen.getByText("Hospedados")).toBeInTheDocument();
    expect(screen.getByText("Chamados em aberto")).toBeInTheDocument();
    expect(screen.getByText("Consumo a lançar")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("R$ 132,00")).toBeInTheDocument();

    const urls = fetchMock.mock.calls.map((chamada) => String(chamada[0]));
    expect(urls).not.toContain("/fila-do-dia");
    expect(urls).not.toContain("/solicitacoes");
    expect(urls).not.toContain("/consumos/pendentes");
    expect(urls).not.toContain("/indicadores/chegadas-do-dia");
    expect(screen.queryByText("Marina Duarte")).not.toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("zeros honestos não são recado de falha", async () => {
    vi.stubGlobal(
      "fetch",
      fetchIndicadores({
        chegadas_hoje: 0,
        hospedados: 0,
        chamados_abertos: 0,
        consumo_a_lancar: 0,
      }),
    );
    renderPainel();
    expect(await screen.findByText("Chegadas hoje")).toBeInTheDocument();
    expect(screen.getByText("R$ 0,00")).toBeInTheDocument();
    expect(screen.queryByText(/não carreg/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tentar de novo" })).not.toBeInTheDocument();
  });

  it("GET 500 declara falha e não mostra zeros como vazio", async () => {
    const fetchMock = fetchIndicadores("erro");
    vi.stubGlobal("fetch", fetchMock);
    renderPainel();

    expect(await screen.findByText(/não carreg/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tentar de novo" })).toBeInTheDocument();
    expect(screen.queryByText("Chegadas hoje")).not.toBeInTheDocument();
    expect(screen.queryByText("R$ 0,00")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(await screen.findByText("Chegadas hoje")).toBeInTheDocument();
    expect(screen.getByText("R$ 0,00")).toBeInTheDocument();
  });
});
