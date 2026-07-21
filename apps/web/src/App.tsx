import { Navigate, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import VoiceTrade from "./pages/VoiceTrade";
import Portfolio from "./pages/Portfolio";
import Orders from "./pages/Orders";
import AuditLog from "./pages/AuditLog";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/voice" element={<VoiceTrade />} />
      <Route path="/portfolio" element={<Portfolio />} />
      <Route path="/orders" element={<Orders />} />
      <Route path="/audit-log" element={<AuditLog />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
