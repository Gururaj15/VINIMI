import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import Hero from "@/components/home/Hero";
import KPIs from "@/components/home/KPIs";
import Features from "@/components/home/Features";
import HowItWorks from "@/components/home/HowItWorks";
import UseCases from "@/components/home/UseCases";
import SocialProof from "@/components/home/SocialProof";
import FinalCTA from "@/components/home/FinalCTA";
import logo from "@/assets/logo1.png";
import { getManager, clearManager } from "@/lib/auth";

const Home = () => {
  const [user, setUser] = useState(() => getManager());

  useEffect(() => {
    setUser(getManager());
  }, []);

  const handleLogout = () => {
    clearManager();
    setUser(null);
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="sticky top-0 z-40 backdrop-blur border-b border-white/10 bg-white/70">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-[0.1rem]">
            <img src={logo} alt="VINIMI logo" className="h-14 w-auto rounded-lg p-0" />
            <div className="text-lg font-bold tracking-tight">VINIMI</div>
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm text-slate-700">
            <Link to="/" className="hover:text-primary transition-colors">Home</Link>
            <Link to="/dashboard" className="hover:text-primary transition-colors">Dashboard</Link>
            <Link to="/live" className="hover:text-primary transition-colors">Live Monitoring</Link>
            <Link to="/workers" className="hover:text-primary transition-colors">Workers</Link>
            <Link to="/violations" className="hover:text-primary transition-colors">Violations</Link>
            <a href="https://docs.vinimi.ai" className="hover:text-primary transition-colors">Docs</a>
            <a href="mailto:hello@vinimi.ai" className="hover:text-primary transition-colors">Contact</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link
              to="/live"
              className="hidden md:inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary text-white font-semibold shadow-lg shadow-primary/40 hover:translate-y-[-1px] transition-transform"
            >
              Try Live Monitoring
            </Link>
            {!user ? (
              <div className="hidden md:flex items-center gap-3 text-sm">
                <Link to="/signin" className="text-slate-700 hover:text-primary">
                  Sign In
                </Link>
                <Link
                  to="/signup"
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/20 hover:border-primary/60"
                >
                  Sign Up
                </Link>
              </div>
            ) : (
              <div className="hidden md:flex items-center gap-3 text-sm">
                <Link to="/account" className="text-slate-700 hover:text-primary">
                  Profile
                </Link>
                <button
                  onClick={handleLogout}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/20 hover:border-primary/60"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-12 space-y-14 md:space-y-20">
        <Hero />
        <KPIs />
        <Features />
        <HowItWorks />
        <UseCases />
        <SocialProof />
        <FinalCTA />
      </main>

      <footer className="border-t border-white/10 bg-white/80">
        <div className="max-w-6xl mx-auto px-4 py-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 text-sm text-slate-300">
          <div className="flex items-center gap-[0.1rem]">
            <img src={logo} alt="VINIMI logo" className="h-14 w-auto rounded-md p-0" />
            <span>VINIMI — Safety, Recognition, Compliance.</span>
          </div>
          <div className="flex gap-4">
            <a href="https://docs.vinimi.ai" className="hover:text-primary transition-colors">Docs</a>
            <a href="/privacy" className="hover:text-primary transition-colors">Privacy</a>
            <a href="/terms" className="hover:text-primary transition-colors">Terms</a>
            <a href="https://github.com" className="hover:text-primary transition-colors">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
