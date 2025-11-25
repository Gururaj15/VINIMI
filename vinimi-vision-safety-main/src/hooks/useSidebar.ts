import { useEffect, useState } from "react";

const STORAGE_KEY = "vinimi.sidebar.open";

const getInitial = () => {
  if (typeof window === "undefined") return true;
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved !== null) {
    return saved === "true";
  }
  return window.innerWidth >= 1024; // open on desktop, closed on mobile
};

export const useSidebar = () => {
  const [open, setOpen] = useState<boolean>(getInitial);

  useEffect(() => {
    const handler = () => {
      if (window.innerWidth < 1024) {
        setOpen(false);
      }
    };
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, String(open));
    }
  }, [open]);

  const toggle = () => setOpen((p) => !p);

  return { open, setOpen, toggle };
};
