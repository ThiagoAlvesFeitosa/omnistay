import { FormEvent, useState } from "react";

import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { entrar } from "./sessao";

type Props = {
  onSucesso?: () => void | Promise<void>;
};

const AVISO_CREDENCIAL = "Credenciais inválidas.";
const AVISO_CAMPOS = "Preencha e-mail e senha.";

export function TelaEntrada({ onSucesso }: Props) {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [aviso, setAviso] = useState("");

  async function enviar(evento: FormEvent): Promise<void> {
    evento.preventDefault();
    if (!email.trim() || !senha) {
      setAviso(AVISO_CAMPOS);
      return;
    }
    const criada = await entrar(email.trim(), senha);
    if (!criada) {
      setAviso(AVISO_CREDENCIAL);
      return;
    }
    setAviso("");
    await onSucesso?.();
  }

  return (
    <main className="mx-auto flex min-h-[70vh] max-w-sm flex-col justify-center p-6">
      <h1 className="mb-6 text-2xl font-semibold">Entrar</h1>
      {aviso ? (
        <p role="status" className="mb-4 rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm">
          {aviso}
        </p>
      ) : null}
      <form onSubmit={(evento) => void enviar(evento)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <Label htmlFor="email">E-mail</Label>
          <Input
            id="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(evento) => setEmail(evento.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="senha">Senha</Label>
          <Input
            id="senha"
            type="password"
            autoComplete="current-password"
            value={senha}
            onChange={(evento) => setSenha(evento.target.value)}
          />
        </div>
        <Button type="submit">Entrar</Button>
      </form>
    </main>
  );
}
