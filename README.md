# Linux Python Utils

Bibliothèque utilitaire Python pour systèmes Linux. Fournit des classes réutilisables pour le logging, la configuration, la gestion de fichiers, systemd et la vérification d'intégrité.

## Prérequis

- Python 3.11+ (utilise `tomllib`)
- Linux (pour les modules `systemd` et `filesystem`)

## Installation

### Installation locale (développement)

```bash
# Clone du dépôt
git clone /home/fred/PycharmProjects/linux_python_utils
cd linux_python_utils

# Installation en mode éditable
pip install -e .
```

### Installation via pip

```bash
# Depuis un dépôt local
pip install git+file:///home/fred/PycharmProjects/linux_python_utils

# Depuis GitHub (si publié)
pip install git+https://github.com/user/linux_python_utils.git
```

### Vérification de l'installation

```python
import linux_python_utils
print(linux_python_utils.__version__)  # 0.1.0
```

## Modules disponibles

| Module | Description |
|--------|-------------|
| `logging` | Système de logging avec fichier et console |
| `config` | Chargement de configuration TOML/JSON |
| `filesystem` | Opérations sur fichiers et sauvegardes |
| `systemd` | Gestion des services et timers systemd |
| `integrity` | Vérification d'intégrité par checksums |

---

## Module `logging`

Système de logging robuste avec support fichier et console.

### Classes

#### `Logger` (ABC)

Interface abstraite définissant les méthodes de logging.

```python
from abc import ABC, abstractmethod

class Logger(ABC):
    @abstractmethod
    def log_info(self, message: str) -> None: ...

    @abstractmethod
    def log_warning(self, message: str) -> None: ...

    @abstractmethod
    def log_error(self, message: str) -> None: ...
```

#### `FileLogger`

Implémentation concrète qui écrit dans un fichier avec option console.

**Caractéristiques :**
- Logger unique par instance (évite les conflits)
- Encodage UTF-8 explicite
- Flush immédiat après chaque log
- Pas de propagation (évite les doublons)
- Sortie console optionnelle

**Constructeur :**

```python
FileLogger(
    log_file: str,
    config: Optional[Dict[str, Any]] = None,
    console_output: bool = False
)
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `log_file` | `str` | Chemin du fichier de log |
| `config` | `dict` ou `ConfigurationManager` | Configuration optionnelle |
| `console_output` | `bool` | Activer la sortie console |

**Configuration supportée :**

```python
config = {
    "logging": {
        "level": "DEBUG",  # DEBUG, INFO, WARNING, ERROR
        "format": "%(asctime)s - %(levelname)s - %(message)s"
    }
}
```

**Exemple d'utilisation :**

```python
from linux_python_utils import FileLogger

# Usage simple
logger = FileLogger("/var/log/myapp.log")
logger.log_info("Application démarrée")
logger.log_warning("Attention: ressource limitée")
logger.log_error("Erreur critique")

# Avec console
logger = FileLogger("/var/log/myapp.log", console_output=True)

# Avec configuration
config = {"logging": {"level": "DEBUG"}}
logger = FileLogger("/var/log/myapp.log", config=config)

# Écriture directe sans formatage
logger.log_to_file("Message brut")
```

---

## Module `config`

Chargement et gestion de configuration TOML et JSON.

### Fonctions

#### `load_config`

Charge un fichier de configuration TOML ou JSON.

```python
load_config(config_path: Union[str, Path]) -> dict
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `config_path` | `str` ou `Path` | Chemin vers le fichier |

**Exemple :**

```python
from linux_python_utils import load_config

# Chargement TOML
config = load_config("/etc/myapp/config.toml")

# Chargement JSON
config = load_config("~/.config/myapp/config.json")

# Accès aux valeurs
print(config["section"]["key"])
```

### Classes

#### `ConfigurationManager`

Gestionnaire de configuration avancé avec fonctionnalités étendues.

**Fonctionnalités :**
- Support TOML et JSON (détection automatique)
- Recherche dans plusieurs emplacements
- Fusion profonde avec configuration par défaut
- Accès par chemin pointé (`"section.subsection.key"`)
- Gestion de profils

**Constructeur :**

```python
ConfigurationManager(
    config_path: Optional[Union[str, Path]] = None,
    default_config: Optional[Dict[str, Any]] = None,
    search_paths: Optional[List[Union[str, Path]]] = None
)
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `config_path` | `str` ou `Path` | Chemin vers le fichier de config |
| `default_config` | `dict` | Configuration par défaut |
| `search_paths` | `list` | Liste de chemins de recherche |

**Méthodes :**

| Méthode | Description |
|---------|-------------|
| `get(key_path, default)` | Récupère une valeur par chemin pointé |
| `get_section(section)` | Récupère une section complète |
| `get_profile(name)` | Récupère un profil avec chemins expandés |
| `list_profiles()` | Liste tous les profils disponibles |
| `create_default_config(path)` | Crée un fichier de config par défaut |

**Exemple :**

```python
from linux_python_utils import ConfigurationManager

# Configuration par défaut
DEFAULT_CONFIG = {
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(message)s"
    },
    "backup": {
        "destination": "/media/backup",
        "compression": True
    },
    "profiles": {
        "home": {
            "source": "~",
            "destination": "/media/backup/home"
        },
        "documents": {
            "source": "~/Documents",
            "destination": "/media/backup/docs"
        }
    }
}

# Chemins de recherche
SEARCH_PATHS = [
    "~/.config/myapp/config.toml",
    "~/.myapp.toml",
    "/etc/myapp/config.toml"
]

# Initialisation
config = ConfigurationManager(
    default_config=DEFAULT_CONFIG,
    search_paths=SEARCH_PATHS
)

# Accès par chemin pointé
level = config.get("logging.level", "INFO")
dest = config.get("backup.destination")

# Accès à une section
logging_config = config.get_section("logging")

# Gestion des profils
profiles = config.list_profiles()  # ["home", "documents"]
home_profile = config.get_profile("home")
# {"source": "/home/user", "destination": "/media/backup/home"}

# Création d'un fichier de config par défaut
config.create_default_config("~/.config/myapp/config.toml")
```

**Fichier TOML exemple :**

```toml
[logging]
level = "DEBUG"
format = "%(asctime)s - %(levelname)s - %(message)s"

[backup]
destination = "/media/nas/backup"
compression = true

[profiles.home]
source = "~"
destination = "/media/nas/backup/home"
description = "Sauvegarde du home"

[profiles.documents]
source = "~/Documents"
destination = "/media/nas/backup/docs"
```

---

## Module `filesystem`

Opérations sur les fichiers et sauvegardes.

### Classes

#### `FileManager` (ABC)

Interface abstraite pour la gestion des fichiers.

```python
class FileManager(ABC):
    @abstractmethod
    def create_file(self, file_path: str, content: str) -> bool: ...

    @abstractmethod
    def file_exists(self, file_path: str) -> bool: ...
```

#### `LinuxFileManager`

Implémentation Linux avec logging intégré.

**Constructeur :**

```python
LinuxFileManager(logger: Logger)
```

**Méthodes :**

| Méthode | Retour | Description |
|---------|--------|-------------|
| `create_file(path, content)` | `bool` | Crée un fichier |
| `file_exists(path)` | `bool` | Vérifie l'existence |
| `read_file(path)` | `str` | Lit le contenu |
| `delete_file(path)` | `bool` | Supprime le fichier |

**Exemple :**

```python
from linux_python_utils import FileLogger, LinuxFileManager

logger = FileLogger("/var/log/myapp.log")
fm = LinuxFileManager(logger)

# Créer un fichier
fm.create_file("/tmp/test.txt", "Contenu du fichier")

# Vérifier l'existence
if fm.file_exists("/tmp/test.txt"):
    content = fm.read_file("/tmp/test.txt")
    print(content)

# Supprimer
fm.delete_file("/tmp/test.txt")
```

#### `FileBackup` (ABC)

Interface abstraite pour les sauvegardes.

```python
class FileBackup(ABC):
    @abstractmethod
    def backup(self, file_path: str, backup_path: str) -> None: ...

    @abstractmethod
    def restore(self, file_path: str, backup_path: str) -> None: ...
```

#### `LinuxFileBackup`

Implémentation Linux utilisant `shutil.copy2` (préserve les métadonnées).

**Constructeur :**

```python
LinuxFileBackup(logger: Logger)
```

**Méthodes :**

| Méthode | Description |
|---------|-------------|
| `backup(file_path, backup_path)` | Crée une sauvegarde |
| `restore(file_path, backup_path)` | Restaure depuis la sauvegarde |

**Exemple :**

```python
from linux_python_utils import FileLogger, LinuxFileBackup

logger = FileLogger("/var/log/myapp.log")
backup = LinuxFileBackup(logger)

# Sauvegarder avant modification
backup.backup("/etc/myapp.conf", "/etc/myapp.conf.bak")

# ... modifications ...

# Restaurer en cas d'erreur
backup.restore("/etc/myapp.conf", "/etc/myapp.conf.bak")
```

---

## Module `systemd`

Gestion des services et timers systemd.

### Classes

#### `SystemdServiceManager` (ABC)

Interface abstraite pour systemd.

```python
class SystemdServiceManager(ABC):
    @abstractmethod
    def enable_timer(self, timer_name: str) -> bool: ...

    @abstractmethod
    def reload_systemd(self) -> bool: ...
```

#### `LinuxSystemdServiceManager`

Implémentation utilisant `systemctl`.

**Constructeur :**

```python
LinuxSystemdServiceManager(logger: Logger)
```

**Méthodes :**

| Méthode | Retour | Description |
|---------|--------|-------------|
| `enable_timer(name)` | `bool` | Active et démarre un timer |
| `disable_timer(name)` | `bool` | Désactive et arrête un timer |
| `reload_systemd()` | `bool` | Recharge systemd (daemon-reload) |
| `start_service(name)` | `bool` | Démarre un service |
| `stop_service(name)` | `bool` | Arrête un service |
| `get_status(name)` | `str` | Récupère le statut |
| `is_active(name)` | `bool` | Vérifie si actif |

**Exemple :**

```python
from linux_python_utils import FileLogger, LinuxSystemdServiceManager

logger = FileLogger("/var/log/myapp.log")
sm = LinuxSystemdServiceManager(logger)

# Recharger après modification des fichiers unit
sm.reload_systemd()

# Activer un timer
sm.enable_timer("flatpak-update.timer")

# Vérifier le statut
if sm.is_active("flatpak-update.timer"):
    print("Timer actif")

status = sm.get_status("flatpak-update.timer")
print(f"Statut: {status}")

# Gestion de services
sm.start_service("nginx.service")
sm.stop_service("nginx.service")
```

---

## Module `integrity`

Vérification d'intégrité par checksums.

### Fonctions

#### `calculate_checksum`

Calcule le checksum d'un fichier.

```python
calculate_checksum(
    file_path: Union[str, Path],
    algorithm: str = 'sha256'
) -> str
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` ou `Path` | Chemin du fichier |
| `algorithm` | `str` | Algorithme (sha256, sha512, md5, etc.) |

**Exemple :**

```python
from linux_python_utils import calculate_checksum

# SHA256 (défaut)
checksum = calculate_checksum("/path/to/file")
print(f"SHA256: {checksum}")

# MD5
checksum_md5 = calculate_checksum("/path/to/file", algorithm="md5")

# SHA512
checksum_512 = calculate_checksum("/path/to/file", algorithm="sha512")
```

### Classes

#### `IntegrityChecker` (ABC)

Interface abstraite pour la vérification d'intégrité.

```python
class IntegrityChecker(ABC):
    @abstractmethod
    def verify(self, source: str, destination: str) -> bool: ...
```

#### `SHA256IntegrityChecker`

Vérificateur basé sur SHA256 pour fichiers et répertoires.

**Constructeur :**

```python
SHA256IntegrityChecker(
    logger: Logger,
    algorithm: str = 'sha256'
)
```

**Méthodes :**

| Méthode | Retour | Description |
|---------|--------|-------------|
| `verify_file(source, dest)` | `bool` | Vérifie un fichier unique |
| `verify(source, dest, subdir)` | `bool` | Vérifie un répertoire complet |
| `get_checksum(path)` | `str` | Calcule et log le checksum |

**Exemple :**

```python
from linux_python_utils import FileLogger, SHA256IntegrityChecker

logger = FileLogger("/var/log/backup.log")
checker = SHA256IntegrityChecker(logger)

# Vérifier un fichier unique
if checker.verify_file("/source/file.txt", "/dest/file.txt"):
    print("Fichier identique")

# Vérifier un répertoire complet (après rsync par exemple)
if checker.verify("/home/user/Documents", "/media/backup"):
    print("Sauvegarde vérifiée")
else:
    print("Erreur d'intégrité!")

# Obtenir le checksum d'un fichier
checksum = checker.get_checksum("/path/to/file")
```

---

## Exemple complet

Script de sauvegarde utilisant tous les modules :

```python
#!/usr/bin/env python3
from linux_python_utils import (
    FileLogger,
    ConfigurationManager,
    LinuxFileManager,
    LinuxFileBackup,
    LinuxSystemdServiceManager,
    SHA256IntegrityChecker
)

# Configuration
DEFAULT_CONFIG = {
    "logging": {"level": "INFO"},
    "backup": {"destination": "/media/backup"},
    "profiles": {
        "documents": {
            "source": "~/Documents",
            "destination": "/media/backup/docs"
        }
    }
}

config = ConfigurationManager(
    config_path="~/.config/backup/config.toml",
    default_config=DEFAULT_CONFIG
)

# Initialisation des composants
logger = FileLogger(
    "/var/log/backup.log",
    config=config,
    console_output=True
)

file_manager = LinuxFileManager(logger)
file_backup = LinuxFileBackup(logger)
integrity_checker = SHA256IntegrityChecker(logger)

# Récupération du profil
profile = config.get_profile("documents")
source = profile["source"]
destination = profile["destination"]

logger.log_info(f"Sauvegarde de {source} vers {destination}")

# ... exécution de la sauvegarde ...

# Vérification d'intégrité
if integrity_checker.verify(source, destination):
    logger.log_info("Sauvegarde vérifiée avec succès")
else:
    logger.log_error("Échec de la vérification d'intégrité")
```

---

## Tests

```bash
# Installer les dépendances de dev
pip install -e ".[dev]"

# Lancer les tests
pytest tests/ -v

# Vérifier PEP8
pycodestyle linux_python_utils/
```

## Licence

MIT
