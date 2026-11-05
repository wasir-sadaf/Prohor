import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import {
  Menu,
  X,
  MessageSquare,
  FileText,
  Search,
  LogOut,
  LogIn,
  UserPlus,
  Globe,
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { useLanguage } from "../../contexts/LanguageContext";
import Logo from "../ui/Logo";
import Button from "../ui/Button";

export default function Navbar() {
  const { user, logout } = useAuth();
  const { lang, t, toggleLanguage } = useLanguage();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
    setMobileOpen(false);
  };

  const navLinks = user
    ? [
        { to: "/chat", label: t("chat"), icon: MessageSquare },
        { to: "/documents", label: t("documents"), icon: FileText },
        { to: "/search", label: t("search"), icon: Search },
      ]
    : [];

  return (
    <nav className="sticky top-0 z-50 glass border-b border-slate-200/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex-shrink-0" onClick={() => setMobileOpen(false)}>
            <Logo size="sm" />
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium text-slate-600 hover:text-green-600 hover:bg-green-50/80 transition-colors"
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}
          </div>

          {/* Right side */}
          <div className="hidden md:flex items-center gap-2">
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              title="Switch language"
            >
              <Globe className="h-4 w-4" />
              {lang === "bn" ? "EN" : "বাং"}
            </button>

            {user ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-50 border border-green-100">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
                    <span className="text-xs font-bold text-white">
                      {(user.email || "U")[0].toUpperCase()}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-green-700 max-w-[120px] truncate">
                    {user.email}
                  </span>
                </div>
                <Button variant="ghost" size="sm" onClick={handleLogout} icon={LogOut}>
                  {t("logout")}
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate("/login")}
                  icon={LogIn}
                >
                  {t("login")}
                </Button>
                <Button
                  size="sm"
                  onClick={() => navigate("/register")}
                  icon={UserPlus}
                >
                  {t("register")}
                </Button>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-slate-100 bg-white animate-fade-in">
          <div className="px-4 py-3 space-y-1">
            {navLinks.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:text-green-600 hover:bg-green-50 transition-colors"
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}

            <button
              onClick={toggleLanguage}
              className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            >
              <Globe className="h-4 w-4" />
              {lang === "bn" ? "English" : "বাংলা"}
            </button>

            <div className="pt-2 border-t border-slate-100">
              {user ? (
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  {t("logout")}
                </button>
              ) : (
                <div className="space-y-2">
                  <Button
                    variant="ghost"
                    className="w-full"
                    onClick={() => {
                      navigate("/login");
                      setMobileOpen(false);
                    }}
                    icon={LogIn}
                  >
                    {t("login")}
                  </Button>
                  <Button
                    className="w-full"
                    onClick={() => {
                      navigate("/register");
                      setMobileOpen(false);
                    }}
                    icon={UserPlus}
                  >
                    {t("register")}
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}