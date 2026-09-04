import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelaNovaReserva } from "./TelaNovaReserva";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function Localizacao() {
  const loc = useLocation();
  const aviso = (loc.state as { aviso?: string } | null)?.aviso ?? "";
  return (
    <>
      <div data-testid="path">{loc.pathname}</div>
      <div data-testid="aviso">{aviso}</div>
      <TelaNovaReserva />
    </>
  );
}

function renderCadastro() {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/reserva"]}>
      <Localizacao />
    </MemoryRouter>,
  );
}

function preencherValido(entrada = "2026-08-31", saida = "2026-09-02") {
  fireEvent.change(screen.getByLabelText("Nome do hóspede"), {
    target: { value: "Marina Duarte" },
  });
  fireEvent.change(screen.getByLabelText("Telefone com DDD"), {
    target: { value: "(11) 98765-4321" },
  });
  fireEvent.change(screen.getByLabelText("Entrada"), { target: { value: entrada } });
  fireEvent.change(screen.getByLabelText("Saída"), { target: { value: saida } });
}

describe("TelaNovaReserva", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("pede só nome, telefone e datas, sem e-mail", () => {
    renderCadastro();
    expect(screen.getByLabelText("Nome do hóspede")).toBeInTheDocument();
    expect(screen.getByLabelText("Telefone com DDD")).toBeInTheDocument();
    expect(screen.getByLabelText("Entrada")).toHaveAttribute("type", "date");
    expect(screen.getByLabelText("Saída")).toHaveAttribute("type", "date");
    expect(screen.queryByLabelText(/e-mail/i)).not.toBeInTheDocument();
  });

  it("não dispara POST com campos em branco", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderCadastro();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("telefone ilegível na digitação não dispara POST", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderCadastro();
    fireEvent.change(screen.getByLabelText("Nome do hóspede"), { target: { value: "Ana" } });
    fireEvent.change(screen.getByLabelText("Telefone com DDD"), { target: { value: "123" } });
    fireEvent.change(screen.getByLabelText("Entrada"), { target: { value: "2026-08-31" } });
    fireEvent.change(screen.getByLabelText("Saída"), { target: { value: "2026-09-02" } });
    expect(screen.getByText(/brasileiro com DDD/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("datas invertidas não disparam POST", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderCadastro();
    preencherValido("2026-09-02", "2026-08-31");
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.getByText(/saída.*posterior|depois da entrada/i)).toBeInTheDocument();
  });

  it("submit válido posta JSON ISO e volta à fila quando a reserva aparece", async () => {
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/reservas" && metodo === "POST") {
        return json(
          {
            id_reserva: 42,
            nome: "Marina Duarte",
            telefone_contato: "5511987654321",
            data_checkin_prevista: "2026-08-31",
            data_checkout_prevista: "2026-09-02",
            status: "aguardando_cadastro",
          },
          201,
        );
      }
      if (url === "/fila-do-dia" && metodo === "GET") {
        return json({
          itens: [
            {
              id_reserva: 42,
              nome: "Marina Duarte",
              telefone_contato: "5511987654321",
              data_checkin_prevista: "2026-08-31",
              data_checkout_prevista: "2026-09-02",
              status: "aguardando_cadastro",
              estado_cadastro: "aguardando",
              chegada_nao_confirmada: false,
              boas_vindas_nao_enviadas: false,
              precisa_atendimento_humano: false,
              saida_nao_confirmada: false,
            },
          ],
        });
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderCadastro();
    preencherValido();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
    await waitFor(() => expect(screen.getByTestId("path")).toHaveTextContent("/fila"));
    const post = fetchMock.mock.calls.find(
      (chamada) => chamada[0] === "/reservas" && chamada[1]?.method === "POST",
    );
    expect(post).toBeDefined();
    expect(post?.[1]).toEqual(expect.objectContaining({ credentials: "include" }));
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({
      nome: "Marina Duarte",
      telefone: "(11) 98765-4321",
      data_checkin_prevista: "2026-08-31",
      data_checkout_prevista: "2026-09-02",
    });
    expect(screen.getByTestId("aviso")).toHaveTextContent("");
  });

  it("cadastro futuro avisa que entra no dia da entrada", async () => {
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/reservas" && metodo === "POST") {
        return json({ id_reserva: 99, status: "aguardando_cadastro" }, 201);
      }
      if (url === "/fila-do-dia" && metodo === "GET") {
        return json({ itens: [] });
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderCadastro();
    preencherValido("2026-12-01", "2026-12-05");
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
    await waitFor(() => expect(screen.getByTestId("path")).toHaveTextContent("/fila"));
    expect(screen.getByTestId("aviso")).toHaveTextContent(/entra na fila no dia da entrada/i);
  });

  it("Cancelar volta à fila sem POST", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderCadastro();
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.getByTestId("path")).toHaveTextContent("/fila");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
