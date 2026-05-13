import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

export async function POST(req: NextRequest) {
  try {
    const { email } = await req.json();

    if (!email) {
      return NextResponse.json({ needsVerification: false });
    }

    const { data: users } = await getSupabase()
      .from("users")
      .select("email_verified")
      .eq("email", email)
      .limit(1);

    if (!users || users.length === 0) {
      return NextResponse.json({ needsVerification: false });
    }

    return NextResponse.json({
      needsVerification: !users[0].email_verified,
    });
  } catch {
    return NextResponse.json({ needsVerification: false });
  }
}
