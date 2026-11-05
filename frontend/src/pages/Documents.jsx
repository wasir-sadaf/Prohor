import { useState, useEffect } from "react";
import {
  FileText,
  Search,
  ExternalLink,
  CheckCircle,
  Calendar,
  Building,
  Loader2,
} from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import api from "../api/client";
import EmptyState from "../components/ui/EmptyState";

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const { t } = useLanguage();

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const data = await api.getDocuments();
        setDocuments(data.documents || []);
        setFiltered(data.documents || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDocs();
  }, []);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setFiltered(documents);
    } else {
      const q = searchQuery.toLowerCase();
      setFiltered(
        documents.filter(
          (d) =>
            d.title?.toLowerCase().includes(q) ||
            d.source_type?.toLowerCase().includes(q) ||
            d.issuing_authority?.toLowerCase().includes(q)
        )
      );
    }
  }, [searchQuery, documents]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 text-green-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">
          {t("documentsTitle")}
        </h1>
        <div className="w-12 h-1 bg-gradient-to-r from-green-500 to-green-600 rounded-full" />
      </div>

      {/* Search */}
      <div className="relative max-w-lg mb-8">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t("searchDocuments")}
          className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 bg-white text-sm
            focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500
            hover:border-slate-300 transition-all"
        />
      </div>

      {/* Documents Grid */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={t("noDocuments")}
          description="No legal documents match your search"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((doc, i) => (
            <div
              key={doc.id}
              className="group bg-white rounded-2xl border border-slate-100 p-6
                hover:shadow-lg hover:shadow-slate-200/50 hover:-translate-y-0.5
                transition-all duration-300 animate-fade-in"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              {/* Type badge */}
              <div className="flex items-center justify-between mb-4">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-green-50 text-xs font-medium text-green-700">
                  <FileText className="h-3 w-3" />
                  {doc.source_type || "Document"}
                </span>
                {doc.is_verified && (
                  <span className="inline-flex items-center gap-1 text-xs text-green-600">
                    <CheckCircle className="h-3.5 w-3.5" />
                    {t("verified")}
                  </span>
                )}
              </div>

              {/* Title */}
              <h3 className="text-base font-semibold text-slate-800 mb-3 line-clamp-2 group-hover:text-green-700 transition-colors">
                {doc.title}
              </h3>

              {/* Meta */}
              <div className="space-y-1.5 text-xs text-slate-500">
                {doc.issuing_authority && (
                  <div className="flex items-center gap-1.5">
                    <Building className="h-3 w-3" />
                    {doc.issuing_authority}
                  </div>
                )}
                {doc.publication_date && (
                  <div className="flex items-center gap-1.5">
                    <Calendar className="h-3 w-3" />
                    {new Date(doc.publication_date).toLocaleDateString()}
                  </div>
                )}
              </div>

              {/* Link */}
              {doc.url && (
                <a
                  href={doc.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 mt-4 text-xs font-medium text-green-600 hover:text-green-700 transition-colors"
                >
                  View Source
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
