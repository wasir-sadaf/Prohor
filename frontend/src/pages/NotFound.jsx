import { Link } from "react-router-dom";
import { Home, ArrowLeft } from "lucide-react";
import Button from "../components/ui/Button";

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <div className="text-center animate-slide-up">
        <div className="text-8xl font-extrabold gradient-text mb-4">404</div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">
          Page Not Found
        </h1>
        <p className="text-slate-500 mb-8 max-w-md mx-auto">
          The page you are looking for doesn't exist or has been moved.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            onClick={() => window.history.back()}
            icon={ArrowLeft}
          >
            Go Back
          </Button>
          <Link to="/">
            <Button icon={Home}>Home</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

