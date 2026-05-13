import { createClient } from "@supabase/supabase-js";

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  resetAt: Date;
}

export interface RateLimitService {
  check(ip: string, action: string, limit: number): Promise<RateLimitResult>;
  record(ip: string, action: string): Promise<void>;
}

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

export class SupabaseRateLimitService implements RateLimitService {
  async check(ip: string, action: string, limit: number): Promise<RateLimitResult> {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    const { data } = await getSupabase()
      .from("ip_rate_limits")
      .select("*")
      .eq("ip_address", ip)
      .eq("action_type", action)
      .gte("window_start", oneHourAgo.toISOString())
      .order("window_start", { ascending: false })
      .limit(1);

    if (!data || data.length === 0) {
      return { allowed: true, remaining: limit, resetAt: new Date(now.getTime() + 60 * 60 * 1000) };
    }

    const record = data[0];
    const windowEnd = new Date(new Date(record.window_start).getTime() + 60 * 60 * 1000);

    if (record.count >= limit) {
      return { allowed: false, remaining: 0, resetAt: windowEnd };
    }

    return { allowed: true, remaining: limit - record.count, resetAt: windowEnd };
  }

  async record(ip: string, action: string): Promise<void> {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    const { data: existing } = await getSupabase()
      .from("ip_rate_limits")
      .select("*")
      .eq("ip_address", ip)
      .eq("action_type", action)
      .gte("window_start", oneHourAgo.toISOString())
      .order("window_start", { ascending: false })
      .limit(1);

    if (existing && existing.length > 0) {
      await getSupabase()
        .from("ip_rate_limits")
        .update({ count: existing[0].count + 1 })
        .eq("id", existing[0].id);
    } else {
      await getSupabase()
        .from("ip_rate_limits")
        .insert({
          ip_address: ip,
          action_type: action,
          count: 1,
          window_start: now.toISOString(),
        });
    }
  }
}

export const rateLimitService = new SupabaseRateLimitService();
