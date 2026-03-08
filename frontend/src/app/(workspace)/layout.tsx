import { ProtectedLayout } from "@/components/layout/protected-layout";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedLayout>{children}</ProtectedLayout>;
}
