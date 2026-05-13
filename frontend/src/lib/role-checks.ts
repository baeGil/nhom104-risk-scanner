export type Role = "free" | "premium" | "admin";

const roleHierarchy: Record<Role, number> = {
  free: 0,
  premium: 1,
  admin: 2,
};

export function hasRole(userRole: Role, requiredRole: Role): boolean {
  return roleHierarchy[userRole] >= roleHierarchy[requiredRole];
}

export function isFree(role: Role): boolean {
  return role === "free";
}

export function isPremium(role: Role): boolean {
  return role === "premium" || role === "admin";
}

export function isAdmin(role: Role): boolean {
  return role === "admin";
}

export const LIMITS = {
  free: {
    contractsPerMonth: 5,
    qaPerDay: 10,
    apiCallsPerHour: 100,
    maxUploadSizeMB: 5,
  },
  premium: {
    contractsPerMonth: Infinity,
    qaPerDay: Infinity,
    apiCallsPerHour: 1000,
    maxUploadSizeMB: 25,
  },
  admin: {
    contractsPerMonth: Infinity,
    qaPerDay: Infinity,
    apiCallsPerHour: Infinity,
    maxUploadSizeMB: 100,
  },
};

export function getLimits(role: Role) {
  return LIMITS[role];
}
