import { BrowserRouter, Routes, Route } from "react-router-dom";
import ShopPage from "./pages/ShopPage";
import AdminPage from "./pages/AdminPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import AcceptQuotePage from "./pages/AcceptQuotePage";
import TopBar from "./components/TopBar";
import { LanguageProvider } from "./i18n";
import "./styles/header.css";
import "./styles/hero.css";
import "./styles/shop.css";
import "./styles/modal.css";
import "./styles/contact.css";
import "./styles/admin.css";
import "./styles/accept.css";

function App() {
  return (
    <LanguageProvider>
      <BrowserRouter>
        <TopBar />

        <Routes>
          <Route path="/shop" element={<ShopPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/accept-quote" element={<AcceptQuotePage />} />
          <Route path="/" element={<ShopPage />} />
        </Routes>
      </BrowserRouter>
    </LanguageProvider>
  );
}

export default App;