/**
 * Purpose: A small, stable bar pattern for any id (each voice gets its own "voiceprint").
 * Layer:   web/lib (framework-free, pure)
 * Exports: voiceprint
 */
const FNV_OFFSET = 2166136261;
const FNV_PRIME = 16777619;
const MIX = 1597334677;

/** Bar heights in 0.18..1: FNV-1a hash of the id, stirred per bar, shaped by a soft arch. */
export function voiceprint(id: string, bars = 14): number[] {
  let hash = FNV_OFFSET;
  for (const char of id) hash = Math.imul(hash ^ char.charCodeAt(0), FNV_PRIME);
  const heights: number[] = [];
  for (let k = 0; k < bars; k++) {
    hash = Math.imul(hash ^ (hash >>> 13), MIX);
    const random = ((hash >>> 0) % 1000) / 1000;
    const arch = 0.45 + 0.55 * Math.sin((Math.PI * (k + 0.5)) / bars);
    heights.push(0.18 + 0.82 * random * arch);
  }
  return heights;
}
