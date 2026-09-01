import { FormEvent, useCallback, useEffect, useState } from "react";

import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { pedirAutenticado } from "./sessao";
import { formatarPreco, type ItemVendavel } from "./vendaveis";

type Estado = "carregando" | "ok" | "falha";

type Formulario =
  | { modo: "novo" }
  | { modo: "editar"; item: ItemVendavel };

type Props = {
  somenteLeitura?: boolean;
};

async function detalheRecusa(resposta: Response): Promise<string> {
  try {
    const corpo = (await resposta.json()) as { detail?: unknown };
    if (typeof corpo.detail === "string" && corpo.detail) {
      return corpo.detail;
    }
  } catch {
    /* corpo ilegível */
  }
  return "Não foi possível salvar.";
}

function precoParaEnvio(texto: string): number {
  return Number(texto.replace(",", "."));
}

export function TelaVendaveis({ somenteLeitura = false }: Props) {
  const [estado, setEstado] = useState<Estado>("carregando");
  const [itens, setItens] = useState<ItemVendavel[]>([]);
  const [aviso, setAviso] = useState("");
  const [emVoo, setEmVoo] = useState(false);
  const [formulario, setFormulario] = useState<Formulario | null>(null);
  const [nome, setNome] = useState("");
  const [preco, setPreco] = useState("");

  const atualizarItens = useCallback(async () => {
    try {
      const resposta = await pedirAutenticado("/itens-vendaveis");
      if (!resposta.ok) {
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as { itens?: ItemVendavel[] };
      setItens(Array.isArray(corpo.itens) ? corpo.itens : []);
      setEstado("ok");
    } catch {
      setEstado("falha");
    }
  }, []);

  const carregar = useCallback(async () => {
    setEstado("carregando");
    setAviso("");
    await atualizarItens();
  }, [atualizarItens]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const vazia = estado === "ok" && itens.length === 0;

  function abrirNovo(): void {
    setFormulario({ modo: "novo" });
    setNome("");
    setPreco("");
    setAviso("");
  }

  function abrirEdicao(linha: ItemVendavel): void {
    setFormulario({ modo: "editar", item: linha });
    setNome(linha.nome);
    setPreco(formatarPreco(linha.preco_atual));
    setAviso("");
  }

  async function salvar(evento: FormEvent): Promise<void> {
    evento.preventDefault();
    if (!formulario) {
      return;
    }
    setEmVoo(true);
    try {
      if (formulario.modo === "novo") {
        const resposta = await pedirAutenticado("/itens-vendaveis", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nome, preco_atual: precoParaEnvio(preco) }),
        });
        if (resposta.status === 409 || resposta.status === 422) {
          setAviso(await detalheRecusa(resposta));
          return;
        }
        if (!resposta.ok) {
          setAviso("Não foi possível salvar.");
          return;
        }
      } else {
        const corpo: { nome?: string; preco_atual?: number } = {};
        if (nome !== formulario.item.nome) {
          corpo.nome = nome;
        }
        const precoNovo = precoParaEnvio(preco);
        const precoAntigo = Number(formulario.item.preco_atual);
        if (precoNovo !== precoAntigo) {
          corpo.preco_atual = precoNovo;
        }
        const resposta = await pedirAutenticado(
          `/itens-vendaveis/${formulario.item.id_item_vendavel}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(corpo),
          },
        );
        if (resposta.status === 409 || resposta.status === 422) {
          setAviso(await detalheRecusa(resposta));
          return;
        }
        if (!resposta.ok) {
          setAviso("Não foi possível salvar.");
          return;
        }
      }
      setFormulario(null);
      setAviso("");
      await atualizarItens();
    } finally {
      setEmVoo(false);
    }
  }

  async function alterarAtivo(id: number, ativo: boolean): Promise<void> {
    setEmVoo(true);
    try {
      const resposta = await pedirAutenticado(`/itens-vendaveis/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ativo }),
      });
      if (!resposta.ok) {
        setAviso(
          resposta.status === 409 || resposta.status === 422
            ? await detalheRecusa(resposta)
            : "Não foi possível salvar.",
        );
        await atualizarItens();
        return;
      }
      setAviso("");
      await atualizarItens();
    } finally {
      setEmVoo(false);
    }
  }

  return (
    <main className="p-8">
      <h1 className="mb-4 border-b border-zinc-900 pb-2 text-2xl font-semibold">Itens vendáveis</h1>

      {aviso ? (
        <p role="status" className="mb-4 text-sm text-red-800">
          {aviso}
        </p>
      ) : null}

      {estado === "carregando" ? <p className="text-sm text-zinc-500">Carregando…</p> : null}

      {estado === "falha" ? (
        <div className="space-y-3">
          <p role="status">A lista não carregou.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {estado === "ok" ? (
        <>
          {somenteLeitura ? null : (
            <div className="mb-4">
              <Button type="button" onClick={abrirNovo}>
                + Novo item
              </Button>
            </div>
          )}

          {formulario && !somenteLeitura ? (
            <form
              className="mb-6 max-w-xl space-y-3 rounded border border-zinc-200 bg-white p-4"
              onSubmit={(evento) => void salvar(evento)}
            >
              <div className="space-y-1">
                <Label htmlFor="vendavel-nome">Nome</Label>
                <Input
                  id="vendavel-nome"
                  value={nome}
                  onChange={(evento) => setNome(evento.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="vendavel-preco">Preço</Label>
                <Input
                  id="vendavel-preco"
                  inputMode="decimal"
                  value={preco}
                  onChange={(evento) => setPreco(evento.target.value)}
                />
              </div>
              <Button type="submit" disabled={emVoo}>
                Salvar
              </Button>
            </form>
          ) : null}

          {vazia ? <p role="status">Não há item vendável.</p> : null}

          {itens.length > 0 ? (
            <table className="w-full border-collapse bg-white text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-200">
                  <th className="p-3 font-medium">Nome</th>
                  <th className="p-3 font-medium">Preço</th>
                  <th className="p-3 font-medium">Situação</th>
                  {somenteLeitura ? null : <th className="p-3 font-medium text-right">Ação</th>}
                </tr>
              </thead>
              <tbody>
                {itens.map((linha) => (
                  <tr
                    key={linha.id_item_vendavel}
                    className={linha.ativo ? "border-b border-zinc-100" : "border-b border-zinc-100 opacity-60"}
                  >
                    <td className="p-3">{linha.nome}</td>
                    <td className="p-3">{formatarPreco(linha.preco_atual)}</td>
                    <td className="p-3">{linha.ativo ? "ativo" : "desativado"}</td>
                    {somenteLeitura ? null : (
                      <td className="p-3 text-right">
                        {linha.ativo ? (
                          <>
                            <Button
                              type="button"
                              className="mr-2 border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-100"
                              disabled={emVoo}
                              onClick={() => abrirEdicao(linha)}
                            >
                              Editar
                            </Button>
                            <Button
                              type="button"
                              className="border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-100"
                              disabled={emVoo}
                              onClick={() => void alterarAtivo(linha.id_item_vendavel, false)}
                            >
                              Desativar
                            </Button>
                          </>
                        ) : (
                          <Button
                            type="button"
                            className="border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-100"
                            disabled={emVoo}
                            onClick={() => void alterarAtivo(linha.id_item_vendavel, true)}
                          >
                            Reativar
                          </Button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </>
      ) : null}
    </main>
  );
}
