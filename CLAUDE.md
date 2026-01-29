# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**linux-python-utils** is a French-language Python utility library for Linux systems. It provides reusable classes and functions for logging, configuration management, file operations, systemd service management, and file integrity verification.

- Python 3.11+ required (uses `tomllib` for TOML parsing)
- No external runtime dependencies (stdlib only)
- Platform: Linux only

## Code Conventions

- **PEP 8**: Style guide (max-line-length = 79)
- **PEP 257**: Docstrings en français pour tous les modules, classes et fonctions publiques
- **PEP 484**: Type hints requis pour les signatures de fonctions et méthodes

## Development Commands

```bash
make help             # Afficher toutes les commandes disponibles
make install-dev      # Installer avec dépendances de développement
make test             # Lancer les tests
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

| Module | ABC | Implementation | Purpose |
|--------|-----|----------------|---------|
| `logging` | `Logger` | `FileLogger` | File logging with optional console output |
| `config` | — | `ConfigurationManager`, `load_config()` | TOML/JSON config with dot-notation access and profile support |
| `filesystem` | `FileManager`, `FileBackup` | `LinuxFileManager`, `LinuxFileBackup` | File CRUD and metadata-preserving backups |
| `systemd` | `SystemdServiceManager` | `LinuxSystemdServiceManager` | systemctl operations (start/stop/enable/status) |
| `integrity` | `IntegrityChecker` | `SHA256IntegrityChecker`, `calculate_checksum()` | File/directory checksum verification |

### Key Patterns

- **Dependency Injection**: Implementations accept Logger instances
- **Configuration-Driven**: `ConfigurationManager` supports deep merge, search paths, and tilde expansion
- **UTF-8 Throughout**: Explicit UTF-8 encoding (important for French documentation)

## Public API

All public classes and functions are exported from the package root:

```python
from linux_python_utils import (
    FileLogger, ConfigurationManager, load_config,
    LinuxFileManager, LinuxFileBackup,
    LinuxSystemdServiceManager,
    SHA256IntegrityChecker, calculate_checksum
)
```

## CI/CD

GitHub Actions workflow (`.github/workflows/python-package.yml`) :
- **lint**: Vérification PEP8
- **test**: Tests sur Python 3.11, 3.12, 3.13
- **build**: Construction du package

## Language

All docstrings, comments, and documentation are in French.
