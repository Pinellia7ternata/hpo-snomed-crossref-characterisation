"""
Quantitative slice for the SNOMED CT / HPO manuscript.

Empirical basis: the public HPO->SNOMED CT_US cross-reference set extracted from
the HPO OBO release (hp.obo, obophenotype/human-phenotype-ontology, master).
These are curator-declared cross-references; we treat them as the largest openly
available mapping between the two resources and analyze them as a reproducible
mapping sample (clearly scoped: HPO-curated SNOMED CT codes, not a random draw of
the full SNOMED CT Clinical finding branch, which requires a licensed RF2 release).

Outputs:
  mapping_full.csv        every (HPO term, SNOMED CT_US code) cross-reference with
                          cardinality type and information-loss dimensions
  summary.json            descriptive statistics + chi-square result
  (printed)               human-readable summary used to write the manuscript
"""
import re, json, csv, os, random
from collections import Counter, defaultdict

OBO = os.path.join(os.path.dirname(__file__), 'hp.obo')

# ---------- parse OBO ----------
terms = {}          # hp_id -> {'name':, 'is_a':[parents], 'xrefs':[codes]}
cur = None
with open(OBO, encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\n')
        if line == '[Term]':
            cur = {'id': None, 'name': None, 'is_a': [], 'xrefs': []}
        elif line == '' or line.startswith('['):
            if cur and cur['id']:
                terms[cur['id']] = cur
            cur = {'id': None, 'name': None, 'is_a': [], 'xrefs': []} if line.startswith('[') else None
            if line.startswith('['):
                cur = {'id': None, 'name': None, 'is_a': [], 'xrefs': []}
        elif cur is not None:
            if line.startswith('id: '):
                cur['id'] = line[4:].strip()
            elif line.startswith('name: '):
                cur['name'] = line[6:].strip()
            elif line.startswith('is_a: '):
                cur['is_a'].append(line[6:].split(' ')[0].strip())
            elif line.startswith('xref: SNOMEDCT_US:'):
                cur['xrefs'].append(line.split(':', 2)[2].strip())

# ---------- build parent closure for modifier-branch detection ----------
parents = {tid: set(t['is_a']) for tid, t in terms.items()}
def ancestors(tid, _seen=None):
    if _seen is None: _seen = set()
    for p in parents.get(tid, ()):
        if p not in _seen:
            _seen.add(p)
            ancestors(p, _seen)
    return _seen

MOD_KW = {
    'severity': ['severity'],
    'onset': ['onset'],
    'frequency': ['frequency'],
    'course/temporality': ['clinical course', 'course', 'temporal', 'timing'],
    'laterality': ['laterality', 'left', 'right', 'bilateral'],
}

def modifier_dims(hp_id):
    dims = set()
    anc_names = [terms.get(a, {}).get('name', '').lower() for a in ancestors(hp_id)]
    blob = ' '.join(anc_names)
    for dim, kws in MOD_KW.items():
        if any(k in blob for k in kws):
            dims.add(dim)
    return dims

# ---------- build mapping records ----------
records = []                 # (hp_id, hp_name, snomed_code)
snomed_to_hpo = defaultdict(set)
hpo_to_snomed = defaultdict(set)
for tid, t in terms.items():
    for code in t['xrefs']:
        records.append((tid, t['name'], code))
        snomed_to_hpo[code].add(tid)
        hpo_to_snomed[tid].add(code)

N = len(records)
distinct_snomed = len(snomed_to_hpo)
distinct_hpo = len(hpo_to_snomed)

# ---------- cardinality type (source = SNOMED CT_US code) ----------
def card_type(code):
    hpos = snomed_to_hpo[code]
    if len(hpos) == 1:
        h = next(iter(hpos))
        return 'exact' if len(hpo_to_snomed[h]) == 1 else 'narrow'
    return 'broad'

card_counter = Counter()
loss_modifier = 0
loss_granularity = 0
rows = []
for hp_id, hp_name, code in records:
    ct = card_type(code)
    card_counter[ct] += 1
    if ct != 'exact':
        loss_granularity += 1
    md = modifier_dims(hp_id)
    if md:
        loss_modifier += 1
    rows.append({
        'hpo_id': hp_id,
        'hpo_label': hp_name,
        'snomed_ct_us': code,
        'cardinality': ct,
        'loss_modifier_dim': ';'.join(sorted(md)),
        'loss_granularity': 'yes' if ct != 'exact' else 'no',
    })

# ---------- write full CSV ----------
out_csv = os.path.join(os.path.dirname(__file__), 'mapping_full.csv')
with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['hpo_id', 'hpo_label', 'snomed_ct_us',
                                      'cardinality', 'loss_modifier_dim', 'loss_granularity'])
    w.writeheader()
    w.writerows(rows)

# ---------- statistics ----------
def pct(n, d):
    return round(100.0 * n / d, 1) if d else 0.0

stats = {
    'n_crossrefs': N,
    'distinct_snomed_ct_us': distinct_snomed,
    'distinct_hpo_terms': distinct_hpo,
    'cardinality': {k: {'count': v, 'pct': pct(v, N)} for k, v in card_counter.items()},
    'loss_modifier_count': loss_modifier,
    'loss_modifier_pct': pct(loss_modifier, N),
    'loss_granularity_count': loss_granularity,
    'loss_granularity_pct': pct(loss_granularity, N),
}

# ---------- testable proposition: cardinality vs modifier loss (chi-square) ----------
# 2x2-ish contingency: exact vs non-exact (granularity) x modifier-loss vs not.
try:
    from scipy.stats import chi2_contingency
    a = sum(1 for r in rows if r['cardinality'] == 'exact' and r['loss_modifier_dim'])
    b = sum(1 for r in rows if r['cardinality'] == 'exact' and not r['loss_modifier_dim'])
    c = sum(1 for r in rows if r['cardinality'] != 'exact' and r['loss_modifier_dim'])
    d = sum(1 for r in rows if r['cardinality'] != 'exact' and not r['loss_modifier_dim'])
    chi2, p, _, _ = chi2_contingency([[a, b], [c, d]])
    stats['chi2_exact_vs_modifierloss'] = {'chi2': round(chi2, 2), 'p': p,
                                            'table': {'exact&modloss': a, 'exact&nomod': b,
                                                      'nonexact&modloss': c, 'nonexact&nomod': d}}
except Exception as e:
    stats['chi2_note'] = 'scipy unavailable: ' + str(e)

with open(os.path.join(os.path.dirname(__file__), 'summary.json'), 'w', encoding='utf-8') as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)

# ---------- 300-subsample for an illustrative "slice" ----------
random.seed(20260729)
sample = random.sample(rows, 300)
s_card = Counter(r['cardinality'] for r in sample)
s_mod = sum(1 for r in sample if r['loss_modifier_dim'])
s_gran = sum(1 for r in sample if r['cardinality'] != 'exact')

# ---------- print human-readable summary ----------
print('HPO->SNOMED CT_US cross-reference analysis')
print('=' * 50)
print(f'Total cross-references (mappings) : {N}')
print(f'Distinct SNOMED CT_US codes        : {distinct_snomed}')
print(f'Distinct HPO terms involved        : {distinct_hpo}')
print()
print('Cardinality type (source = SNOMED CT_US code):')
for k in ['exact', 'broad', 'narrow']:
    v = card_counter.get(k, 0)
    print(f'  {k:8s}: {v:5d}  ({pct(v, N)}%)')
print()
print(f'Mappings carrying a modifier-dimension loss risk : {loss_modifier} ({pct(loss_modifier, N)}%)')
print(f'Mappings carrying a granularity/coverage loss     : {loss_granularity} ({pct(loss_granularity, N)}%)')
print()
if 'chi2_exact_vs_modifierloss' in stats:
    c = stats['chi2_exact_vs_modifierloss']
    print(f'Testable proposition (exact-vs-modifier-loss, chi2={c["chi2"]}, p={c["p"]:.2e}):')
    print('  ', c['table'])
print()
print(f'Illustrative 300-subsample: cardinality={dict(s_card)}, modifier-loss={s_mod} ({pct(s_mod,300)}%), granularity-loss={s_gran} ({pct(s_gran,300)}%)')
print()
print('Wrote:', out_csv, 'and summary.json')
