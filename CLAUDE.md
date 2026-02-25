# CLAUDE.md

## Projet

**linux-python-utils** — bibliothèque utilitaire Python pour Linux (français).

- Python 3.11+ · stdlib uniquement · Linux only
- Dépendances optionnelles : `pydantic>=2.0`, `python-dotenv`, `keyring`

## Conventions

- **PEP 8** : max-line-length = 79
- **PEP 257** : docstrings en **français** — modules, classes, fonctions publiques
- **PEP 484** : type hints obligatoires sur toutes les signatures
- **SOLID** : ABCs + injection de dépendances · toutes les classes acceptent un `Logger` optionnel

## Commandes

```bash
make test          # lancer les tests
make lint          # vérifier PEP 8
make all           # lint + tests + build
pytest tests/test_foo.py::TestBar::test_baz -v  # test ciblé
```

## Architecture

Interfaces via ABCs, implémentations concrètes Linux.

| Module | Contenu clé |
|--------|-------------|
| `logging` | `FileLogger`, `SecurityLogger`, `SecurityEventType` |
| `config` | `ConfigurationManager`, `FileConfigLoader` (TOML/JSON, dot-notation) |
| `filesystem` | `LinuxFileManager`, `LinuxFileBackup` |
| `systemd` | `LinuxServiceUnitManager`, `LinuxTimerUnitManager`, `LinuxMountUnitManager`, user variants, `SystemdScheduledTaskInstaller` |
| `systemd.config_loaders` | `ServiceConfigLoader`, `TimerConfigLoader`, `MountConfigLoader`, `BashScriptConfigLoader` (TOML → dataclass) |
| `commands` | `CommandBuilder` (fluent), `LinuxCommandExecutor`, `AnsiCommandFormatter` |
| `scripts` | `BashScriptConfig`, `BashScriptInstaller` |
| `notification` | `NotificationConfig` (KDE Plasma) |
| `integrity` | `SHA256IntegrityChecker`, `IniSectionIntegrityChecker` |
| `dotconf` | `LinuxIniConfigManager`, `ValidatedSection` |
| `validation` | `PathChecker`, `PathCheckerPermission`, `PathCheckerWorldWritable` |
| `errors` | `ErrorHandlerChain`, `ErrorContext`, hiérarchie d'exceptions |
| `credentials` | `CredentialChain` : env → .env → keyring |
| `network` | `LinuxArpScanner`, `LinuxNmapScanner`, `AsusRouterClient`, DHCP/DNS |

## Patterns clés

- **TOCTOU-safe** : `os.open(O_NOFOLLOW)` + `os.fchmod(0o644)` dans les classes de base
- **Validation noms** : regex + anti-traversal dans `systemd/validators.py`
- **UTF-8 explicite** partout (docstrings français)
- **API publique** : tout exporté depuis `linux_python_utils/__init__.py`
