# FIX — DÉTECTION uv ROBUSTE + sudo CONDITIONNEL (LinuxCliInstaller)
> **Date :** 2026-05-30 à 21:10
> **Complexité estimée :** Faible

---

## Contexte

### Problématique
`LinuxCliInstaller._run_uv_install` plante dans deux cas :

1. **`uv` introuvable alors qu'il est installé.** `shutil.which("uv")` ne
   cherche que dans le PATH du process courant. Lancé en root (sudo), le
   PATH n'inclut pas `~/.local/bin` de l'utilisateur invoquant → uv
   « introuvable » bien qu'installé (ex. `/home/fred/.local/bin/uv`).
   Message trompeur : « installez uv : pip install uv ».
2. **`sudo` codé en dur pour le mode system.** La commande préfixe
   toujours `sudo` ; quand on est **déjà root**, c'est inutile et ça
   échoue si `sudo` n'est pas installé (`sudo: commande non trouvée`).

### Solution technique retenue
- Helper `_find_uv()` : `shutil.which` puis repli vers
  `~/.local/bin/uv`, `~/.cargo/bin/uv` du user courant **et** de
  `$SUDO_USER`.
- `sudo` ajouté uniquement si `os.geteuid() != 0`.
- Message d'erreur explicite (PATH + emplacements testés).

### Fichiers impactés
- `src/linux_python_utils/scripts/installer.py` — `_find_uv` + `_run_uv_install`
- `tests/test_scripts.py` — tests détection/sudo + mocks 4-tuple

### Hors scope (à signaler)
8 tests `test_scripts.py` échouent **avant** ce changement à cause d'un
drift indépendant : `check_dependencies` renvoie désormais un 4-tuple
`(missing, installed, total, install_cmd)` (impl + installer) mais l'ABC
`CliScriptChecker.check_dependencies` et plusieurs tests sont restés en
3-tuple. Les 3 tests `TestLinuxScriptCheckerDeps` relèvent de ce bug
distinct — **non traités ici**. Les tests `TestLinuxCliInstaller` qui
échouent pour la même raison et que je touche seront corrigés (mock
4-tuple) en passant.

---

## Évolutions à mettre en place

### `src/linux_python_utils/scripts/installer.py`

#### Imports
`os`, `shutil`, `subprocess`, `Path` déjà présents. Ajouter `import pwd`
(stdlib) en tête de module.

#### Nouveau helper `_find_uv`
```python
def _find_uv(self) -> str | None:
    """Localise l'exécutable uv, PATH puis emplacements usuels.

    Cherche dans l'ordre :
    1. PATH courant (shutil.which).
    2. ~/.local/bin/uv et ~/.cargo/bin/uv de l'utilisateur courant.
    3. Mêmes chemins dans le home de $SUDO_USER (cas sudo/root).

    Returns:
        Chemin absolu vers uv, ou None si introuvable.
    """
    found = shutil.which("uv")
    if found:
        return found
    candidates: list[Path] = []
    for home in self._candidate_homes():
        candidates.append(home / ".local" / "bin" / "uv")
        candidates.append(home / ".cargo" / "bin" / "uv")
    for path in candidates:
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return None

@staticmethod
def _candidate_homes() -> list[Path]:
    """Homes à sonder pour trouver uv : courant + $SUDO_USER."""
    homes = [Path.home()]
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        try:
            homes.append(Path(pwd.getpwnam(sudo_user).pw_dir))
        except KeyError:
            pass
    return homes
```

#### Modification `_run_uv_install`
```python
uv_path = self._find_uv()
if uv_path is None:
    self._logger.log_error(
        "uv introuvable (ni dans le PATH, ni dans "
        "~/.local/bin ou ~/.cargo/bin). "
        "Installez-le (pip install uv) ou ajoutez-le au PATH."
    )
    return False

base = [
    "env", "UV_TOOL_BIN_DIR=/usr/local/bin",
    uv_path, "tool", "install",
    "--python", self._PYTHON_EXEC,
    "--editable", str(config.source_dir),
]
if config.deploy_type == "system":
    # sudo uniquement si on n'est pas déjà root
    cmd = (["sudo"] if os.geteuid() != 0 else []) + base
else:
    cmd = [
        uv_path, "tool", "install",
        "--editable", str(config.source_dir),
    ]
```
Le reste (`subprocess.run`, gestion returncode) inchangé.

#### Conventions
- [x] PEP 8 — lignes ≤ 79, snake_case
- [x] PEP 257 — docstrings Google Style
- [x] PEP 484 — `-> str | None`, `-> list[Path]`
- [x] PEP 20 — repli explicite, une responsabilité par méthode

---

## Checklist d'implémentation

### Code
- [ ] `import pwd` en tête de `installer.py`
- [ ] `_candidate_homes()` (staticmethod)
- [ ] `_find_uv()` (PATH + repli)
- [ ] `_run_uv_install` : utilise `_find_uv`, sudo conditionnel, message clair

### Tests (`tests/test_scripts.py`)
- [ ] `test_find_uv_prefere_le_path` — `shutil.which` renvoie un chemin → utilisé
- [ ] `test_find_uv_repli_local_bin` — which=None, faux uv dans un home → trouvé
- [ ] `test_find_uv_repli_sudo_user` — which=None, SUDO_USER pointant un home avec uv
- [ ] `test_find_uv_introuvable_retourne_none` — which=None, aucun candidat
- [ ] `test_system_sans_sudo_si_root` — patch `os.geteuid`→0 → "sudo" absent du cmd
- [ ] `test_system_avec_sudo_si_non_root` — patch `os.geteuid`→1000 → "sudo" présent
      (remplace/complète `test_system_type_uses_sudo_in_command`)
- [ ] Corriger les mocks `check_dependencies` 3→4-tuple dans les tests
      `TestLinuxCliInstaller` que je touche, pour qu'ils repassent au vert
- [ ] `pytest tests/test_scripts.py -q` : les tests installer au vert
      (les 3 `TestLinuxScriptCheckerDeps` restent rouges — hors scope, signalé)

### Documentation
- [ ] Docstrings des nouvelles méthodes (PEP 257)

---

## Points d'attention

- **`os.access(path, os.X_OK)` en root** : root a le bit exec si une
  permission d'exécution est posée ; `uv` en mode 0700 (owner) → OK pour
  root. Acceptable.
- **uv exécuté en root depuis le home d'un user** : `uv tool install`
  écrit dans les répertoires du process (root → `/root/.local/share/uv`),
  pas dans le home du user — comportement attendu (cohérent avec
  `UV_TOOL_BIN_DIR=/usr/local/bin`).
- **Ne pas élargir au bug `check_dependencies`** (3 vs 4-tuple) — bug
  distinct, à traiter séparément. Mentionner à l'utilisateur.
- **fedora_post_install** consomme cette lib en éditable : la correction
  est immédiatement effective sans réinstaller.

---

## ⏸ Validation requise

**Ce plan doit être validé explicitement avant toute modification du code source.**
Répondre **"OK"** pour démarrer l'implémentation.
