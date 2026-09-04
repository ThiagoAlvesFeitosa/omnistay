import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelaEstadia } from "./TelaEstadia";
import { formatarHorarioBolha } from "./apresentacao";
import type { FichaResposta } from "./TelaFicha";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fichaParcial: FichaResposta = {
  id_reserva: 1042,
  id_hospede: 7,
  ficha_completa: false,
  status_reserva: "ficha_parcial",
  estado_cadastro: "parcial",
  nome_completo: "Marina Duarte",
  profissao: null,
  data_nascimento: null,
  tipo_documento: null,
  numero_documento: null,
  endereco: null,
  cep: null,
  cidade: null,
  telefone: "5511987654321",
};

const conversaAberta = {
  id_reserva: 1042,
  janela: { aberta: true, motivo: null },
  mensagens: [
    {
      id_mensagem: 1,
      direcao: "recebida",
      origem: "hospede",
      conteudo: "tem berco?",
      status_envio: null,
      entrega: null,
      nova_tentativa: null,
      em: "2026-09-02T18:00:00Z",
    },
    {
      id_mensagem: 2,
      direcao: "enviada",
      origem: "automatico",
      conteudo: "A recepção vai atender.",
      status_envio: "enviada",
      entrega: "enviada",
      nova_tentativa: false,
      em: "2026-09-02T18:01:00Z",
    },
    {
      id_mensagem: 3,
      direcao: "enviada",
      origem: "recepcao",
      conteudo: "Sim, temos berço.",
      status_envio: "pendente",
      entrega: "enviando",
      nova_tentativa: false,
      em: "2026-09-02T18:02:00Z",
    },
  ],
};

function fetchEstadia(conversa = conversaAberta, ficha: FichaResposta = fichaParcial) {
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (String(url).includes("/conversa") && metodo === "GET") {
      return json(conversa);
    }
    if (String(url).includes("/consentimento")) {
      return json({
        id_hospede: 7,
        finalidade: "comunicacao_marketing",
        concedido: false,
        momento: null,
        origem: null,
        em: "2026-08-31T00:00:00Z",
      });
    }
    if (String(url).includes("/ficha")) {
      return json(ficha);
    }
    return json({});
  });
}

function renderEstadia(rota: string, fetchMock: ReturnType<typeof vi.fn>) {
  vi.stubGlobal("fetch", fetchMock);
  return render(
    <MemoryRouter basename="/app" initialEntries={[rota]}>
      <Routes>
        <Route path="/ficha/:idReserva?" element={<TelaEstadia />} />
        <Route path="/fila" element={<div data-testid="fila" />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("TelaEstadia", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("menu sem reserva não busca conversa nem ficha", async () => {
    const fetchMock = vi.fn();
    renderEstadia("/app/ficha", fetchMock);
    expect(await screen.findByText(/abre pela fila do dia/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Estadia" })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("ao abrir busca a conversa antes da ficha e mostra o fio sem cadastrais", async () => {
    const fetchMock = fetchEstadia();
    renderEstadia("/app/ficha/1042", fetchMock);
    expect(await screen.findByText("tem berco?")).toBeInTheDocument();
    expect(screen.getByText("Hóspede")).toBeInTheDocument();
    expect(screen.getByText("Automático")).toBeInTheDocument();
    expect(screen.getByText("Recepção")).toBeInTheDocument();
    expect(screen.getByText("enviando")).toBeInTheDocument();
    expect(screen.getByText("tem berco?").closest("[data-lado]")).toHaveAttribute("data-lado", "hospede");
    expect(screen.getByText("A recepção vai atender.").closest("[data-lado]")).toHaveAttribute(
      "data-lado",
      "hotel",
    );
    expect(screen.getByText("Sim, temos berço.").closest("[data-lado]")).toHaveAttribute("data-lado", "hotel");
    expect(
      screen.getByText(formatarHorarioBolha(conversaAberta.mensagens[0].em, new Date())),
    ).toBeInTheDocument();
    expect(screen.queryByText("Marina Duarte")).not.toBeInTheDocument();
    const ordem = fetchMock.mock.calls.map((chamada) => String(chamada[0]));
    const iConversa = ordem.findIndex((url) => url.includes("/conversa"));
    const iFicha = ordem.findIndex((url) => url.includes("/ficha"));
    expect(iConversa).toBeGreaterThanOrEqual(0);
    expect(iFicha).toBe(-1);
  });

  it("ver dados cadastrais dispara o GET da ficha e o copiar permanece no bloco", async () => {
    const fetchMock = fetchEstadia();
    renderEstadia("/app/ficha/1042", fetchMock);
    fireEvent.click(await screen.findByRole("button", { name: "ver dados cadastrais" }));
    expect((await screen.findAllByText("Marina Duarte")).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Copiar tudo" })).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some((chamada) => String(chamada[0]).includes("/reservas/1042/ficha")),
    ).toBe(true);
  });

  it("mostra enviada, falhou e nova tentativa marcada", async () => {
    const fetchMock = fetchEstadia({
      ...conversaAberta,
      mensagens: [
        {
          ...conversaAberta.mensagens[2],
          entrega: "enviada",
          status_envio: "enviada",
        },
        {
          ...conversaAberta.mensagens[2],
          id_mensagem: 4,
          entrega: "falhou",
          nova_tentativa: true,
          conteudo: "Vamos levar toalha.",
        },
      ],
    });
    renderEstadia("/app/ficha/1042", fetchMock);
    expect(await screen.findByText("enviada")).toBeInTheDocument();
    expect(screen.getByText("falhou · nova tentativa marcada")).toBeInTheDocument();
    expect(screen.getByText("Vamos levar toalha.")).toBeInTheDocument();
  });

  it("Enviar fica inerte durante o POST e Enter não dispara envio", async () => {
    let resolverPost: ((valor: Response) => void) | undefined;
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (String(url).includes("/conversa") && metodo === "GET") {
        return json(conversaAberta);
      }
      if (metodo === "POST" && String(url).includes("/respostas")) {
        return new Promise<Response>((resolver) => {
          resolverPost = resolver;
        });
      }
      return json({});
    });
    renderEstadia("/app/ficha/1042", fetchMock);
    const campo = await screen.findByLabelText("Resposta ao hóspede");
    fireEvent.change(campo, { target: { value: "Sim." } });
    fireEvent.keyDown(campo, { key: "Enter" });
    expect(
      fetchMock.mock.calls.filter((chamada) => (chamada[1]?.method ?? "GET") === "POST"),
    ).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled());
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(
      fetchMock.mock.calls.filter((chamada) => (chamada[1]?.method ?? "GET") === "POST"),
    ).toHaveLength(1);
    resolverPost?.(json({ ...conversaAberta.mensagens[2], janela: conversaAberta.janela }, 201));
    await waitFor(() => expect(screen.getByRole("button", { name: "Enviar" })).not.toBeDisabled());
  });

  it("falha ao gravar preserva o texto no campo", async () => {
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (String(url).includes("/conversa") && metodo === "GET") {
        return json(conversaAberta);
      }
      if (metodo === "POST") {
        return json({ detail: "falha" }, 500);
      }
      return json({});
    });
    renderEstadia("/app/ficha/1042", fetchMock);
    const campo = await screen.findByLabelText("Resposta ao hóspede");
    fireEvent.change(campo, { target: { value: "Texto que nao pode sumir" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText(/não foi possível gravar/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Resposta ao hóspede")).toHaveValue("Texto que nao pode sumir");
  });

  it("janela fechada mantém o campo visível e o envio inerte", async () => {
    const fetchMock = fetchEstadia({
      id_reserva: 1042,
      janela: { aberta: false, motivo: "nunca_escreveu" },
      mensagens: [],
    });
    renderEstadia("/app/ficha/1042", fetchMock);
    expect(
      await screen.findByText(/hóspede ainda não escreveu/i),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Resposta ao hóspede")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
  });

  it("janela sem mensagem recente mostra o motivo e mantém o campo", async () => {
    const fetchMock = fetchEstadia({
      id_reserva: 1042,
      janela: { aberta: false, motivo: "sem_mensagem_recente" },
      mensagens: [],
    });
    renderEstadia("/app/ficha/1042", fetchMock);
    expect(
      await screen.findByText(/não escreveu nas últimas 24 horas/i),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Resposta ao hóspede")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
  });
});
