import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { Casca } from "./painel/Casca";
import "./index.css";

const raiz = document.getElementById("root");
if (!raiz) {
  throw new Error("elemento root ausente");
}
createRoot(raiz).render(
  <BrowserRouter basename="/app">
    <Casca />
  </BrowserRouter>,
);
