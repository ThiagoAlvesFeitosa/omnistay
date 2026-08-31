type Props = {
  titulo: string;
  compacto?: boolean;
};

export function TelaNomeada({ titulo, compacto = false }: Props) {
  return (
    <main className={compacto ? "p-4" : "p-8"}>
      <h1
        className={
          compacto
            ? "text-xl font-semibold tracking-tight"
            : "border-b border-zinc-900 pb-2 text-2xl font-semibold"
        }
      >
        {titulo}
      </h1>
    </main>
  );
}
