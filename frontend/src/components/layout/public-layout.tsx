import Link from "next/link";

export function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b-2 border-fg bg-white/80 backdrop-blur-sm">
        <nav className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-heading text-2xl text-fg hover:text-accent transition-colors">
            PhápLý
          </Link>
          <div className="flex gap-3">
            <Link href="/login" className="font-body text-lg text-fg px-4 py-2 border-2 border-fg/30 hover:border-secondary hover:text-secondary hover:bg-secondary/5 transition-all duration-200" style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}>
              Đăng nhập
            </Link>
            <Link href="/register" className="font-body text-lg text-white px-4 py-2 bg-fg border-2 border-fg hover:bg-secondary hover:border-secondary transition-all duration-200" style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}>
              Đăng ký
            </Link>
          </div>
        </nav>
      </header>
      <main>{children}</main>
      <footer className="border-t-2 border-fg bg-white/60 mt-20">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-heading text-xl text-fg mb-3">PhápLý</h3>
              <p className="font-body text-fg/70">
                AI rà soát hợp đồng & hỏi đáp pháp lý tiếng Việt
              </p>
            </div>
            <div>
              <h3 className="font-heading text-xl text-fg mb-3">Tính năng</h3>
              <ul className="font-body space-y-2">
                <li><Link href="/contract-review" className="hover:text-accent hover:line-through transition-colors">Rà soát hợp đồng</Link></li>
                <li><Link href="/legal-qa" className="hover:text-accent hover:line-through transition-colors">Hỏi đáp pháp lý</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="font-heading text-xl text-fg mb-3">Liên hệ</h3>
              <ul className="font-body space-y-2 text-fg/70">
                <li>contact@phaply.ai</li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-6 border-t border-fg/20 text-center font-body text-fg/50">
            © 2026 PhápLý. Bảo lưu mọi quyền.
          </div>
        </div>
      </footer>
    </div>
  );
}
