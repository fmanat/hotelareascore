// Same deterministic rules as Python. Attribute diagnostics never run here.
import {readFileSync} from 'node:fs';
import {normalizeName, checkHotelExports} from './institution-guard.mjs';
const config = JSON.parse(readFileSync(new URL('../../src/hotelareascore/brand_rules.json', import.meta.url), 'utf8'));
if (config.version !== 1 || !config.rules?.length) throw new Error('Invalid brand rules');
const escaped = t => normalizeName(t).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const word = p => `(?<![\\p{L}\\p{N}_])(?:${p})(?![\\p{L}\\p{N}_])`;
const rules = config.rules.map(r => {
  if (!['word','substring','full'].includes(r.match) || !r.terms.length) throw new Error('Invalid brand rule');
  const p = `(?:${r.terms.map(escaped).join('|')})`;
  return {...r, pattern:new RegExp(r.match === 'full' ? `^${p}$` : r.match === 'word' ? word(p) : p, 'u')};
});
const groups = Object.entries(config.groups).map(([g, a]) => [g, new RegExp(word(a.map(escaped).join('|')), 'u')]);
const property = new RegExp(word(config.property_prefix_terms.map(escaped).join('|')), 'u');
const filler = new RegExp(word([...config.property_prefix_terms,'the','a','an','official','loyalty','program','programme'].map(escaped).join('|')), 'gu');
const quarantine = new Map(config.quarantined_records.flatMap(r => [[r.id,r],[r.slug,r]]));
export function brandMatches(name, hotelId) {
  const text = normalizeName(name ?? '');
  const group = groups.find(([,p]) => p.test(text))?.[0] ?? 'unresolved';
  const matches = rules.flatMap(r => {
    const m = r.pattern.exec(text);
    if (!m) return [];
    const prefix = text.slice(0,m.index).trim();
    if (r.allow_property_prefix && property.test(prefix) && prefix.replace(filler,' ').trim()) return [];
    return [{reason:r.reason, group:r.group ?? group, language:r.language, term:m[0]}];
  });
  const pinned = quarantine.get(hotelId);
  if (pinned) return matches.length ? matches.map(m => ({...m,group:pinned.group})) : [{reason:pinned.reason,group:pinned.group,language:'record',term:'quarantined_id'}];
  const approved = config.reviewed_hotels.find(h => (h.id === hotelId || h.slug === hotelId) && text === normalizeName(h.name));
  return approved ? matches.filter(m => !approved.allowed_reasons.includes(m.reason)) : matches;
}
export function checkBrandExports(webRoot) {
  checkHotelExports(webRoot, brandMatches, 'Non-establishment brand');
}
