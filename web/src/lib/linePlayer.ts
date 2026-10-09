/**
 * Purpose: Play one audio blob at a time; resolve when it ends, fails or is stopped.
 * Layer:   web/lib (framework-free)
 * Exports: LinePlayer
 * Notes:   Object URLs are revoked when the next clip starts, so long sessions do not leak.
 */
const STATE_EVENTS = ['play', 'pause', 'ended', 'emptied'] as const;

export class LinePlayer {
  private readonly audio = new Audio();
  private url: string | null = null;
  private finish: (() => void) | null = null;

  /** `onState(playing)` fires whenever the element starts or stops making sound. */
  constructor(onState: (playing: boolean) => void) {
    for (const name of STATE_EVENTS) {
      this.audio.addEventListener(name, () => onState(!this.audio.paused));
    }
    this.audio.addEventListener('ended', () => this.settle());
    this.audio.addEventListener('error', () => this.settle());
  }

  play(blob: Blob): Promise<void> {
    this.settle();
    this.release();
    this.url = URL.createObjectURL(blob);
    this.audio.src = this.url;
    return new Promise((resolve) => {
      this.finish = resolve;
      this.audio.play().catch(() => this.settle());
    });
  }

  /** Pause or resume the current clip (does nothing when idle). */
  toggle(): void {
    if (!this.url) return;
    if (this.audio.paused) void this.audio.play();
    else this.audio.pause();
  }

  stop(): void {
    this.audio.pause();
    this.settle();
  }

  private settle(): void {
    const finish = this.finish;
    this.finish = null;
    finish?.();
  }

  private release(): void {
    if (this.url) URL.revokeObjectURL(this.url);
    this.url = null;
  }
}
