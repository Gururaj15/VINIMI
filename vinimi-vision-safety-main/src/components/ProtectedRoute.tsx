import { ReactNode } from "react";
import { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

const ProtectedRoute = ({ children }: Props) => {
  return <>{children}</>;
};

export default ProtectedRoute;
