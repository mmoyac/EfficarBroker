import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import TenantGate from "@/components/TenantGate";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import PlatformView from "@/pages/PlatformView";
import Dashboard from "@/pages/Dashboard";
import Users from "@/pages/Users";
import NuevaActa from "@/pages/NuevaActa";
import Actas from "@/pages/Actas";
import ActaDetalle from "@/pages/ActaDetalle";
import MisCaptaciones from "@/pages/MisCaptaciones";
import DerivadasVentas from "@/pages/DerivadasVentas";
import Vehiculos from "@/pages/Vehiculos";
import Comisiones from "@/pages/Comisiones";
import ConfigComisiones from "@/pages/ConfigComisiones";
import OrdenesPago from "@/pages/OrdenesPago";
import EstadoResultado from "@/pages/EstadoResultado";
import Tasacion from "@/pages/Tasacion";
import CatalogoVehicular from "@/pages/CatalogoVehicular";
import Placeholder from "@/pages/Placeholder";
import PwaUpdatePrompt from "@/components/PwaUpdatePrompt";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Vista de plataforma para SuperAdmin (elegir tenant activo) */}
          <Route
            path="/plataforma"
            element={
              <ProtectedRoute>
                <PlatformView />
              </ProtectedRoute>
            }
          />

          {/* Área operativa: requiere sesión y, para SuperAdmin, un tenant activo */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <TenantGate>
                  <Layout />
                </TenantGate>
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="tasacion" element={<Tasacion />} />
            <Route path="catalogo" element={<CatalogoVehicular />} />
            <Route path="saas/catalogo-vehicular" element={<CatalogoVehicular />} />
            <Route path="config/usuarios" element={<Users />} />
            <Route path="actas" element={<Actas />} />
            <Route path="actas/nueva" element={<NuevaActa />} />
            <Route path="actas/:id" element={<ActaDetalle />} />
            <Route path="vehiculos" element={<Vehiculos />} />
            <Route path="captaciones" element={<MisCaptaciones />} />
            <Route path="captaciones/derivadas" element={<DerivadasVentas />} />
            <Route path="comisiones" element={<Comisiones />} />
            <Route path="config/comisiones" element={<ConfigComisiones />} />
            <Route path="liquidaciones/ordenes" element={<OrdenesPago />} />
            <Route path="bi/resultados" element={<EstadoResultado />} />
            {/* Rutas del menú aún sin página: placeholder hasta implementar cada módulo */}
            <Route path="*" element={<Placeholder />} />
          </Route>
        </Routes>
        <PwaUpdatePrompt />
      </AuthProvider>
    </BrowserRouter>
  );
}
