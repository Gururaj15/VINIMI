import { useNavigate, useLocation, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { ShieldCheck, Lock, Mail, ArrowLeftRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { managerLogin } from "@/lib/api";
import { setSession } from "@/lib/auth";
import brandLogo from "@/assets/logof.png";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(6, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

const Login = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const {
    handleSubmit,
    register,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (values: LoginForm) => {
    try {
      const data = await managerLogin({ email: values.email, password: values.password });
      if (!data) throw new Error("Login failed");
      setSession(data as any);
      toast({ title: "Welcome back", description: "Session started." });
      const redirectTo = (location.state as any)?.from || "/dashboard";
      navigate(redirectTo, { replace: true });
    } catch (err: any) {
      toast({
        title: "Login failed",
        description:
          err?.message ||
          (err?.toString && err.toString()) ||
          "Unable to sign in. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900 text-white relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute -left-10 top-10 h-64 w-64 bg-sky-500/15 blur-3xl" />
        <div className="absolute right-0 bottom-10 h-72 w-72 bg-purple-500/20 blur-3xl" />
      </div>

      <div className="relative max-w-6xl mx-auto px-6 py-10">
        <header className="flex items-center justify-between mb-10">
          <div className="flex items-center gap-3">
            <img src={brandLogo} alt="VINIMI" className="h-10 w-10 rounded-xl" />
            <div>
              <p className="text-sm uppercase tracking-[0.25em] text-slate-400">Manager</p>
              <p className="text-xl font-semibold">VINIMI Safety Console</p>
            </div>
          </div>
          <Link
            to="/"
            className="text-sm text-slate-300 hover:text-white inline-flex items-center gap-2"
          >
            <ArrowLeftRight className="h-4 w-4" />
            Back to site
          </Link>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/10 text-xs uppercase tracking-[0.25em]">
              Secure Access
              <ShieldCheck className="h-4 w-4 text-sky-400" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold leading-tight">
              Manager Login for real-time safety, recognition, and alerts.
            </h1>
            <p className="text-lg text-slate-300 max-w-xl">
              Sign in to control live monitoring, manage your worker gallery, and review
              helmet violations across every site you protect.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-slate-300">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="font-semibold text-white mb-1">Single console</p>
                <p className="text-slate-400">Live cameras, alerts, and worker identities in one place.</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="font-semibold text-white mb-1">Secure sessions</p>
                <p className="text-slate-400">JWT auth with manager roles and company scoping.</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-sky-500/20 border border-sky-400/40 flex items-center justify-center">
                <Lock className="h-5 w-5 text-sky-300" />
              </div>
              <p className="text-sm text-slate-300">
                Need an account?{" "}
                <Link to="/signup" className="text-sky-400 hover:text-sky-300 font-semibold">
                  Create one here
                </Link>
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Card className="bg-slate-950/70 border-white/10 shadow-2xl backdrop-blur">
              <CardHeader>
                <CardTitle className="text-2xl">Login</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <div className="relative">
                      <Mail className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
                      <Input
                        id="email"
                        type="email"
                        placeholder="manager@company.com"
                        className="pl-9"
                        {...register("email")}
                      />
                    </div>
                    {errors.email && (
                      <p className="text-xs text-red-400">{errors.email.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <div className="relative">
                      <Lock className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
                      <Input
                        id="password"
                        type="password"
                        placeholder="••••••••"
                        className="pl-9"
                        {...register("password")}
                      />
                    </div>
                    {errors.password && (
                      <p className="text-xs text-red-400">{errors.password.message}</p>
                    )}
                  </div>

                  <Button type="submit" className="w-full" disabled={isSubmitting}>
                    {isSubmitting ? "Signing in..." : "Login"}
                  </Button>
                </form>

                <p className="text-sm text-slate-400 mt-4">
                  No account yet?{" "}
                  <Link to="/signup" className="text-sky-400 hover:text-sky-300 font-semibold">
                    Create one
                  </Link>
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Login;
