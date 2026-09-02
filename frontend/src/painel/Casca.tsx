import { useCallback, useEffect, useState } from "react";
import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import { TelaSimulacao } from "../TelaSimulacao";
import { Button } from "../components/ui/button";
import {
  DESTINOS,
  caminhoRelativo,
  destinoInicial,
  itensMenu,
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

export function Casca() {
  const [carregando, setCarregando] = useState(true);
  const [sessao, setSessao] = useState<SessaoAtual | null>(null);
  const [avisoSessao, setAvisoSessao] = useState("");
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

  async function aoSair(): Promise<void> {
    await sair();
    setSessao(null);
    setAvisoSessao("");
    navigate("/entrar", { replace: true });
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      {sessao ? (
        <header className="flex flex-wrap items-center justify-between gap-3 border-b bg-zinc-900 px-4 py-3 text-white">
          <span className="text-sm font-medium">{sessao.nome}</span>
          {!compacto ? (
            <nav className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
              {itensMenu(sessao.perfil).map((destino) => (
                <NavLink
                  key={destino.id}
                  to={caminhoRelativo(destino.caminho)}
                  className={({ isActive }) =>
                    isActive ? "underline" : "text-zinc-300 hover:text-white"
                  }
                >
                  {destino.titulo}
                </NavLink>
              ))}
            </nav>
          ) : null}
          <Button
            type="button"
            className="bg-white text-zinc-900 hover:bg-zinc-200"
            onClick={() => void aoSair()}
          >
            Sair
          </Button>
        </header>
      ) : null}
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
  );
}
