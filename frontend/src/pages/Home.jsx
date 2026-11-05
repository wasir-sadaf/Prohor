import { Link, useNavigate } from "react-router-dom";
import {
  MessageSquare,
  Shield,
  FileText,
  AlertTriangle,
  MapPin,
  BookOpen,
  ArrowRight,
  Sparkles,
  Users,
  Scale,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import Button from "../components/ui/Button";
import Logo from "../components/ui/Logo";

const features = [
  { icon: MessageSquare, titleKey: "feature1Title", descKey: "feature1Desc", color: "green" },
  { icon: Shield, titleKey: "feature2Title", descKey: "feature2Desc", color: "blue" },
  { icon: FileText, titleKey: "feature3Title", descKey: "feature3Desc", color: "purple" },
  { icon: AlertTriangle, titleKey: "feature4Title", descKey: "feature4Desc", color: "amber" },
  { icon: MapPin, titleKey: "feature5Title", descKey: "feature5Desc", color: "rose" },
  { icon: BookOpen, titleKey: "feature6Title", descKey: "feature6Desc", color: "cyan" },
];

const colorMap = {
  green: { bg: "bg-green-50", text: "text-green-600", border: "border-green-100" },
  blue: { bg: "bg-blue-50", text: "text-blue-600", border: "border-blue-100" },
  purple: { bg: "bg-purple-50", text: "text-purple-600", border: "border-purple-100" },
  amber: { bg: "bg-amber-50", text: "text-amber-600", border: "border-amber-100" },
  rose: { bg: "bg-rose-50", text: "text-rose-600", border: "border-rose-100" },
  cyan: { bg: "bg-cyan-50", text: "text-cyan-600", border: "border-cyan-100" },
};

const stats = [
  { value: "৩০০+", label: "আইনি বিষয়", labelEn: "Legal Topics" },
  { value: "২৪/৭", label: "সেবা", labelEn: "Service" },
  { value: "বাংলা", label: "ও ইংরেজি", labelEn: "& English" },
];

export default function Home() {
  const { user } = useAuth();
  const { t, lang } = useLanguage();
  const navigate = useNavigate();

  return (
    <div className="overflow-hidden">
      {/* ========== HERO ========== */}
      <section className="relative hero-gradient overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-green-200/20 rounded-full blur-3xl" />
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-green-300/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-green-100/20 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 lg:pt-28 lg:pb-32">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-green-100/80 border border-green-200/60 text-sm font-medium text-green-700 mb-8 animate-fade-in">
              <Sparkles className="h-4 w-4" />
              AI-Powered Legal Literacy
            </div>

            {/* Title */}
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold text-slate-900 leading-tight tracking-tight mb-6 animate-slide-up">
              {t("heroTitle").split(",").map((part, i) => (
                <span key={i}>
                  {i === 1 ? (
                    <span className="gradient-text">{part}</span>
                  ) : (
                    part
                  )}
                  {i === 0 && <br className="hidden sm:block" />}
                </span>
              ))}
            </h1>

            {/* Subtitle */}
            <p
              className="text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto mb-10 leading-relaxed animate-slide-up"
              style={{ animationDelay: "0.1s" }}
            >
              {t("heroSubtitle")}
            </p>

            {/* CTAs */}
            <div
              className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up"
              style={{ animationDelay: "0.2s" }}
            >
              <Button
                size="xl"
                onClick={() => navigate(user ? "/chat" : "/register")}
                icon={ArrowRight}
                className="group"
              >
                {t("getStarted")}
              </Button>
              <Button
                variant="outline"
                size="xl"
                onClick={() =>
                  document
                    .getElementById("features")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
              >
                {t("learnMore")}
              </Button>
            </div>

            {/* Stats */}
            <div
              className="flex items-center justify-center gap-8 sm:gap-12 mt-16 animate-fade-in"
              style={{ animationDelay: "0.4s" }}
            >
              {stats.map((s, i) => (
                <div key={i} className="text-center">
                  <div className="text-2xl sm:text-3xl font-bold gradient-text">
                    {s.value}
                  </div>
                  <div className="text-xs sm:text-sm text-slate-500 mt-0.5">
                    {lang === "bn" ? s.label : s.labelEn}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Wave divider */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 60" fill="none" className="w-full">
            <path
              d="M0 60V30C240 0 480 0 720 30C960 60 1200 60 1440 30V60H0Z"
              fill="#f8fafc"
            />
          </svg>
        </div>
      </section>

      {/* ========== FEATURES ========== */}
      <section id="features" className="bg-slate-50 py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
              {t("featuresTitle")}
            </h2>
            <div className="w-16 h-1 bg-gradient-to-r from-green-500 to-green-600 rounded-full mx-auto" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map(({ icon: Icon, titleKey, descKey, color }, i) => {
              const c = colorMap[color];
              return (
                <div
                  key={i}
                  className={`
                    group relative bg-white rounded-2xl p-7 border ${c.border}
                    hover:shadow-xl hover:shadow-slate-200/50 hover:-translate-y-1
                    transition-all duration-300 cursor-default
                  `}
                  style={{ animationDelay: `${i * 0.08}s` }}
                >
                  <div
                    className={`w-12 h-12 ${c.bg} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}
                  >
                    <Icon className={`h-6 w-6 ${c.text}`} />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-800 mb-2">
                    {t(titleKey)}
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    {t(descKey)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ========== CTA SECTION ========== */}
      <section className="py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative bg-gradient-to-br from-green-600 via-green-500 to-emerald-500 rounded-3xl p-10 sm:p-14 lg:p-20 overflow-hidden">
            {/* Decorative */}
            <div className="absolute top-0 right-0 w-80 h-80 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-2xl" />
            <div className="absolute bottom-0 left-0 w-60 h-60 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2 blur-2xl" />

            <div className="relative text-center max-w-2xl mx-auto">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 text-white/90 text-sm font-medium mb-6">
                <Scale className="h-4 w-4" />
                {lang === "bn" ? "আজই শুরু করুন" : "Start Today"}
              </div>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-5 leading-tight">
                {lang === "bn"
                  ? "আপনার আইনি অধিকার সম্পর্কে জানুন"
                  : "Learn About Your Legal Rights"}
              </h2>
              <p className="text-green-100 text-lg mb-8 leading-relaxed">
                {lang === "bn"
                  ? "প্রহর আপনার পাশে আছে। যেকোনো আইনি প্রশ্নের উত্তর পান সহজ ভাষায়।"
                  : "Prohor is by your side. Get answers to any legal question in simple language."}
              </p>
              <Button
                variant="secondary"
                size="xl"
                onClick={() => navigate(user ? "/chat" : "/register")}
                className="!bg-white !text-green-700 hover:!bg-green-50 !shadow-xl"
              >
                {t("getStarted")}
                <ChevronRight className="h-5 w-5 ml-1" />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* ========== TRUST / DISCLAIMER ========== */}
      <section className="bg-slate-50 py-12">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200/60 text-sm text-amber-700">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>{t("disclaimer")}</span>
          </div>
        </div>
      </section>
    </div>
  );
}
