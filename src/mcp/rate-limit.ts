export interface RateLimitDecision {
  allowed: boolean;
  retryAfterSeconds: number;
}

interface WindowState {
  startedAt: number;
  count: number;
  lastSeenAt: number;
}

/** In-memory fixed-window limiter; production multi-replica deployments need a shared store. */
export class IdentityRateLimiter {
  private readonly identities = new Map<string, WindowState>();
  private global: WindowState;

  constructor(
    private readonly perIdentityLimit: number,
    private readonly globalLimit: number,
    private readonly now: () => number = Date.now,
  ) {
    const current = now();
    this.global = { startedAt: current, count: 0, lastSeenAt: current };
  }

  take(identityKey: string): RateLimitDecision {
    const current = this.now();
    this.global = this.refresh(this.global, current);
    const identity = this.refresh(this.identities.get(identityKey) ?? { startedAt: current, count: 0, lastSeenAt: current }, current);
    identity.lastSeenAt = current;
    this.identities.set(identityKey, identity);
    this.prune(current);

    const globalAllowed = this.global.count < this.globalLimit;
    const identityAllowed = identity.count < this.perIdentityLimit;
    if (!globalAllowed || !identityAllowed) {
      const waitUntil = Math.max(
        !globalAllowed ? this.global.startedAt + 60_000 : current,
        !identityAllowed ? identity.startedAt + 60_000 : current,
      );
      return { allowed: false, retryAfterSeconds: Math.max(1, Math.ceil((waitUntil - current) / 1000)) };
    }
    this.global.count += 1;
    identity.count += 1;
    return { allowed: true, retryAfterSeconds: 0 };
  }

  private refresh(state: WindowState, current: number): WindowState {
    return current - state.startedAt >= 60_000
      ? { startedAt: current, count: 0, lastSeenAt: current }
      : state;
  }

  private prune(current: number): void {
    if (this.identities.size < 10_000) return;
    for (const [key, state] of this.identities) {
      if (current - state.lastSeenAt > 120_000) this.identities.delete(key);
    }
  }
}
