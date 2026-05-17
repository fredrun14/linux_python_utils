# EXTENSION MODULE SCRIPTS — CLI SYSTEM/USER AVEC RAPPORT
> **Date :** 2026-05-17 à 01:11
> **Complexité estimée :** Moyenne
> **Remplace :** TODO-20260517-0101-module-deploy-cli.md (approche abandonnée)

---

## Contexte

### Problématique
Le module `scripts/` existant est trop étroit : il installe uniquement des
scripts bash à un chemin explicite, sans notion de scope system/user, sans
vérification des dépendances Python, sans rapport d'installation. Il faut
l'étendre pour gérer le déploiement de scripts Python CLI en respectant le
standard FHS, avec pyproject.toml comme source de vérité et un rapport de
déploiement traçable.

### Solution technique retenue
Étendre le module `scripts/` existant **sans casser l'API actuelle**
(`BashScriptConfig`, `ScriptInstaller`, `BashScriptInstaller` restent intacts).
Quatre nouveaux fichiers complètent le module :

| Fichier | Rôle |
|---------|------|
| `config.py` (étendu) | Ajouter `PythonCliConfig` |
| `paths.py` (nouveau) | `ScriptPaths` — chemins FHS via platformdirs |
| `checker.py` (nouveau) | `ScriptChecker` (ABC) + `LinuxScriptChecker` |
| `report.py` (nouveau) | `MissingDependency` + `InstallReport` |
| `installer.py` (étendu) | Ajouter `CliInstaller` (ABC) + `LinuxCliInstaller` |

Alternative écartée : nouveau module `deploy/` — crée une duplication de
concept avec `scripts/`, frontières floues, deux endroits pour chercher la
même fonctionnalité.

### Fichiers impactés

**Fichiers modifiés :**
- `src/linux_python_utils/scripts/config.py` — ajout `PythonCliConfig`
- `src/linux_python_utils/scripts/installer.py` — ajout `CliInstaller` + `LinuxCliInstaller`
- `src/linux_python_utils/scripts/__init__.py` — exports mis à jour
- `src/linux_python_utils/__init__.py` — exports mis à jour
- `pyproject.toml` — ajout `platformdirs>=4.0` dans `deploy` et `dev`

**Fichiers nouveaux :**
- `src/linux_python_utils/scripts/paths.py`
- `src/linux_python_utils/scripts/checker.py`
- `src/linux_python_utils/scripts/report.py`
- `tests/scripts/test_python_cli_config.py`
- `tests/scripts/test_script_paths.py`
- `tests/scripts/test_script_checker.py`
- `tests/scripts/test_install_report.py`
- `tests/scripts/test_linux_cli_installer.py`

---

## Évolutions à mettre en place (Détail Junior)

### `pyproject.toml`

Ajouter `platformdirs` en dépendance optionnelle et dans `dev` :

```toml
[project.optional-dependencies]
validation = ["pydantic>=2.0"]
credentials = ["python-dotenv>=1.0", "keyring>=24.0"]
deploy = ["platformdirs>=4.0"]          # ← nouveau
dev = [
    "pytest>=7.0",
    "pycodestyle>=2.10",
    "pydantic>=2.0",
    "python-dotenv>=1.0",
    "keyring>=24.0",
    "platformdirs>=4.0",                # ← ajouté
    "bandit",
    "safety",
]
```

---

### `src/linux_python_utils/scripts/report.py` (nouveau)

#### Imports
```python
# stdlib
from dataclasses import dataclass, field
from pathlib import Path
```

#### Signatures

```python
@dataclass
class MissingDependency:
    """Représente une dépendance manquante lors de la vérification.

    Attributes:
        package: Nom du paquet manquant.
        required: Contrainte de version requise (ex. '>=2.0').
        reason: Raison de l'absence (ex. 'non installé').
    """
    package: str
    required: str
    reason: str = "non installé"
```

```python
@dataclass
class InstallReport:
    """Rapport de déploiement d'un script CLI.

    Conserve le résultat complet d'une installation : succès, chemin
    d'installation, dépendances vérifiées et commande de remédiation.

    Attributes:
        success: True si le déploiement s'est terminé sans erreur fatale.
        app_name: Nom de l'application déployée.
        deploy_type: Portée du déploiement ('system' ou 'user').
        install_path: Chemin du script/wrapper installé.
        missing_deps: Liste des dépendances manquantes.
        total_deps: Nombre total de dépendances vérifiées.
        install_command: Commande pip suggérée pour les manquants.
        warnings: Avertissements non bloquants.
    """
    success: bool
    app_name: str
    deploy_type: str
    install_path: Path
    missing_deps: list[MissingDependency] = field(default_factory=list)
    total_deps: int = 0
    install_command: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def deps_satisfied(self) -> bool:
        """Retourne True si toutes les dépendances sont installées."""

    def format_summary(self) -> str:
        """Retourne un résumé textuel lisible du rapport.

        Returns:
            Chaîne multiligne avec statut, dépendances et avertissements.
        """
```

#### Logique détaillée

**`deps_satisfied`** :
1. Retourner `len(self.missing_deps) == 0`

**`format_summary`** :
1. Ligne de statut : `"✓ Succès"` ou `"✗ Échec"` selon `self.success`
2. `f"  Application : {self.app_name} ({self.deploy_type})"`
3. `f"  Installé dans : {self.install_path}"`
4. Si `self.total_deps > 0` :
   - `f"  Dépendances : {self.total_deps - len(self.missing_deps)}/{self.total_deps} satisfaites"`
   - Pour chaque `dep` dans `self.missing_deps` : `f"    ✗ {dep.package} {dep.required}"`
   - Si `self.install_command` : `f"  Commande : {self.install_command}"`
5. Pour chaque warning : `f"  ⚠ {w}"`
6. Retourner la chaîne jointe avec `"\n"`

---

### `src/linux_python_utils/scripts/paths.py` (nouveau)

#### Imports
```python
# stdlib
from pathlib import Path
from typing import Literal

# third-party (optionnel)
from platformdirs import user_data_dir, site_data_dir
```

#### Signature

```python
class ScriptPaths:
    """Résout les chemins FHS pour un script CLI system ou user.

    Calcule les chemins d'installation selon le standard FHS en
    utilisant platformdirs pour la conformité Linux.

    | Type   | data_dir                      | bin_path               |
    |--------|-------------------------------|------------------------|
    | system | /usr/local/share/{name}/      | /usr/local/bin/{name}  |
    | user   | ~/.local/share/{name}/        | ~/.local/bin/{name}    |

    Attributes:
        name: Nom de l'application.
        deploy_type: Portée ('system' ou 'user').
    """

    def __init__(
        self,
        name: str,
        deploy_type: Literal["system", "user"],
    ) -> None:
        """Initialise avec le nom de l'app et la portée.

        Args:
            name: Nom de l'application.
            deploy_type: 'system' ou 'user'.
        """

    @property
    def data_dir(self) -> Path:
        """Répertoire de données principal de l'application.

        Returns:
            /usr/local/share/{name} (system)
            ~/.local/share/{name} (user).
        """

    @property
    def bin_path(self) -> Path:
        """Chemin du binaire/wrapper dans le PATH.

        Returns:
            /usr/local/bin/{name} (system)
            ~/.local/bin/{name} (user).
        """

    @property
    def venv_dir(self) -> Path:
        """Chemin du venv dans data_dir → {data_dir}/venv/."""

    @property
    def wrapper_path(self) -> Path:
        """Alias explicite de bin_path pour la clarté sémantique."""

    @property
    def config_dir(self) -> Path:
        """Répertoire de configuration.

        Returns:
            /etc/{name}/ (system) ou ~/.config/{name}/ (user).
        """
```

#### Logique détaillée

**`data_dir`** :
1. Si `system` → `Path(site_data_dir(self._name))`
   (`site_data_dir` retourne `/usr/local/share/{name}` sous Linux)
2. Sinon → `Path(user_data_dir(self._name))`
   (`user_data_dir` retourne `~/.local/share/{name}` sous Linux)

**`bin_path`** :
1. Si `system` → `Path("/usr/local/bin") / self._name`
2. Sinon → `self.data_dir.parent.parent / "bin" / self._name`
   (remonte de `~/.local/share/{name}` → `~/.local` → `~/.local/bin/{name}`)

**`venv_dir`** : `self.data_dir / "venv"`

**`wrapper_path`** : `self.bin_path`

**`config_dir`** :
1. Si `system` → `Path("/etc") / self._name`
2. Sinon → `Path.home() / ".config" / self._name`

---

### `src/linux_python_utils/scripts/checker.py` (nouveau)

#### Imports
```python
# stdlib
import re
import subprocess
import tomllib
from abc import ABC, abstractmethod
from pathlib import Path

# local
from linux_python_utils.logging import Logger
from linux_python_utils.scripts.report import InstallReport, MissingDependency
```

#### Signatures

```python
class ScriptChecker(ABC):
    """Interface abstraite pour les vérifications pré-déploiement.

    Définit le contrat à respecter avant d'installer un script CLI.
    """

    @abstractmethod
    def check_python(
        self, required_version: str | None = None
    ) -> bool:
        """Vérifie que python3 est disponible et suffisamment récent.

        Args:
            required_version: Version minimale requise (ex. '3.11').

        Returns:
            True si python3 satisfait la version requise.
        """

    @abstractmethod
    def check_script_syntax(self, script_path: Path) -> bool:
        """Vérifie l'existence et la syntaxe d'un script Python.

        Args:
            script_path: Chemin du script à analyser.

        Returns:
            True si le script existe et est syntaxiquement correct.
        """

    @abstractmethod
    def check_venv(self, venv_path: Path) -> bool:
        """Vérifie qu'un venv est fonctionnel.

        Args:
            venv_path: Chemin du répertoire de l'environnement virtuel.

        Returns:
            True si le venv existe et son interpréteur répond.
        """

    @abstractmethod
    def read_pyproject(self, pyproject_path: Path) -> dict[str, object]:
        """Lit et valide un fichier pyproject.toml (PEP 621).

        Args:
            pyproject_path: Chemin du fichier.

        Returns:
            Dictionnaire avec name, version, requires_python,
            dependencies, optional_dependencies, scripts.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            ValueError: Si la section [project] est absente.
        """

    @abstractmethod
    def check_dependencies(
        self,
        pyproject_path: Path,
        venv_path: Path | None,
        check_extras: list[str],
    ) -> tuple[list[MissingDependency], int, str]:
        """Vérifie les dépendances déclarées dans pyproject.toml.

        Args:
            pyproject_path: Chemin du pyproject.toml.
            venv_path: Chemin du venv (None → pip3 système).
            check_extras: Groupes d'extras à inclure dans la vérif.

        Returns:
            Tuple (missing_deps, total_count, install_command).
        """
```

```python
class LinuxScriptChecker(ScriptChecker):
    """Implémentation Linux des vérifications pré-déploiement.

    Utilise subprocess, tomllib (stdlib Python 3.11+) et des
    expressions régulières pour analyser les dépendances.

    Attributes:
        _logger: Logger pour la journalisation.
    """

    _PYTHON_EXEC: str = "/usr/bin/python3"

    def __init__(self, logger: Logger) -> None:
        """Initialise avec le logger.

        Args:
            logger: Instance de Logger pour la journalisation.
        """
        self._logger = logger
```

#### Logique détaillée — `LinuxScriptChecker`

**`check_python(required_version)`** :
1. `if not Path(self._PYTHON_EXEC).exists()` → logger erreur + `return False`
2. `result = subprocess.run([self._PYTHON_EXEC, "--version"], capture_output=True, text=True)`
3. Parser : `"Python 3.11.2"` → `(3, 11, 2)` via split et `map(int, ...)`
4. Si parsing échoue → logger warning + `return True` (python existe, version illisible)
5. Si `required_version` fourni → comparer tuples → si insuffisant, logger erreur + `return False`
6. Logger info + `return True`

**`check_script_syntax(script_path)`** :
1. `if not script_path.is_file()` → logger erreur + `return False`
2. `result = subprocess.run([self._PYTHON_EXEC, "-m", "py_compile", str(script_path)], capture_output=True, text=True)`
3. Si `returncode != 0` → logger erreur avec `result.stderr` + `return False`
4. Logger info + `return True`

**`check_venv(venv_path)`** :
1. `if not venv_path.is_dir()` → logger erreur + `return False`
2. `python_bin = venv_path / "bin" / "python"`
3. `if not python_bin.is_file()` → logger erreur + `return False`
4. `result = subprocess.run([str(python_bin), "--version"], capture_output=True)`
5. `return result.returncode == 0`

**`read_pyproject(pyproject_path)`** :
1. `if not pyproject_path.is_file()` → `raise FileNotFoundError(...)`
2. `with open(pyproject_path, "rb") as f: data = tomllib.load(f)`
3. `if "project" not in data` → `raise ValueError("Section [project] manquante")`
4. `project = data["project"]`
5. Retourner :
```python
{
    "name": project.get("name", ""),
    "version": project.get("version", ""),
    "requires_python": project.get("requires-python"),
    "dependencies": project.get("dependencies", []),
    "optional_dependencies": project.get("optional-dependencies", {}),
    "scripts": project.get("scripts", {}),
}
```

**`check_dependencies(pyproject_path, venv_path, check_extras)`** :
1. `pyproject_data = self.read_pyproject(pyproject_path)` (propage les exceptions)
2. `deps = list(pyproject_data["dependencies"])`
3. `opt = pyproject_data["optional_dependencies"]`
4. Pour chaque `extra` dans `check_extras` : si `extra in opt` → `deps.extend(opt[extra])`
5. Déterminer `pip_cmd` : si `venv_path` → `str(venv_path / "bin" / "pip")` sinon `"pip3"`
6. `missing: list[MissingDependency] = []`
7. Pour chaque `dep` dans `deps` :
   - `pkg = self._extract_package_name(dep)`
   - `constraint = self._extract_version_constraint(dep)`
   - `r = subprocess.run([pip_cmd, "show", pkg], capture_output=True)`
   - Si `r.returncode != 0` → `missing.append(MissingDependency(pkg, constraint))`
8. `install_cmd = f"{pip_cmd} install -e '{pyproject_path.parent}'"`
9. Retourner `(missing, len(deps), install_cmd)`

**`_extract_package_name(dep: str) -> str`** (méthode statique privée) :
1. Supprimer les extras : `re.sub(r'\[.*?\]', '', dep)`
2. Couper sur le premier opérateur : `re.split(r'[>=<!~\s]', dep_clean, 1)[0]`
3. Retourner `.strip()`

**`_extract_version_constraint(dep: str) -> str`** (méthode statique privée) :
1. Chercher `re.search(r'[>=<!~][^,\s]+', dep)`
2. Retourner `.group()` si trouvé, sinon `""`

#### Gestion d'erreurs
| Cas | Condition | Action |
|---|---|---|
| python3 absent | `not Path(exec).exists()` | Logger erreur + return False |
| Script introuvable | `not script_path.is_file()` | Logger erreur + return False |
| Syntaxe invalide | `py_compile returncode != 0` | Logger erreur + return False |
| Venv absent | `not venv_path.is_dir()` | Logger erreur + return False |
| pyproject absent | `not pyproject_path.is_file()` | `raise FileNotFoundError` |
| [project] absent | clé manquante | `raise ValueError` |

#### Principes SOLID
| Principe | Question clé | Statut |
|---|---|---|
| **S** Single Responsibility | `LinuxScriptChecker` ne vérifie que | [x] |
| **O** Open/Closed | Nouveau checker OS = nouvelle sous-classe | [x] |
| **L** Liskov Substitution | Substituable sans casser le code appelant | [x] |
| **I** Interface Segregation | 5 méthodes ciblées | [x] |
| **D** Dependency Inversion | `Logger` injecté | [x] |

---

### `src/linux_python_utils/scripts/config.py` (extension)

Ajouter après `BashScriptConfig` (ne pas toucher à l'existant) :

#### Imports à ajouter
```python
# stdlib (ajouter en tête)
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
```

#### Signature

```python
@dataclass(frozen=True)
class PythonCliConfig:
    """Configuration pour le déploiement d'un script Python CLI.

    Source de vérité pour le déploiement : l'installation respecte
    le standard FHS (system ou user scope) en s'appuyant sur
    pyproject.toml pour les dépendances et les points d'entrée.

    Attributes:
        name: Nom de l'application (utilisé pour les chemins FHS).
        deploy_type: Portée du déploiement ('system' ou 'user').
        source_dir: Répertoire contenant pyproject.toml et le code.
        venv_path: Chemin du venv (None → pas de venv géré).
        check_extras: Groupes d'extras à vérifier (ex. ['dev']).
        generate_wrapper: Si True, génère un wrapper bash si nécessaire.

    Example:
        >>> config = PythonCliConfig(
        ...     name="mon-app",
        ...     deploy_type="user",
        ...     source_dir=Path("/home/user/mon-app"),
        ... )
    """

    name: str
    deploy_type: Literal["system", "user"]
    source_dir: Path
    venv_path: Path | None = None
    check_extras: list[str] = field(default_factory=list)
    generate_wrapper: bool = True

    def __post_init__(self) -> None:
        """Valide les champs après initialisation.

        Raises:
            ValueError: Si name est vide ou deploy_type invalide.
        """
        if not self.name.strip():
            raise ValueError("name est requis et ne peut pas être vide")
        if self.deploy_type not in ("system", "user"):
            raise ValueError(
                f"deploy_type invalide : '{self.deploy_type}'. "
                "Valeurs acceptées : 'system', 'user'"
            )
```

---

### `src/linux_python_utils/scripts/installer.py` (extension)

Ajouter à la fin du fichier existant (ne pas modifier `ScriptInstaller` ni
`BashScriptInstaller`) :

#### Imports à ajouter (en haut du fichier)
```python
# stdlib (ajouter)
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

# local (ajouter)
from linux_python_utils.scripts.config import PythonCliConfig
from linux_python_utils.scripts.paths import ScriptPaths
from linux_python_utils.scripts.checker import ScriptChecker
from linux_python_utils.scripts.report import InstallReport, MissingDependency
```

Note : `ABC` et `abstractmethod` sont déjà importés — ne pas dupliquer.

#### Signatures

```python
class CliInstaller(ABC):
    """Interface abstraite pour l'installation de scripts CLI Python.

    Contrat de haut niveau : reçoit une PythonCliConfig, orchestre
    les vérifications, la génération du wrapper et l'installation,
    et retourne un InstallReport.
    """

    @abstractmethod
    def install(
        self,
        config: PythonCliConfig,
        confirm_wrapper: bool = True,
    ) -> InstallReport:
        """Installe un script Python CLI selon la configuration.

        Args:
            config: Configuration de déploiement.
            confirm_wrapper: Si True, demande confirmation avant
                de générer un wrapper bash.

        Returns:
            Rapport complet du déploiement.
        """
```

```python
class LinuxCliInstaller(CliInstaller):
    """Installateur de scripts Python CLI pour systèmes Linux.

    Orchestre dans l'ordre :
    1. Résolution des chemins FHS via ScriptPaths.
    2. Vérification python3, pyproject.toml, dépendances, venv.
    3. Génération d'un wrapper bash si aucun [project.scripts]
       n'est déclaré dans pyproject.toml (avec confirmation).
    4. Installation via `uv tool install` (user) ou
       `sudo uv tool install --python /usr/bin/python3` (system).
    5. Retour d'un InstallReport avec le résultat complet.

    Attributes:
        _logger: Logger pour la journalisation.
        _checker: Implémentation de ScriptChecker.
        _script_installer: BashScriptInstaller pour écrire le wrapper.
    """

    _PYTHON_EXEC: str = "/usr/bin/python3"

    def __init__(
        self,
        logger: Logger,
        checker: ScriptChecker,
        script_installer: ScriptInstaller,
    ) -> None:
        """Initialise avec les dépendances injectées.

        Args:
            logger: Instance de Logger.
            checker: Implémentation de ScriptChecker.
            script_installer: Installateur bas niveau (wrapper bash).
        """
        self._logger = logger
        self._checker = checker
        self._script_installer = script_installer
```

#### Logique détaillée — `LinuxCliInstaller.install`

```
paths = ScriptPaths(config.name, config.deploy_type)
warnings: list[str] = []

# Étape 1 : Vérifier python3
if not self._checker.check_python():
    return InstallReport(success=False, app_name=config.name,
                         deploy_type=config.deploy_type,
                         install_path=paths.bin_path)

# Étape 2 : Lire pyproject.toml
pyproject_path = config.source_dir / "pyproject.toml"
try:
    pyproject_data = self._checker.read_pyproject(pyproject_path)
except (FileNotFoundError, ValueError) as e:
    logger erreur
    return InstallReport(success=False, ..., warnings=[str(e)])

# Étape 3 : Vérifier les dépendances
missing, total, install_cmd = self._checker.check_dependencies(
    pyproject_path, config.venv_path, config.check_extras
)
if missing:
    warnings.append(f"{len(missing)}/{total} dépendances manquantes")

# Étape 4 : Vérifier le venv si fourni
if config.venv_path:
    if not self._checker.check_venv(config.venv_path):
        warnings.append(f"Venv inaccessible : {config.venv_path}")

# Étape 5 : Détecter si wrapper nécessaire
needs_wrapper = (
    config.generate_wrapper
    and not pyproject_data.get("scripts")
)

# Étape 6 : Générer le wrapper (avec confirmation si demandée)
if needs_wrapper:
    if confirm_wrapper:
        # Afficher le message et lire l'input
        print(
            f"\nAucun [project.scripts] détecté dans pyproject.toml.\n"
            f"Générer un wrapper bash → {paths.bin_path} ? [o/N] ",
            end="",
        )
        answer = input().strip().lower()
        if answer not in ("o", "oui", "y", "yes"):
            return InstallReport(
                success=False, ...,
                warnings=["Wrapper refusé par l'utilisateur"]
            )
    wrapper_content = self._generate_wrapper_content(config, paths)
    wrapper_config = BashScriptConfig(exec_command="")  # contenu brut
    # Écrire directement via paths.bin_path
    self._write_wrapper(wrapper_content, paths.bin_path)

# Étape 7 : Installer via uv
if not self._run_uv_install(config):
    return InstallReport(success=False, ...)

# Étape 8 : Succès
return InstallReport(
    success=True,
    app_name=config.name,
    deploy_type=config.deploy_type,
    install_path=paths.bin_path,
    missing_deps=missing,
    total_deps=total,
    install_command=install_cmd,
    warnings=warnings,
)
```

**`_generate_wrapper_content(config, paths) -> str`** (méthode privée) :
- Utiliser les templates bash définis comme constantes de module
  (`_WRAPPER_SYSTEM` et `_WRAPPER_USER`) — identiques à ceux du
  `wrapper_generator.py` de `systemd-service-manager`
- Appliquer `.format(name=config.name)`
- Si `config.venv_path is None` → supprimer le bloc `if [ -f ...activate ]...fi`

**`_write_wrapper(content, target_path) -> None`** (méthode privée) :
1. `target_path.parent.mkdir(parents=True, exist_ok=True)`
2. `target_path.write_text(content, encoding="utf-8")`
3. TOCTOU-safe chmod 0o755 :
   ```python
   fd = os.open(str(target_path), os.O_RDONLY | os.O_NOFOLLOW)
   try:
       os.fchmod(fd, 0o755)  # nosec B103
   finally:
       os.close(fd)
   ```

**`_run_uv_install(config) -> bool`** (méthode privée) :
1. Si `deploy_type == "system"` :
   `cmd = ["sudo", "uv", "tool", "install", "--python", self._PYTHON_EXEC, str(config.source_dir)]`
2. Sinon :
   `cmd = ["uv", "tool", "install", str(config.source_dir)]`
3. `result = subprocess.run(cmd, capture_output=True, text=True)`
4. Si `returncode != 0` → logger erreur avec `result.stderr` + `return False`
5. `return True`

#### Gestion d'erreurs
| Cas | Condition | Action |
|---|---|---|
| python3 absent | `check_python()` False | return InstallReport(success=False) |
| pyproject invalide | FileNotFoundError/ValueError | return InstallReport(success=False, warnings) |
| uv échec | returncode != 0 | logger erreur + return InstallReport(success=False) |
| Wrapper refusé | input != o/oui | return InstallReport(success=False, warnings) |
| Dépendances manquantes | missing non vide | warning non bloquant dans rapport |

#### Principes SOLID
| Principe | Question clé | Statut |
|---|---|---|
| **S** Single Responsibility | Orchestration uniquement | [x] |
| **O** Open/Closed | Nouveau OS/déployeur = nouvelle sous-classe | [x] |
| **L** Liskov Substitution | `LinuxCliInstaller` substituable à `CliInstaller` | [x] |
| **I** Interface Segregation | 1 méthode publique `install()` | [x] |
| **D** Dependency Inversion | logger, checker, script_installer injectés | [x] |

---

### `src/linux_python_utils/scripts/__init__.py` (mise à jour)

```python
"""
Module de génération et installation de scripts bash pour systèmes Linux.

Classes disponibles:
- BashScriptConfig: Configuration pour générer des scripts bash
  avec support optionnel des notifications.
- PythonCliConfig: Configuration pour déployer un script Python CLI
  (system ou user scope, avec vérification des dépendances).
- ScriptInstaller: Interface abstraite pour l'installation de scripts.
- BashScriptInstaller: Implémentation pour installer des scripts bash.
- ScriptPaths: Résolution des chemins FHS via platformdirs.
- ScriptChecker: Interface abstraite pour les vérifications pré-install.
- LinuxScriptChecker: Vérification python3, pyproject.toml, dépendances.
- InstallReport: Rapport complet du déploiement.
- MissingDependency: Dépendance manquante dans le rapport.
- CliInstaller: Interface abstraite pour l'installation de scripts CLI.
- LinuxCliInstaller: Installateur CLI Linux (uv + wrapper bash).
"""

from linux_python_utils.scripts.config import BashScriptConfig, PythonCliConfig
from linux_python_utils.scripts.installer import (
    ScriptInstaller,
    BashScriptInstaller,
    CliInstaller,
    LinuxCliInstaller,
)
from linux_python_utils.scripts.paths import ScriptPaths
from linux_python_utils.scripts.checker import ScriptChecker, LinuxScriptChecker
from linux_python_utils.scripts.report import InstallReport, MissingDependency

__all__ = [
    "BashScriptConfig",
    "PythonCliConfig",
    "ScriptInstaller",
    "BashScriptInstaller",
    "CliInstaller",
    "LinuxCliInstaller",
    "ScriptPaths",
    "ScriptChecker",
    "LinuxScriptChecker",
    "InstallReport",
    "MissingDependency",
]
```

### `src/linux_python_utils/__init__.py` (mise à jour)

Remplacer le bloc `scripts` existant :

```python
from linux_python_utils.scripts import (
    BashScriptConfig,
    PythonCliConfig,         # ← nouveau
    ScriptInstaller,
    BashScriptInstaller,
    CliInstaller,            # ← nouveau
    LinuxCliInstaller,       # ← nouveau
    ScriptPaths,             # ← nouveau
    ScriptChecker,           # ← nouveau
    LinuxScriptChecker,      # ← nouveau
    InstallReport,           # ← nouveau
    MissingDependency,       # ← nouveau
)
```

Et dans `__all__` ajouter après `"BashScriptInstaller"` :
```python
    "PythonCliConfig",
    "CliInstaller",
    "LinuxCliInstaller",
    "ScriptPaths",
    "ScriptChecker",
    "LinuxScriptChecker",
    "InstallReport",
    "MissingDependency",
```

---

## Checklist d'implémentation

### Code
- [ ] Créer `src/linux_python_utils/scripts/report.py`
  — `MissingDependency`, `InstallReport`, `InstallReport.format_summary()`
- [ ] Créer `src/linux_python_utils/scripts/paths.py`
  — `ScriptPaths` avec 5 propriétés (platformdirs)
- [ ] Créer `src/linux_python_utils/scripts/checker.py`
  — `ScriptChecker` (ABC) + `LinuxScriptChecker`
- [ ] Étendre `src/linux_python_utils/scripts/config.py`
  — ajouter `PythonCliConfig` après `BashScriptConfig`
- [ ] Étendre `src/linux_python_utils/scripts/installer.py`
  — ajouter `CliInstaller` (ABC) + `LinuxCliInstaller`
- [ ] Mettre à jour `src/linux_python_utils/scripts/__init__.py`
- [ ] Mettre à jour `src/linux_python_utils/__init__.py`

### Dépendances
- [ ] Modifier `pyproject.toml` — ajouter `deploy = ["platformdirs>=4.0"]` et dans `dev`
- [ ] `pip install -e ".[deploy,dev]"` pour le dev local
- [ ] Vérifier licence platformdirs (MIT — compatible)

### Tests (pytest)
- [ ] Créer `tests/scripts/test_python_cli_config.py`
  - [ ] `test_python_cli_config_valid_user_creates_instance`
  - [ ] `test_python_cli_config_valid_system_creates_instance`
  - [ ] `test_python_cli_config_empty_name_raises_value_error`
  - [ ] `test_python_cli_config_invalid_type_raises_value_error`
  - [ ] `test_python_cli_config_defaults_are_correct`
- [ ] Créer `tests/scripts/test_install_report.py`
  - [ ] `test_deps_satisfied_returns_true_when_no_missing`
  - [ ] `test_deps_satisfied_returns_false_when_missing`
  - [ ] `test_format_summary_success_contains_app_name`
  - [ ] `test_format_summary_failure_shows_missing_deps`
  - [ ] `test_format_summary_includes_install_command`
- [ ] Créer `tests/scripts/test_script_paths.py`
  - [ ] `test_user_data_dir_returns_local_share` (mock user_data_dir)
  - [ ] `test_user_bin_path_returns_local_bin`
  - [ ] `test_user_venv_dir_inside_data_dir`
  - [ ] `test_user_config_dir_returns_dot_config`
  - [ ] `test_system_data_dir_returns_usr_local_share` (mock site_data_dir)
  - [ ] `test_system_bin_path_returns_usr_local_bin`
  - [ ] `test_system_config_dir_returns_etc`
- [ ] Créer `tests/scripts/test_script_checker.py`
  - [ ] `test_check_python_returns_true_when_available` (mock subprocess)
  - [ ] `test_check_python_returns_false_when_exec_missing` (mock Path.exists)
  - [ ] `test_check_python_returns_false_when_version_too_old`
  - [ ] `test_check_script_syntax_returns_true_for_valid_script`
  - [ ] `test_check_script_syntax_returns_false_when_not_found`
  - [ ] `test_check_script_syntax_returns_false_when_syntax_error`
  - [ ] `test_check_venv_returns_true_when_valid`
  - [ ] `test_check_venv_returns_false_when_missing`
  - [ ] `test_read_pyproject_returns_dict_when_valid` (tmp_path)
  - [ ] `test_read_pyproject_raises_file_not_found`
  - [ ] `test_read_pyproject_raises_value_error_missing_project`
  - [ ] `test_check_dependencies_all_installed` (mock subprocess)
  - [ ] `test_check_dependencies_with_missing_package`
  - [ ] `test_check_dependencies_with_extras`
- [ ] Créer `tests/scripts/test_linux_cli_installer.py`
  - [ ] `test_install_user_returns_success_report` (mocks complets)
  - [ ] `test_install_returns_failure_when_python_check_fails`
  - [ ] `test_install_returns_failure_when_pyproject_invalid`
  - [ ] `test_install_generates_wrapper_when_no_scripts_entry`
  - [ ] `test_install_skips_wrapper_when_scripts_entry_exists`
  - [ ] `test_install_returns_failure_when_uv_fails`
  - [ ] `test_install_system_type_uses_sudo`
  - [ ] `test_install_confirm_wrapper_false_skips_input`
  - [ ] `test_install_missing_deps_in_report_as_warning_not_failure`
- [ ] `pytest tests/scripts/ --cov=src/linux_python_utils/scripts --cov-report=term-missing --cov-fail-under=90`

### Documentation
- [ ] Docstrings PEP 257 françaises sur tous les éléments publics nouveaux
- [ ] Mettre à jour `CLAUDE.md` — ajouter `scripts` étendu dans le tableau Architecture

---

## Points d'attention

1. **Rétrocompatibilité** : `BashScriptConfig`, `ScriptInstaller`, `BashScriptInstaller`
   ne sont pas modifiés. Les imports existants dans `__init__.py` continuent de
   fonctionner sans changement.

2. **platformdirs sur CI** : `user_data_dir()` peut retourner des chemins
   différents selon l'environnement (snap, container). Toujours mocker dans
   les tests de `ScriptPaths`.

3. **`input()` bloque les tests** : dans `LinuxCliInstaller.install`, le `input()`
   pour confirmation doit être mocké via `mocker.patch("builtins.input")`.
   Passer `confirm_wrapper=False` dans les tests pour éviter le bloc.

4. **`uv` absent** : si `uv` n'est pas installé, `subprocess.run(["uv", ...])` lève
   `FileNotFoundError`. Catcher l'exception dans `_run_uv_install` → logger erreur
   + return False.

5. **TOCTOU-safe chmod** : utiliser `os.open(O_NOFOLLOW)` + `os.fchmod(fd, 0o755)`
   dans `_write_wrapper`, cohérent avec `BashScriptInstaller._set_executable`.

6. **`nosec B103`** : annoter le `os.chmod`/`os.fchmod(0o755)` avec `# nosec B103`
   (intentionnel pour rendre le wrapper exécutable).

7. **Wrapper vs `[project.scripts]`** : la heuristique "wrapper nécessaire si
   aucun `[project.scripts]`" est volontairement simple pour la v1. Un script
   déclarant `[project.scripts]` sera déployé directement par `uv` sans wrapper.

---

## ⏸ Validation requise

**Ce plan doit être validé explicitement avant toute modification du code source.**
Répondre **"OK"** pour démarrer l'implémentation.
