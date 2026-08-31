import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ItemFila } from "./fila";
import { TelaFila } from "./TelaFila";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function item(parcial: Partial<ItemFila> & { id_reserva: number; nome: string }): ItemFila {
  return {
    telefone_contato: "5511987654321",
    data_checkin_prevista: "2026-08-31",
    data_checkout_prevista: "2026-09-02",
    status: "aguardando_cadastro",
    estado_cadastro: "aguardando",
    chegada_nao_confirmada: false,
    boas_vindas_nao_enviadas: false,
    ...parcial,
  };
}

function fetchFila(itens: ItemFila[] | "erro", extras?: (url: string, init?: RequestInit) => Response | null) {
  let tentativasGet = 0;
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const extra = extras?.(url, init);
    if (extra) {
      return extra;
    }
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/fila-do-dia" && metodo === "GET") {
      tentativasGet += 1;
      if (itens === "erro") {
        if (tentativasGet === 1) {
          return json({ detail: "falha" }, 500);
        }
        return json({
          itens: [item({ id_reserva: 9, nome: "Recuperada" })],
        });
      }
      return json({ itens });
    }
    return new Response(null, { status: 404 });
  });
}

function renderFila() {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/fila"]}>
      <TelaFila />
    </MemoryRouter>,
  );
}

describe("TelaFila", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("busca a fila e mostra nome, telefone, datas e o resumo", async () => {
    const itens = [
      item({ id_reserva: 1, nome: "Marina Duarte", status: "ficha_recebida", estado_cadastro: "completa" }),
      item({
        id_reserva: 2,
        nome: "Carlos Beltrão",
        status: "hospedado",
        estado_cadastro: "completa",
      }),
      item({
        id_reserva: 3,
        nome: "Ana Prado",
        status: "ficha_parcial",
        estado_cadastro: "parcial",
        chegada_nao_confirmada: true,
        data_checkin_prevista: "2026-08-30",
      }),
    ];
    const fetchMock = fetchFila(itens);
    vi.stubGlobal("fetch", fetchMock);
    renderFila();

    expect(await screen.findByText("Marina Duarte")).toBeInTheDocument();
    expect(screen.getByText("Carlos Beltrão")).toBeInTheDocument();
    expect(screen.getByText("Ana Prado")).toBeInTheDocument();
    expect(screen.getAllByText("5511987654321").length).toBeGreaterThan(0);
    expect(screen.getAllByText("2026-08-31").length).toBeGreaterThan(0);
    expect(screen.queryByText("Hóspede futuro")).not.toBeInTheDocument();

    expect(screen.getByText(/1 hoje sem confirmar/)).toBeInTheDocument();
    expect(screen.getByText(/1 hospedados/)).toBeInTheDocument();
    expect(screen.getByText(/1 entrada vencida/)).toBeInTheDocument();

    const gets = fetchMock.mock.calls.filter(
      (chamada) => chamada[0] === "/fila-do-dia" && (chamada[1]?.method ?? "GET") === "GET",
    );
    expect(gets.length).toBeGreaterThanOrEqual(1);
    expect(gets[0][1]).toEqual(expect.objectContaining({ credentials: "include" }));
  });

  it("fila vazia zera o resumo e oferece nova reserva, sem recado de falha", async () => {
    vi.stubGlobal("fetch", fetchFila([]));
    renderFila();
    expect(await screen.findByText(/ninguém no turno/i)).toBeInTheDocument();
    expect(screen.getByText(/0 hoje sem confirmar/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Nova reserva" })).toBeInTheDocument();
    expect(screen.queryByText(/não foi possível carregar/i)).not.toBeInTheDocument();
  });

  it("falha de leitura não se disfarça de vazio e tentar de novo recupera", async () => {
    vi.stubGlobal("fetch", fetchFila("erro"));
    renderFila();
    expect(await screen.findByText(/não foi possível carregar a fila/i)).toBeInTheDocument();
    expect(screen.queryByText(/ninguém no turno/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(await screen.findByText("Recuperada")).toBeInTheDocument();
  });

  it("oferece Confirmar chegada só no botão da linha elegível", async () => {
    const inicial = [
      item({ id_reserva: 10, nome: "Elegível", status: "ficha_recebida", estado_cadastro: "completa" }),
      item({ id_reserva: 11, nome: "Aguardando", status: "aguardando_cadastro" }),
      item({ id_reserva: 12, nome: "Já no hotel", status: "hospedado", estado_cadastro: "completa" }),
    ];
    let itens = inicial;
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/fila-do-dia" && metodo === "GET") {
        return json({ itens });
      }
      if (url === "/reservas/10/chegada" && metodo === "POST") {
        itens = [
          item({
            id_reserva: 10,
            nome: "Elegível",
            status: "hospedado",
            estado_cadastro: "completa",
          }),
          inicial[1],
          inicial[2],
        ];
        return json({ id_reserva: 10, status: "hospedado", boas_vindas: "agendada" });
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderFila();
    expect(await screen.findByText("Elegível")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Confirmar chegada" })).toHaveLength(1);

    fireEvent.click(screen.getByText("Elegível"));
    expect(
      fetchMock.mock.calls.filter((chamada) => String(chamada[0]).includes("/chegada")),
    ).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Confirmar chegada" }));
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: "Confirmar chegada" })).not.toBeInTheDocument();
    });
    expect(screen.getByText("Elegível").closest("tr")).toHaveTextContent("hospedado");
    expect(screen.queryByText(/tem certeza/i)).not.toBeInTheDocument();
    const posts = fetchMock.mock.calls.filter(
      (chamada) => chamada[0] === "/reservas/10/chegada" && chamada[1]?.method === "POST",
    );
    expect(posts).toHaveLength(1);
    expect(posts[0][1]).toEqual(
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
    expect(posts[0][1]?.body).toBeUndefined();
    const gets = fetchMock.mock.calls.filter((chamada) => chamada[0] === "/fila-do-dia");
    expect(gets.length).toBeGreaterThanOrEqual(2);
  });

  it("409 mostra o motivo e não afirma hospedado", async () => {
    const linha = item({
      id_reserva: 20,
      nome: "Corrida",
      status: "ficha_recebida",
      estado_cadastro: "completa",
    });
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/fila-do-dia" && metodo === "GET") {
        return json({ itens: [linha] });
      }
      if (String(url).includes("/chegada") && metodo === "POST") {
        return json({ detail: "Reserva já hospedada." }, 409);
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderFila();
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar chegada" }));
    expect(await screen.findByText("Reserva já hospedada.")).toBeInTheDocument();
    expect(screen.getByText("ficha recebida")).toBeInTheDocument();
    expect(screen.queryByText("hospedado")).not.toBeInTheDocument();
  });

  it("distingue as três pendências com rótulos diferentes", async () => {
    vi.stubGlobal(
      "fetch",
      fetchFila([
        item({
          id_reserva: 31,
          nome: "Parcial",
          status: "ficha_parcial",
          estado_cadastro: "parcial",
        }),
        item({
          id_reserva: 32,
          nome: "Sem recado",
          status: "hospedado",
          estado_cadastro: "completa",
          boas_vindas_nao_enviadas: true,
        }),
        item({
          id_reserva: 33,
          nome: "Vencida",
          status: "ficha_recebida",
          estado_cadastro: "completa",
          chegada_nao_confirmada: true,
        }),
        item({
          id_reserva: 34,
          nome: "Em dia",
          status: "hospedado",
          estado_cadastro: "completa",
        }),
      ]),
    );
    renderFila();
    expect(await screen.findByText("parcial", { exact: true })).toBeInTheDocument();
    expect(screen.getByText("recado não enviado")).toBeInTheDocument();
    expect(screen.getByText("não confirmada")).toBeInTheDocument();
    expect(screen.getByText("Em dia").closest("tr")).not.toHaveTextContent("parcial");
    expect(screen.getByText("Em dia").closest("tr")).not.toHaveTextContent("recado não enviado");
    expect(screen.getByText("Em dia").closest("tr")).not.toHaveTextContent("não confirmada");
  });
});
