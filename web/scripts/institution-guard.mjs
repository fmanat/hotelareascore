// Same reviewed literals as Python ingestion; keep normalization in parity tests.
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const config = JSON.parse(readFileSync(new URL('../../src/hotelareascore/institution_rules.json', import.meta.url), 'utf8'));
if (config.version !== 1 || !config.rules?.length) throw new Error('Invalid institution rules');

export function normalizeName(name) {
  let latin = false;
  let text = '';
  for (const ch of name.normalize('NFKC').toLowerCase().normalize('NFD')) {
    if (/\p{M}/u.test(ch)) {
      if (!latin) text += ch;
    } else {
      latin = /\p{Script=Latin}/u.test(ch);
      text += ch;
    }
  }
  text = text.normalize('NFC').replace(/['’‘ʼ`＇]/gu, '');
  text = /^[\x00-\x7F]*$/.test(text) ? text.replace(/[\W_]+/g, ' ') : text.replace(/[\p{P}\p{Z}]/gu, ' ');
  return text.trim().replace(/\s+/gu, ' ');
}
const rules = config.rules.map(rule => {
  if (!['word', 'substring'].includes(rule.match) || !rule.terms.length) throw new Error('Invalid institution rule');
  const terms = rule.terms.map(t => normalizeName(t).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const pattern = `(?:${terms.join('|')})`;
  return { ...rule, pattern: new RegExp(rule.match === 'word' ? `(?<![\\p{L}\\p{N}_])${pattern}(?![\\p{L}\\p{N}_])` : pattern, 'u') };
});

export function institutionMatches(name, hotelId) {
  const text = normalizeName(name ?? '');
  const matches = rules.flatMap(rule => {
    const match = rule.pattern.exec(text);
    return match ? [{ reason: rule.reason, language: rule.language, term: match[0] }] : [];
  });
  const quarantined = (config.quarantined_records ?? []).find(h => h.id === hotelId || h.slug === hotelId);
  if (quarantined) return matches.length ? matches : [{ reason: quarantined.reason, language: 'record', term: 'quarantined_id' }];
  const approved = (config.reviewed_hotels ?? []).find(h => (h.id === hotelId || h.slug === hotelId) && text === normalizeName(h.name));
  return approved ? matches.filter(m => !approved.allowed_reasons.includes(m.reason)) : matches;
}

export function checkInstitutionExports(webRoot) {
  return checkHotelExports(webRoot, institutionMatches, 'Institution');
}

export function checkHotelExports(webRoot, matcher, label) {
  const failures = [];
  // Include static cards, global/sharded search, city representatives, comparisons.
  function visit(value, file) {
    if (Array.isArray(value)) return value.forEach(v => visit(v, file));
    if (!value || typeof value !== 'object') return;
    if (typeof value.name === 'string' || value.id || value.slug) {
      const matches = matcher(value.name, value.id ?? value.slug);
      if (!matches.length && value.id && value.slug) matches.push(...matcher(value.name, value.slug));
      if (matches.length) failures.push({ file, id: value.id ?? value.slug, name: value.name, matches });
    }
    for (const [key, child] of Object.entries(value)) {
      // Nearby POIs are contextual facts, not hotel identities.
      if (key !== 'nearby_facts' && key !== 'reason_codes') visit(child, file);
    }
  }
  for (const dir of ['src/data', 'public/data']) {
    for (const file of readdirSync(path.join(webRoot, dir)).filter(f => f.endsWith('.json'))) {
      visit(JSON.parse(readFileSync(path.join(webRoot, dir, file), 'utf8')), `${dir}/${file}`);
    }
  }
  if (failures.length) {
    throw new Error(`${label} candidates in web exports; no pages may be built:\n${JSON.stringify(failures, null, 2)}`);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  checkInstitutionExports(path.resolve(fileURLToPath(import.meta.url), '../..'));
}
