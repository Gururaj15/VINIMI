import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAuthed } from "@/lib/auth";

interface Props {
  children: ReactNode;
}

const ProtectedRoute = ({ children }: Props) => {
  const location = useLocation();
  if (!isAuthed()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return <>{children}</>;
};

export default ProtectedRoute;
