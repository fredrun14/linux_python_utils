# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**linux-python-utils** is a French-language Python utility library for Linux systems. It provides reusable classes and functions for logging, configuration management, file operations, systemd service management, bash script generation, and file integrity verification.

- Python 3.11+ required (uses `tomllib` for TOML parsing)
- No external runtime dependencies (stdlib only)
- Platform: Linux only

## Code Conventions

- **PEP 8**: Style guide (max-line-length = 79)
- **PEP 257**: Docstrings en français pour tous les modules, classes et fonctions publiques
- **PEP 484**: Type hints requis pour les signatures de fonctions et méthodes
- **SOLID**: Architecture with ABCs and dependency injection

## Development Commands

```bash
make help             # Afficher toutes les commandes disponibles
make install-dev      # Installer avec dépendances de développement
make test             # Lancer les tests (177 tests)
make test-verbose     # Lancer les tests en mode verbose
make lint             # Vérifier PEP8
make clean            # Nettoyer les fichiers générés
make build            # Construire le package
make all              # Lint + tests + build
```

Pour lancer un test spécifique :
```bash
pytest tests/test_logging.py::TestFileLogger::test_log_info -v
```

## Architecture

The library uses Abstract Base Classes (ABCs) to define interfaces, with concrete Linux implementations. All implementations accept an optional Logger instance for integrated logging.

### Module Structure

| Module | Purpose |
|--------|---------|
| `logging` | File logging with optional console output (`Logger` → `FileLogger`) |
| `config` | TOML/JSON config with dot-notation access (`ConfigurationManager`, `load_config()`) |
| `filesystem` | File CRUD and metadata-preserving backups (`LinuxFileManager`, `LinuxFileBackup`) |
| `systemd` | Complete systemd management (services, timers, mounts) |
| `systemd.config_loaders` | TOML → dataclass loaders for systemd configs |
| `scripts` | Bash script generation with notification support |
| `notification` | Desktop notification configuration (KDE Plasma) |
| `integrity` | File/directory checksum verification (`SHA256IntegrityChecker`) |
| `dotconf` | INI-style configuration file management |

### Systemd Module

```
systemd/
├── executor.py          # SystemdExecutor, UserSystemdExecutor
├── mount.py             # LinuxMountUnitManager
├── timer.py             # LinuxTimerUnitManager
├── service.py           # LinuxServiceUnitManager
├── user_timer.py        # LinuxUserTimerUnitManager (no root)
├── user_service.py      # LinuxUserServiceUnitManager (no root)
├── scheduled_task.py    # SystemdScheduledTaskInstaller
└── config_loaders/      # TOML → dataclass loaders
    ├── base.py          # TomlConfigLoader[T] (ABC)
    ├── service_loader.py
    ├── timer_loader.py
    ├── mount_loader.py
    └── script_loader.py
```

### Config Loaders

Load TOML files and create typed dataclasses:

```python
from linux_python_utils.systemd.config_loaders import (
    ServiceConfigLoader,
    TimerConfigLoader,
    BashScriptConfigLoader,
)

# TOML → ServiceConfig
loader = ServiceConfigLoader("config.toml")
service_config = loader.load()

# TOML → TimerConfig (with custom service name)
loader = TimerConfigLoader("config.toml")
timer_config = loader.load_for_service("my-service")

# TOML → BashScriptConfig (with notifications)
loader = BashScriptConfigLoader("config.toml")
script_config = loader.load()
```

### Key Patterns

- **Dependency Injection**: All classes accept Logger and other dependencies
- **Generic Config Loaders**: `TomlConfigLoader[T]` base class for type-safe loading
- **Configuration-Driven**: `ConfigurationManager` supports deep merge, search paths, tilde expansion
- **UTF-8 Throughout**: Explicit UTF-8 encoding (important for French documentation)

## Public API

All public classes and functions are exported from the package root:

```python
from linux_python_utils import (
    # Logging
    FileLogger,
    # Config
    ConfigurationManager, load_config,
    # Filesystem
    LinuxFileManager, LinuxFileBackup,
    # Systemd
    SystemdExecutor, UserSystemdExecutor,
    LinuxServiceUnitManager, LinuxTimerUnitManager, LinuxMountUnitManager,
    LinuxUserServiceUnitManager, LinuxUserTimerUnitManager,
    SystemdScheduledTaskInstaller,
    ServiceConfig, TimerConfig, MountConfig,
    # Config Loaders
    ServiceConfigLoader, TimerConfigLoader, MountConfigLoader, BashScriptConfigLoader,
    # Scripts
    BashScriptConfig, BashScriptInstaller,
    # Notifications
    NotificationConfig,
    # Integrity
    SHA256IntegrityChecker, calculate_checksum,
)
```

## CI/CD

GitHub Actions workflow (`.github/workflows/python-package.yml`) :
- **lint**: Vérification PEP8
- **test**: Tests sur Python 3.11, 3.12, 3.13
- **build**: Construction du package

## Language

All docstrings, comments, and documentation are in French.
