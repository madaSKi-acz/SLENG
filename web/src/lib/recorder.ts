/**
 * Purpose: Record the microphone into one Blob, with a seconds tick and an automatic limit.
 * Layer:   web/lib (framework-free)
 * Exports: ClipRecorder
 */
const TICK_MS = 250;

export class ClipRecorder {
  private recorder: MediaRecorder | null = null;
  private timer = 0;

  get recording(): boolean {
    return this.recorder !== null;
  }

  /** Resolves with the recording once stop() is called or `maxSeconds` is reached. */
  async record(onTick: (seconds: number) => void, maxSeconds = 60): Promise<Blob> {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    const parts: Blob[] = [];
    const started = Date.now();
    this.recorder = recorder;
    recorder.ondataavailable = (event) => parts.push(event.data);
    this.timer = window.setInterval(() => {
      const seconds = Math.round((Date.now() - started) / 1000);
      onTick(seconds);
      if (seconds >= maxSeconds) this.stop();
    }, TICK_MS);
    const done = new Promise<Blob>((resolve) => {
      recorder.onstop = () => resolve(this.finish(stream, parts, recorder.mimeType));
    });
    recorder.start();
    return done;
  }

  stop(): void {
    if (this.recorder?.state === 'recording') this.recorder.stop();
  }

  private finish(stream: MediaStream, parts: Blob[], type: string): Blob {
    window.clearInterval(this.timer);
    stream.getTracks().forEach((track) => track.stop());
    this.recorder = null;
    return new Blob(parts, { type });
  }
}
