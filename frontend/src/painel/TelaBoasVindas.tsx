import { FormEvent, useCallback, useEffect, useState } from "react";

import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { pedirAutenticado } from "./sessao";

type Estado = "carregando" | "ok" | "falha";

type Recado = {
  cafe: string;
  wifi: string;
  checkout: string;
  convite: string;
};

type Props = {
  somenteLeitura?: boolean;
};

const vazio: Recado = { cafe: "", wifi: "", checkout: "", convite: "" };

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

function textoCampo(valor: unknown): string {
  return typeof valor === "string" ? valor : "";
}

export function TelaBoasVindas({ somenteLeitura = false }: Props) {
  const [estado, setEstado] = useState<Estado>("carregando");
  const [gravado, setGravado] = useState<Recado>(vazio);
  const [cafe, setCafe] = useState("");
  const [wifi, setWifi] = useState("");
  const [checkout, setCheckout] = useState("");
  const [convite, setConvite] = useState("");
  const [aviso, setAviso] = useState("");
  const [emVoo, setEmVoo] = useState(false);

  function aplicar(recado: Recado): void {
    setGravado(recado);
    setCafe(recado.cafe);
    setWifi(recado.wifi);
    setCheckout(recado.checkout);
    setConvite(recado.convite);
  }

  const atualizar = useCallback(async () => {
    try {
      const resposta = await pedirAutenticado("/propriedade/boas-vindas");
      if (!resposta.ok) {
        setEstado("falha");
        return;
      }
      const corpo = (await resposta.json()) as Partial<Recado>;
      aplicar({
        cafe: textoCampo(corpo.cafe),
        wifi: textoCampo(corpo.wifi),
        checkout: textoCampo(corpo.checkout),
        convite: textoCampo(corpo.convite),
      });
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

  async function salvar(evento: FormEvent): Promise<void> {
    evento.preventDefault();
    setEmVoo(true);
    try {
      const resposta = await pedirAutenticado("/propriedade/boas-vindas", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cafe, wifi, checkout, convite }),
      });
      if (resposta.status === 422) {
        setAviso(await detalheRecusa(resposta));
        setCafe(gravado.cafe);
        setWifi(gravado.wifi);
        setCheckout(gravado.checkout);
        setConvite(gravado.convite);
        return;
      }
      if (!resposta.ok) {
        setAviso("Não foi possível salvar.");
        return;
      }
      const corpo = (await resposta.json()) as Partial<Recado>;
      aplicar({
        cafe: textoCampo(corpo.cafe),
        wifi: textoCampo(corpo.wifi),
        checkout: textoCampo(corpo.checkout),
        convite: textoCampo(corpo.convite),
      });
      setAviso("");
    } finally {
      setEmVoo(false);
    }
  }

  return (
    <main className="p-8">
      <h1 className="mb-4 border-b border-zinc-900 pb-2 text-2xl font-semibold">
        Recado de boas-vindas
      </h1>

      {aviso ? (
        <p role="status" className="mb-4 text-sm text-red-800">
          {aviso}
        </p>
      ) : null}

      {estado === "carregando" ? <p className="text-sm text-zinc-500">Carregando…</p> : null}

      {estado === "falha" ? (
        <div className="space-y-3">
          <p role="status">O recado não carregou.</p>
          <Button type="button" onClick={() => void carregar()}>
            Tentar de novo
          </Button>
        </div>
      ) : null}

      {estado === "ok" ? (
        <form className="max-w-xl space-y-4" onSubmit={(evento) => void salvar(evento)}>
          <div className="space-y-1">
            <Label htmlFor="boas-cafe">Café da manhã</Label>
            <Input
              id="boas-cafe"
              value={cafe}
              readOnly={somenteLeitura}
              onChange={(evento) => setCafe(evento.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="boas-wifi">Wi-fi</Label>
            <Input
              id="boas-wifi"
              value={wifi}
              readOnly={somenteLeitura}
              onChange={(evento) => setWifi(evento.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="boas-checkout">Horário de saída</Label>
            <Input
              id="boas-checkout"
              value={checkout}
              readOnly={somenteLeitura}
              onChange={(evento) => setCheckout(evento.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="boas-convite">Convite</Label>
            <Input
              id="boas-convite"
              value={convite}
              readOnly={somenteLeitura}
              onChange={(evento) => setConvite(evento.target.value)}
            />
          </div>
          {somenteLeitura ? null : (
            <Button type="submit" disabled={emVoo}>
              Salvar
            </Button>
          )}
        </form>
      ) : null}
    </main>
  );
}
