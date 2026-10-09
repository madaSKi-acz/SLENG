/**
 * Purpose: Hand items from a producer to a consumer by index, in any order, with waiting.
 * Layer:   web/lib (framework-free)
 * Exports: ClipQueue
 * Notes:   Speech: synthesis puts line i when ready; playback takes line i (waits if needed).
 *          close() wakes every waiter with null so a stopped run ends cleanly.
 */
export class ClipQueue<T> {
  private readonly items = new Map<number, T>();
  private readonly waiters = new Map<number, (item: T | null) => void>();
  private closed = false;

  put(index: number, item: T): void {
    if (this.closed) return;
    this.items.set(index, item);
    this.waiters.get(index)?.(item);
    this.waiters.delete(index);
  }

  take(index: number): Promise<T | null> {
    const item = this.items.get(index);
    if (item !== undefined) return Promise.resolve(item);
    if (this.closed) return Promise.resolve(null);
    return new Promise((resolve) => this.waiters.set(index, resolve));
  }

  close(): void {
    this.closed = true;
    for (const wake of this.waiters.values()) wake(null);
    this.waiters.clear();
  }
}
