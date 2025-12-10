// src/pages/Workers.tsx
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Search, Eye, Edit, Trash2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";

import { fetchWorkers, WorkerApi } from "@/lib/api";
import DashboardLayout from "@/components/DashboardLayout";

interface Worker {
  id: number;
  name: string;
  phone: string;
  location: string;   // mapped from location_name
  joinedAt: string;   // mapped from joined_at
  violations: number; // placeholder for now
  companyName: string;
}

export default function WorkersPage() {
  const { toast } = useToast();

  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    location: "",
  });

  // ---- Load from backend ----
  useEffect(() => {
    (async () => {
      try {
        const apiWorkers = await fetchWorkers();

        const mapped: Worker[] = apiWorkers.map((w: WorkerApi) => ({
          id: w.id,
          name: w.name,
          phone: w.phone,
          location: w.location_name,
          joinedAt: w.joined_at,
          violations: w.violation_count ?? (w.violations ? w.violations.length : 0) ?? 0,
          companyName: w.company_name,
        }));

        setWorkers(mapped);
      } catch (err: any) {
        console.error(err);
        toast({
          title: "Failed to load workers",
          description: err?.message || "Please try again.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    })();
  }, [toast]);

  // ---- Search / filter ----
  const filteredWorkers = useMemo(() => {
    if (!searchQuery.trim()) return workers;
    const q = searchQuery.toLowerCase();
    return workers.filter(
      (w) =>
        w.name.toLowerCase().includes(q) ||
        w.phone.toLowerCase().includes(q) ||
        w.location.toLowerCase().includes(q) ||
        w.companyName.toLowerCase().includes(q)
    );
  }, [searchQuery, workers]);

  // ---- Add / delete (local only for now) ----
  const handleAddWorker = () => {
    if (!formData.name || !formData.phone || !formData.location) {
      toast({
        title: "Missing fields",
        description: "Please fill in name, phone and location.",
        variant: "destructive",
      });
      return;
    }

    const newWorker: Worker = {
      id: workers.length ? workers[workers.length - 1].id + 1 : 1,
      name: formData.name,
      phone: formData.phone,
      location: formData.location,
      joinedAt: new Date().toISOString().slice(0, 10),
      violations: 0,
      companyName: "Custom",
    };

    setWorkers((prev) => [...prev, newWorker]);
    setFormData({ name: "", phone: "", location: "" });
    setIsAddDialogOpen(false);

    toast({
      title: "Worker added",
      description: `${newWorker.name} has been added locally.`,
    });
  };

  const handleDeleteWorker = (id: number, name: string) => {
    setWorkers((prev) => prev.filter((w) => w.id !== id));
    toast({
      title: "Worker removed (local)",
      description: `${name} has been removed from the table.`,
    });
  };

  const content = (
    <div className="space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          Workers
        </h1>
        <p className="text-slate-600 mt-1">Manage your construction workers</p>
      </div>

      <Card className="bg-white border border-slate-200 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div className="space-y-1">
            <CardTitle className="text-xl text-slate-900">Worker Directory</CardTitle>
            <CardDescription className="text-slate-600">
              Search and manage workers on site.
            </CardDescription>
          </div>
          <Button onClick={() => setIsAddDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Add Worker
          </Button>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                className="pl-9 bg-white border-slate-200 text-slate-900"
                placeholder="Search by name, phone, company or location..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="text-slate-700">Name</TableHead>
                  <TableHead className="text-slate-700">Phone</TableHead>
                  <TableHead className="text-slate-700">Location</TableHead>
                  <TableHead className="text-slate-700">Joined</TableHead>
                  <TableHead className="text-slate-700">Violations</TableHead>
                  <TableHead className="text-right text-slate-700">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading && (
                  <TableRow>
                    <TableCell colSpan={6} className="py-8 text-center">
                      Loading workers...
                    </TableCell>
                  </TableRow>
                )}

                {!loading && filteredWorkers.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="py-8 text-center">
                      No workers found.
                    </TableCell>
                  </TableRow>
                )}

                {!loading &&
                  filteredWorkers.map((worker) => (
                    <TableRow key={worker.id} className="hover:bg-slate-50">
                      <TableCell className="font-medium text-slate-900">
                        <div className="flex flex-col">
                          <span>{worker.name}</span>
                          <span className="text-xs text-slate-500">
                            {worker.companyName}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-800">{worker.phone}</TableCell>
                      <TableCell className="text-slate-800">{worker.location}</TableCell>
                      <TableCell className="text-slate-800">{worker.joinedAt}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            worker.violations > 3
                              ? "destructive"
                              : worker.violations > 0
                              ? "secondary"
                              : "outline"
                          }
                        >
                          {worker.violations}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2 text-slate-500">
                          <Link to={`/workers/${worker.id}`}>
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </Link>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              handleDeleteWorker(worker.id, worker.name)
                            }
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Worker</DialogTitle>
            <DialogDescription>
              This currently adds a worker only in the UI (not yet saved to
              backend).
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <Input
              placeholder="Name"
              value={formData.name}
              onChange={(e) =>
                setFormData((f) => ({ ...f, name: e.target.value }))
              }
            />
            <Input
              placeholder="Phone"
              value={formData.phone}
              onChange={(e) =>
                setFormData((f) => ({ ...f, phone: e.target.value }))
              }
            />
            <Input
              placeholder="Location"
              value={formData.location}
              onChange={(e) =>
                setFormData((f) => ({ ...f, location: e.target.value }))
              }
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddWorker}>Add</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
  return <DashboardLayout title="Workers">{content}</DashboardLayout>;
}
