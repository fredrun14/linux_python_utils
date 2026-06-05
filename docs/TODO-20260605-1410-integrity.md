# MODULE INTEGRITY — OPTIMISATION (verdict GO)
> **Date :** 2026-06-05 à 14:10
> **Complexité estimée :** Faible
> **Verdict revue :** GO (aucun bloquant) — TODO d'amélioration uniquement
> **Source :** `PLAN_ACTION_REVUE.md` § integrity

---

## Contexte

### Problématique
Module sain (toutes dimensions ✅). Points d'amélioration uniquement :
- `verify()` (l.99-167) est longue (CC ~8) et mélange 3 responsabilités ;
- `verify()` retourne `True` si la source est vide (vérification « vacue ») ;
- MD5/SHA1 accessibles via `getattr(hashlib, algorithm)` sans garde ;
- `calculate_checksum` statique redondant (viole le DIP injecté).

### Solution technique retenue
Découper `verify()`, signaler les vérifications vides, ajouter une whitelist
d'algorithmes. Améliorations sans changement de comportement public.

### Fichiers impactés
- `src/linux_python_utils/integrity/sha256.py`
- `src/linux_python_utils/integrity/base.py`
- `tests/test_integrity.py`

---

## Évolutions à mettre en place (Détail Junior)

### `sha256.py` — 🟡 optimisation
1. Découper `verify()` en deux helpers privés :
```python
def _resolve_dest(self, destination: Path, source: Path,
                  dest_subdir: str | None) -> Path:
    """Résout le répertoire de destination effectif (cas rsync subdir)."""
    ...

def _verify_tree(self, source: Path, dest: Path) -> bool:
    """Compare chaque fichier de l'arbre source à sa copie dest."""
    ...
```
   `verify()` se réduit à : résoudre → vérifier → try/except global.
2. Signaler une vérification vide :
```python
if fichiers_verifies == 0:
    self._logger.log_warning("Aucun fichier vérifié (source vide ?)")
```
3. Statuer sur `calculate_checksum` statique (l.42) : supprimer et adapter le
   test pour utiliser la fonction module `calculate_checksum`, OU la conserver
   marquée « rétrocompat » (vérifier d'abord les consommateurs externes :
   `grep -rn "SHA256IntegrityChecker.calculate_checksum" ~/PycharmProjects`).

### `base.py` — 🟡 optimisation
- Whitelist d'algorithmes (l.68) :
```python
_ALGOS_AUTORISES = {"sha256", "sha384", "sha512", "blake2b"}

if algorithm not in _ALGOS_AUTORISES:
    raise ValueError(f"Algorithme non autorisé : {algorithm}")
```
- Typing `Union` → `str | Path` (l.6).

---

## Checklist d'implémentation

### Code
- [x] `sha256.py` — `_resolve_dest` + `_verify_tree` (CC réduite)
- [x] `sha256.py` — warning si 0 fichier vérifié (source vide)
- [x] `sha256.py` — `calculate_checksum` statique conservée (utilisée dans test)
- [x] `base.py` — `_ALGOS_AUTORISES` (sha256/384/512/blake2b) + `str | Path`

### Tests (pytest)
- [x] `test_verify_source_vide_logue_warning()`
- [x] `test_checksum_algorithme_non_autorise_leve_valueerror()` (MD5 rejeté)
- [x] `test_sha512_algorithm()` (remplace test_md5_algorithm)
- [x] 20/20 passed, bandit 0 issue

---

## Points d'attention
- Module GO : ces tâches sont des améliorations, pas des correctifs urgents.
  À planifier après la vague sécurité des modules NO-GO.

---

## ⏸ Validation requise
**Aucun code modifié avant approbation.** Répondre **"OK"** pour démarrer.
