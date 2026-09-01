import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ItemConsumoPendente } from "./consumos";
import { TelaSaida } from "./TelaSaida";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fichaHospedada = {
  id_reserva: 42,
  id_hospede: 7,
  ficha_completa: true,
  status_reserva: "hospedado",
  estado_cadastro: "completa",
  nome_completo: "Marina Duarte",
  telefone: "5511987654321",
};

function pendente(
  parcial: Partial<ItemConsumoPendente> & { id_solicitacao: number },
): ItemConsumoPendente {
  return {
    id_reserva: 42,
    descricao: "interno",
    descricao_item: "Lavanderia",
    numero_quarto: "210",
    valor_praticado: "32.00",
    status_lancamento: "pendente",
    aberta_em: "2026-08-29T15:00:00.000Z",
    resolvida_em: null,
    ...parcial,
  };
}

type Cargas = {
  ficha?: unknown | "erro" | "404";
  pedidos?: { itens: { descricao_item: string; valor_praticado: string | number }[]; total: number } | "erro" | "404";
  pendentes?: ItemConsumoPendente[];
  fila?: { id_reserva: number; data_checkin_prevista: string; data_checkout_prevista: string }[];
};

function fetchDaSaida(cargas: Cargas = {}) {
  const ficha = cargas.ficha ?? fichaHospedada;
  const pedidos = cargas.pedidos ?? {
    itens: [
      { descricao_item: "Lavanderia", valor_praticado: "32.00" },
      { descricao_item: "Frigobar", valor_praticado: 56 },
    ],
    total: 88,
  };
  const pendentes = cargas.pendentes ?? [];
  const fila = cargas.fila ?? [
    {
      id_reserva: 42,
      data_checkin_prevista: "2026-08-29",
      data_checkout_prevista: "2026-08-31",
    },
  ];
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/reservas/42/ficha" && metodo === "GET") {
      if (ficha === "erro") {
        return json({ detail: "falha" }, 500);
      }
      if (ficha === "404") {
        return json({ detail: "Reserva nao encontrada." }, 404);
      }
      return json(ficha);
    }
    if (url === "/reservas/42/pedidos-feitos-pelo-chat" && metodo === "GET") {
      if (pedidos === "erro") {
        return json({ detail: "falha" }, 500);
      }
      if (pedidos === "404") {
        return json({ detail: "Reserva nao encontrada." }, 404);
      }
      return json(pedidos);
    }
    if (url === "/consumos/pendentes" && metodo === "GET") {
      return json({ itens: pendentes });
    }
    if (url === "/fila-do-dia" && metodo === "GET") {
      return json({ itens: fila });
    }
    return new Response(null, { status: 404 });
  });
}

function renderSaida(rota: string, fetchMock: ReturnType<typeof vi.fn>) {
  vi.stubGlobal("fetch", fetchMock);
  return render(
    <MemoryRouter basename="/app" initialEntries={[rota]}>
      <Routes>
        <Route path="/saida/:idReserva?" element={<TelaSaida />} />
        <Route path="/consumos" element={<div data-testid="consumos" />} />
        <Route path="/fila" element={<div data-testid="fila" />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("TelaSaida", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("sem reserva não busca nada e aponta para a fila", async () => {
    const fetchMock = vi.fn();
    renderSaida("/app/saida", fetchMock);
    expect(await screen.findByRole("heading", { name: "Saída do hóspede" })).toBeInTheDocument();
    expect(screen.getByText(/abre pela fila do dia/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Confirmar saída" })).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("com reserva busca ficha, pedidos, pendentes e fila e mostra a lista cobrável", async () => {
    const fetchMock = fetchDaSaida({
      pendentes: [pendente({ id_solicitacao: 9, id_reserva: 99, descricao_item: "Outra estadia" })],
    });
    renderSaida("/app/saida/42", fetchMock);
    expect(await screen.findByText("Marina Duarte")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Pedidos feitos pelo chat" })).toBeInTheDocument();
    expect(screen.getByText("Lavanderia")).toBeInTheDocument();
    expect(screen.getByText("Frigobar")).toBeInTheDocument();
    expect(screen.getByText(/88/)).toBeInTheDocument();
    expect(screen.queryByText(/status_lancamento/i)).not.toBeInTheDocument();
    const corpo = (document.body.textContent ?? "").toLowerCase();
    expect(corpo).not.toMatch(/extrato|\bconta\b/);
    expect(screen.queryByText(/consumo pendente/i)).not.toBeInTheDocument();
    const gets = fetchMock.mock.calls.filter((chamada) => (chamada[1]?.method ?? "GET") === "GET");
    expect(gets.map((chamada) => chamada[0])).toEqual(
      expect.arrayContaining([
        "/reservas/42/ficha",
        "/reservas/42/pedidos-feitos-pelo-chat",
        "/consumos/pendentes",
        "/fila-do-dia",
      ]),
    );
    for (const chamada of gets) {
      expect(chamada[1]).toEqual(expect.objectContaining({ credentials: "include" }));
    }
  });

  it("aviso de pendência da estadia aponta para Consumos a lançar da casa", async () => {
    const fetchMock = fetchDaSaida({
      pendentes: [
        pendente({ id_solicitacao: 1, id_reserva: 42, numero_quarto: "210" }),
        pendente({ id_solicitacao: 2, id_reserva: 7 }),
      ],
    });
    renderSaida("/app/saida/42", fetchMock);
    expect(await screen.findByText(/consumo pendente/i)).toBeInTheDocument();
    const aviso = screen.getByRole("link", { name: /consumos a lançar/i });
    expect(aviso).toHaveAttribute("href", expect.stringMatching(/\/consumos$/));
    expect(aviso.getAttribute("href")).not.toMatch(/reserva=/);
  });

  it("pedidos vazios são lista honesta, sem aviso de pendência", async () => {
    const fetchMock = fetchDaSaida({ pedidos: { itens: [], total: 0 } });
    renderSaida("/app/saida/42", fetchMock);
    expect(await screen.findByText("Marina Duarte")).toBeInTheDocument();
    expect(screen.getByText(/nenhum pedido feito pelo chat/i)).toBeInTheDocument();
    expect(screen.queryByText(/consumo pendente/i)).not.toBeInTheDocument();
  });

  it("falha de leitura não se disfarça de vazio e tentar de novo recupera", async () => {
    let falhou = true;
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (falhou && metodo === "GET" && url === "/reservas/42/pedidos-feitos-pelo-chat") {
        return json({ detail: "falha" }, 500);
      }
      if (url === "/reservas/42/ficha") {
        return json(fichaHospedada);
      }
      if (url === "/reservas/42/pedidos-feitos-pelo-chat") {
        return json({ itens: [{ descricao_item: "Lavanderia", valor_praticado: "32.00" }], total: 32 });
      }
      if (url === "/consumos/pendentes") {
        return json({ itens: [] });
      }
      if (url === "/fila-do-dia") {
        return json({ itens: [] });
      }
      return new Response(null, { status: 404 });
    });
    renderSaida("/app/saida/42", fetchMock);
    expect(await screen.findByText(/não carregou/i)).toBeInTheDocument();
    expect(screen.queryByText(/nenhum pedido feito pelo chat/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Confirmar saída" })).not.toBeInTheDocument();
    falhou = false;
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(await screen.findByText("Lavanderia")).toBeInTheDocument();
  });

  it("404 é recado genérico, sem nome", async () => {
    renderSaida("/app/saida/42", fetchDaSaida({ ficha: "404" }));
    expect(await screen.findByText(/nao encontrada/i)).toBeInTheDocument();
    expect(screen.queryByText("Marina Duarte")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Confirmar saída" })).not.toBeInTheDocument();
  });

  it("Confirmar saída faz POST e some o botão mesmo com pendência", async () => {
    const fetchMock = fetchDaSaida({
      pendentes: [pendente({ id_solicitacao: 1, id_reserva: 42 })],
    });
    fetchMock.mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/reservas/42/saida" && metodo === "POST") {
        return json({ id_reserva: 42, status: "encerrado" });
      }
      const original = fetchDaSaida({
        pendentes: [pendente({ id_solicitacao: 1, id_reserva: 42 })],
      });
      return original(url, init);
    });
    renderSaida("/app/saida/42", fetchMock);
    expect(await screen.findByRole("button", { name: "Confirmar saída" })).toBeInTheDocument();
    fireEvent.click(screen.getByText("Lavanderia"));
    fireEvent.click(screen.getByText(/consumo pendente/i));
    expect(
      fetchMock.mock.calls.filter(
        (chamada) => String(chamada[0]).includes("/saida") && (chamada[1]?.method ?? "GET") === "POST",
      ),
    ).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "Confirmar saída" }));
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Confirmar saída" })).not.toBeInTheDocument(),
    );
    expect(screen.getByText("Lavanderia")).toBeInTheDocument();
    expect(screen.getByText(/consumo pendente/i)).toBeInTheDocument();
    const posts = fetchMock.mock.calls.filter(
      (chamada) => chamada[0] === "/reservas/42/saida" && chamada[1]?.method === "POST",
    );
    expect(posts).toHaveLength(1);
    expect(posts[0][1]).toEqual(expect.objectContaining({ credentials: "include", method: "POST" }));
    expect(posts[0][1]?.body).toBeUndefined();
    expect(screen.queryByText(/tem certeza/i)).not.toBeInTheDocument();
  });

  it("ficha encerrada não oferece Confirmar saída", async () => {
    renderSaida(
      "/app/saida/42",
      fetchDaSaida({ ficha: { ...fichaHospedada, status_reserva: "encerrado" } }),
    );
    expect(await screen.findByText("Marina Duarte")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Confirmar saída" })).not.toBeInTheDocument();
  });

  it("409 de saída mostra o motivo e não afirma encerrado", async () => {
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/reservas/42/saida" && metodo === "POST") {
        return json({ detail: "Reserva ja encerrada." }, 409);
      }
      return fetchDaSaida()(url, init);
    });
    renderSaida("/app/saida/42", fetchMock);
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar saída" }));
    expect(await screen.findByText(/ja encerrada/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar saída" })).toBeInTheDocument();
    expect(screen.queryByText(/encerrado/i)).not.toBeInTheDocument();
  });
});
