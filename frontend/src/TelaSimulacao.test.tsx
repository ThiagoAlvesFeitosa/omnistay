import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelaSimulacao } from "./TelaSimulacao";
import { formatarHorarioBolha } from "./painel/apresentacao";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const hoje = new Date();
const enviadaHoje = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate(), 14, 32, 0).toISOString();
const enviadaOutroDia = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() - 2, 14, 32, 0).toISOString();

const conversa = {
  id_reserva: 7,
  status: "hospedado",
  nome_titular: "Marina Duarte",
  telefone_contato: "5511999",
};

function fetchSimulador(posts: unknown[] = []) {
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/simulador/conversas" && metodo === "GET") {
      return json({ conversas: [conversa] });
    }
    if (url === "/simulador/conversas/7" && metodo === "GET") {
      return json({
        ...conversa,
        mensagens: [
          {
            id_mensagem: 1,
            direcao: "recebida",
            conteudo: "tem berco?",
            status_envio: null,
            enviada_em: enviadaHoje,
          },
          {
            id_mensagem: 2,
            direcao: "enviada",
            conteudo: "Sim, temos.",
            status_envio: "enviada",
            enviada_em: enviadaOutroDia,
          },
        ],
      });
    }
    if (String(url).includes("/mensagens") && metodo === "POST") {
      posts.push(await new Response((init?.body as string) ?? "{}").json());
      return json({ ok: true }, 201);
    }
    return json({});
  });
}

describe("TelaSimulacao", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("usa a tipografia da casca, cartões e dois lados de bolha", async () => {
    vi.stubGlobal("fetch", fetchSimulador());
    const { container } = render(<TelaSimulacao />);
    expect(await screen.findByText(/Marina Duarte/)).toBeInTheDocument();
    expect(container.innerHTML).not.toMatch(/Georgia/i);
    fireEvent.click(screen.getByRole("button", { name: /Marina Duarte/ }));
    expect(await screen.findByText("tem berco?")).toBeInTheDocument();
    expect(screen.getByText("tem berco?").closest("[data-lado]")).toHaveAttribute("data-lado", "hospede");
    expect(screen.getByText("Sim, temos.").closest("[data-lado]")).toHaveAttribute("data-lado", "hotel");
    expect(screen.getByText(formatarHorarioBolha(enviadaHoje, new Date()))).toBeInTheDocument();
    expect(screen.getByText(formatarHorarioBolha(enviadaOutroDia, new Date()))).toBeInTheDocument();
  });

  it("Enter envia e Shift+Enter não envia; vazio não inventa POST", async () => {
    const posts: unknown[] = [];
    vi.stubGlobal("fetch", fetchSimulador(posts));
    render(<TelaSimulacao />);
    fireEvent.click(await screen.findByRole("button", { name: /Marina Duarte/ }));
    const campo = await screen.findByPlaceholderText("Falar como o hóspede");
    fireEvent.keyDown(campo, { key: "Enter", shiftKey: false });
    expect(posts).toHaveLength(0);
    fireEvent.change(campo, { target: { value: "olá" } });
    fireEvent.keyDown(campo, { key: "Enter", shiftKey: true });
    expect(posts).toHaveLength(0);
    fireEvent.keyDown(campo, { key: "Enter", shiftKey: false });
    await waitFor(() => expect(posts).toHaveLength(1));
  });
});
