import { PublicLayout } from "@/components/layout/public-layout";
import { DotPattern } from "@/components/decorative/dot-pattern";

export default function PublicRootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <DotPattern />
      <PublicLayout>{children}</PublicLayout>
    </>
  );
}
