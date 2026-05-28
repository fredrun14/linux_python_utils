# XDG APP CONFIG + SYSTEM COMMAND VALIDATOR
> **Date :** 2026-05-21 à 10:20
> **Complexité estimée :** Faible

---

## Contexte

### Problématique
Deux fonctionnalités transversales sont dupliquées entre `fedora_post_install`
et `backup-py-manager` :
1. Gestion du répertoire XDG `~/.config/<app>/` : chaque projet le
   réimplémente à sa façon (pas encore dans `fedora_post_install`, déjà
   identifié comme besoin lors de la conception du `GlobalConfig`).
2. Vérification de la présence de commandes système : `backup-py-manager`
   possède son propre `SystemRequirementsValidator` qui réimplémente un
   pattern générique.

### Solution technique retenue
Ajouter deux modules dans `linux_python_utils` :
- `config/xdg.py` — `XdgAppConfig` : encapsule la convention XDG base dir
  (`~/.config/<app>/`) via `platformdirs` (déjà dépendance de la lib).
- `validation/system.py` — `SystemCommandValidator` : vérifie la présence
  de commandes système avec `shutil.which()`, lève `MissingDependencyError`
  (déjà dans `linux_python_utils.errors`).

Alternatives écartées :
- Utiliser `platformdirs` directement dans les projets consommateurs → casse
  l'isolation, expose une dépendance tierce non nécessaire à l'appelant.
- Ajouter une fonction standalone → une classe respecte mieux DIP (injectable
  dans les tests).

### Fichiers impactés
- `src/linux_python_utils/config/xdg.py` — **nouveau**
- `src/linux_python_utils/config/__init__.py` — exporter `XdgAppConfig`
- `src/linux_python_utils/validation/system.py` — **nouveau**
- `src/linux_python_utils/validation/__init__.py` — exporter `SystemCommandValidator`
- `src/linux_python_utils/__init__.py` — exporter les deux
- `tests/test_config_xdg.py` — **nouveau**
- `tests/test_validation_system.py` — **nouveau**

---

## Évolutions à mettre en place (Détail Junior)

---

### `src/linux_python_utils/config/xdg.py` (nouveau)

#### Imports
```python
# stdlib
from pathlib import Path

# third-party
from platformdirs import user_config_path
```

#### Classe `XdgAppConfig`
```python
class XdgAppConfig:
    """Gestion du répertoire de configuration XDG pour une application.

    Encapsule la convention XDG Base Directory Specification :
    le répertoire de configuration utilisateur par défaut est
    ``~/.config/<app_name>/`` sur Linux.

    Attributes:
        _app_name: Nom de l'application (slug kebab-case).

    Example:
        >>> cfg = XdgAppConfig("fedora-post-install")
        >>> cfg.config_dir
        PosixPath('/home/user/.config/fedora-post-install')
        >>> cfg.init_config_file("[log]\\nlevel = 'INFO'\\n")
        PosixPath('/home/user/.config/fedora-post-install/global.toml')
    """

    def __init__(self, app_name: str) -> None:
        """Initialise la configuration XDG pour l'application.

        Args:
            app_name: Nom de l'application en kebab-case
                (ex: 'fedora-post-install', 'backup-py-manager').
        """
        self._app_name = app_name
```

#### Propriété `config_dir`
```python
    @property
    def config_dir(self) -> Path:
        """Retourne le répertoire de configuration XDG de l'application.

        Returns:
            Chemin vers ~/.config/<app_name>/ (non créé).
        """
        return user_config_path(self._app_name)
```

#### Méthode `ensure_subdir`
```python
    def ensure_subdir(self, name: str) -> Path:
        """Crée un sous-répertoire dans le répertoire de config.

        Args:
            name: Nom du sous-répertoire (ex: 'configs', 'logs').

        Returns:
            Chemin absolu du sous-répertoire créé.
        """
        subdir = self.config_dir / name
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir
```

#### Méthode `init_config_file`
```python
    def init_config_file(
        self,
        template: str,
        filename: str = "global.toml",
        force: bool = False,
    ) -> Path:
        """Crée le fichier de configuration avec le template fourni.

        Crée le répertoire ~/.config/<app>/ si nécessaire, puis écrit
        le template dans filename. Lève FileExistsError si le fichier
        existe déjà et que force est False.

        Args:
            template: Contenu TOML (ou autre) à écrire dans le fichier.
            filename: Nom du fichier de configuration.
                Défaut: 'global.toml'.
            force: Si True, écrase le fichier existant sans erreur.

        Returns:
            Chemin absolu du fichier créé.

        Raises:
            FileExistsError: Si le fichier existe et force est False.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.config_dir / filename
        if config_file.exists() and not force:
            raise FileExistsError(
                f"Le fichier de configuration existe déjà : "
                f"{config_file}. "
                f"Utilisez force=True pour l'écraser."
            )
        config_file.write_text(template, encoding="utf-8")
        return config_file
```

#### Logique détaillée
1. `config_dir` — délègue à `user_config_path(self._app_name)` de `platformdirs` → retourne `~/.config/<app>/` sur Linux.
2. `ensure_subdir(name)` — `(self.config_dir / name).mkdir(parents=True, exist_ok=True)`, retourne le chemin.
3. `init_config_file(template, filename, force)` :
   - `self.config_dir.mkdir(parents=True, exist_ok=True)` — crée le parent
   - `config_file = self.config_dir / filename`
   - Si `config_file.exists()` et `not force` → `raise FileExistsError(...)`
   - `config_file.write_text(template, encoding="utf-8")`
   - `return config_file`

#### Gestion d'erreurs
| Cas | Condition | Action |
|---|---|---|
| Fichier déjà présent | `exists()` et `force=False` | `raise FileExistsError(chemin)` |
| Répertoire non créable | Permission refusée | `PermissionError` propagée nativement |

#### Conventions PEP
- [x] PEP 8  — Imports ordonnés : stdlib → third-party → local
- [x] PEP 8  — Nommage snake_case / PascalCase
- [x] PEP 8  — Lignes ≤ 79 caractères
- [x] PEP 257 — Docstrings Google Style
- [x] PEP 484 — Type hints complets
- [x] PEP 20  — Pas de complexité inutile

#### Principes SOLID
| Principe | Application |
|---|---|
| **S** SRP | `XdgAppConfig` gère uniquement la convention XDG |
| **O** OCP | Extension via sous-classe sans modifier `XdgAppConfig` |
| **D** DIP | `user_config_path` injecté indirectement via `platformdirs` (pas instancié en dur dans les méthodes) |

---

### `src/linux_python_utils/validation/system.py` (nouveau)

#### Imports
```python
# stdlib
import shutil

# local
from linux_python_utils.errors.exceptions import MissingDependencyError
from linux_python_utils.validation.base import Validator
```

#### Classe `SystemCommandValidator`
```python
class SystemCommandValidator(Validator):
    """Vérifie la présence de commandes système requises.

    Utilise shutil.which() pour tester la disponibilité de chaque
    commande dans le PATH courant. Lève MissingDependencyError avec
    les instructions d'installation si des commandes sont absentes.

    Attributes:
        _requirements: Dictionnaire commande → instruction d'installation.

    Example:
        >>> validator = SystemCommandValidator({
        ...     "borg": "sudo dnf install borgbackup",
        ...     "rsync": "sudo dnf install rsync",
        ... })
        >>> validator.validate()  # lève si borg ou rsync absent
    """

    def __init__(self, requirements: dict[str, str]) -> None:
        """Initialise le validateur avec les dépendances requises.

        Args:
            requirements: Dictionnaire {commande: instruction}.
                La commande est le nom de l'exécutable (ex: 'borg').
                L'instruction est le message d'aide à afficher
                (ex: 'sudo dnf install borgbackup').
        """
        self._requirements = requirements
```

#### Méthode `validate`
```python
    def validate(self) -> None:
        """Vérifie que toutes les commandes requises sont disponibles.

        Raises:
            MissingDependencyError: Si une ou plusieurs commandes
                sont introuvables dans le PATH.
        """
        missing = [
            cmd
            for cmd in self._requirements
            if shutil.which(cmd) is None
        ]
        if missing:
            lines = ["Commandes système manquantes :"]
            for cmd in missing:
                lines.append(f"  - {self._requirements[cmd]}")
            raise MissingDependencyError("\n".join(lines))
```

#### Méthode `missing_commands` (helper informatif)
```python
    def missing_commands(self) -> list[str]:
        """Retourne la liste des commandes absentes du PATH.

        Returns:
            Liste des noms de commandes non trouvées.
            Liste vide si toutes sont présentes.
        """
        return [
            cmd
            for cmd in self._requirements
            if shutil.which(cmd) is None
        ]
```

#### Logique détaillée `validate`
1. List comprehension sur `self._requirements` : `shutil.which(cmd) is None` → cmd absent.
2. Si liste vide → retour silencieux.
3. Si liste non vide → construire message multi-lignes avec `self._requirements[cmd]` pour chaque absent.
4. `raise MissingDependencyError(message)`.

#### Gestion d'erreurs
| Cas | Condition | Action |
|---|---|---|
| Commande absente | `shutil.which(cmd) is None` | `raise MissingDependencyError` avec liste |
| Toutes présentes | Toutes trouvées | Retour silencieux |

---

### `src/linux_python_utils/config/__init__.py` (modifier)

Ajouter l'import et l'entrée `__all__` :
```python
from linux_python_utils.config.xdg import XdgAppConfig

# Dans __all__
"XdgAppConfig",
```

---

### `src/linux_python_utils/validation/__init__.py` (modifier)

Ajouter :
```python
from linux_python_utils.validation.system import SystemCommandValidator

# Dans __all__
"SystemCommandValidator",
```

---

### `src/linux_python_utils/__init__.py` (modifier)

Ajouter dans les imports `config` et `validation` :
```python
from linux_python_utils.config import (
    ConfigManager,
    ConfigLoader,
    FileConfigLoader,
    ConfigurationManager,
    XdgAppConfig,          # ← nouveau
)

from linux_python_utils.validation import (
    Validator,
    PathChecker,
    PathCheckerPermission,
    PathCheckerWorldWritable,
    SystemCommandValidator,  # ← nouveau
)
```

Et dans `__all__` :
```python
"XdgAppConfig",
"SystemCommandValidator",
```

---

### `tests/test_config_xdg.py` (nouveau)

#### Imports
```python
# stdlib
from pathlib import Path

# third-party
import pytest
from pytest import MonkeyPatch

# local
from linux_python_utils.config.xdg import XdgAppConfig
```

#### Fixture
```python
@pytest.fixture
def xdg(tmp_path: Path, monkeypatch: MonkeyPatch) -> XdgAppConfig:
    """XdgAppConfig avec config_dir redirigé vers tmp_path."""
    # Monkey-patch user_config_path pour éviter d'écrire dans ~/.config
    monkeypatch.setattr(
        "linux_python_utils.config.xdg.user_config_path",
        lambda app: tmp_path / app,
    )
    return XdgAppConfig("test-app")
```

#### Tests
```python
class TestXdgAppConfig:
    def test_config_dir_contient_app_name(
        self, xdg: XdgAppConfig, tmp_path: Path
    ) -> None:
        """config_dir se termine par le nom de l'app."""

    def test_init_config_file_cree_fichier(
        self, xdg: XdgAppConfig
    ) -> None:
        """init_config_file crée le fichier avec le template."""

    def test_init_config_file_cree_repertoire_parent(
        self, xdg: XdgAppConfig
    ) -> None:
        """init_config_file crée ~/.config/<app>/ si absent."""

    def test_init_config_file_leve_file_exists_error(
        self, xdg: XdgAppConfig
    ) -> None:
        """Lève FileExistsError si fichier existe et force=False."""

    def test_init_config_file_force_ecrase(
        self, xdg: XdgAppConfig
    ) -> None:
        """force=True écrase le fichier sans erreur."""

    def test_init_config_file_nom_personnalise(
        self, xdg: XdgAppConfig
    ) -> None:
        """filename personnalisé crée le bon fichier."""

    def test_ensure_subdir_cree_repertoire(
        self, xdg: XdgAppConfig
    ) -> None:
        """ensure_subdir crée le sous-répertoire et retourne son chemin."""

    def test_ensure_subdir_idempotent(
        self, xdg: XdgAppConfig
    ) -> None:
        """Appels répétés sur le même nom n'échouent pas."""

    def test_contenu_fichier_egal_template(
        self, xdg: XdgAppConfig
    ) -> None:
        """Le contenu écrit correspond exactement au template."""
```

---

### `tests/test_validation_system.py` (nouveau)

#### Imports
```python
# stdlib
from unittest.mock import patch

# third-party
import pytest

# local
from linux_python_utils.errors.exceptions import MissingDependencyError
from linux_python_utils.validation.system import SystemCommandValidator
```

#### Tests
```python
class TestSystemCommandValidator:
    def test_validate_passe_si_toutes_presentes(self) -> None:
        """validate() silencieux si toutes les commandes existent."""
        # Arrange: patcher shutil.which pour retourner un chemin
        with patch("shutil.which", return_value="/usr/bin/cmd"):
            validator = SystemCommandValidator(
                {"cmd": "sudo dnf install cmd"}
            )
            validator.validate()  # ne lève pas

    def test_validate_leve_si_commande_absente(self) -> None:
        """Lève MissingDependencyError si commande absente."""
        with patch("shutil.which", return_value=None):
            validator = SystemCommandValidator(
                {"missing-cmd": "sudo dnf install missing-cmd"}
            )
            with pytest.raises(MissingDependencyError):
                validator.validate()

    def test_message_contient_instruction_installation(self) -> None:
        """Le message d'erreur inclut l'instruction d'installation."""
        with patch("shutil.which", return_value=None):
            validator = SystemCommandValidator(
                {"borg": "sudo dnf install borgbackup"}
            )
            with pytest.raises(MissingDependencyError) as exc_info:
                validator.validate()
            assert "borgbackup" in str(exc_info.value)

    def test_validate_partiel_liste_manquants_seulement(self) -> None:
        """Seules les commandes absentes apparaissent dans l'erreur."""
        def which_side_effect(cmd: str) -> str | None:
            return "/usr/bin/borg" if cmd == "borg" else None

        with patch("shutil.which", side_effect=which_side_effect):
            validator = SystemCommandValidator({
                "borg": "sudo dnf install borgbackup",
                "rsync": "sudo dnf install rsync",
            })
            with pytest.raises(MissingDependencyError) as exc_info:
                validator.validate()
            assert "rsync" in str(exc_info.value)
            assert "borgbackup" not in str(exc_info.value)

    def test_missing_commands_retourne_liste_vide_si_toutes_presentes(
        self,
    ) -> None:
        """missing_commands() retourne [] si toutes trouvées."""
        with patch("shutil.which", return_value="/usr/bin/x"):
            validator = SystemCommandValidator({"x": "install x"})
            assert validator.missing_commands() == []

    def test_missing_commands_retourne_commandes_absentes(
        self,
    ) -> None:
        """missing_commands() retourne les noms manquants."""
        with patch("shutil.which", return_value=None):
            validator = SystemCommandValidator({
                "a": "install a",
                "b": "install b",
            })
            missing = validator.missing_commands()
            assert sorted(missing) == ["a", "b"]

    def test_requirements_vide_ne_leve_pas(self) -> None:
        """validate() silencieux si requirements={} (rien à vérifier)."""
        validator = SystemCommandValidator({})
        validator.validate()
```

---

## Checklist d'implémentation

### Code
- [ ] Créer `src/linux_python_utils/config/xdg.py`
- [ ] Modifier `src/linux_python_utils/config/__init__.py` — exporter `XdgAppConfig`
- [ ] Créer `src/linux_python_utils/validation/system.py`
- [ ] Modifier `src/linux_python_utils/validation/__init__.py` — exporter `SystemCommandValidator`
- [ ] Modifier `src/linux_python_utils/__init__.py` — exporter les deux + `__all__`

### Tests
- [ ] Créer `tests/test_config_xdg.py` (9 tests)
- [ ] Créer `tests/test_validation_system.py` (7 tests)
- [ ] `pytest --cov=src/linux_python_utils --cov-report=term-missing`

### Documentation
- [ ] Docstrings PEP 257 sur tous les éléments créés

---

## Points d'attention

1. **`platformdirs` déjà en dépendance** dans `pyproject.toml` — aucun ajout nécessaire.
2. **`MissingDependencyError` déjà dans `linux_python_utils.errors`** — pas de nouvelle exception à créer.
3. **`user_config_path` vs `user_config_dir`** — `platformdirs.user_config_path()` retourne un `Path`, `user_config_dir()` retourne un `str`. Utiliser `user_config_path()` pour rester dans le monde `Path`.
4. **Tests XdgAppConfig** — toujours monkey-patcher `user_config_path` pour éviter d'écrire dans `~/.config` lors des tests.
5. **Tests SystemCommandValidator** — patcher `shutil.which` au niveau du module consommateur (`linux_python_utils.validation.system.shutil.which` ou via `patch("shutil.which")`).
6. **Version** — ne pas modifier la version de `linux_python_utils` (hors scope).

---

## ⏸ Validation requise

**Ce plan doit être validé explicitement avant toute modification du code source.**
Répondre **"OK"** pour démarrer l'implémentation.
