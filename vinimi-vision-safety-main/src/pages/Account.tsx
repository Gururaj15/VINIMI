import { useEffect, useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { managerGet, managerUpdate } from "@/lib/api";
import { getManager, setManager } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import DashboardLayout from "@/components/DashboardLayout";

const Account = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    name: "",
    company_id: "",
    password: "",
  });

  useEffect(() => {
    const mgr = getManager();
    if (!mgr) {
      setLoading(false);
      return;
    }
    setForm({
      name: mgr.name || "",
      company_id: mgr.company_id?.toString() || "",
      password: "",
    });
    setLoading(false);
  }, []);

  const handleSave = async () => {
    const mgr = getManager();
    if (!mgr) {
      toast({ title: "Not signed in", variant: "destructive" });
      return;
    }
    try {
      const payload: any = {
        name: form.name,
        company_id: Number(form.company_id) || mgr.company_id,
      };
      if (form.password) {
        payload.password = form.password;
      }
      const updated = await managerUpdate(mgr.id, payload);
      setManager(updated as any);
      toast({ title: "Account updated" });
      setForm((f) => ({ ...f, password: "" }));
    } catch (err: any) {
      toast({
        title: "Update failed",
        description: err?.message || "Could not save changes",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <DashboardLayout title="Profile">
        <div className="p-6 text-muted-foreground">Loading...</div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Profile">
      <div className="p-6 max-w-2xl mx-auto">
        <Card className="bg-white border border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle>Manager Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Company ID</Label>
              <Input
                type="number"
                value={form.company_id}
                onChange={(e) => setForm((f) => ({ ...f, company_id: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>New Password (optional)</Label>
              <Input
                type="password"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
              />
            </div>
            <Button onClick={handleSave}>Save Changes</Button>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Account;
