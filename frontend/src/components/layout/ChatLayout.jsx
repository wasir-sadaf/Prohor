import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";

export default function ChatLayout() {
  return (
    <div className="h-screen flex flex-col bg-white">
      <Navbar />
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}