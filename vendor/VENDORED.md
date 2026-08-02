# Pinned copy of the CLIQUEBAIT library

`vendor/cliquebait/` is a byte-exact copy of `../CLIQUEBAIT/cliquebait/` taken on
**2026-08-02**. PENUMBRA imports from this copy, never from the sibling directory.

## Why a copy rather than an editable install

CLIQUEBAIT's paper is under review at DMKD and its code base is neither frozen nor under
version control. An editable install would let an edit made over there change a number
reported here, silently and with no record of which version produced it — which is the same
class of defect CLIQUEBAIT itself documents in the paper it audits (five construction details
that did not match the released code, PROTOCOL §1). Copying costs a second maintenance
surface and buys the ability to state exactly what was run.

If the upstream library changes and PENUMBRA wants the change, re-copy deliberately, update
the hashes below, and record in `DECISIONS.md` what moved and whether any PENUMBRA number
had to be recomputed.

## Pinned artefacts

Machine-readable in `pin.json`. SHA-256, truncated to 16 hex characters for reading:

| file | sha256 (16) | bytes |
|---|---|---|
| `cliquebait/__init__.py` | `6b75885626faca7f` | 235 |
| `cliquebait/core.py` | `45d245ac5fd60c14` | 17110 |
| `cliquebait/diagnostics.py` | `4dbe069534c33ea3` | 22836 |
| `cliquebait/synthetic.py` | `9b2f7f0f62abe5e3` | 10985 |

## Governing documents, hashed but not copied

These are not code and PENUMBRA does not execute them, but its protocol is inherited from
them and "inherited" has to name a version. They stay in the CLIQUEBAIT directory; what is
pinned is which text was binding.

| file | sha256 (16) | bytes | what it binds |
|---|---|---|---|
| `PROTOCOL.md` | `d46bd8b7b2b2e72e` | 7305 | the checklist PENUMBRA inherits in full (manifesto §9) |
| `MANIFESTO-OUTCOMES.md` | `3110c68621a4c3bb` | 11153 | which manifesto instructions are known wrong and overridden |
| `FINDINGS.md` | `3fe58d8d22782368` | 34163 | the measurements every inherited constraint rests on |
| `target-relation-leakage-manifesto.md` | `844b4f191b3b95bb` | 12086 | the prior pre-registration, for the H4 → P6 restatement |

## Verifying

    python scripts/verify_pin.py

Fails loudly if `vendor/cliquebait/` has drifted from `pin.json`, or if a governing document
upstream has changed since it was pinned. The second case is not an error — documents are
allowed to evolve — but it must be seen rather than discovered later.
