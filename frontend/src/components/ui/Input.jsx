import { forwardRef } from "react";

const Input = forwardRef(
  ({ label, error, icon: Icon, className = "", ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          {Icon && (
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
              <Icon className="h-4 w-4 text-slate-400" />
            </div>
          )}
          <input
            ref={ref}
            className={`
              w-full rounded-xl border border-slate-200 bg-white
              px-4 py-2.5 text-sm text-slate-800
              placeholder:text-slate-400
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500
              hover:border-slate-300
              disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-slate-50
              ${Icon ? "pl-10" : ""}
              ${error ? "border-red-400 focus:ring-red-500/50 focus:border-red-500" : ""}
              ${className}
            `}
            {...props}
          />
        </div>
        {error && (
          <p className="mt-1 text-xs text-red-500 animate-fade-in">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
