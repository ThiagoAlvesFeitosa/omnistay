import { FormEvent, useCallback, useEffect, useState } from "react";

import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { pedirAutenticado } from "./sessao";
import {
  contarSituacao,
  rotuloPerfil,
  type PerfilUsuario,
  type UsuarioLista,
} from "./usuarios";

type Estado = "carregando" | "ok" | "falha";

type Props = {
  idUsuarioSessao: number;
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

export function TelaUsuarios({ idUsuarioSessao }: Props) {
  const [estado, setEstado] = useState<Estado>("carregando");
  const [usuarios, setUsuarios] = useState<UsuarioLista[]>([]);
  const [aviso, setAviso] = useState("");
  const [formAberto, setFormAberto] = useState(false);
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [perfil, setPerfil] = useState<PerfilUsuario>("staff");
  const [senha, setSenha] = useState("");
  const [emVoo, setEmVoo] = useState(false);

  const atualizar = useCallback(async () => {
    try {
      const resposta = await pedirAutenticado("/usuarios");
      if (!resposta.ok) {
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as { usuarios?: UsuarioLista[] };
      setUsuarios(Array.isArray(corpo.usuarios) ? corpo.usuarios : []);
      setEstado("ok");
    } catch {
      setEstado("falha");
    }
  }, []);

  const carregar = useCallback(async () => {
    setEstado("carregando");
    setAviso("");
    await atualizar();
  }, [atualizar]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  async function cadastrar(evento: FormEvent): Promise<void> {
    evento.preventDefault();
    setEmVoo(true);
    try {
      const resposta = await pedirAutenticado("/usuarios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, email, perfil, senha }),
      });
      if (!resposta.ok) {
        setAviso(await detalheRecusa(resposta));
        return;
      }
      setAviso("");
      setFormAberto(false);
      setNome("");
      setEmail("");
      setSenha("");
      setPerfil("staff");
      await atualizar();
    } finally {
      setEmVoo(false);
    }
  }

  async function desativar(idUsuario: number): Promise<void> {
    setEmVoo(true);
    try {
      const resposta = await pedirAutenticado(`/usuarios/${idUsuario}`, {
        method: "DELETE",
      });
      if (resposta.status === 409) {
        setAviso(await detalheRecusa(resposta));
        return;
      }
      if (!resposta.ok) {
        setAviso("Não foi possível desativar.");
        await atualizar();
        return;
      }
      setAviso("");
      await atualizar();
    } finally {
      setEmVoo(false);
    }
  }

  const situacao = contarSituacao(usuarios);

  return (
    <main className="p-8">
      <h1 className="mb-4 border-b border-zinc-900 pb-2 text-2xl font-semibold">Usuários</h1>

      {estado === "carregando" ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : null}

      {estado === "falha" ? (
        <div className="space-y-3">
          <p role="status">A lista não carregou.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {aviso ? (
        <p role="status" className="mb-4 text-sm text-red-800">
          {aviso}
        </p>
      ) : null}

      {estado === "ok" ? (
        <>
          <p className="mb-4 text-sm text-zinc-600">
            {situacao.ativos} ativos · {situacao.desativados} desativados
          </p>
          <Button type="button" className="mb-4" onClick={() => setFormAberto(true)}>
            + Novo
          </Button>
          {formAberto ? (
            <form className="mb-6 max-w-md space-y-3" onSubmit={(evento) => void cadastrar(evento)}>
              <div>
                <Label htmlFor="usuario-nome">Nome</Label>
                <Input id="usuario-nome" value={nome} onChange={(e) => setNome(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="usuario-email">E-mail</Label>
                <Input
                  id="usuario-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="usuario-perfil">Perfil</Label>
                <select
                  id="usuario-perfil"
                  className="flex h-9 w-full rounded-md border border-zinc-300 bg-white px-3 text-sm"
                  value={perfil}
                  onChange={(e) => setPerfil(e.target.value as PerfilUsuario)}
                >
                  <option value="recepcao">Recepção</option>
                  <option value="staff">Equipe</option>
                  <option value="gestor">Gestão</option>
                </select>
              </div>
              <div>
                <Label htmlFor="usuario-senha">Senha</Label>
                <Input
                  id="usuario-senha"
                  type="password"
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                />
              </div>
              <Button type="submit" disabled={emVoo}>
                Cadastrar
              </Button>
            </form>
          ) : null}
          <ul className="space-y-3">
            {usuarios.map((item) => {
              const propria = item.id_usuario === idUsuarioSessao;
              return (
                <li key={item.id_usuario} className="rounded border border-zinc-200 bg-white p-4">
                  <p className="font-medium">
                    {item.nome}
                    {propria ? <span className="ml-2 text-sm font-normal text-zinc-500">você</span> : null}
                  </p>
                  <p className="text-sm text-zinc-600">{item.email}</p>
                  <p className="text-sm text-zinc-600">
                    <span>{rotuloPerfil(item.perfil)}</span>
                    {" · "}
                    <span>{item.ativo ? "Ativo" : "Desativado"}</span>
                  </p>
                  {item.ativo && !propria ? (
                    <Button
                      type="button"
                      className="mt-2"
                      disabled={emVoo}
                      aria-label={`Desativar ${item.nome}`}
                      onClick={() => void desativar(item.id_usuario)}
                    >
                      Desativar
                    </Button>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </>
      ) : null}
    </main>
  );
}
