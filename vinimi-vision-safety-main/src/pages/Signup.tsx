import { Link, useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { managerSignup } from "@/lib/api";
import { setSession } from "@/lib/auth";
import brandLogo from "@/assets/logo1.png";
import { ShieldPlus, Mail, Lock, User2, Hash } from "lucide-react";

const signupSchema = z
  .object({
    name: z.string().min(2, "Name is required"),
    email: z.string().email("Enter a valid email"),
    companyId: z.preprocess(
      (v) => Number(v),
      z.number().int().positive("Company ID is required"),
    ),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm: z.string().min(8, "Confirm your password"),
  })
  .refine((vals) => vals.password === vals.confirm, {
    path: ["confirm"],
    message: "Passwords must match",
  });

type SignupForm = z.infer<typeof signupSchema>;

const Signup = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const {
    handleSubmit,
    register,
    formState: { errors, isSubmitting },
  } = useForm<SignupForm>({
    resolver: zodResolver(signupSchema),
    defaultValues: { name: "", email: "", companyId: 1, password: "", confirm: "" },
  });

  const onSubmit = async (values: SignupForm) => {
    try {
      const data = await managerSignup({
        name: values.name,
        email: values.email,
        password: values.password,
        company_id: values.companyId,
      });
      if (!data) throw new Error("Signup failed");
      setSession(data as any);
      toast({ title: "Welcome to VINIMI", description: "Manager account created." });
      const redirectTo = (location.state as any)?.from || "/dashboard";
      navigate(redirectTo, { replace: true });
    } catch (err: any) {
      toast({
        title: "Signup failed",
        description:
          err?.message ||
          (err?.toString && err.toString()) ||
          "Unable to create account. Please try again.",
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
            to="/login"
            className="text-sm text-slate-300 hover:text-white inline-flex items-center gap-2"
          >
            Have an account? Login
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
              <ShieldPlus className="h-4 w-4 text-sky-400" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold leading-tight">
              Create a manager account to monitor PPE and identities in real time.
            </h1>
            <p className="text-lg text-slate-300 max-w-xl">
              Sign up to control live monitoring, manage your worker gallery, and review helmet
              violations across every site you protect.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-slate-300">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="font-semibold text-white mb-1">Manager scope</p>
                <p className="text-slate-400">Company-scoped access with secure JWT auth.</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="font-semibold text-white mb-1">Instant alerts</p>
                <p className="text-slate-400">Enable live detections and SMS alerts once signed in.</p>
              </div>
            </div>
            <p className="text-sm text-slate-300">
              By signing up you agree to our{" "}
              <a href="/terms" className="text-sky-400 hover:text-sky-300 font-semibold">
                Terms
              </a>{" "}
              and{" "}
              <a href="/privacy" className="text-sky-400 hover:text-sky-300 font-semibold">
                Privacy
              </a>
              .
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Card className="bg-slate-950/70 border-white/10 shadow-2xl backdrop-blur">
              <CardHeader>
                <CardTitle className="text-2xl">Create account</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
                  <div className="space-y-2">
                    <Label htmlFor="name">Full name</Label>
                    <div className="relative">
                      <User2 className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
                      <Input id="name" placeholder="Priya Sharma" className="pl-9" {...register("name")} />
                    </div>
                    {errors.name && <p className="text-xs text-red-400">{errors.name.message}</p>}
                  </div>

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
                    {errors.email && <p className="text-xs text-red-400">{errors.email.message}</p>}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="companyId">Company ID</Label>
                    <div className="relative">
                      <Hash className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
                      <Input
                        id="companyId"
                        type="number"
                        placeholder="e.g. 1"
                        className="pl-9"
                        {...register("companyId", { valueAsNumber: true })}
                      />
                    </div>
                    {errors.companyId && (
                      <p className="text-xs text-red-400">{errors.companyId.message}</p>
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

                  <div className="space-y-2">
                    <Label htmlFor="confirm">Confirm password</Label>
                    <div className="relative">
                      <Lock className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
                      <Input
                        id="confirm"
                        type="password"
                        placeholder="••••••••"
                        className="pl-9"
                        {...register("confirm")}
                      />
                    </div>
                    {errors.confirm && <p className="text-xs text-red-400">{errors.confirm.message}</p>}
                  </div>

                  <Button type="submit" className="w-full" disabled={isSubmitting}>
                    {isSubmitting ? "Creating..." : "Create account"}
                  </Button>
                </form>

                <p className="text-sm text-slate-400 mt-4">
                  Already have an account?{" "}
                  <Link to="/login" className="text-sky-400 hover:text-sky-300 font-semibold">
                    Login here
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

export default Signup;
