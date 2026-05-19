import { AuthGuard } from "@/components/auth/AuthGuard";
import { Sidebar } from "@/components/layouts/Sidebar";
import { TopNav } from "@/components/layouts/TopNav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex h-full">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopNav />
          <main className="flex-1 overflow-auto p-6">{children}</main>
        </div>
      </div>
    </AuthGuard>
  );
}
