import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, Lock, ArrowRight } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { useLanguage } from "../../contexts/LanguageContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Logo from "../../components/ui/Logo";
import toast from "react-hot-toast";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const { login } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const validate = () => {
    const e = {};
    if (!email.trim()) e.email = "Email is required";
    if (!password) e.password = "Password is required";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      await login(email, password);
      toast.success("Welcome back!");
      navigate("/chat");
    } catch (err) {
      toast.error(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50/50 via-white to-green-50/30 px-4 py-12">
      {/* Decorative */}
      <div className="absolute top-20 right-20 w-72 h-72 bg-green-100/40 rounded-full blur-3xl" />
      <div className="absolute bottom-20 left-20 w-64 h-64 bg-green-200/20 rounded-full blur-3xl" />

      <div className="relative w-full max-w-md animate-slide-up">
        {/* Card */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 p-8 sm:p-10">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <Logo size="lg" />
          </div>

          <h1 className="text-2xl font-bold text-slate-900 text-center mb-2">
            {t("loginTitle")}
          </h1>
          <p className="text-sm text-slate-500 text-center mb-8">
            {t("heroSubtitle").substring(0, 60)}...
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label={t("email")}
              type="email"
              icon={Mail}
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
              autoComplete="email"
            />
            <Input
              label={t("password")}
              type="password"
              icon={Lock}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
              autoComplete="current-password"
            />
            <Button
              type="submit"
              className="w-full"
              size="lg"
              loading={loading}
              icon={ArrowRight}
            >
              {t("login")}
            </Button>
          </form>

          <p className="text-sm text-center text-slate-500 mt-6">
            {t("noAccount")}{" "}
            <Link
              to="/register"
              className="font-semibold text-green-600 hover:text-green-700 transition-colors"
            >
              {t("register")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
