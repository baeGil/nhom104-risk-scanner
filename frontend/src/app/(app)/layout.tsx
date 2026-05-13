import { AppLayout } from "@/components/layout/app-layout";
import { DotPattern } from "@/components/decorative/dot-pattern";
import { auth } from "@/auth";
import { AuthProvider } from "@/lib/auth-context";
import { LogoutProvider } from "@/lib/logout-context";

export default async function AppRootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  return (
    <AuthProvider session={session}>
      <LogoutProvider>
        <DotPattern />
        <AppLayout>{children}</AppLayout>
      </LogoutProvider>
    </AuthProvider>
  );
}
