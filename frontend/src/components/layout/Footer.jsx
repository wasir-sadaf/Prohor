import { Scale, Heart } from "lucide-react";
import { useLanguage } from "../../contexts/LanguageContext";

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="bg-slate-900 text-slate-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-1.5">
                <Scale className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-bold text-white">প্রহর</span>
            </div>
            <p className="text-sm leading-relaxed">{t("tagline")}</p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-3">
              Quick Links
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/chat" className="hover:text-green-400 transition-colors">
                  {t("chat")}
                </a>
              </li>
              <li>
                <a href="/documents" className="hover:text-green-400 transition-colors">
                  {t("documents")}
                </a>
              </li>
              <li>
                <a href="/search" className="hover:text-green-400 transition-colors">
                  {t("search")}
                </a>
              </li>
            </ul>
          </div>

          {/* Disclaimer */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-3">
              Disclaimer
            </h4>
            <p className="text-xs leading-relaxed text-slate-500">
              {t("disclaimer")}
            </p>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-3">
          <p className="text-xs">{t("copyright")}</p>
          <p className="text-xs flex items-center gap-1">
            Made with <Heart className="h-3 w-3 text-red-400 fill-red-400" /> for Bangladesh
          </p>
        </div>
      </div>
    </footer>
  );
}