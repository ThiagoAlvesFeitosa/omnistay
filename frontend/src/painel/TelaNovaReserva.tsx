import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { pedirAutenticado } from "./sessao";
import { TelefoneInvalido, normalizar } from "./telefone";
import type { ItemFila } from "./fila";

export function TelaNovaReserva() {
  const navigate = useNavigate();
  const [nome, setNome] = useState("");
  const [telefone, setTelefone] = useState("");
  const [entrada, setEntrada] = useState("");
  const [saida, setSaida] = useState("");
  const [aviso, setAviso] = useState("");

  function recusaTelefone(): string {
    if (!telefone.trim()) {
      return "";
    }
    try {
      normalizar(telefone);
      return "";
    } catch (erro) {
      if (erro instanceof TelefoneInvalido) {
        return erro.message;
      }
      return "Informe um telefone brasileiro com DDD (celular com 11 dígitos ou fixo com 10).";
    }
  }

  const erroTelefone = recusaTelefone();

  async function enviar(evento: FormEvent): Promise<void> {
    evento.preventDefault();
    if (!nome.trim() || !telefone.trim() || !entrada || !saida) {
      setAviso("Preencha nome, telefone e as duas datas.");
      return;
    }
    if (erroTelefone) {
      setAviso(erroTelefone);
      return;
    }
    if (saida <= entrada) {
      setAviso("A data de saída deve ser posterior à de entrada.");
      return;
    }
    const resposta = await pedirAutenticado("/reservas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nome: nome.trim(),
        telefone,
        data_checkin_prevista: entrada,
        data_checkout_prevista: saida,
      }),
    });
    if (!resposta.ok) {
      setAviso("Não foi possível cadastrar a reserva.");
      return;
    }
    const criada = (await resposta.json()) as { id_reserva: number };
    const fila = await pedirAutenticado("/fila-do-dia");
    let naFila = false;
    if (fila.ok) {
      const corpo = (await fila.json()) as { itens?: ItemFila[] };
      naFila = (corpo.itens ?? []).some((linha) => linha.id_reserva === criada.id_reserva);
    }
    if (naFila) {
      navigate("/fila");
      return;
    }
    navigate("/fila", {
      state: { aviso: "Reserva registrada. Entra na fila no dia da entrada." },
    });
  }

  return (
    <main className="p-8">
      <h1 className="mb-6 border-b border-zinc-900 pb-2 text-2xl font-semibold">Nova reserva</h1>
      {aviso ? (
        <p role="status" className="mb-4 rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm">
          {aviso}
        </p>
      ) : null}
      <form onSubmit={(evento) => void enviar(evento)} className="flex max-w-md flex-col gap-4">
        <div className="flex flex-col gap-1">
          <Label htmlFor="nome">Nome do hóspede</Label>
          <Input id="nome" value={nome} onChange={(evento) => setNome(evento.target.value)} />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="telefone">Telefone com DDD</Label>
          <Input
            id="telefone"
            value={telefone}
            onChange={(evento) => setTelefone(evento.target.value)}
          />
          {erroTelefone ? <p className="text-sm text-red-700">{erroTelefone}</p> : null}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <Label htmlFor="entrada">Entrada</Label>
            <Input
              id="entrada"
              type="date"
              value={entrada}
              onChange={(evento) => setEntrada(evento.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="saida">Saída</Label>
            <Input
              id="saida"
              type="date"
              value={saida}
              onChange={(evento) => setSaida(evento.target.value)}
            />
          </div>
        </div>
        <div className="flex gap-2">
          <Button type="submit">Cadastrar</Button>
          <Button type="button" className="bg-zinc-200 text-zinc-900 hover:bg-zinc-300" onClick={() => navigate("/fila")}>
            Cancelar
          </Button>
        </div>
      </form>
    </main>
  );
}
