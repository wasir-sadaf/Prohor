import { useState } from "react";
import { Search, FileText, Loader2, BookOpen } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import api from "../api/client";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const { t } = useLanguage();

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const data = await api.searchLegal(query);
      setResults(data.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-green-50 mb-4">
          <Search className="h-8 w-8 text-green-500" />
        </div>
        <h1 className="text-3xl font-bold text-slate-900 mb-2">
          {t("searchTitle")}
        </h1>
        <p className="text-slate-500 text-sm">{t("disclaimer")}</p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="mb-10">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("searchPlaceholder")}
              className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-slate-200 bg-white text-sm
                focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500
                hover:border-slate-300 transition-all"
            />
          </div>
          <Button type="submit" size="lg" loading={loading} icon={Search}>
            {t("searchButton")}
          </Button>
        </div>
      </form>

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 text-green-500 animate-spin" />
        </div>
      ) : searched && results.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title={t("noResults")}
          description="Try using different keywords or search in both Bangla and English"
        />
      ) : (
        <div className="space-y-4">
          {results.map((item, i) => (
            <div
              key={item.id || i}
              className="bg-white rounded-2xl border border-slate-100 p-6
                hover:shadow-md hover:border-green-100 transition-all duration-200
                animate-fade-in"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <FileText className="h-4 w-4 text-green-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-0.5 rounded">
                      Chunk #{item.chunk_index}
                    </span>
                    {item.page_number && (
                      <span className="text-xs text-slate-400">
                        Page {item.page_number}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                    {item.content}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
