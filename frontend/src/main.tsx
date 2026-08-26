import { createRoot } from "react-dom/client";
import { TelaSimulacao } from "./TelaSimulacao";

const raiz = document.getElementById("root");
if (!raiz) {
  throw new Error("elemento root ausente");
}
createRoot(raiz).render(<TelaSimulacao />);
