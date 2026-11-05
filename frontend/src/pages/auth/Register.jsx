import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, Lock, User, ArrowRight } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { useLanguage } from "../../contexts/LanguageContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Logo from "../../components/ui/Logo";
import toast from "react-hot-toast";

export default function Register() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const { register } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const validate = () => {
    const e = {};
    if (!fullName.trim()) e.fullName = "Name is required";
    if (!email.trim()) e.email = "Email is required";
    if (!password) e.password = "Password is required";
    else if (password.length < 6) e.password = "Minimum 6 characters";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const data = await register(email, password, fullName);
      if (data.session) {
        toast.success("Welcome to Prohor!");
        navigate("/chat");
      } else {
        toast.success(data.message || "Please verify your email");
        navigate("/login");
      }
    } catch (err) {
      toast.error(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50/50 via-white to-green-50/30 px-4 py-12">
      <div className="absolute top-20 left-20 w-72 h-72 bg-green-100/40 rounded-full blur-3xl" />
      <div className="absolute bottom-20 right-20 w-64 h-64 bg-green-200/20 rounded-full blur-3xl" />

      <div className="relative w-full max-w-md animate-slide-up">
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 p-8 sm:p-10">
          <div className="flex justify-center mb-8">
            <Logo size="lg" />
          </div>

          <h1 className="text-2xl font-bold text-slate-900 text-center mb-2">
            {t("registerTitle")}
          </h1>
          <p className="text-sm text-slate-500 text-center mb-8">
            {t("tagline")}
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label={t("fullName")}
              type="text"
              icon={User}
              placeholder="আপনার নাম"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              error={errors.fullName}
              autoComplete="name"
            />
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
              autoComplete="new-password"
            />
            <Button
              type="submit"
              className="w-full"
              size="lg"
              loading={loading}
              icon={ArrowRight}
            >
              {t("register")}
            </Button>
          </form>

          <p className="text-sm text-center text-slate-500 mt-6">
            {t("hasAccount")}{" "}
            <Link
              to="/login"
              className="font-semibold text-green-600 hover:text-green-700 transition-colors"
            >
              {t("login")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
