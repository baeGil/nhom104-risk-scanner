import { AppLayout } from "@/components/layout/app-layout";
import { DotPattern } from "@/components/decorative/dot-pattern";

export default function AppRootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <DotPattern />
      <AppLayout>{children}</AppLayout>
    </>
  );
}
