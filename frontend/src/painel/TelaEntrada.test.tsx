import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelaEntrada } from "./TelaEntrada";

function respostaJson(corpo: unknown, status: number): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("TelaEntrada", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("mostra e-mail, senha e Entrar", () => {
    render(
      <MemoryRouter>
        <TelaEntrada />
      </MemoryRouter>,
    );
    expect(screen.getByLabelText("E-mail")).toBeInTheDocument();
    expect(screen.getByLabelText("Senha")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument();
  });

  it("não chama fetch com campos em branco", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(
      <MemoryRouter>
        <TelaEntrada />
      </MemoryRouter>,
    );
    fireEvent.submit(screen.getByRole("button", { name: "Entrar" }).closest("form")!);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.getByText("Preencha e-mail e senha.")).toBeInTheDocument();
  });

  it("submit válido chama POST /sessoes", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      respostaJson(
        { id_usuario: 1, nome: "Cleber", perfil: "recepcao", expira_em: "2026-09-01T00:00:00Z" },
        201,
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(
      <MemoryRouter>
        <TelaEntrada />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText("E-mail"), {
      target: { value: "cleber@hotel.com" },
    });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "segredo-longo" } });
    fireEvent.submit(screen.getByRole("button", { name: "Entrar" }).closest("form")!);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(fetchMock.mock.calls[0][0]).toBe("/sessoes");
    expect(fetchMock.mock.calls[0][1].method).toBe("POST");
  });

  it("dois 401 mostram o mesmo texto e permanecem na entrada", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(respostaJson({ detail: "nao existe" }, 401))
      .mockResolvedValueOnce(respostaJson({ detail: "senha errada" }, 401));
    vi.stubGlobal("fetch", fetchMock);
    render(
      <MemoryRouter>
        <TelaEntrada />
      </MemoryRouter>,
    );

    async function tentar(): Promise<void> {
      fireEvent.change(screen.getByLabelText("E-mail"), {
        target: { value: "a@hotel.com" },
      });
      fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "xxxx" } });
      fireEvent.submit(screen.getByRole("button", { name: "Entrar" }).closest("form")!);
      await waitFor(() => expect(screen.getByText("Credenciais inválidas.")).toBeInTheDocument());
    }

    await tentar();
    const primeiro = screen.getByText("Credenciais inválidas.").textContent;
    fireEvent.change(screen.getByLabelText("E-mail"), {
      target: { value: "b@hotel.com" },
    });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "yyyy" } });
    fireEvent.submit(screen.getByRole("button", { name: "Entrar" }).closest("form")!);
    await waitFor(() => expect(screen.getByText("Credenciais inválidas.")).toBeInTheDocument());
    expect(screen.getByText("Credenciais inválidas.").textContent).toBe(primeiro);
    expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument();
  });
});
