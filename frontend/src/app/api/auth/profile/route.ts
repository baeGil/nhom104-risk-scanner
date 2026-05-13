import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import { createClient } from "@supabase/supabase-js";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

export async function PUT(req: NextRequest) {
  const session = await auth();

  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { name } = await req.json();

  if (!name || name.trim().length === 0) {
    return NextResponse.json(
      { error: "Tên không được để trống" },
      { status: 400 }
    );
  }

  const { error } = await getSupabase()
    .from("users")
    .update({ name: name.trim() })
    .eq("id", session.user.id);

  if (error) {
    console.error("Profile update error:", error);
    return NextResponse.json(
      { error: "Không thể cập nhật hồ sơ" },
      { status: 500 }
    );
  }

  return NextResponse.json({ success: true, name: name.trim() });
}
