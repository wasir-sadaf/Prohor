import { Scale } from "lucide-react";

export default function Logo({ size = "md", showText = true }) {
  const sizes = {
    sm: { icon: "h-6 w-6", text: "text-lg", wrapper: "gap-2" },
    md: { icon: "h-8 w-8", text: "text-xl", wrapper: "gap-2.5" },
    lg: { icon: "h-10 w-10", text: "text-2xl", wrapper: "gap-3" },
    xl: { icon: "h-14 w-14", text: "text-4xl", wrapper: "gap-4" },
  };

  const s = sizes[size];

  return (
    <div className={`flex items-center ${s.wrapper}`}>
      <div className="relative">
        <div className="absolute inset-0 bg-green-400/20 rounded-xl blur-md" />
        <div className="relative bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-2 shadow-lg shadow-green-500/20">
          <Scale className={`${s.icon} text-white`} strokeWidth={2.2} />
        </div>
      </div>
      {showText && (
        <div className="flex flex-col">
          <span className={`${s.text} font-bold gradient-text leading-tight`}>
            প্রহর
          </span>
          <span className="text-[10px] font-medium text-slate-400 tracking-widest uppercase">
            Prohor
          </span>
        </div>
      )}
    </div>
  );
}
