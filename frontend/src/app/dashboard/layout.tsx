import DashboardShell from "@/components/layout/DashboardShell";

export const metadata = {
  title: "Dashboard | Conversiono",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <DashboardShell>{children}</DashboardShell>;
}
