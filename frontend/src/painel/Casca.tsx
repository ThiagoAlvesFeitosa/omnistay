import { useCallback, useEffect, useState } from "react";
import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import { TelaSimulacao } from "../TelaSimulacao";
import { Button } from "../components/ui/button";
import {
  DESTINOS,
  ROTULO_PERFIL,
  caminhoRelativo,
  destinoInicial,
  itensMenu,
  menuAgrupado,
} from "./destinos";
import type { SessaoAtual } from "./sessao";
import { definirManipulador401, obterAtual, sair } from "./sessao";
import { TelaAlertas } from "./TelaAlertas";
import { TelaChamados } from "./TelaChamados";
import { TelaEntrada } from "./TelaEntrada";
import { TelaConsumos } from "./TelaConsumos";
import { TelaEstadia } from "./TelaEstadia";
import { TelaFila } from "./TelaFila";
import { TelaNomeada } from "./TelaNomeada";
import { TelaNovaReserva } from "./TelaNovaReserva";
import { TelaSaida } from "./TelaSaida";
import { TelaCatalogo } from "./TelaCatalogo";
import { TelaVendaveis } from "./TelaVendaveis";
import { TelaBoasVindas } from "./TelaBoasVindas";
import { TelaPainel } from "./TelaPainel";
import { TelaMercado } from "./TelaMercado";
import { TelaUsuarios } from "./TelaUsuarios";
import { TelaRetencao } from "./TelaRetencao";
import { cn } from "../lib/utils";

function telaLargaAgora(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return true;
  }
  return window.matchMedia("(min-width: 768px)").matches;
}

function usarTelaLarga(): boolean {
  const [larga, setLarga] = useState(telaLargaAgora);
  useEffect(() => {
    if (typeof window.matchMedia !== "function") {
      return;
    }
    const consulta = window.matchMedia("(min-width: 768px)");
    const aoMudar = () => setLarga(consulta.matches);
    consulta.addEventListener("change", aoMudar);
    return () => consulta.removeEventListener("change", aoMudar);
  }, []);
  return larga;
}

export function Casca() {
  const [carregando, setCarregando] = useState(true);
  const [sessao, setSessao] = useState<SessaoAtual | null>(null);
  const [avisoSessao, setAvisoSessao] = useState("");
  const [menuAberto, setMenuAberto] = useState(false);
  const larga = usarTelaLarga();
  const navigate = useNavigate();
  const location = useLocation();

  const ao401 = useCallback(() => {
    setSessao(null);
    setAvisoSessao("Sessão ausente ou inválida.");
    navigate("/entrar", { replace: true });
  }, [navigate]);

  useEffect(() => {
    definirManipulador401(ao401);
    return () => definirManipulador401(null);
  }, [ao401]);

  useEffect(() => {
    let vivo = true;
    void obterAtual().then((atual) => {
      if (!vivo) {
        return;
      }
      setSessao(atual);
      setCarregando(false);
    });
    return () => {
      vivo = false;
    };
  }, []);

  if (carregando) {
    return <p className="p-8 text-sm text-zinc-500">Carregando…</p>;
  }

  const naEntrada = location.pathname === "/entrar";

  if (!sessao && !naEntrada) {
    return <Navigate to="/entrar" replace />;
  }

  if (sessao && (naEntrada || location.pathname === "/")) {
    return <Navigate to={caminhoRelativo(destinoInicial(sessao.perfil))} replace />;
  }

  const compacto = sessao?.perfil === "staff";
  const mostrarNav = Boolean(sessao) && (larga || menuAberto);

  function fecharMenu(): void {
    setMenuAberto(false);
  }

  async function aoSair(): Promise<void> {
    fecharMenu();
    await sair();
    setSessao(null);
    setAvisoSessao("");
    navigate("/entrar", { replace: true });
  }

  const classeLink = ({ isActive }: { isActive: boolean }) =>
    isActive
      ? "rounded px-2 py-1.5 font-medium underline"
      : "rounded px-2 py-1.5 text-zinc-300 hover:text-white";

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 md:flex">
      {sessao && !larga ? (
        <Button
          type="button"
          className="fixed right-4 top-4 z-50 bg-zinc-900 text-white hover:bg-zinc-800"
          aria-expanded={menuAberto}
          aria-label={menuAberto ? "Fechar menu" : "Abrir menu"}
          onClick={() => setMenuAberto((aberto) => !aberto)}
        >
          Menu
        </Button>
      ) : null}
      {sessao && mostrarNav ? (
        <>
          {!larga ? (
            <button
              type="button"
              data-testid="fundo-navegacao"
              className="fixed inset-0 z-40 bg-black/40"
              onClick={fecharMenu}
            />
          ) : null}
        <aside
          className={cn(
            "flex h-screen w-60 shrink-0 flex-col bg-zinc-900 text-white",
            !larga && "fixed inset-y-0 left-0 z-50",
          )}
        >
          <div className="border-b border-zinc-700 px-4 py-4">
            <p className="text-lg font-semibold leading-tight">{sessao.nome_hotel}</p>
            <p className="mt-1 text-sm text-zinc-400">OmniStay</p>
          </div>
          <nav className="flex flex-1 flex-col gap-4 overflow-y-auto px-3 py-3 text-sm">
            {menuAgrupado(sessao.perfil).map((grupo) => (
              <div key={grupo.id}>
                <p className="px-2 pb-1 text-xs font-medium uppercase tracking-wide text-zinc-500">
                  {grupo.rotulo}
                </p>
                <div className="flex flex-col gap-1">
                  {grupo.itens.map((destino) => (
                    <NavLink
                      key={destino.id}
                      to={caminhoRelativo(destino.caminho)}
                      className={classeLink}
                      onClick={fecharMenu}
                    >
                      {destino.titulo}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
            {itensMenu(sessao.perfil)
              .filter((destino) => !destino.grupo)
              .map((destino) => (
                <NavLink
                  key={destino.id}
                  to={caminhoRelativo(destino.caminho)}
                  className={classeLink}
                  onClick={fecharMenu}
                >
                  {destino.titulo}
                </NavLink>
              ))}
          </nav>
          <div className="mt-auto border-t border-zinc-700 px-4 py-4">
            <p className="text-sm font-medium">{sessao.nome}</p>
            <p className="text-xs text-zinc-400">{ROTULO_PERFIL[sessao.perfil]}</p>
            <Button
              type="button"
              className="mt-3 w-full bg-white text-zinc-900 hover:bg-zinc-200"
              onClick={() => void aoSair()}
            >
              Sair
            </Button>
          </div>
        </aside>
        </>
      ) : null}
      <div className="min-w-0 flex-1">
      {avisoSessao && naEntrada ? (
        <p role="status" className="bg-amber-50 px-4 py-2 text-sm">
          {avisoSessao}
        </p>
      ) : null}
      <Routes>
        <Route
          path="/entrar"
          element={
            <TelaEntrada
              onSucesso={async () => {
                const atual = await obterAtual();
                setSessao(atual);
                setAvisoSessao("");
              }}
            />
          }
        />
        {DESTINOS.map((destino) => (
          <Route
            key={destino.id}
            path={
              destino.id === "ficha"
                ? "/ficha/:idReserva?"
                : destino.id === "saida"
                  ? "/saida/:idReserva?"
                  : caminhoRelativo(destino.caminho)
            }
            element={
              sessao && !destino.perfis.includes(sessao.perfil) ? (
                <Navigate
                  to={caminhoRelativo(destinoInicial(sessao.perfil))}
                  replace
                />
              ) : destino.id === "simulador" ? (
                <TelaSimulacao />
              ) : destino.id === "fila" ? (
                <TelaFila />
              ) : destino.id === "reserva" ? (
                <TelaNovaReserva />
              ) : destino.id === "ficha" ? (
                <TelaEstadia />
              ) : destino.id === "alertas" ? (
                <TelaAlertas />
              ) : destino.id === "consumos" ? (
                <TelaConsumos />
              ) : destino.id === "saida" ? (
                <TelaSaida />
              ) : destino.id === "chamados" ? (
                <TelaChamados />
              ) : destino.id === "catalogo" ? (
                <TelaCatalogo somenteLeitura={sessao?.perfil === "gestor"} />
              ) : destino.id === "vendaveis" ? (
                <TelaVendaveis somenteLeitura={sessao?.perfil === "gestor"} />
              ) : destino.id === "boas-vindas" ? (
                <TelaBoasVindas somenteLeitura={sessao?.perfil === "gestor"} />
              ) : destino.id === "indicadores" ? (
                <TelaPainel />
              ) : destino.id === "mercado" ? (
                <TelaMercado />
              ) : destino.id === "usuarios" ? (
                <TelaUsuarios idUsuarioSessao={sessao?.id_usuario ?? 0} />
              ) : destino.id === "retencao" ? (
                <TelaRetencao />
              ) : (
                <TelaNomeada titulo={destino.titulo} compacto={compacto} />
              )
            }
          />
        ))}
      </Routes>
      </div>
    </div>
  );
}
