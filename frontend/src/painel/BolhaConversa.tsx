import { formatarHorarioBolha } from "./apresentacao";
import { cn } from "../lib/utils";

type Props = {
  lado: "hospede" | "hotel";
  quando: string | Date | null;
  agora?: Date;
  rotulo?: string;
  entrega?: string | null;
  children: string;
};

export function BolhaConversa({ lado, quando, agora = new Date(), rotulo, entrega, children }: Props) {
  const horario = quando ? formatarHorarioBolha(quando, agora) : "";
  return (
    <li
      data-lado={lado}
      className={cn(
        "max-w-[80%] rounded-lg px-3 py-2",
        lado === "hospede" ? "ml-auto bg-zinc-200" : "mr-auto bg-sky-50",
      )}
    >
      {rotulo ? <p className="text-xs text-zinc-500">{rotulo}</p> : null}
      <p className="whitespace-pre-wrap">{children}</p>
      {entrega ? <p className="mt-1 text-xs text-zinc-600">{entrega}</p> : null}
      {horario ? <p className="mt-1 text-xs text-zinc-500">{horario}</p> : null}
    </li>
  );
}
