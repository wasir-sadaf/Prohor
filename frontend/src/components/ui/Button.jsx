import { forwardRef } from "react";

const variants = {
  primary:
    "bg-gradient-to-r from-green-500 to-green-600 text-white hover:from-green-600 hover:to-green-700 shadow-lg shadow-green-500/25 hover:shadow-green-500/40",
  secondary:
    "bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200",
  outline:
    "border-2 border-green-500 text-green-600 hover:bg-green-50",
  ghost:
    "text-slate-600 hover:bg-slate-100 hover:text-slate-800",
  danger:
    "bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-500/25",
};

const sizes = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-5 py-2.5 text-sm",
  lg: "px-7 py-3 text-base",
  xl: "px-8 py-4 text-lg",
};

const Button = forwardRef(
  (
    {
      variant = "primary",
      size = "md",
      className = "",
      children,
      disabled,
      loading,
      icon: Icon,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`
          inline-flex items-center justify-center gap-2 rounded-xl font-medium
          transition-all duration-200 ease-out
          focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:ring-offset-2
          disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
          active:scale-[0.98]
          ${variants[variant]}
          ${sizes[size]}
          ${className}
        `}
        {...props}
      >
        {loading ? (
          <svg
            className="animate-spin h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        ) : Icon ? (
          <Icon className="h-4 w-4" />
        ) : null}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
export default Button;
