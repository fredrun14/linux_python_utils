# 🐧 Linux Python Utils

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-60%20passed-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP8-black.svg)]()
[![SOLID](https://img.shields.io/badge/Architecture-SOLID-purple.svg)]()

> Bibliothèque utilitaire Python pour systèmes Linux, conçue avec les principes SOLID.

Fournit des classes réutilisables et extensibles pour le logging, la configuration, la gestion de fichiers, les services systemd et la vérification d'intégrité. Architecture basée sur des Abstract Base Classes (ABC) permettant l'injection de dépendances et facilitant les tests unitaires.

## 📋 Table des Matières

- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
  - [Module logging](#module-logging)
  - [Module config](#module-config)
  - [Module filesystem](#module-filesystem)
  - [Module systemd](#module-systemd)
  - [Module integrity](#module-integrity)
- [Documentation API](#-documentation-api)
- [Architecture des Classes](#-architecture-des-classes)
- [Structure du Projet](#-structure-du-projet)
- [Tests](#-tests)
- [Troubleshooting](#-troubleshooting)
- [Contribution](#-contribution)
- [Licence](#-licence)

## ✨ Fonctionnalités

- **📝 Logging robuste** — Logger fichier/console avec encodage UTF-8 et flush immédiat
- **⚙️ Configuration flexible** — Support TOML/JSON avec fusion profonde et profils
- **📁 Gestion de fichiers** — CRUD fichiers et sauvegardes préservant les métadonnées
- **🔧 Systemd complet** — Gestion services, timers et unités de montage (.mount/.automount)
- **🔐 Vérification d'intégrité** — Checksums SHA256/SHA512/MD5 pour fichiers et répertoires
- **🏗️ Architecture SOLID** — ABCs, injection de dépendances, testabilité maximale
- **🧪 Bien testé** — 60 tests unitaires couvrant tous les modules

## 📦 Prérequis

| Prérequis | Version | Vérification |
|-----------|---------|--------------|
| Python | 3.11+ | `python --version` |
| pip | 21.0+ | `pip --version` |
| Linux | Kernel 4.0+ | `uname -r` |

> **Note** : Python 3.11+ est requis car la bibliothèque utilise `tomllib` (stdlib).

## 🔧 Installation

### Installation depuis les Sources

```bash
# 1. Cloner le repository
git clone https://github.com/user/linux-python-utils.git
cd linux-python-utils

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate

# 3. Installer en mode développement
pip install -e .

# 4. (Optionnel) Installer les dépendances de dev
pip install -e ".[dev]"
```

### Installation via pip

```bash
# Depuis GitHub
pip install git+https://github.com/user/linux-python-utils.git
```

### Vérification de l'Installation

```python
import linux_python_utils
print(linux_python_utils.__version__)  # 0.1.0
```

## 💻 Utilisation

### Module `logging`

Système de logging robuste avec support fichier et console.

```python
from linux_python_utils import FileLogger

# Usage simple
logger = FileLogger("/var/log/myapp.log")
logger.log_info("Application démarrée")
logger.log_warning("Attention: ressource limitée")
logger.log_error("Erreur critique")

# Avec sortie console
logger = FileLogger("/var/log/myapp.log", console_output=True)

# Avec configuration
config = {"logging": {"level": "DEBUG"}}
logger = FileLogger("/var/log/myapp.log", config=config)
```

### Module `config`

Chargement et gestion de configuration TOML et JSON.

#### Fonction `load_config`

```python
from linux_python_utils import load_config

# Chargement TOML ou JSON (détection automatique)
config = load_config("/etc/myapp/config.toml")
print(config["section"]["key"])
```

#### Classe `ConfigurationManager`

```python
from linux_python_utils import ConfigurationManager

# Configuration par défaut avec profils
DEFAULT_CONFIG = {
    "logging": {"level": "INFO"},
    "backup": {"destination": "/media/backup"},
    "profiles": {
        "home": {"source": "~", "destination": "/media/backup/home"},
        "documents": {"source": "~/Documents", "destination": "/media/backup/docs"}
    }
}

# Chemins de recherche automatique
SEARCH_PATHS = [
    "~/.config/myapp/config.toml",
    "/etc/myapp/config.toml"
]

config = ConfigurationManager(
    default_config=DEFAULT_CONFIG,
    search_paths=SEARCH_PATHS
)

# Accès par chemin pointé
level = config.get("logging.level", "INFO")
dest = config.get("backup.destination")

# Gestion des profils
profiles = config.list_profiles()  # ["home", "documents"]
home_profile = config.get_profile("home")
# {"source": "/home/user", "destination": "/media/backup/home"}
```

**Fichier TOML exemple :**

```toml
[logging]
level = "DEBUG"

[backup]
destination = "/media/nas/backup"

[profiles.home]
source = "~"
destination = "/media/nas/backup/home"
```

### Module `filesystem`

Opérations sur les fichiers et sauvegardes.

```python
from linux_python_utils import FileLogger, LinuxFileManager, LinuxFileBackup

logger = FileLogger("/var/log/myapp.log")

# Gestion de fichiers
fm = LinuxFileManager(logger)
fm.create_file("/tmp/test.txt", "Contenu du fichier")

if fm.file_exists("/tmp/test.txt"):
    content = fm.read_file("/tmp/test.txt")
    print(content)

fm.delete_file("/tmp/test.txt")

# Sauvegarde avec préservation des métadonnées
backup = LinuxFileBackup(logger)
backup.backup("/etc/myapp.conf", "/etc/myapp.conf.bak")
# ... modifications ...
backup.restore("/etc/myapp.conf", "/etc/myapp.conf.bak")
```

### Module `systemd`

Gestion des services, timers et unités de montage systemd.

#### Services et Timers

```python
from linux_python_utils import FileLogger, LinuxSystemdServiceManager

logger = FileLogger("/var/log/myapp.log")
sm = LinuxSystemdServiceManager(logger)

# Recharger après modification des fichiers unit
sm.reload_systemd()

# Gestion des timers
sm.enable_timer("backup.timer")
if sm.is_active("backup.timer"):
    print("Timer actif")

# Gestion des services
sm.start_service("nginx.service")
status = sm.get_status("nginx.service")
sm.stop_service("nginx.service")
```

#### Unités de Montage (.mount / .automount)

```python
from linux_python_utils import (
    FileLogger,
    LinuxSystemdServiceManager,
    LinuxMountUnitManager,
    MountConfig
)

logger = FileLogger("/var/log/mount.log")
systemd = LinuxSystemdServiceManager(logger)
mount_mgr = LinuxMountUnitManager(logger, systemd)

# Configuration du montage NFS
config = MountConfig(
    description="NAS Backup",
    what="192.168.1.10:/share",
    where="/media/nas/backup",
    type="nfs",
    options="defaults,soft,timeo=10"
)

# Installer avec automount (montage à la demande)
mount_mgr.install_mount_unit(config, with_automount=True, automount_timeout=60)

# Activer le montage
mount_mgr.enable_mount("/media/nas/backup", with_automount=True)

# Vérifier le statut
if mount_mgr.is_mounted("/media/nas/backup"):
    print("Montage actif")

# Désactiver et supprimer
mount_mgr.disable_mount("/media/nas/backup")
mount_mgr.remove_mount_unit("/media/nas/backup")
```

### Module `integrity`

Vérification d'intégrité par checksums.

```python
from linux_python_utils import FileLogger, SHA256IntegrityChecker, calculate_checksum

# Fonction utilitaire rapide
checksum = calculate_checksum("/path/to/file")  # SHA256 par défaut
checksum_md5 = calculate_checksum("/path/to/file", algorithm="md5")

# Vérificateur avec logging
logger = FileLogger("/var/log/backup.log")
checker = SHA256IntegrityChecker(logger)

# Vérifier un fichier unique
if checker.verify_file("/source/file.txt", "/dest/file.txt"):
    print("Fichier identique")

# Vérifier un répertoire complet (après rsync)
if checker.verify("/home/user/Documents", "/media/backup"):
    print("Sauvegarde vérifiée")
else:
    print("Erreur d'intégrité!")

# Obtenir le checksum avec logging
checksum = checker.get_checksum("/path/to/file")
```

### Exemple Complet

Script de sauvegarde utilisant tous les modules :

```python
#!/usr/bin/env python3
from linux_python_utils import (
    FileLogger,
    ConfigurationManager,
    LinuxFileBackup,
    SHA256IntegrityChecker
)

# Configuration
DEFAULT_CONFIG = {
    "logging": {"level": "INFO"},
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

# Initialisation
logger = FileLogger("/var/log/backup.log", config=config, console_output=True)
integrity_checker = SHA256IntegrityChecker(logger)

# Récupération du profil
profile = config.get_profile("documents")
source = profile["source"]
destination = profile["destination"]

logger.log_info(f"Sauvegarde de {source} vers {destination}")

# ... exécution de la sauvegarde (rsync, etc.) ...

# Vérification d'intégrité
if integrity_checker.verify(source, destination):
    logger.log_info("Sauvegarde vérifiée avec succès")
else:
    logger.log_error("Échec de la vérification d'intégrité")
```

## 📖 Documentation API

### Classes et Interfaces Exportées

| Module | ABC (Interface) | Implémentation | Description |
|--------|-----------------|----------------|-------------|
| `logging` | `Logger` | `FileLogger` | Logging fichier/console |
| `config` | `ConfigManager` | `ConfigurationManager` | Gestion de configuration |
| `config` | `ConfigLoader` | `FileConfigLoader` | Chargement TOML/JSON |
| `filesystem` | `FileManager` | `LinuxFileManager` | CRUD fichiers |
| `filesystem` | `FileBackup` | `LinuxFileBackup` | Sauvegarde/restauration |
| `systemd` | `SystemdServiceManager` | `LinuxSystemdServiceManager` | Services/timers |
| `systemd` | `MountUnitManager` | `LinuxMountUnitManager` | Unités de montage |
| `integrity` | `IntegrityChecker` | `SHA256IntegrityChecker` | Vérification checksums |
| `integrity` | `ChecksumCalculator` | `HashLibChecksumCalculator` | Calcul checksums |

### Dataclasses

| Classe | Description |
|--------|-------------|
| `MountConfig` | Configuration d'une unité .mount |
| `AutomountConfig` | Configuration d'une unité .automount |

## 🏗️ Architecture des Classes

### Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                    linux-python-utils                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  logging  │  │  config   │  │filesystem │  │  systemd  │    │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘    │
│        │              │              │              │           │
│        ▼              ▼              ▼              ▼           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  Logger   │  │ConfigMgr  │  │FileManager│  │ServiceMgr │    │
│  │   (ABC)   │  │  (ABC)    │  │   (ABC)   │  │   (ABC)   │    │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘    │
│        │              │              │              │           │
│        ▼              ▼              ▼              ▼           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │FileLogger │  │ConfigMgr  │  │LinuxFile  │  │LinuxSysd  │    │
│  │           │  │           │  │Manager    │  │ServiceMgr │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Principes SOLID Appliqués

| Principe | Application |
|----------|-------------|
| **S** - Single Responsibility | `FileManager` (CRUD) séparé de `FileBackup` (sauvegarde) |
| **O** - Open/Closed | ABCs stables, nouvelles implémentations sans modification |
| **L** - Liskov Substitution | Toutes les implémentations respectent leurs contrats ABC |
| **I** - Interface Segregation | `SystemdServiceManager` séparé de `MountUnitManager` |
| **D** - Dependency Inversion | Injection de `Logger`, `ConfigLoader`, `ChecksumCalculator` |

### Injection de Dépendances

```python
# Toutes les classes acceptent des abstractions en injection
class SHA256IntegrityChecker(IntegrityChecker):
    def __init__(
        self,
        logger: Logger,                              # ABC
        algorithm: str = 'sha256',
        checksum_calculator: ChecksumCalculator = None  # ABC (optionnel)
    ): ...

class ConfigurationManager(ConfigManager):
    def __init__(
        self,
        config_path: str = None,
        default_config: dict = None,
        search_paths: list = None,
        config_loader: ConfigLoader = None           # ABC (optionnel)
    ): ...

# Facilite les tests avec des mocks
class MockLogger(Logger):
    def log_info(self, message): pass
    def log_warning(self, message): pass
    def log_error(self, message): pass

checker = SHA256IntegrityChecker(MockLogger())
```

## 🗂️ Structure du Projet

```
linux-python-utils/
├── linux_python_utils/
│   ├── __init__.py              # Exports publics
│   ├── logging/
│   │   ├── __init__.py
│   │   ├── base.py              # ABC Logger
│   │   └── file_logger.py       # FileLogger
│   ├── config/
│   │   ├── __init__.py
│   │   ├── base.py              # ABC ConfigManager
│   │   ├── loader.py            # ABC ConfigLoader + FileConfigLoader
│   │   └── manager.py           # ConfigurationManager
│   ├── filesystem/
│   │   ├── __init__.py
│   │   ├── base.py              # ABCs FileManager, FileBackup
│   │   ├── linux.py             # LinuxFileManager
│   │   └── backup.py            # LinuxFileBackup
│   ├── systemd/
│   │   ├── __init__.py
│   │   ├── base.py              # ABCs + dataclasses
│   │   ├── linux.py             # LinuxSystemdServiceManager
│   │   └── mount.py             # LinuxMountUnitManager
│   └── integrity/
│       ├── __init__.py
│       ├── base.py              # ABCs + calculate_checksum
│       └── sha256.py            # SHA256IntegrityChecker
├── tests/
│   ├── __init__.py
│   ├── test_logging.py          # 8 tests
│   ├── test_config.py           # 13 tests
│   ├── test_integrity.py        # 11 tests
│   └── test_systemd_mount.py    # 28 tests
├── pyproject.toml
├── Makefile
├── CLAUDE.md
└── README.md
```

## 🧪 Tests

### Lancer les Tests

```bash
# Afficher les commandes disponibles
make help

# Lancer tous les tests
make test

# Lancer les tests en mode verbose
make test-verbose

# Lancer un test spécifique
pytest tests/test_logging.py::TestFileLogger::test_log_info -v

# Vérifier PEP8
make lint

# Tout lancer (lint + tests + build)
make all
```

### Résumé des Tests

| Module | Tests | Description |
|--------|-------|-------------|
| `test_config.py` | 13 | Chargement TOML/JSON, profils, fusion |
| `test_logging.py` | 8 | FileLogger, UTF-8, configuration |
| `test_integrity.py` | 11 | Checksums, vérification fichiers/répertoires |
| `test_systemd_mount.py` | 28 | Génération .mount/.automount, enable/disable |
| **Total** | **60** | |

### Tests Paramétrés

```python
@pytest.mark.parametrize("path,expected", [
    ("/media/nas", "media-nas"),
    ("/media/nas/backup/daily", "media-nas-backup-daily"),
    ("/mnt", "mnt"),
])
def test_path_conversion(path, expected):
    assert mount_mgr.path_to_unit_name(path) == expected
```

## 🐛 Troubleshooting

<details>
<summary><b>❌ ModuleNotFoundError: No module named 'linux_python_utils'</b></summary>

**Cause :** Package non installé ou environnement virtuel non activé.

**Solution :**
```bash
# Vérifier l'environnement virtuel
which python

# Réinstaller
pip install -e .
```
</details>

<details>
<summary><b>❌ ModuleNotFoundError: No module named 'tomllib'</b></summary>

**Cause :** Version Python < 3.11.

**Solution :**
```bash
# Vérifier la version
python --version

# Installer Python 3.11+
# Ubuntu/Debian
sudo apt install python3.11

# Fedora
sudo dnf install python3.11
```
</details>

<details>
<summary><b>❌ PermissionError lors de l'écriture des fichiers .mount</b></summary>

**Cause :** Les fichiers systemd nécessitent des droits root.

**Solution :**
```bash
# Exécuter avec sudo
sudo python mon_script.py

# Ou utiliser le répertoire utilisateur
~/.config/systemd/user/
```
</details>

<details>
<summary><b>❌ FileNotFoundError pour le fichier de configuration</b></summary>

**Cause :** Le fichier de configuration n'existe pas aux chemins spécifiés.

**Solution :**
```python
# Utiliser search_paths avec un fallback
config = ConfigurationManager(
    default_config=DEFAULT_CONFIG,  # Toujours fournir des défauts
    search_paths=["~/.config/app/config.toml"]
)

# Ou créer le fichier par défaut
config.create_default_config("~/.config/app/config.toml")
```
</details>

## 🤝 Contribution

Les contributions sont les bienvenues !

### Processus

1. **Fork** le projet
2. **Créer** une branche (`git checkout -b feature/amazing-feature`)
3. **Commiter** (`git commit -m 'Add amazing feature'`)
4. **Pusher** (`git push origin feature/amazing-feature`)
5. **Ouvrir** une Pull Request

### Guidelines

- Suivre PEP 8 (max 79 caractères par ligne)
- Docstrings en français (PEP 257)
- Type hints requis (PEP 484)
- Respecter l'architecture SOLID existante
- Ajouter des tests pour les nouvelles fonctionnalités

### Développement Local

```bash
# Installer les dépendances de dev
make install-dev

# Vérifier le style
make lint

# Lancer les tests
make test

# Build complet
make all
```

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

<p align="center">
  <b>linux-python-utils</b> — Conçu avec les principes SOLID pour une extensibilité maximale
</p>
