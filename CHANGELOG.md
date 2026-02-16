# Changelog

## [1.2.0] - 2026-02-16

### Sécurité

- **MOYENNE** : Élimination TOCTOU dans `_write_unit_file()` — remplacement du pattern `islink()` + `open()` par `os.open(O_NOFOLLOW)` qui refuse atomiquement les liens symboliques. Pas de fenêtre de course exploitable.
- **MOYENNE** : Élimination TOCTOU dans `_remove_unit_file()` — remplacement du pattern `exists()` + `remove()` par `try/except FileNotFoundError`.
- **MOYENNE** : Permissions explicites 0o644 sur les fichiers unit — `os.fchmod(fd, 0o644)` après création, indépendant du umask.
- **MOYENNE** : Validation des noms d'unités dans `SystemdExecutor` — tous les noms passés à `enable_unit()`, `disable_unit()`, `start_unit()`, `stop_unit()`, `restart_unit()`, `get_status()` et `is_enabled()` sont validés via `validate_unit_name()`.
- **MOYENNE** : Validation des noms dans les méthodes timer — `enable_timer()`, `disable_timer()`, `remove_timer_unit()`, `get_timer_status()` valident via `validate_unit_name()` dans `timer.py` et `user_timer.py`.
- **MOYENNE** : Validation des noms dans les méthodes service — `start_service()`, `stop_service()`, `restart_service()`, `enable_service()`, `disable_service()`, `remove_service_unit()`, `get_service_status()`, `is_service_enabled()` valident via `validate_service_name()` dans `service.py` et `user_service.py`.
- **BASSE** : Réduction des `except Exception` dans `executor.py` — `get_status()` et `is_enabled()` capturent désormais `(subprocess.SubprocessError, OSError)` au lieu de `Exception`.
- **BASSE** : Validation de `ServiceConfig.type` — restreint aux 7 types systemd connus (`simple`, `exec`, `forking`, `oneshot`, `dbus`, `notify`, `idle`).
- **BASSE** : Validation de `ServiceConfig.restart` — restreint aux 7 politiques connues (`no`, `always`, `on-success`, `on-failure`, `on-abnormal`, `on-abort`, `on-watchdog`).
- **BASSE** : Protection contre l'injection via `Environment=` dans `ServiceConfig` — les clés contenant `=` ou `\n` et les valeurs contenant `\n` sont rejetées.

### Refactoring

- **DRY** : Factorisation de `_write_unit_file()` et `_remove_unit_file()` dans les classes de base `UnitManager` et `UserUnitManager` (`base.py`). Suppression des 5 copies dupliquées dans `service.py`, `timer.py`, `mount.py`, `user_service.py` et `user_timer.py`.
- **DRY** : Factorisation de `_ensure_unit_directory()` dans `UserUnitManager` (`base.py`). Suppression des copies dans `user_service.py` et `user_timer.py`.
- **LSP** : Les méthodes `install_service_unit()` et `install_service_unit_with_name()` capturent désormais `ValueError` des validators et retournent `False` avec un log d'erreur, respectant le contrat `bool` de l'ABC.

### Tests

- 310 tests (était 276) — ajout de 34 tests couvrant :
  - Validation `ServiceConfig.type`, `ServiceConfig.restart` et `ServiceConfig.environment`
  - Protection anti-symlink TOCTOU de `_write_unit_file()`
  - Permissions 0o644 des fichiers unit créés
  - Suppression idempotente via `_remove_unit_file()`
  - Validation des noms dans `SystemdExecutor` et `UserSystemdExecutor`
  - Validation dans `start_service()`, `stop_service()`, `enable_service()`
  - Contrat LSP : `install_service_unit()` retourne `False` sur nom invalide

## [1.1.0] - 2026-02-15

### Sécurité

- **CRITIQUE** : Suppression de `eval()` dans `dotconf/section.py` — `parse_validator()` n'accepte plus que des listes de valeurs autorisées. Les validateurs callable doivent être passés directement en Python via `set_validators()`.
- **HAUTE** : Échappement des paramètres bash dans `notification/config.py` — utilisation de `shlex.quote()` dans `to_bash_call_success()` et `to_bash_call_failure()` pour prévenir les injections de commandes.
- **HAUTE** : Utilisation du context manager `with` pour `subprocess.Popen` dans `commands/runner.py` — garantit la fermeture des pipes en cas d'erreur.
- **HAUTE** : Protection anti-symlink dans les modules systemd — vérification `os.path.islink()` avant l'écriture des fichiers unit dans `service.py`, `timer.py`, `mount.py`, `user_service.py` et `user_timer.py`.
- **MOYENNE** : Validation des noms d'unités systemd — nouveau module `validators.py` avec `validate_unit_name()` et `validate_service_name()` (regex + anti-traversée).
- **MOYENNE** : Validation de `MountConfig` — `where` doit être absolu, `what` validé selon le type de montage (NFS, CIFS, device).
- **BASSE** : Réduction des `except Exception` dans `sha256.py` — `verify_file()` et `verify()` capturent `OSError` au lieu de `Exception`.
- **BASSE** : Parsing robuste de `list_timers()` — utilisation de `--output=json` avec fallback texte, gestion `FileNotFoundError`/`OSError`.

### Changements incompatibles

- `parse_validator()` n'accepte plus de strings lambda. Seules les listes `list[str]` sont acceptées.
- `set_validators()` accepte désormais directement des callables Python en plus des listes.
- Le format de sortie de `to_bash_call_success()` et `to_bash_call_failure()` utilise `shlex.quote()` au lieu de doubles quotes manuelles.
- `ServiceConfig` lève `ValueError` si `type` ou `restart` contient une valeur non reconnue par systemd.
- `ServiceConfig` lève `ValueError` si une clé d'environnement contient `=` ou `\n`, ou si une valeur contient `\n`.
