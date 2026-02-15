# Changelog

## [1.1.0] - 2026-02-15

### Sécurité

- **CRITIQUE** : Suppression de `eval()` dans `dotconf/section.py` — `parse_validator()` n'accepte plus que des listes de valeurs autorisées. Les validateurs callable doivent être passés directement en Python via `set_validators()`.
- **HAUTE** : Échappement des paramètres bash dans `notification/config.py` — utilisation de `shlex.quote()` dans `to_bash_call_success()` et `to_bash_call_failure()` pour prévenir les injections de commandes.
- **HAUTE** : Utilisation du context manager `with` pour `subprocess.Popen` dans `commands/runner.py` — garantit la fermeture des pipes en cas d'erreur.
- **HAUTE** : Protection anti-symlink dans les modules systemd — vérification `os.path.islink()` avant l'écriture des fichiers unit dans `service.py`, `timer.py`, `mount.py`, `user_service.py` et `user_timer.py`.

### Changements incompatibles

- `parse_validator()` n'accepte plus de strings lambda. Seules les listes `list[str]` sont acceptées.
- `set_validators()` accepte désormais directement des callables Python en plus des listes.
- Le format de sortie de `to_bash_call_success()` et `to_bash_call_failure()` utilise `shlex.quote()` au lieu de doubles quotes manuelles.
