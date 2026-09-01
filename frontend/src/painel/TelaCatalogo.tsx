import { FormEvent, useCallback, useEffect, useState } from "react";

import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  CATEGORIAS,
  contarSituacao,
  itensDaCategoria,
  type CategoriaCatalogo,
  type ItemCatalogo,
} from "./catalogo";
import { pedirAutenticado } from "./sessao";

type Estado = "carregando" | "ok" | "falha";

type Formulario =
  | { modo: "novo" }
  | { modo: "editar"; item: ItemCatalogo };

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

export function TelaCatalogo({ somenteLeitura = false }: Props) {
  const [estado, setEstado] = useState<Estado>("carregando");
  const [itens, setItens] = useState<ItemCatalogo[]>([]);
  const [aba, setAba] = useState<CategoriaCatalogo>("horario");
  const [aviso, setAviso] = useState("");
  const [emVoo, setEmVoo] = useState(false);
  const [formulario, setFormulario] = useState<Formulario | null>(null);
  const [titulo, setTitulo] = useState("");
  const [conteudo, setConteudo] = useState("");

  const atualizarItens = useCallback(async () => {
    try {
      const resposta = await pedirAutenticado("/catalogo");
      if (!resposta.ok) {
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as { itens?: ItemCatalogo[] };
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

  const daAba = itensDaCategoria(itens, aba);
  const situacao = contarSituacao(daAba);
  const vazia = estado === "ok" && daAba.length === 0;

  function abrirNovo(): void {
    setFormulario({ modo: "novo" });
    setTitulo("");
    setConteudo("");
    setAviso("");
  }

  function abrirEdicao(linha: ItemCatalogo): void {
    setFormulario({ modo: "editar", item: linha });
    setTitulo(linha.titulo);
    setConteudo(linha.conteudo);
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
        const resposta = await pedirAutenticado("/catalogo", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ categoria: aba, titulo, conteudo }),
        });
        if (resposta.status === 422) {
          setAviso(await detalheRecusa(resposta));
          return;
        }
        if (!resposta.ok) {
          setAviso("Não foi possível salvar.");
          return;
        }
      } else {
        const resposta = await pedirAutenticado(
          `/catalogo/${formulario.item.id_catalogo_item}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ titulo, conteudo }),
          },
        );
        if (resposta.status === 422) {
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
      const resposta = await pedirAutenticado(`/catalogo/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ativo }),
      });
      if (!resposta.ok) {
        setAviso(resposta.status === 422 ? await detalheRecusa(resposta) : "Não foi possível salvar.");
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
      <h1 className="mb-4 border-b border-zinc-900 pb-2 text-2xl font-semibold">Catálogo</h1>

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
          <div role="tablist" className="mb-4 flex flex-wrap gap-2">
            {CATEGORIAS.map((categoria) => (
              <Button
                key={categoria.chave}
                type="button"
                role="tab"
                aria-selected={aba === categoria.chave}
                className={
                  aba === categoria.chave
                    ? ""
                    : "border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-100"
                }
                onClick={() => {
                  setAba(categoria.chave);
                  setFormulario(null);
                }}
              >
                {categoria.rotulo}
              </Button>
            ))}
          </div>

          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-zinc-600">
              {situacao.ativos} ativos · {situacao.desativados} desativados
            </p>
            {somenteLeitura ? null : (
              <Button type="button" onClick={abrirNovo}>
                + Novo item
              </Button>
            )}
          </div>

          {formulario && !somenteLeitura ? (
            <form className="mb-6 max-w-xl space-y-3 rounded border border-zinc-200 bg-white p-4" onSubmit={(e) => void salvar(e)}>
              <div className="space-y-1">
                <Label htmlFor="catalogo-titulo">Título</Label>
                <Input
                  id="catalogo-titulo"
                  value={titulo}
                  onChange={(evento) => setTitulo(evento.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="catalogo-conteudo">Conteúdo</Label>
                <Input
                  id="catalogo-conteudo"
                  value={conteudo}
                  onChange={(evento) => setConteudo(evento.target.value)}
                />
              </div>
              <Button type="submit" disabled={emVoo}>
                Salvar
              </Button>
            </form>
          ) : null}

          {vazia ? <p role="status">Não há item nesta categoria.</p> : null}

          {daAba.length > 0 ? (
            <table className="w-full border-collapse bg-white text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-200">
                  <th className="p-3 font-medium">Título</th>
                  <th className="p-3 font-medium">Conteúdo</th>
                  <th className="p-3 font-medium">Situação</th>
                  {somenteLeitura ? null : <th className="p-3 font-medium text-right">Ação</th>}
                </tr>
              </thead>
              <tbody>
                {daAba.map((linha) => (
                  <tr
                    key={linha.id_catalogo_item}
                    className={linha.ativo ? "border-b border-zinc-100" : "border-b border-zinc-100 opacity-60"}
                  >
                    <td className="p-3">{linha.titulo}</td>
                    <td className="p-3">{linha.conteudo}</td>
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
                              onClick={() => void alterarAtivo(linha.id_catalogo_item, false)}
                            >
                              Desativar
                            </Button>
                          </>
                        ) : (
                          <Button
                            type="button"
                            className="border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-100"
                            disabled={emVoo}
                            onClick={() => void alterarAtivo(linha.id_catalogo_item, true)}
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
