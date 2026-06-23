# REFACTORING TEMPLATE METHOD — MODULE LOGGING
> **Date :** 2026-06-23 à 15:00
> **Complexité estimée :** Faible

---

## Contexte

### Problématique
`FileLogger` et `RotatingFileLogger` dupliquent mot pour mot 7 méthodes identiques : `_flush`, `_log`, `log_info`, `log_warning`, `log_error`, `log_success`, `log_to_file` (~40 lignes dupliquées). Toute modification de la logique de log (ex. ajouter un `log_debug`) doit être faite en double, avec risque de divergence.

### Solution technique retenue
Extraire une classe abstraite intermédiaire `_BaseFileLogger(Logger)` dans `file_logger.py` qui factorise le code commun. `FileLogger` et `RotatingFileLogger` en héritent au lieu de `Logger` directement. C'est le pattern **Template Method** : le squelette (`_log` → `flush`) est figé dans la base, seule la construction du handler varie dans les sous-classes.

Alternative écartée : créer un fichier séparé `_base_file_logger.py` — ajouterait un fichier sans gain réel, et `rotating_file_logger.py` dépend déjà de `file_logger.py` pour `_ColoredFormatter`, `_resolve_config`, etc.

### Fichiers impactés
- `src/linux_python_utils/logging/file_logger.py` — ajout de `_BaseFileLogger`, `FileLogger` en hérite
- `src/linux_python_utils/logging/rotating_file_logger.py` — `RotatingFileLogger` hérite de `_BaseFileLogger` au lieu de `Logger`
- `tests/test_logging.py` — ajout test vérifiant que `_BaseFileLogger` n'est pas instanciable + test héritage
- `Obsidian note` — mise à jour du diagramme d'architecture et de la section Design Pattern

---

## Évolutions à mettre en place (Détail Junior)

### `src/linux_python_utils/logging/file_logger.py`

#### Classe `_BaseFileLogger` à ajouter (avant `FileLogger`)

```python
class _BaseFileLogger(Logger):
    """Base commune pour les loggers avec fichier."""

    log_file: str
    logger: logging.Logger
    handler: logging.StreamHandler[Any]
```

#### Méthodes factorisées dans `_BaseFileLogger`

```python
def _flush(self) -> None:
    """Force l'écriture immédiate sur le disque."""
    self.handler.flush()

def _log(self, level: int, message: str) -> None:
    """Émet un log au niveau donné et force le flush."""
    self.logger.log(level, message)
    self._flush()

def log_info(self, message: str) -> None:
    """Log un message d'information."""
    self._log(logging.INFO, message)

def log_warning(self, message: str) -> None:
    """Log un avertissement."""
    self._log(logging.WARNING, message)

def log_error(self, message: str) -> None:
    """Log une erreur."""
    self._log(logging.ERROR, message)

def log_success(self, message: str) -> None:
    """Log un message de succès (niveau INFO avec préfixe SUCCESS).

    Args:
        message: Message de succès à enregistrer.
    """
    self._log(logging.INFO, f"SUCCESS: {message}")

def log_to_file(self, message: str) -> None:
    """Écrit directement dans le fichier via le handler existant.

    Args:
        message: Message brut à écrire dans le fichier.
    """
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    self.handler.stream.write(f"{timestamp} - {message}\n")
    self.handler.stream.flush()
```

#### Logique détaillée
1. **Insérer `_BaseFileLogger`** entre `_ColoredFormatter` et `FileLogger` dans `file_logger.py`
2. **`FileLogger`** : changer `class FileLogger(Logger)` → `class FileLogger(_BaseFileLogger)`, supprimer les 7 méthodes dupliquées (`_flush`, `_log`, `log_info`, `log_warning`, `log_error`, `log_success`, `log_to_file`)
3. **Conserver dans `FileLogger`** : `__init__`, `_ensure_log_dir`, `_make_file_handler`, `_make_console_handler` (méthodes statiques spécifiques à la création du handler fichier)

### `src/linux_python_utils/logging/rotating_file_logger.py`

#### Imports à modifier
```python
# Remplacer l'import de Logger par _BaseFileLogger
from linux_python_utils.logging.file_logger import (
    _BaseFileLogger,
    _ColoredFormatter,
    _DEFAULT_FORMAT,
    _NIVEAUX,
    _resolve_config,
)
```

#### Logique détaillée
1. **`RotatingFileLogger`** : changer `class RotatingFileLogger(Logger)` → `class RotatingFileLogger(_BaseFileLogger)`, supprimer les 7 méthodes dupliquées
2. **Retirer l'import** `from linux_python_utils.logging.base import Logger`
3. **Conserver dans `RotatingFileLogger`** : `__init__` (construction du `_SecureRotatingHandler`, `_SecureRotatingHandler` (classe privée)

### `src/linux_python_utils/logging/__init__.py`

Aucun changement — `_BaseFileLogger` est privée (préfixe `_`), pas exportée.

### `tests/test_logging.py`

#### Tests à ajouter

```python
class TestBaseFileLogger:
    """Tests pour _BaseFileLogger."""

    def test_base_file_logger_non_instanciable(self) -> None:
        """_BaseFileLogger ne peut pas être instanciée directement."""
        # _BaseFileLogger hérite de Logger (ABC) sans implémenter __init__
        # → pas de handler/logger configuré, donc inutilisable seule.
        # Ce test vérifie que l'héritage ABC est préservé.

    def test_file_logger_est_base_file_logger(self, tmp_path) -> None:
        """FileLogger est une instance de _BaseFileLogger."""

    def test_rotating_file_logger_est_base_file_logger(self, tmp_path) -> None:
        """RotatingFileLogger est une instance de _BaseFileLogger."""
```

#### Gestion d'erreurs
Aucune nouvelle gestion d'erreur — le refactoring est purement structurel.

#### Conventions PEP
- [x] PEP 8  — Imports ordonnés : stdlib → local
- [x] PEP 8  — Nommage : `_BaseFileLogger` (PascalCase, préfixe `_` = privée)
- [x] PEP 257 — Docstring Google Style sur la classe et chaque méthode
- [x] PEP 484 — Type hints complets (déjà présents, reportés depuis les classes existantes)
- [x] PEP 20  — Éliminer la duplication = "There should be one obvious way to do it"

#### Principes SOLID
| Principe | Question clé | Statut |
|---|---|---|
| **S** Single Responsibility | `_BaseFileLogger` gère uniquement la mécanique de log (flush + dispatch par niveau) | [x] |
| **O** Open/Closed | Ajout d'une classe, aucune modification de l'interface publique existante | [x] |
| **L** Liskov Substitution | `FileLogger` et `RotatingFileLogger` restent substituables partout où `Logger` est attendu | [x] |
| **I** Interface Segregation | `Logger` (4 méthodes) reste l'interface publique, `_BaseFileLogger` ajoute `log_to_file` sans polluer `Logger` | [x] |
| **D** Dependency Inversion | Les consommateurs continuent de dépendre de `Logger` (ABC), pas de `_BaseFileLogger` | [x] |

---

## Checklist d'implémentation

### Code
- [ ] Ajouter `_BaseFileLogger` dans `file_logger.py`
- [ ] `FileLogger` hérite de `_BaseFileLogger`, supprimer les 7 méthodes dupliquées
- [ ] `RotatingFileLogger` hérite de `_BaseFileLogger`, supprimer les 7 méthodes dupliquées
- [ ] Mettre à jour les imports dans `rotating_file_logger.py`

### Tests (pytest)
- [ ] Ajouter `TestBaseFileLogger` dans `test_logging.py`
- [ ] Exécuter `pytest tests/test_logging.py -v` — tous les tests existants doivent passer
- [ ] `pytest tests/test_logging.py --cov=src/linux_python_utils/logging --cov-report=term-missing`

### Documentation
- [ ] Mettre à jour la note Obsidian `linux-python-utils – Module logging.md` (diagramme d'architecture + section Design Pattern)

---

## Points d'attention

- **Aucun breaking change d'API publique** — `_BaseFileLogger` est privée, les exports dans `__init__.py` ne changent pas.
- **`log_to_file()` n'est pas dans l'ABC `Logger`** — c'est une méthode spécifique aux loggers fichier. La factoriser dans `_BaseFileLogger` est cohérent car seuls les loggers fichier l'implémentent.
- **L'héritage `Logger` → `_BaseFileLogger` → `FileLogger`/`RotatingFileLogger`** est vérifié par les tests existants `isinstance(logger, Logger)` — ils passeront sans modification grâce à la transitivité de l'héritage.
- **`rotating_file_logger.py` importait déjà depuis `file_logger.py`** — ajouter `_BaseFileLogger` à cet import ne crée pas de couplage nouveau.

---

## ⏸ Validation requise

**Ce plan doit être validé explicitement avant toute modification du code source.**
Répondre **"OK"** pour démarrer l'implémentation.
