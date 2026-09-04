export type Perfil = "recepcao" | "staff" | "gestor";

export type SessaoCriada = {
  id_usuario: number;
  nome: string;
  perfil: Perfil;
  expira_em: string;
  nome_hotel: string;
};

export type SessaoAtual = {
  id_sessao: number;
  id_usuario: number;
  nome: string;
  perfil: Perfil;
  dispositivo: string | null;
  expira_em: string;
  nome_hotel: string;
};

type Manipulador401 = () => void;

let aoNaoAutorizado: Manipulador401 | null = null;

export function definirManipulador401(fn: Manipulador401 | null): void {
  aoNaoAutorizado = fn;
}

export async function pedirAutenticado(
  url: string,
  init: RequestInit = {},
): Promise<Response> {
  const resposta = await fetch(url, { credentials: "include", ...init });
  if (resposta.status === 401) {
    aoNaoAutorizado?.();
  }
  return resposta;
}

export async function entrar(email: string, senha: string): Promise<SessaoCriada | null> {
  const resposta = await fetch("/sessoes", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, senha }),
  });
  if (!resposta.ok) {
    return null;
  }
  return (await resposta.json()) as SessaoCriada;
}

export async function obterAtual(): Promise<SessaoAtual | null> {
  const resposta = await fetch("/sessoes/atual", { credentials: "include" });
  if (!resposta.ok) {
    return null;
  }
  return (await resposta.json()) as SessaoAtual;
}

export async function sair(): Promise<void> {
  await fetch("/sessoes/atual", {
    method: "DELETE",
    credentials: "include",
  });
}
