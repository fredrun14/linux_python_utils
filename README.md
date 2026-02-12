# 🐧 Linux Python Utils

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-229%20passed-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP8-black.svg)]()
[![SOLID](https://img.shields.io/badge/Architecture-SOLID-purple.svg)]()

> Bibliothèque utilitaire Python pour systèmes Linux, conçue avec les principes SOLID.

Fournit des classes réutilisables et extensibles pour le logging, la configuration, la gestion de fichiers, les services systemd, l'exécution de commandes, la gestion de fichiers INI, la validation de données et la vérification d'intégrité. Architecture basée sur des Abstract Base Classes (ABC) permettant l'injection de dépendances et facilitant les tests unitaires.

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
  - [Module dotconf](#module-dotconf)
  - [Module commands](#module-commands)
  - [Module scripts](#module-scripts)
  - [Module notification](#module-notification)
  - [Module validation](#module-validation)
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
- **🔧 Systemd complet** — Gestion services, timers et unités de montage (système et utilisateur)
- **📄 Chargeurs de config** — Loaders typés pour créer des dataclasses depuis TOML ou JSON
- **🔐 Vérification d'intégrité** — Checksums SHA256/SHA512/MD5 pour fichiers et répertoires
- **🖥️ Exécution de commandes** — Construction fluent et exécution avec streaming temps réel
- **📋 Fichiers INI (.conf)** — Lecture, écriture et validation de fichiers de configuration INI
- **📜 Scripts bash** — Génération de scripts bash avec support des notifications
- **🔔 Notifications** — Configuration des notifications desktop (KDE Plasma)
- **✅ Validation** — Validation de chemins et données avec support optionnel Pydantic
- **🏗️ Architecture SOLID** — ABCs, injection de dépendances, testabilité maximale
- **🧪 Bien testé** — 229 tests unitaires couvrant tous les modules

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

# 5. (Optionnel) Installer avec support validation Pydantic
pip install -e ".[validation]"
```

### Installation via pip

```bash
# Depuis GitHub
pip install git+https://github.com/user/linux-python-utils.git
```

### Vérification de l'Installation

```python
import linux_python_utils
print(linux_python_utils.__version__)  # 1.0.0
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
#### Classe `FileConfigLoader`

 ```python
from linux_python_utils import FileConfigLoader

# Chargement TOML ou JSON (détection automatique)
loader = FileConfigLoader()
config = loader.load("/etc/myapp/config.toml")
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

Gestion complète des unités systemd : services, timers et montages, en mode système (root) ou utilisateur.

#### Architecture

```
┌─────────────────────┐          ┌─────────────────────┐
│   SystemdExecutor   │          │ UserSystemdExecutor │
│  systemctl          │          │  systemctl --user   │
│  /etc/systemd/system│          │  ~/.config/systemd/ │
└─────────┬───────────┘          └─────────┬───────────┘
          │                                │
    ┌─────┼─────┐                    ┌─────┼─────┐
    ▼     ▼     ▼                    ▼           ▼
 Mount  Timer Service          UserTimer   UserService
 UnitMgr UnitMgr UnitMgr       UnitMgr     UnitMgr
```

#### Unités Système (requiert root)

##### Unités de Montage (.mount / .automount)

```python
from linux_python_utils import (
    FileLogger,
    SystemdExecutor,
    LinuxMountUnitManager,
    MountConfig
)

logger = FileLogger("/var/log/mount.log")
executor = SystemdExecutor(logger)
mount_mgr = LinuxMountUnitManager(logger, executor)

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

##### Timers Système

```python
from linux_python_utils import (
    FileLogger,
    SystemdExecutor,
    LinuxTimerUnitManager,
    TimerConfig
)

logger = FileLogger("/var/log/timer.log")
executor = SystemdExecutor(logger)
timer_mgr = LinuxTimerUnitManager(logger, executor)

# Configuration du timer
config = TimerConfig(
    description="Backup quotidien",
    unit="backup.service",
    on_calendar="*-*-* 02:00:00",  # Tous les jours à 2h
    persistent=True,  # Rattraper les exécutions manquées
    randomized_delay_sec="1h"
)

# Installer et activer
timer_mgr.install_timer_unit(config)
timer_mgr.enable_timer("backup")

# Lister les timers actifs
timers = timer_mgr.list_timers()
for t in timers:
    print(f"{t['unit']}: prochaine exécution {t['next']}")
```

##### Services Système

```python
from linux_python_utils import (
    FileLogger,
    SystemdExecutor,
    LinuxServiceUnitManager,
    ServiceConfig
)

logger = FileLogger("/var/log/service.log")
executor = SystemdExecutor(logger)
service_mgr = LinuxServiceUnitManager(logger, executor)

# Configuration du service
config = ServiceConfig(
    description="Mon application web",
    exec_start="/usr/bin/python /opt/myapp/app.py",
    type="simple",
    user="www-data",
    working_directory="/opt/myapp",
    restart="on-failure",
    restart_sec=5,
    environment={"PYTHONPATH": "/opt/myapp"}
)

# Installer avec un nom spécifique
service_mgr.install_service_unit_with_name("myapp", config)

# Contrôler le service
service_mgr.enable_service("myapp")
service_mgr.start_service("myapp")

if service_mgr.is_service_active("myapp"):
    print("Service actif")

service_mgr.restart_service("myapp")
service_mgr.stop_service("myapp")
```

#### Unités Utilisateur (sans root)

Les unités utilisateur sont stockées dans `~/.config/systemd/user/` et ne nécessitent pas de privilèges root.

##### Timers Utilisateur

```python
from linux_python_utils import (
    FileLogger,
    UserSystemdExecutor,
    LinuxUserTimerUnitManager,
    TimerConfig
)

logger = FileLogger("~/.local/log/timer.log")
executor = UserSystemdExecutor(logger)
timer_mgr = LinuxUserTimerUnitManager(logger, executor)

# Timer pour synchroniser des fichiers toutes les heures
config = TimerConfig(
    description="Sync fichiers",
    unit="sync.service",
    on_calendar="hourly",
    persistent=True
)

timer_mgr.install_timer_unit(config)
timer_mgr.enable_timer("sync")
```

##### Services Utilisateur

```python
from linux_python_utils import (
    FileLogger,
    UserSystemdExecutor,
    LinuxUserServiceUnitManager,
    ServiceConfig
)

logger = FileLogger("~/.local/log/service.log")
executor = UserSystemdExecutor(logger)
service_mgr = LinuxUserServiceUnitManager(logger, executor)

# Service de synchronisation
config = ServiceConfig(
    description="Synchronisation Dropbox",
    exec_start="/home/user/.local/bin/sync.sh",
    type="oneshot",
    working_directory="/home/user"
)

service_mgr.install_service_unit_with_name("sync", config)
service_mgr.enable_service("sync")
```

### Module `systemd.config_loaders`

Chargeurs de configuration pour créer des dataclasses systemd depuis TOML ou JSON.
Le format est automatiquement détecté par l'extension du fichier.

```python
from linux_python_utils.systemd.config_loaders import (
    ServiceConfigLoader,
    TimerConfigLoader,
    MountConfigLoader,
    BashScriptConfigLoader,
)

# Charger un ServiceConfig depuis TOML ou JSON
service_loader = ServiceConfigLoader("config/app.toml")  # ou .json
service_config = service_loader.load()
print(service_config.description)

# Charger un TimerConfig pour un service spécifique
timer_loader = TimerConfigLoader("config/app.toml")
timer_config = timer_loader.load_for_service("my-service")
print(timer_config.unit)  # "my-service.service"

# Charger un BashScriptConfig avec notifications
script_loader = BashScriptConfigLoader("config/app.toml")
script_config = script_loader.load()
if script_config.notification:
    print("Notifications activées")

# Charger plusieurs montages depuis une liste TOML
mount_loader = MountConfigLoader("config/mounts.toml")
mounts = mount_loader.load_multiple("mounts")  # [[mounts]] dans TOML
for mount in mounts:
    print(f"{mount.what} → {mount.where}")
```

**Fichier TOML exemple :**

```toml
[service]
description = "Mon service"
exec_start = "/usr/bin/mon-app"
type = "oneshot"

[timer]
description = "Timer quotidien"
unit = "mon-service.service"
on_calendar = "daily"
persistent = true

[notification]
enabled = true
title = "Mon App"
message_success = "Succès!"
message_failure = "Échec!"
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

### Module `dotconf`

Gestion de fichiers de configuration INI (.conf) avec validation externe.

```python
from dataclasses import dataclass
from pathlib import Path
from linux_python_utils import (
    FileLogger,
    ValidatedSection,
    LinuxIniConfigManager,
)

# Définir une section avec validation
@dataclass(frozen=True)
class CommandsSection(ValidatedSection):
    upgrade_type: str = "default"
    download_updates: str = "yes"

    @staticmethod
    def section_name() -> str:
        return "commands"

# Injecter les validateurs depuis le TOML
CommandsSection.set_validators({
    "upgrade_type": ["default", "security"],
    "download_updates": ["yes", "no"],
})

# Créer et écrire une section
section = CommandsSection(
    upgrade_type="security", download_updates="yes"
)

logger = FileLogger("/var/log/config.log")
manager = LinuxIniConfigManager(logger)

# Écrire une section dans un fichier
manager.write_section(Path("/etc/myapp.conf"), section)

# Lire un fichier INI complet
config = manager.read(Path("/etc/myapp.conf"))
print(config["commands"]["upgrade_type"])  # "security"

# Mise à jour conditionnelle (n'écrit que si changé)
updated = manager.update_section(
    Path("/etc/myapp.conf"), section
)
print(f"Modifié: {updated}")
```

### Module `commands`

Construction fluent et exécution de commandes système.

```python
from linux_python_utils import (
    FileLogger,
    CommandBuilder,
    LinuxCommandExecutor,
)

# Construire une commande avec l'API fluent
cmd = (
    CommandBuilder("rsync")
    .with_options(["-av", "--delete"])
    .with_option("--compress-level", "3")
    .with_flag("--stats")
    .with_args(["/src/", "/dest/"])
    .build()
)
# Résultat : ["rsync", "-av", "--delete",
#             "--compress-level=3", "--stats",
#             "/src/", "/dest/"]

# Exécuter avec capture de sortie
logger = FileLogger("/var/log/commands.log")
executor = LinuxCommandExecutor(logger=logger)
result = executor.run(cmd)

print(result.success)      # True/False
print(result.return_code)  # 0
print(result.stdout)       # Sortie standard
print(result.duration)     # Durée en secondes

# Streaming temps réel vers le logger
result = executor.run_streaming(cmd)

# Mode dry-run (simulation sans exécution)
dry_executor = LinuxCommandExecutor(
    logger=logger, dry_run=True
)
result = dry_executor.run(cmd)  # Log seulement

# Options conditionnelles
cmd = (
    CommandBuilder("rsync")
    .with_options(["-av"])
    .with_option_if("--bwlimit", "1000", condition=True)
    .with_option_if("--exclude", None)  # Ignoré (None)
    .with_args(["/src/", "/dest/"])
    .build()
)
```

### Module `scripts`

Génération de scripts bash avec support des notifications.

```python
from linux_python_utils import BashScriptConfig, BashScriptInstaller

# Configuration d'un script bash
config = BashScriptConfig(
    name="backup",
    description="Script de sauvegarde quotidien",
    commands=["rsync -av /src /dest", "echo 'Done'"],
    notification=None  # Ou NotificationConfig
)

# Générer le contenu du script
print(config.to_bash_script())

# Installer le script sur le système
installer = BashScriptInstaller(logger)
installer.install(config, "/usr/local/bin/backup.sh")
```

### Module `notification`

Configuration des notifications desktop (KDE Plasma).

```python
from linux_python_utils import NotificationConfig

# Configuration de notification
notif = NotificationConfig(
    enabled=True,
    title="Sauvegarde",
    message_success="Sauvegarde terminée avec succès",
    message_failure="Échec de la sauvegarde"
)

# Générer les appels bash pour notify-send
bash_calls = notif.to_bash_calls()
bash_function = notif.to_bash_function()
```

### Module `validation`

Validation de chemins et données avec support optionnel Pydantic.

```python
from linux_python_utils import PathChecker, FileConfigLoader

# Validation de chemins (répertoires parents existent et sont
# accessibles en écriture)
checker = PathChecker([
    "/var/log/myapp.log",
    "/etc/myapp/config.toml",
])
checker.validate()  # Lève ValueError ou PermissionError

# Validation de configuration avec Pydantic (optionnel)
# pip install linux-python-utils[validation]
from pydantic import BaseModel

class AppConfig(BaseModel):
    name: str
    debug: bool = False
    port: int = 8080

loader = FileConfigLoader()
config = loader.load("config.toml", schema=AppConfig)
print(config.name)  # Instance AppConfig validée
```

### Exemple Complet

Script de sauvegarde utilisant tous les modules :

```python
#!/usr/bin/env python3
from linux_python_utils import (
    FileLogger,
    ConfigurationManager,
    LinuxFileBackup,
    SHA256IntegrityChecker,
    UserSystemdExecutor,
    LinuxUserTimerUnitManager,
    LinuxUserServiceUnitManager,
    TimerConfig,
    ServiceConfig
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
logger = FileLogger("~/.local/log/backup.log", config=config, console_output=True)
executor = UserSystemdExecutor(logger)

# Créer le service de backup
service_mgr = LinuxUserServiceUnitManager(logger, executor)
service_config = ServiceConfig(
    description="Sauvegarde documents",
    exec_start="/home/user/scripts/backup.sh",
    type="oneshot"
)
service_mgr.install_service_unit_with_name("backup", service_config)

# Créer le timer (tous les jours à 6h)
timer_mgr = LinuxUserTimerUnitManager(logger, executor)
timer_config = TimerConfig(
    description="Timer backup quotidien",
    unit="backup.service",
    on_calendar="*-*-* 06:00:00",
    persistent=True
)
timer_mgr.install_timer_unit(timer_config)
timer_mgr.enable_timer("backup")

logger.log_info("Backup automatique configuré")
```

## 📖 Documentation API

### Classes et Interfaces Exportées

#### Module `logging`

| ABC (Interface) | Implémentation | Description |
|-----------------|----------------|-------------|
| `Logger` | `FileLogger` | Logging fichier/console |

#### Module `config`

| ABC (Interface) | Implémentation | Description |
|-----------------|----------------|-------------|
| `ConfigManager` | `ConfigurationManager` | Gestion de configuration |
| `ConfigLoader` | `FileConfigLoader` | Chargement TOML/JSON |

#### Module `filesystem`

| ABC (Interface) | Implémentation | Description |
|-----------------|----------------|-------------|
| `FileManager` | `LinuxFileManager` | CRUD fichiers |
| `FileBackup` | `LinuxFileBackup` | Sauvegarde/restauration |

#### Module `systemd`

| ABC (Interface) | Implémentation | Description |
|-----------------|----------------|-------------|
| — | `SystemdExecutor` | Exécuteur systemctl (système) |
| — | `UserSystemdExecutor` | Exécuteur systemctl --user |
| `MountUnitManager` | `LinuxMountUnitManager` | Unités .mount/.automount |
| `TimerUnitManager` | `LinuxTimerUnitManager` | Unités .timer (système) |
| `ServiceUnitManager` | `LinuxServiceUnitManager` | Unités .service (système) |
| `UserTimerUnitManager` | `LinuxUserTimerUnitManager` | Unités .timer (utilisateur) |
| `UserServiceUnitManager` | `LinuxUserServiceUnitManager` | Unités .service (utilisateur) |
| `ScheduledTaskInstaller` | `SystemdScheduledTaskInstaller` | Installation tâche planifiée complète |

#### Module `systemd.config_loaders`

| ABC (Interface) | Implémentation | Description |
|-----------------|----------------|-------------|
| `ConfigFileLoader[T]` | — | Classe de base générique (TOML/JSON) |
| — | `ServiceConfigLoader` | Config → ServiceConfig |
| — | `TimerConfigLoader` | Config → TimerConfig |
| — | `MountConfigLoader` | Config → MountConfig |
| — | `BashScriptConfigLoader` | Config → BashScriptConfig |

#### Module `integrity`

| ABC (Interface) | Implémentation | Description |
|-----------------|----------------|-------------|
| `IntegrityChecker` | `SHA256IntegrityChecker` | Vérification checksums |
| `ChecksumCalculator` | `HashLibChecksumCalculator` | Calcul checksums |

#### Module `dotconf`

| ABC (Interface) | Implémentation | Description |
|-----------------|----------------|-------------|
| `IniSection` | `ValidatedSection` | Section INI avec validation |
| `IniConfig` | — | Fichier INI complet |
| `IniConfigManager` | `LinuxIniConfigManager` | Gestion lecture/écriture INI |

#### Module `commands`

| ABC (Interface) | Implémentation | Description |
|-----------------|----------------|-------------|
| `CommandExecutor` | `LinuxCommandExecutor` | Exécution subprocess |
| — | `CommandBuilder` | Construction fluent de commandes |

#### Module `scripts`

| ABC (Interface) | Implémentation | Description |
|-----------------|----------------|-------------|
| `ScriptInstaller` | `BashScriptInstaller` | Installation de scripts bash |

#### Module `validation`

| ABC (Interface) | Implémentation | Description |
|-----------------|----------------|-------------|
| `Validator` | `PathChecker` | Validation de chemins fichiers |

### Dataclasses

| Classe | Description |
|--------|-------------|
| `MountConfig` | Configuration d'une unité .mount |
| `AutomountConfig` | Configuration d'une unité .automount |
| `TimerConfig` | Configuration d'une unité .timer |
| `ServiceConfig` | Configuration d'une unité .service |
| `BashScriptConfig` | Configuration d'un script bash |
| `NotificationConfig` | Configuration des notifications desktop |
| `CommandResult` | Résultat d'exécution de commande |
| `ValidatedSection` | Section INI avec validation externe |

## 🏗️ Architecture des Classes

### Vue d'Ensemble

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          linux-python-utils                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ logging  │ │  config  │ │filesystem│ │ systemd  │ │integrity │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
│       │            │            │            │            │               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ commands │ │ dotconf  │ │ scripts  │ │notificat.│ │validation│        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
│       │            │            │            │            │               │
│       ▼            ▼            ▼            ▼            ▼               │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │              Abstract Base Classes (ABCs)                        │      │
│  │  Logger, ConfigLoader, FileManager, Validator, CommandExecutor   │      │
│  │  IniConfigManager, ScriptInstaller, IntegrityChecker ...        │      │
│  └──────────────────────────┬──────────────────────────────────────┘      │
│                             │                                             │
│                             ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │              Implémentations Linux concrètes                    │      │
│  │  FileLogger, LinuxFileManager, LinuxCommandExecutor,            │      │
│  │  LinuxIniConfigManager, PathChecker, SHA256IntegrityChecker ... │      │
│  └─────────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Systemd

```
                    ┌─────────────────────────────────────────────┐
                    │              SystemdExecutor                 │
                    │  - _run_systemctl(args)                     │
                    │  - reload_systemd()                         │
                    │  - enable_unit() / disable_unit()           │
                    │  - start_unit() / stop_unit()               │
                    │  - get_status() / is_active()               │
                    └─────────────────────┬───────────────────────┘
                                          │ hérite
                                          ▼
                    ┌─────────────────────────────────────────────┐
                    │            UserSystemdExecutor              │
                    │  surcharge _run_systemctl pour --user       │
                    └─────────────────────┬───────────────────────┘
                                          │
                                          │ injection
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
        ▼                                 ▼                                 ▼
┌───────────────────┐           ┌───────────────────┐           ┌───────────────────┐
│    UnitManager    │           │  UserUnitManager  │           │  (autres futurs)  │
│ /etc/systemd/sys  │           │ ~/.config/systemd │           │                   │
├───────────────────┤           ├───────────────────┤           └───────────────────┘
│ LinuxMountUnitMgr │           │ LinuxUserTimerMgr │
│ LinuxTimerUnitMgr │           │ LinuxUserServiceMgr│
│ LinuxServiceUnitMgr│          └───────────────────┘
└───────────────────┘
```

### Principes SOLID Appliqués

| Principe | Application |
|----------|-------------|
| **S** - Single Responsibility | `SystemdExecutor` (commandes) séparé de `UnitManager` (fichiers unit) |
| **O** - Open/Closed | ABCs stables, nouvelles implémentations sans modification |
| **L** - Liskov Substitution | Toutes les implémentations respectent leurs contrats ABC |
| **I** - Interface Segregation | `MountUnitManager`, `TimerUnitManager`, `ServiceUnitManager` séparés |
| **D** - Dependency Inversion | Injection de `Logger` et `SystemdExecutor` dans les managers |

### Injection de Dépendances

```python
# Toutes les classes acceptent des abstractions en injection
class LinuxMountUnitManager(MountUnitManager):
    def __init__(
        self,
        logger: Logger,           # ABC injectée
        executor: SystemdExecutor  # Executor injecté
    ): ...

# Facilite les tests avec des mocks
class MockLogger(Logger):
    def log_info(self, message): pass
    def log_warning(self, message): pass
    def log_error(self, message): pass

class MockExecutor(SystemdExecutor):
    def reload_systemd(self): return True
    def enable_unit(self, name): return True
    # ...

mount_mgr = LinuxMountUnitManager(MockLogger(), MockExecutor(MockLogger()))
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
│   │   ├── __init__.py          # Exports module systemd
│   │   ├── base.py              # ABCs + dataclasses (configs)
│   │   ├── executor.py          # SystemdExecutor, UserSystemdExecutor
│   │   ├── mount.py             # LinuxMountUnitManager
│   │   ├── timer.py             # LinuxTimerUnitManager
│   │   ├── service.py           # LinuxServiceUnitManager
│   │   ├── user_timer.py        # LinuxUserTimerUnitManager
│   │   ├── user_service.py      # LinuxUserServiceUnitManager
│   │   ├── scheduled_task.py    # SystemdScheduledTaskInstaller
│   │   └── config_loaders/      # Chargeurs de configuration (TOML/JSON)
│   │       ├── __init__.py
│   │       ├── base.py          # ConfigFileLoader[T] (ABC)
│   │       ├── service_loader.py # ServiceConfigLoader
│   │       ├── timer_loader.py  # TimerConfigLoader
│   │       ├── mount_loader.py  # MountConfigLoader
│   │       └── script_loader.py # BashScriptConfigLoader
│   ├── integrity/
│   │   ├── __init__.py
│   │   ├── base.py              # ABCs + calculate_checksum
│   │   └── sha256.py            # SHA256IntegrityChecker
│   ├── dotconf/
│   │   ├── __init__.py
│   │   ├── base.py              # ABCs IniSection, IniConfig, IniConfigManager
│   │   ├── section.py           # ValidatedSection + utilitaires
│   │   └── manager.py           # LinuxIniConfigManager
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── base.py              # CommandResult + ABC CommandExecutor
│   │   ├── builder.py           # CommandBuilder (API fluent)
│   │   └── runner.py            # LinuxCommandExecutor (subprocess)
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── config.py            # BashScriptConfig (dataclass)
│   │   └── installer.py         # ABC ScriptInstaller + BashScriptInstaller
│   ├── notification/
│   │   ├── __init__.py
│   │   └── config.py            # NotificationConfig (dataclass)
│   └── validation/
│       ├── __init__.py
│       ├── base.py              # ABC Validator
│       └── path_checker.py      # PathChecker
├── tests/
│   ├── __init__.py
│   ├── test_logging.py              # 8 tests
│   ├── test_config.py               # 13 tests
│   ├── test_config_validation.py    # 11 tests
│   ├── test_integrity.py            # 11 tests
│   ├── test_systemd_mount.py        # 28 tests
│   ├── test_systemd_timer.py        # 11 tests
│   ├── test_systemd_service.py      # 13 tests
│   ├── test_systemd_scheduled_task.py # 12 tests
│   ├── test_systemd_config_loaders.py # 30 tests
│   ├── test_dotconf.py              # 21 tests
│   ├── test_commands.py             # 34 tests
│   ├── test_scripts.py             # 19 tests
│   ├── test_notification.py         # 13 tests
│   └── test_validation.py           # 5 tests
├── examples/
│   └── nfs-mounts.toml              # Exemple de configuration
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
| `test_logging.py` | 8 | FileLogger, UTF-8, configuration |
| `test_config.py` | 13 | Chargement TOML/JSON, profils, fusion |
| `test_config_validation.py` | 11 | Validation Pydantic optionnelle |
| `test_integrity.py` | 11 | Checksums, vérification fichiers/répertoires |
| `test_systemd_mount.py` | 28 | Génération .mount/.automount, enable/disable |
| `test_systemd_timer.py` | 11 | TimerConfig, to_unit_file(), validation |
| `test_systemd_service.py` | 13 | ServiceConfig, to_unit_file(), validation |
| `test_systemd_scheduled_task.py` | 12 | SystemdScheduledTaskInstaller |
| `test_systemd_config_loaders.py` | 30 | Tous les loaders (TOML/JSON) |
| `test_dotconf.py` | 21 | Sections INI, validation, lecture/écriture |
| `test_commands.py` | 34 | CommandBuilder, exécution, streaming, dry-run |
| `test_scripts.py` | 19 | BashScriptConfig, installation scripts |
| `test_notification.py` | 13 | NotificationConfig, génération bash |
| `test_validation.py` | 5 | PathChecker, permissions |
| **Total** | **229** | |

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
<summary><b>❌ PermissionError lors de l'écriture des fichiers .mount/.timer/.service</b></summary>

**Cause :** Les fichiers systemd système nécessitent des droits root.

**Solution :**
```bash
# Exécuter avec sudo pour les unités système
sudo python mon_script.py

# Ou utiliser les classes User* pour les unités utilisateur (sans root)
from linux_python_utils import UserSystemdExecutor, LinuxUserTimerUnitManager
```
</details>

<details>
<summary><b>❌ Failed to connect to bus: No such file or directory (systemctl --user)</b></summary>

**Cause :** Le bus D-Bus utilisateur n'est pas disponible (session non graphique).

**Solution :**
```bash
# Activer le lingering pour l'utilisateur
sudo loginctl enable-linger $USER

# Ou définir XDG_RUNTIME_DIR
export XDG_RUNTIME_DIR=/run/user/$(id -u)
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
