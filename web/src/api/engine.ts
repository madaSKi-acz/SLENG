/**
 * Purpose: Typed calls to the engine HTTP API; the only code in the app that knows its URLs.
 * Layer:   web/api
 * Exports: EngineApi, engine (the shared instance)
 * Depends: api/http, api/types
 */
import { HttpClient, apiBase, jsonBody } from '@/api/http';
import type {
  Chunk,
  CloneForm,
  EngineOptions,
  ExportKind,
  Job,
  LineAudio,
  LineRequest,
  Narration,
  VideoJob,
  Voice,
} from '@/api/types';

const GAP_HEADER = 'X-Gap-After';
const SEED_HEADER = 'X-Seed';

export class EngineApi {
  constructor(private readonly http: HttpClient) {}

  options(): Promise<EngineOptions> {
    return this.http.json('/options');
  }

  voices(): Promise<Voice[]> {
    return this.http.json('/voices');
  }

  split(text: string, maxChars: number): Promise<Chunk[]> {
    return this.http.json('/text/split', jsonBody({ text, max_chars: maxChars }));
  }

  /** One line as audio, plus how long to pause before the next line. */
  async speakLine(request: LineRequest): Promise<LineAudio> {
    const response = await this.http.send('/speech/line', jsonBody(request));
    const gapAfter = Number(response.headers.get(GAP_HEADER) ?? 0);
    return { blob: await response.blob(), gapAfter };
  }

  exportFile(kind: ExportKind, narration: Narration): Promise<Blob> {
    return this.http.blob(`/exports/${kind}`, jsonBody(narration));
  }

  startVideo(job: VideoJob): Promise<Job> {
    return this.http.json('/jobs/video', jsonBody(job));
  }

  job(id: string): Promise<Job> {
    return this.http.json(`/jobs/${encodeURIComponent(id)}`);
  }

  async jobResult(id: string): Promise<{ blob: Blob; seed: string | null }> {
    const response = await this.http.send(`/jobs/${encodeURIComponent(id)}/result`);
    return { blob: await response.blob(), seed: response.headers.get(SEED_HEADER) };
  }

  cloneVoice(form: CloneForm): Promise<Voice> {
    const body = new FormData();
    body.set('name', form.name);
    body.set('gender', form.gender);
    body.set('base_id', form.baseId);
    body.set('clean', String(form.clean));
    body.set('clip', form.clip, 'clip');
    return this.http.json('/voices', { method: 'POST', body });
  }

  previewClip(clip: Blob, clean: boolean): Promise<Blob> {
    const body = new FormData();
    body.set('clean', String(clean));
    body.set('clip', clip, 'clip');
    return this.http.blob('/voices/preview', { method: 'POST', body });
  }

  async deleteVoice(id: string): Promise<void> {
    await this.http.send(`/voices/${encodeURIComponent(id)}`, { method: 'DELETE' });
  }
}

export const engine = new EngineApi(new HttpClient(apiBase()));
