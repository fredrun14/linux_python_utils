# MODULE DEPLOY CLI — LINUX_PYTHON_UTILS
> **Date :** 2026-05-17 à 01:01
> **Complexité estimée :** Élevée

---

## Contexte

### Problématique
La bibliothèque `linux_python_utils` ne fournit pas de module pour déployer des
scripts Python CLI sur le système de fichiers en respectant le standard FHS (system
ou user scope). Il faut un module qui effectue les vérifications pré-installation
(pyproject.toml comme source de vérité), génère un wrapper bash si nécessaire
(avec confirmation), et utilise `uv tool install` pour l'installation finale.

### Solution technique retenue
Créer un nouveau module `deploy/` organisé en 5 fichiers selon le pattern du module
`scripts/` existant (config.py + installer.py → ici config.py + paths.py +
checker.py + wrapper.py + deployer.py). Dépendance optionnelle `platformdirs>=4.0`
ajoutée à `pyproject.toml` sous `[project.optional-dependencies.deploy]`. `uv` est
invoqué comme commande système via subprocess (pas de dépendance Python).

Alternatives écartées :
- Un seul fichier monolithique : violerait SRP et rendrait les tests difficiles.
- Utiliser `pipx` : `uv` est plus rapide et recommandé pour les nouveaux projets.
- stdlib `importlib.metadata` pour les chemins : `platformdirs` est plus fiable
  et portable pour les chemins FHS Linux.

### Fichiers impactés

**Nouveaux fichiers :**
- `src/linux_python_utils/deploy/__init__.py` — exports publics du module
- `src/linux_python_utils/deploy/config.py` — `DeployConfig`, `DependencyReport`
- `src/linux_python_utils/deploy/paths.py` — `DeployPaths` (résolution chemins FHS)
- `src/linux_python_utils/deploy/checker.py` — `DeployChecker` (ABC) + `LinuxCliDeployChecker`
- `src/linux_python_utils/deploy/wrapper.py` — `WrapperGenerator` (ABC) + `BashWrapperGenerator`
- `src/linux_python_utils/deploy/deployer.py` — `CliDeployer` (ABC) + `UvCliDeployer`
- `tests/deploy/__init__.py` — package tests
- `tests/deploy/test_config.py` — tests DeployConfig, DependencyReport
- `tests/deploy/test_paths.py` — tests DeployPaths
- `tests/deploy/test_checker.py` — tests LinuxCliDeployChecker
- `tests/deploy/test_wrapper.py` — tests BashWrapperGenerator
- `tests/deploy/test_deployer.py` — tests UvCliDeployer

**Fichiers modifiés :**
- `src/linux_python_utils/__init__.py` — ajout des imports et exports `deploy`
- `pyproject.toml` — ajout `[project.optional-dependencies.deploy]`

---

## Évolutions à mettre en place (Détail Junior)

### `pyproject.toml`

#### Modification
Ajouter la dépendance optionnelle `platformdirs` sous une clé `deploy` :

```toml
[project.optional-dependencies]
# ... existant ...
deploy = [
    "platformdirs>=4.0",
]
dev = [
    "pytest>=7.0",
    "pycodestyle>=2.10",
    "pydantic>=2.0",
    "python-dotenv>=1.0",
    "keyring>=24.0",
    "platformdirs>=4.0",
    "bandit",
    "safety",
]
```

---

### `src/linux_python_utils/deploy/config.py`

#### Imports
```python
# stdlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
```

#### Signatures

```python
@dataclass(frozen=True)
class DeployConfig:
    """Configuration pour le déploiement d'un script Python CLI.

    Attributes:
        name: Nom de l'application (utilisé pour les chemins FHS).
        deploy_type: Portée du déploiement ('system' ou 'user').
        source_dir: Répertoire source contenant pyproject.toml.
        venv_path: Chemin du venv (optionnel).
        check_extras: Groupes d'extras à vérifier (ex. ['dev', 'test']).
    """
    name: str
    deploy_type: Literal["system", "user"]
    source_dir: Path
    venv_path: Path | None = None
    check_extras: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Valide les champs après initialisation.

        Raises:
            ValueError: Si name est vide ou deploy_type invalide.
        """
```

```python
@dataclass
class DependencyReport:
    """Rapport de vérification des dépendances.

    Attributes:
        source: Chemin du pyproject.toml lu.
        missing: Liste des paquets manquants (nom + version requise).
        total: Nombre total de dépendances vérifiées.
        install_command: Commande pip suggérée pour installer les manquants.
    """
    source: Path
    missing: list[dict[str, str]]
    total: int
    install_command: str

    @property
    def is_satisfied(self) -> bool:
        """Retourne True si toutes les dépendances sont installées."""
```

#### Logique détaillée — `DeployConfig.__post_init__`
1. Vérifier que `name` n'est pas vide → `raise ValueError("name est requis")`
2. Vérifier que `deploy_type` est `"system"` ou `"user"` → `raise ValueError(...)`
3. Vérifier que `source_dir` est un `Path` (le frozen dataclass le garantit via type hint)

#### Logique détaillée — `DependencyReport.is_satisfied`
1. Retourner `len(self.missing) == 0`

#### Gestion d'erreurs
| Cas | Condition | Action |
|---|---|---|
| name vide | `not config.name` | `raise ValueError("name est requis")` |
| deploy_type invalide | pas dans `{"system", "user"}` | `raise ValueError(...)` |

#### Conventions PEP
- [x] PEP 8 — Imports ordonnés : stdlib → third-party → local
- [x] PEP 8 — Nommage : `snake_case`, `PascalCase` classes
- [x] PEP 8 — Lignes ≤ 79 caractères
- [x] PEP 257 — Docstrings françaises sur chaque classe/méthode
- [x] PEP 484 — Type hints complets, `Literal["system", "user"]`, `list[str]`
- [x] PEP 20 — Dataclasses simples, sans logique complexe

#### Principes SOLID
| Principe | Question clé | Statut |
|---|---|---|
| **S** Single Responsibility | `DeployConfig` ne stocke que la conf, `DependencyReport` que le rapport | [x] |
| **O** Open/Closed | Extensible par héritage sans modifier | [x] |
| **L** Liskov Substitution | Pas de sous-classes prévues (dataclasses) | [x] |
| **I** Interface Segregation | Classes minimales | [x] |
| **D** Dependency Inversion | Pas de dépendances externes dans les dataclasses | [x] |

---

### `src/linux_python_utils/deploy/paths.py`

#### Imports
```python
# stdlib
from pathlib import Path
from typing import Literal

# third-party
from platformdirs import user_data_dir, site_data_dir
```

#### Signature

```python
class DeployPaths:
    """Résout les chemins FHS pour le déploiement d'une application CLI.

    Calcule les chemins d'installation selon le type de déploiement
    (system ou user) en utilisant platformdirs pour la conformité FHS.

    Attributes:
        name: Nom de l'application.
        deploy_type: Portée du déploiement ('system' ou 'user').
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
        """Répertoire de données de l'application.

        Returns:
            /usr/local/share/{name} (system)
            ou ~/.local/share/{name} (user).
        """

    @property
    def bin_path(self) -> Path:
        """Chemin du wrapper binaire dans le PATH.

        Returns:
            /usr/local/bin/{name} (system)
            ou ~/.local/bin/{name} (user).
        """

    @property
    def venv_dir(self) -> Path:
        """Répertoire du venv dans data_dir.

        Returns:
            {data_dir}/venv/
        """

    @property
    def pyproject_path(self) -> Path:
        """Chemin du pyproject.toml dans data_dir.

        Returns:
            {data_dir}/pyproject.toml
        """

    @property
    def config_dir(self) -> Path:
        """Répertoire de configuration système.

        Returns:
            /etc/{name}/ (system) ou ~/.config/{name}/ (user).
        """
```

#### Logique détaillée

**`data_dir`** :
1. Si `deploy_type == "system"` → `Path(site_data_dir(self._name))`
2. Sinon → `Path(user_data_dir(self._name))`

**`bin_path`** :
1. Si `deploy_type == "system"` → `Path("/usr/local/bin") / self._name`
2. Sinon → `self.data_dir.parent.parent / "bin" / self._name`
   (c.-à-d. `~/.local/share/{name}` → parent = `~/.local/share` → parent = `~/.local` → `~/.local/bin/{name}`)

**`venv_dir`** :
1. `self.data_dir / "venv"`

**`pyproject_path`** :
1. `self.data_dir / "pyproject.toml"`

**`config_dir`** :
1. Si `deploy_type == "system"` → `Path("/etc") / self._name`
2. Sinon → `Path.home() / ".config" / self._name`

#### Gestion d'erreurs
Pas de logique d'erreur ici : `DeployPaths` est un résolveur de chemins pur, sans I/O.

#### Conventions PEP — identiques à config.py

#### Principes SOLID
| Principe | Question clé | Statut |
|---|---|---|
| **S** Single Responsibility | `DeployPaths` résout uniquement les chemins | [x] |
| **O** Open/Closed | Extensible sans modification | [x] |
| **L** Liskov Substitution | N/A (pas d'héritage) | [x] |
| **I** Interface Segregation | API minimale (5 propriétés) | [x] |
| **D** Dependency Inversion | `platformdirs` injecté implicitement (bibliothèque) | [x] |

---

### `src/linux_python_utils/deploy/checker.py`

#### Imports
```python
# stdlib
import subprocess
import sys
import tomllib
from abc import ABC, abstractmethod
from pathlib import Path

# local
from linux_python_utils.logging import Logger
from linux_python_utils.deploy.config import DeployConfig, DependencyReport
```

#### Signatures

```python
class DeployChecker(ABC):
    """Interface abstraite pour les vérifications pré-déploiement.

    Définit le contrat de vérification à effectuer avant d'installer
    un script Python CLI.
    """

    @abstractmethod
    def check_python(self, required_version: str | None = None) -> bool:
        """Vérifie que python3 est disponible et à la bonne version.

        Args:
            required_version: Version minimale requise (ex. '3.11').

        Returns:
            True si python3 est disponible et satisfait la version.
        """

    @abstractmethod
    def check_script(self, script_path: Path) -> bool:
        """Vérifie qu'un script Python existe et a une syntaxe valide.

        Args:
            script_path: Chemin du script à vérifier.

        Returns:
            True si le script existe et est syntaxiquement correct.
        """

    @abstractmethod
    def check_venv(self, venv_path: Path) -> bool:
        """Vérifie qu'un environnement virtuel est fonctionnel.

        Args:
            venv_path: Chemin du répertoire venv.

        Returns:
            True si le venv existe et son interpréteur est exécutable.
        """

    @abstractmethod
    def check_pyproject(self, pyproject_path: Path) -> dict[str, object]:
        """Lit et valide le pyproject.toml.

        Args:
            pyproject_path: Chemin du fichier pyproject.toml.

        Returns:
            Dictionnaire avec les données du projet (name, version,
            requires_python, dependencies, optional_dependencies).

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            ValueError: Si le format est invalide (section [project] manquante).
        """

    @abstractmethod
    def check_dependencies(
        self,
        config: DeployConfig,
        pyproject_data: dict[str, object],
    ) -> DependencyReport:
        """Vérifie les dépendances déclarées dans pyproject.toml.

        Args:
            config: Configuration de déploiement (pour venv_path et extras).
            pyproject_data: Données lues par check_pyproject().

        Returns:
            Rapport de dépendances (manquantes, total, commande).
        """
```

```python
class LinuxCliDeployChecker(DeployChecker):
    """Implémentation Linux des vérifications pré-déploiement.

    Vérifie python3, les scripts, le venv et les dépendances via
    subprocess et tomllib (Python 3.11+).

    Attributes:
        _logger: Instance de Logger pour la journalisation.
    """

    _PYTHON_EXEC: str = "/usr/bin/python3"

    def __init__(self, logger: Logger) -> None:
        """Initialise avec le logger.

        Args:
            logger: Instance de Logger pour la journalisation.
        """
        self._logger = logger
```

#### Logique détaillée — `LinuxCliDeployChecker`

**`check_python(required_version)`** :
1. Vérifier que `Path(self._PYTHON_EXEC).exists()` → si non, logger erreur + `return False`
2. Exécuter `subprocess.run([self._PYTHON_EXEC, "--version"], capture_output=True, text=True)`
3. Parser la version depuis stdout (ex. `"Python 3.11.2"` → `"3.11.2"`)
4. Si `required_version` fourni, comparer avec `tuple(map(int, ...))` → si insuffisant, `return False`
5. Logger info + `return True`

**`check_script(script_path)`** :
1. Si `not script_path.exists()` → logger erreur + `return False`
2. Si `not script_path.is_file()` → logger erreur + `return False`
3. Exécuter `subprocess.run([self._PYTHON_EXEC, "-m", "py_compile", str(script_path)], ...)`
4. Si `returncode != 0` → logger erreur avec stderr + `return False`
5. Logger info + `return True`

**`check_venv(venv_path)`** :
1. Si `not venv_path.exists()` → logger erreur + `return False`
2. `python_bin = venv_path / "bin" / "python"` → si non existant, `return False`
3. Exécuter `subprocess.run([str(python_bin), "--version"], capture_output=True)`
4. Si `returncode != 0` → `return False`
5. `return True`

**`check_pyproject(pyproject_path)`** :
1. Si `not pyproject_path.exists()` → `raise FileNotFoundError(...)`
2. Ouvrir en mode binaire et lire avec `tomllib.load(f)`
3. Si section `[project]` absente → `raise ValueError("Section [project] manquante")`
4. Extraire : `name`, `version`, `requires-python`, `dependencies`, `optional-dependencies`
5. Retourner dictionnaire structuré :
   ```python
   {
       "name": project.get("name", ""),
       "version": project.get("version", ""),
       "requires_python": project.get("requires-python"),
       "dependencies": project.get("dependencies", []),
       "optional_dependencies": project.get("optional-dependencies", {}),
   }
   ```

**`check_dependencies(config, pyproject_data)`** :
1. Récupérer `deps = list(pyproject_data.get("dependencies", []))` (copie)
2. Si `config.check_extras` → pour chaque extra, étendre `deps` avec `optional_dependencies[extra]`
3. Déterminer `pip_cmd` : si `config.venv_path` → `str(config.venv_path / "bin" / "pip")` sinon `"pip3"`
4. Pour chaque dépendance dans `deps` :
   - Extraire `package_name` (tout avant `>=`, `==`, `<`, `>`, `!=`, `~=`, `[`)
   - Extraire `version_constraint` (le reste, ou `""`)
   - Exécuter `subprocess.run([pip_cmd, "show", package_name], capture_output=True)`
   - Si `returncode != 0` → ajouter à `missing` : `{"package": package_name, "required": version_constraint, "reason": "non installé"}`
5. Construire `install_cmd` :
   - Si `config.venv_path` → `f"{pip_cmd} install -e '{config.source_dir}'"`
   - Sinon `f"pip3 install -e '{config.source_dir}'"`
6. Retourner `DependencyReport(source=pyproject_path, missing=missing, total=len(deps), install_command=install_cmd)`

**Fonction privée `_extract_package_name(dep: str) -> str`** :
1. Supprimer les extras `[...]` : `re.sub(r'\[.*?\]', '', dep)`
2. Couper sur le premier opérateur de version (`>=`, `==`, `<`, etc.) via `re.split(r'[>=<!~]', dep_clean, 1)[0]`
3. Retourner `.strip()`

#### Gestion d'erreurs
| Cas | Condition | Action |
|---|---|---|
| python3 absent | `Path(exec).exists()` est False | Logger erreur + return False |
| Script introuvable | `not script_path.exists()` | Logger erreur + return False |
| Syntaxe invalide | `py_compile returncode != 0` | Logger erreur avec stderr + return False |
| Venv absent | `not venv_path.exists()` | Logger erreur + return False |
| pyproject absent | `not pyproject_path.exists()` | `raise FileNotFoundError` |
| section [project] manquante | `"project" not in data` | `raise ValueError` |
| Exception inattendue | Exception générique | Logger + propager |

#### Conventions PEP — identiques

#### Principes SOLID
| Principe | Question clé | Statut |
|---|---|---|
| **S** Single Responsibility | `LinuxCliDeployChecker` ne fait que vérifier | [x] |
| **O** Open/Closed | Nouveau checker = nouvelle sous-classe | [x] |
| **L** Liskov Substitution | `LinuxCliDeployChecker` substituable à `DeployChecker` | [x] |
| **I** Interface Segregation | 5 méthodes ciblées, pas de méthodes inutiles | [x] |
| **D** Dependency Inversion | `Logger` injecté via `__init__` | [x] |

---

### `src/linux_python_utils/deploy/wrapper.py`

#### Imports
```python
# stdlib
import os
from abc import ABC, abstractmethod
from pathlib import Path

# local
from linux_python_utils.logging import Logger
```

#### Templates bash (constantes de module)

```python
_WRAPPER_SYSTEM = """\
#!/bin/bash
# Généré automatiquement par linux_python_utils
# Service system : {name}
# Source : /usr/local/share/{name}/pyproject.toml

APP_DIR="/usr/local/share/{name}"

if [ -f "${{APP_DIR}}/venv/bin/activate" ]; then
    source "${{APP_DIR}}/venv/bin/activate"
fi

export PATH="/usr/local/bin:/usr/bin:/bin"
export PYTHONUNBUFFERED="1"
export PYTHONPATH="${{APP_DIR}}/src:${{PYTHONPATH}}"

cd "${{APP_DIR}}" || exit 1
exec /usr/bin/python3 "${{APP_DIR}}/main.py" "$@"
"""

_WRAPPER_USER = """\
#!/bin/bash
# Généré automatiquement par linux_python_utils
# Service user : {name}

APP_DIR="${{HOME}}/.local/share/{name}"

if [ -f "${{APP_DIR}}/venv/bin/activate" ]; then
    source "${{APP_DIR}}/venv/bin/activate"
fi

export PATH="${{HOME}}/.local/bin:/usr/local/bin:/usr/bin:/bin"
export PYTHONUNBUFFERED="1"
export PYTHONPATH="${{APP_DIR}}/src:${{PYTHONPATH}}"

cd "${{APP_DIR}}" || exit 1
exec /usr/bin/python3 "${{APP_DIR}}/main.py" "$@"
"""
```

#### Signatures

```python
class WrapperGenerator(ABC):
    """Interface abstraite pour la génération de wrappers bash.

    Définit le contrat pour générer et installer un script wrapper
    activant le venv et configurant l'environnement d'exécution.
    """

    @abstractmethod
    def generate(
        self,
        name: str,
        deploy_type: str,
        with_venv: bool = True,
    ) -> str:
        """Génère le contenu du script wrapper bash.

        Args:
            name: Nom de l'application.
            deploy_type: 'system' ou 'user'.
            with_venv: Si True, inclut le bloc d'activation du venv.

        Returns:
            Contenu complet du script bash.
        """

    @abstractmethod
    def install(
        self,
        content: str,
        target_path: Path,
    ) -> Path:
        """Écrit le wrapper sur disque et le rend exécutable.

        Args:
            content: Contenu du script bash.
            target_path: Chemin de destination.

        Returns:
            Chemin où le wrapper a été installé.

        Raises:
            OSError: Si l'écriture ou chmod échoue.
        """
```

```python
class BashWrapperGenerator(WrapperGenerator):
    """Générateur de wrappers bash pour scripts Python CLI Linux.

    Génère et installe un script bash qui active le venv, configure
    PYTHONPATH et PYTHONUNBUFFERED, puis exécute le script Python.

    Attributes:
        _logger: Instance de Logger pour la journalisation.
    """

    def __init__(self, logger: Logger) -> None:
        """Initialise avec le logger.

        Args:
            logger: Instance de Logger pour la journalisation.
        """
        self._logger = logger
```

#### Logique détaillée — `BashWrapperGenerator`

**`generate(name, deploy_type, with_venv)`** :
1. Choisir le template selon `deploy_type` : `_WRAPPER_SYSTEM` ou `_WRAPPER_USER`
2. Appliquer `.format(name=name)` pour substituer `{name}`
3. Si `not with_venv` → supprimer le bloc `if [ -f ...activate ]...fi` via `_strip_venv_block()`
4. Retourner le contenu final

**`install(content, target_path)`** :
1. `target_path.parent.mkdir(parents=True, exist_ok=True)`
2. `target_path.write_text(content, encoding="utf-8")`
3. Rendre exécutable TOCTOU-safe :
   ```python
   fd = os.open(str(target_path), os.O_RDONLY | os.O_NOFOLLOW)
   try:
       os.fchmod(fd, 0o755)
   finally:
       os.close(fd)
   ```
4. Logger info + retourner `target_path`

**`_strip_venv_block(content: str) -> str`** (méthode privée statique) :
1. Parcourir les lignes
2. Dès qu'on trouve `if [ -f "` + `activate`, passer `skip=True`
3. Dès que `skip=True` et ligne = `fi`, passer `skip=False` et continuer
4. Ignorer les lignes pendant `skip=True`

#### Gestion d'erreurs
| Cas | Condition | Action |
|---|---|---|
| Erreur d'écriture | `target_path.write_text` lève `OSError` | Logger + propager |
| Erreur chmod | `os.fchmod` lève `OSError` | Logger + propager |

#### Conventions PEP — identiques

#### Principes SOLID
| Principe | Question clé | Statut |
|---|---|---|
| **S** Single Responsibility | Génération ET installation (couplage naturel) | [x] |
| **O** Open/Closed | Nouveau template = nouvelle sous-classe | [x] |
| **L** Liskov Substitution | `BashWrapperGenerator` substituable | [x] |
| **I** Interface Segregation | 2 méthodes publiques seulement | [x] |
| **D** Dependency Inversion | `Logger` injecté | [x] |

---

### `src/linux_python_utils/deploy/deployer.py`

#### Imports
```python
# stdlib
import subprocess
from abc import ABC, abstractmethod

# local
from linux_python_utils.logging import Logger
from linux_python_utils.deploy.config import DeployConfig
from linux_python_utils.deploy.paths import DeployPaths
from linux_python_utils.deploy.checker import DeployChecker
from linux_python_utils.deploy.wrapper import WrapperGenerator
```

#### Signatures

```python
class CliDeployer(ABC):
    """Interface abstraite pour le déploiement de scripts Python CLI.

    Définit le contrat pour déployer un script CLI : vérifications,
    génération du wrapper optionnelle, installation.
    """

    @abstractmethod
    def deploy(
        self,
        config: DeployConfig,
        confirm_wrapper: bool = True,
    ) -> bool:
        """Déploie un script Python CLI selon la configuration.

        Args:
            config: Configuration de déploiement.
            confirm_wrapper: Si True, demande confirmation avant wrapper.

        Returns:
            True si le déploiement a réussi, False sinon.
        """
```

```python
class UvCliDeployer(CliDeployer):
    """Déployeur de scripts Python CLI utilisant uv tool install.

    Orchestre les étapes :
    1. Vérifications pré-installation via DeployChecker.
    2. Génération du wrapper bash (avec confirmation si demandée).
    3. Installation via `uv tool install` (user) ou
       `sudo uv tool install --python /usr/bin/python3` (system).

    Attributes:
        _logger: Logger pour la journalisation.
        _checker: Implémentation de DeployChecker.
        _wrapper_gen: Générateur de wrapper bash.
    """

    def __init__(
        self,
        logger: Logger,
        checker: DeployChecker,
        wrapper_gen: WrapperGenerator,
    ) -> None:
        """Initialise le déployeur avec ses dépendances.

        Args:
            logger: Instance de Logger.
            checker: Implémentation de DeployChecker.
            wrapper_gen: Générateur de wrapper bash.
        """
        self._logger = logger
        self._checker = checker
        self._wrapper_gen = wrapper_gen
```

#### Logique détaillée — `UvCliDeployer.deploy`

```
Étape 1 : Construire les chemins
    paths = DeployPaths(config.name, config.deploy_type)

Étape 2 : Vérifier python3
    if not self._checker.check_python() → logger erreur + return False

Étape 3 : Lire et valider pyproject.toml (dans source_dir)
    pyproject_path = config.source_dir / "pyproject.toml"
    try:
        pyproject_data = self._checker.check_pyproject(pyproject_path)
    except (FileNotFoundError, ValueError) as e:
        logger erreur + return False

Étape 4 : Vérifier les dépendances
    report = self._checker.check_dependencies(config, pyproject_data)
    Si report.missing → logger warning avec liste des manquants
    (ne bloque pas : uv gère les dépendances)

Étape 5 : Vérifier le script principal (main.py dans source_dir)
    script_path = config.source_dir / "main.py"
    if not self._checker.check_script(script_path) → return False

Étape 6 : Vérifier le venv si spécifié
    if config.venv_path:
        if not self._checker.check_venv(config.venv_path) → logger warning

Étape 7 : Déterminer si wrapper nécessaire
    needs_wrapper = not (config.source_dir / "pyproject.toml").exists()
                    ou si pyproject_data n'a pas de [project.scripts]
    Si needs_wrapper et confirm_wrapper :
        Afficher message + demander input() → si réponse != "o"/"oui" → return False
    Si needs_wrapper :
        content = self._wrapper_gen.generate(
            config.name, config.deploy_type,
            with_venv=config.venv_path is not None
        )
        self._wrapper_gen.install(content, paths.bin_path)

Étape 8 : Installer via uv
    Si deploy_type == "system" :
        cmd = ["sudo", "uv", "tool", "install",
               "--python", "/usr/bin/python3",
               str(config.source_dir)]
    Sinon :
        cmd = ["uv", "tool", "install", str(config.source_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    Si returncode != 0 → logger erreur avec stderr + return False

Étape 9 : Succès
    logger info + return True
```

**Méthode privée `_needs_wrapper(pyproject_data: dict[str, object]) -> bool`** :
1. Vérifier si `pyproject_data` contient une clé `scripts` non vide
2. Si oui → pas besoin de wrapper (`return False`)
3. Si non → wrapper nécessaire (`return True`)

#### Gestion d'erreurs
| Cas | Condition | Action |
|---|---|---|
| python3 absent | `check_python()` → False | Logger erreur + return False |
| pyproject invalide | `FileNotFoundError`/`ValueError` | Logger erreur + return False |
| Script invalide | `check_script()` → False | return False |
| uv échec | `returncode != 0` | Logger erreur + return False |
| Refus wrapper | Input != "o"/"oui" | return False (sans erreur) |

#### Conventions PEP — identiques

#### Principes SOLID
| Principe | Question clé | Statut |
|---|---|---|
| **S** Single Responsibility | Orchestration uniquement | [x] |
| **O** Open/Closed | Nouveau déployeur = nouvelle sous-classe | [x] |
| **L** Liskov Substitution | `UvCliDeployer` substituable à `CliDeployer` | [x] |
| **I** Interface Segregation | 1 méthode publique `deploy()` | [x] |
| **D** Dependency Inversion | Logger, checker, wrapper_gen injectés | [x] |

---

### `src/linux_python_utils/deploy/__init__.py`

```python
"""Module de déploiement de scripts Python CLI pour systèmes Linux.

Gère le déploiement de scripts CLI en respectant le standard FHS
(system ou user scope), avec vérifications pré-installation via
pyproject.toml et génération optionnelle de wrappers bash.

Typical usage example:

    from linux_python_utils.deploy import (
        DeployConfig,
        DeployPaths,
        LinuxCliDeployChecker,
        BashWrapperGenerator,
        UvCliDeployer,
    )

    config = DeployConfig(
        name="mon-app",
        deploy_type="user",
        source_dir=Path("/home/user/mon-app"),
    )
    deployer = UvCliDeployer(logger, checker, wrapper_gen)
    deployer.deploy(config)
"""

from linux_python_utils.deploy.config import DeployConfig, DependencyReport
from linux_python_utils.deploy.paths import DeployPaths
from linux_python_utils.deploy.checker import (
    DeployChecker,
    LinuxCliDeployChecker,
)
from linux_python_utils.deploy.wrapper import (
    WrapperGenerator,
    BashWrapperGenerator,
)
from linux_python_utils.deploy.deployer import CliDeployer, UvCliDeployer

__all__ = [
    "DeployConfig",
    "DependencyReport",
    "DeployPaths",
    "DeployChecker",
    "LinuxCliDeployChecker",
    "WrapperGenerator",
    "BashWrapperGenerator",
    "CliDeployer",
    "UvCliDeployer",
]
```

---

### `src/linux_python_utils/__init__.py`

Ajouter après le bloc `scripts` :

```python
from linux_python_utils.deploy import (
    DeployConfig,
    DependencyReport,
    DeployPaths,
    DeployChecker,
    LinuxCliDeployChecker,
    WrapperGenerator,
    BashWrapperGenerator,
    CliDeployer,
    UvCliDeployer,
)
```

Et dans `__all__` :
```python
    # Deploy
    "DeployConfig",
    "DependencyReport",
    "DeployPaths",
    "DeployChecker",
    "LinuxCliDeployChecker",
    "WrapperGenerator",
    "BashWrapperGenerator",
    "CliDeployer",
    "UvCliDeployer",
```

---

## Checklist d'implémentation

### Code
- [ ] Créer `src/linux_python_utils/deploy/__init__.py`
- [ ] Créer `src/linux_python_utils/deploy/config.py` — DeployConfig, DependencyReport
- [ ] Créer `src/linux_python_utils/deploy/paths.py` — DeployPaths (platformdirs)
- [ ] Créer `src/linux_python_utils/deploy/checker.py` — DeployChecker + LinuxCliDeployChecker
- [ ] Créer `src/linux_python_utils/deploy/wrapper.py` — WrapperGenerator + BashWrapperGenerator
- [ ] Créer `src/linux_python_utils/deploy/deployer.py` — CliDeployer + UvCliDeployer
- [ ] Modifier `src/linux_python_utils/__init__.py` — imports + exports deploy

### Dépendances
- [ ] Modifier `pyproject.toml` — ajouter `deploy = ["platformdirs>=4.0"]`
- [ ] Ajouter `platformdirs>=4.0` dans `dev` extras
- [ ] Vérifier compatibilité licence platformdirs (MIT → compatible)
- [ ] `pip install -e ".[deploy,dev]"` dans le venv de développement

### Tests (pytest)
- [ ] Créer `tests/deploy/__init__.py`
- [ ] `tests/deploy/test_config.py`
  - [ ] `test_deploy_config_valid_user_type_creates_instance`
  - [ ] `test_deploy_config_valid_system_type_creates_instance`
  - [ ] `test_deploy_config_empty_name_raises_value_error`
  - [ ] `test_deploy_config_invalid_type_raises_value_error`
  - [ ] `test_dependency_report_is_satisfied_no_missing`
  - [ ] `test_dependency_report_is_satisfied_with_missing`
- [ ] `tests/deploy/test_paths.py`
  - [ ] `test_deploy_paths_user_data_dir_returns_local_share`
  - [ ] `test_deploy_paths_user_bin_path_returns_local_bin`
  - [ ] `test_deploy_paths_user_venv_dir`
  - [ ] `test_deploy_paths_user_pyproject_path`
  - [ ] `test_deploy_paths_user_config_dir`
  - [ ] `test_deploy_paths_system_data_dir_returns_usr_local_share`
  - [ ] `test_deploy_paths_system_bin_path_returns_usr_local_bin`
  - [ ] `test_deploy_paths_system_config_dir_returns_etc`
- [ ] `tests/deploy/test_checker.py`
  - [ ] `test_check_python_returns_true_when_available`
  - [ ] `test_check_python_returns_false_when_missing`
  - [ ] `test_check_python_returns_false_when_version_too_old`
  - [ ] `test_check_script_returns_true_for_valid_script`
  - [ ] `test_check_script_returns_false_when_not_found`
  - [ ] `test_check_script_returns_false_when_syntax_error`
  - [ ] `test_check_venv_returns_true_when_valid`
  - [ ] `test_check_venv_returns_false_when_missing`
  - [ ] `test_check_pyproject_returns_data_when_valid`
  - [ ] `test_check_pyproject_raises_file_not_found`
  - [ ] `test_check_pyproject_raises_value_error_missing_project`
  - [ ] `test_check_dependencies_all_installed`
  - [ ] `test_check_dependencies_with_missing_package`
  - [ ] `test_check_dependencies_with_extras`
- [ ] `tests/deploy/test_wrapper.py`
  - [ ] `test_generate_system_wrapper_contains_usr_local`
  - [ ] `test_generate_user_wrapper_contains_home_local`
  - [ ] `test_generate_without_venv_strips_activate_block`
  - [ ] `test_generate_with_venv_keeps_activate_block`
  - [ ] `test_install_writes_file_and_sets_permissions`
  - [ ] `test_install_creates_parent_directory`
- [ ] `tests/deploy/test_deployer.py`
  - [ ] `test_deploy_user_type_calls_uv_without_sudo`
  - [ ] `test_deploy_system_type_calls_uv_with_sudo`
  - [ ] `test_deploy_returns_false_when_python_check_fails`
  - [ ] `test_deploy_returns_false_when_pyproject_invalid`
  - [ ] `test_deploy_returns_false_when_script_check_fails`
  - [ ] `test_deploy_returns_false_when_uv_fails`
  - [ ] `test_deploy_generates_wrapper_when_no_scripts_entry`
  - [ ] `test_deploy_skips_wrapper_when_scripts_entry_exists`
- [ ] `pytest tests/deploy/ --cov=src/linux_python_utils/deploy --cov-report=term-missing --cov-fail-under=90`

### Documentation
- [ ] Docstrings PEP 257 françaises sur chaque module, classe, méthode publique
- [ ] Mettre à jour `CLAUDE.md` — ajouter `deploy` dans le tableau Architecture

---

## Points d'attention

1. **platformdirs sur GitHub CI** : `platformdirs` peut retourner des chemins
   différents selon l'OS/utilisateur (ex. snap paths sur Ubuntu). Les tests de
   `DeployPaths` doivent mocker `user_data_dir` et `site_data_dir`.

2. **uv disponible** : `uv` doit être installé sur la machine. Le module ne
   vérifie pas sa présence avant l'étape 8. Ajouter un `check_uv_available()`
   si nécessaire dans une prochaine itération.

3. **Confirmation interactive** : `input()` dans `UvCliDeployer` bloque les tests.
   Dans les tests, mocker `builtins.input` ou passer `confirm_wrapper=False`.

4. **TOCTOU-safe chmod** : suivre le pattern existant de `BashScriptInstaller`
   (`os.open(O_NOFOLLOW)` + `os.fchmod(fd, 0o755)`) dans `BashWrapperGenerator.install`.

5. **`sudo` pour system** : le module construit la commande avec `sudo` mais
   n'effectue pas de vérification de droits root avant. C'est intentionnel :
   `uv` gèrera l'échec si sudo n'est pas disponible.

6. **`_needs_wrapper` heuristique** : la détection "script trop complexe" est
   basée sur l'absence de `[project.scripts]` dans pyproject.toml. Suffisant
   pour la v1 ; une analyse AST pourrait raffiner en v2.

7. **Import platformdirs** : si `platformdirs` n'est pas installé, l'import
   de `deploy.paths` lève `ImportError`. Le module `deploy/__init__.py` peut
   laisser propager cette erreur (conforme aux dépendances optionnelles de la lib).

---

## ⏸ Validation requise

**Ce plan doit être validé explicitement avant toute modification du code source.**
Répondre **"OK"** pour démarrer l'implémentation.
