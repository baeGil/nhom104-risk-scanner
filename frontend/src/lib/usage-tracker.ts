import { createClient } from "@supabase/supabase-js";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

export async function incrementUsageCounter(
  userId: string,
  resourceType: "contract_upload" | "qa_question"
): Promise<void> {
  const now = new Date();
  const periodStart = resourceType === "qa_question"
    ? new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString()
    : new Date(now.getFullYear(), now.getMonth(), 1).toISOString();

  const periodType = resourceType === "qa_question" ? "daily" : "monthly";

  await getSupabase()
    .from("usage_counters")
    .upsert(
      {
        user_id: userId,
        resource_type: resourceType,
        period_start: periodStart,
        period_type: periodType,
        count: 1,
      },
      {
        onConflict: "user_id,resource_type,period_start,period_type",
      }
    );
}

export async function getUsageCount(
  userId: string,
  resourceType: "contract_upload" | "qa_question"
): Promise<number> {
  const now = new Date();
  const periodStart = resourceType === "qa_question"
    ? new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString()
    : new Date(now.getFullYear(), now.getMonth(), 1).toISOString();

  const periodType = resourceType === "qa_question" ? "daily" : "monthly";

  const { data } = await getSupabase()
    .from("usage_counters")
    .select("count")
    .eq("user_id", userId)
    .eq("resource_type", resourceType)
    .eq("period_start", periodStart)
    .eq("period_type", periodType)
    .single();

  return data?.count || 0;
}

export async function checkUsageLimit(
  userId: string,
  resourceType: "contract_upload" | "qa_question",
  limit: number
): Promise<{ allowed: boolean; current: number; limit: number }> {
  const current = await getUsageCount(userId, resourceType);
  return {
    allowed: current < limit,
    current,
    limit,
  };
}
