# SECTIONAWAREEDITOR — ÉDITEUR LIGNE-À-LIGNE PRÉSERVANT LES COMMENTAIRES
> **Date :** 2026-05-16 à 23:30
> **Complexité estimée :** Moyenne

---

## Contexte

### Problématique

`LinuxIniConfigManager.update_section()` utilise `configparser.write()` pour
persister les modifications. Cette méthode **réécrit l'intégralité du fichier**
depuis le modèle mémoire de configparser, ce qui **supprime tous les commentaires
et les lignes vides** présents dans le fichier original.

Pour des fichiers comme `/etc/dnf/dnf.conf` ou `~/.config/yt-dlp/config`, ce
comportement est inacceptable : les commentaires de l'administrateur système
documentent les choix de configuration et ne doivent pas disparaître.

De plus, `LinuxIniConfigManager` ne gère pas les fichiers **plats sans section**
(style yt-dlp : `--option`, `--sub-langs fr`), car `configparser` exige des
en-têtes `[section]`.

### Solution technique retenue

Ajouter une classe `SectionAwareEditor` dans `linux_python_utils/dotconf/line_editor.py`.

Cette classe opère **ligne-à-ligne** : elle lit le fichier comme une liste de
strings, détecte les sections `[nom]` par regex, insère ou décommente uniquement
les lignes nécessaires, et réécrit le fichier uniquement si une modification a
eu lieu. Les commentaires, les lignes vides et le formatage sont préservés.

Elle complète (sans remplacer) `LinuxIniConfigManager`, qui reste pertinent
pour les usages nécessitant une réécriture complète maîtrisée.

### Alternatives écartées

- **Modifier `LinuxIniConfigManager`** : casserait l'API existante et les tests
  actuels. `configparser` ne peut pas préserver les commentaires par conception.
- **Utiliser `configupdater` (bibliothèque tierce)** : ajout de dépendance
  externe non souhaité ; la logique nécessaire est suffisamment simple pour
  être implémentée nativement.

### Fichiers impactés

- `src/linux_python_utils/dotconf/line_editor.py` — nouvelle classe (à créer)
- `src/linux_python_utils/dotconf/__init__.py` — ajout de l'export
- `tests/test_dotconf_line_editor.py` — nouveaux tests unitaires

**Downstream (hors périmètre de ce TODO) :**
- `config-file-manager/src/config_manager/file_editor.py` — pourra déléguer à
  `SectionAwareEditor` au lieu de réimplémenter la logique ligne-à-ligne

---

## Évolutions à mettre en place (Détail Junior)

### `src/linux_python_utils/dotconf/line_editor.py`

#### Imports à ajouter

```python
# stdlib
import re
from pathlib import Path
```

#### Signature complète

```python
class SectionAwareEditor:
    """Éditeur ligne-à-ligne pour fichiers de configuration plats ou INI.

    Préserve les commentaires, les lignes vides et le formatage existant.
    Modifie uniquement les lignes strictement nécessaires.

    Supporte :
    - Les fichiers plats sans section (style yt-dlp : --option)
    - Les fichiers INI avec sections (style dnf.conf : [main])
    - La détection et le décommentage de lignes commentées (#option)
    """

    _SECTION_RE: re.Pattern[str] = re.compile(r"^\[([^\]]+)\]")
    _COMMENT_PREFIXES: tuple[str, ...] = ("#", ";")

    def __init__(self, file_path: Path) -> None:
        """Initialise l'éditeur avec le chemin du fichier cible.

        Args:
            file_path: Chemin absolu du fichier à modifier.
                       Le fichier peut ne pas exister (sera créé si nécessaire).
        """
        self._path = file_path

    def is_block_present(
        self,
        content: str,
        section: str | None = None,
    ) -> bool:
        """Vérifie si toutes les lignes du bloc sont actives dans le fichier.

        Args:
            content: Contenu du bloc (peut être multilignes).
            section: Nom de la section INI, ou None pour les fichiers plats.

        Returns:
            True si toutes les lignes du bloc sont présentes et non commentées.
            False si le fichier n'existe pas ou si une ligne manque.
        """

    def is_block_commented(
        self,
        content: str,
        section: str | None = None,
    ) -> bool:
        """Vérifie si les lignes du bloc sont commentées dans le fichier.

        Args:
            content: Contenu du bloc (peut être multilignes).
            section: Nom de la section INI, ou None pour les fichiers plats.

        Returns:
            True si toutes les lignes du bloc existent sous forme commentée.
            False si le fichier n'existe pas ou si les lignes sont absentes.
        """

    def ensure_block(
        self,
        content: str,
        section: str | None = None,
        comment: str = "",
    ) -> bool:
        """Assure la présence du bloc dans le fichier avec préservation des commentaires.

        Comportement selon l'état du fichier :
        1. Fichier absent → crée le dossier parent, crée le fichier, insère le bloc.
        2. Bloc actif → aucune modification (retourne False).
        3. Bloc commenté → décommente les lignes concernées (retourne True).
        4. Bloc absent, section existante → insère avant la section suivante.
        5. Bloc absent, section manquante → ajoute [section] en fin de fichier.
        6. Section None, bloc absent → appende en fin de fichier.

        Args:
            content: Contenu du bloc (une ou plusieurs lignes).
            section: Nom de la section INI cible. None pour les fichiers plats.
            comment: Ligne de commentaire à ajouter avant le bloc (ex: "# Titre").

        Returns:
            True si le fichier a été modifié, False si aucun changement nécessaire.
        """

    def list_sections(self) -> list[str]:
        """Retourne la liste des sections INI présentes dans le fichier.

        Returns:
            Liste des noms de sections dans leur ordre d'apparition.
            Liste vide si le fichier n'existe pas ou ne contient pas de sections.
        """

    def _read_lines(self) -> list[str]:
        """Lit le fichier et retourne ses lignes avec fins de ligne.

        Returns:
            Liste de lignes (avec \\n), ou liste vide si le fichier n'existe pas.
        """

    def _write_lines(self, lines: list[str]) -> None:
        """Écrit les lignes dans le fichier, en créant le dossier parent si nécessaire.

        Args:
            lines: Lignes à écrire (avec fins de ligne).
        """

    def _find_section_range(
        self,
        lines: list[str],
        section: str,
    ) -> tuple[int, int]:
        """Localise une section INI et retourne ses indices de début et fin.

        Args:
            lines: Lignes du fichier.
            section: Nom de la section à localiser.

        Returns:
            Tuple (start, end) où start est l'index de la ligne [section]
            et end est l'index de la première ligne de la section suivante
            (ou len(lines) si c'est la dernière section).
            Retourne (-1, -1) si la section n'existe pas.
        """

    def _is_active_line(self, line: str, target: str) -> bool:
        """Vérifie si une ligne correspond à la cible (active, non commentée).

        Args:
            line: Ligne du fichier (avec fin de ligne possible).
            target: Ligne cible à rechercher (stripée).

        Returns:
            True si line.strip() == target.
        """

    def _is_commented_line(self, line: str, target: str) -> bool:
        """Vérifie si une ligne est la cible commentée.

        Args:
            line: Ligne du fichier.
            target: Ligne cible à rechercher (stripée).

        Returns:
            True si la ligne, une fois dépouillée de son préfixe de commentaire,
            correspond à target.
        """

    def _uncomment_line(self, line: str) -> str:
        """Supprime le premier préfixe de commentaire (#, ;) et l'espace suivant.

        Args:
            line: Ligne commentée.

        Returns:
            Ligne décommentée, avec préservation de l'indentation restante.
        """

    def _format_block(self, content: str, comment: str) -> list[str]:
        """Formate un bloc de contenu avec commentaire optionnel.

        Args:
            content: Contenu du bloc (peut être multilignes).
            comment: Ligne de commentaire (vide si aucun).

        Returns:
            Liste de lignes formatées prêtes à être insérées (avec \\n).
        """
```

#### Logique détaillée

**`is_block_present(content, section)`**
1. Lire les lignes via `_read_lines()`. Si vide → `False`.
2. Extraire les lignes du bloc : `[ln.strip() for ln in content.splitlines() if ln.strip()]`.
3. Si `section` est None → chercher dans toutes les lignes du fichier.
4. Si `section` est fournie → récupérer la plage via `_find_section_range()`. Si (-1, -1) → `False`. Chercher uniquement dans `lines[start:end]`.
5. Pour chaque ligne du bloc, vérifier qu'au moins une ligne du fichier la satisfait via `_is_active_line()`.
6. Retourner `True` seulement si **toutes** les lignes du bloc sont actives.

**`is_block_commented(content, section)`**
1. Lire les lignes. Si vide → `False`.
2. Même découpage section que `is_block_present`.
3. Pour chaque ligne du bloc, vérifier via `_is_commented_line()`.
4. Retourner `True` seulement si **toutes** les lignes sont commentées.

**`ensure_block(content, section, comment)`**
1. Si `is_block_present(content, section)` → retourner `False` directement.
2. Lire les lignes (`_read_lines()`).
3. Si les lignes sont commentées (`is_block_commented`) :
   - Parcourir les lignes dans la plage section.
   - Remplacer chaque ligne commentée correspondante par `_uncomment_line(ligne)`.
   - Écrire via `_write_lines()`. Retourner `True`.
4. Sinon, construire le bloc à insérer via `_format_block(content, comment)`.
5. Si `section` est None : appender le bloc à la fin (`lines.extend(bloc)`).
6. Si `section` fournie :
   - Appeler `_find_section_range()`.
   - Si (-1, -1) : ajouter `\n[section]\n` + bloc en fin de fichier.
   - Sinon : insérer le bloc à l'index `end` (fin de la section, avant la suivante).
7. Écrire et retourner `True`.

**`_find_section_range(lines, section)`**
1. Chercher la ligne `[section]` avec `_SECTION_RE`.
2. Si trouvée à l'index `i` : `start = i`.
3. Chercher la prochaine ligne correspondant à `_SECTION_RE` à partir de `i+1` → `end`.
4. Si aucune section suivante trouvée : `end = len(lines)`.
5. Retourner `(start, end)`.

**`_uncomment_line(line)`**
1. Stripper la ligne.
2. Pour chaque préfixe dans `_COMMENT_PREFIXES` : si la ligne commence par ce préfixe, le retirer.
3. Retirer l'espace immédiatement après le préfixe si présent.
4. Retourner la ligne avec `\n` final.

**`_format_block(content, comment)`**
1. Résultat = liste vide.
2. Si `comment` non vide : ajouter `comment + "\n"`.
3. Pour chaque ligne de `content.splitlines()` : ajouter `ligne + "\n"`.
4. Ajouter une ligne vide finale `"\n"` pour la lisibilité.
5. Retourner la liste.

#### Gestion d'erreurs

| Cas | Condition | Action |
|---|---|---|
| Fichier absent | `_read_lines()` appelé | Retourner `[]` (pas d'exception) |
| Dossier parent absent | `_write_lines()` → `FileNotFoundError` | `parent.mkdir(parents=True, exist_ok=True)` avant `open()` |
| Fichier illisible | `PermissionError` à la lecture | Propager l'exception (pas de swallowing) |
| Section vide | `content = ""` | `ensure_block` retourne `False` immédiatement |

#### Conventions PEP

- [x] PEP 8  — Imports ordonnés : stdlib uniquement (`re`, `Path`)
- [x] PEP 8  — Nommage : `snake_case`, constantes de classe en `UPPER_CASE`
- [x] PEP 8  — Lignes ≤ 79 caractères
- [x] PEP 257 — Docstring Google Style sur chaque méthode
- [x] PEP 484 — Type hints complets (`str | None`, `tuple[int, int]`, `list[str]`)
- [x] PEP 20  — Méthodes courtes, nommage expressif ; pas de logique imbriquée inutile

#### Principes SOLID

| Principe | Question clé | Statut |
|---|---|---|
| **S** Single Responsibility | `SectionAwareEditor` : édition ligne-à-ligne uniquement. Pas de logging, pas de validation, pas d'audit. | ✅ |
| **O** Open/Closed | Les comportements `is_block_present` / `is_block_commented` sont des méthodes publiques surchargeables sans modifier `ensure_block`. | ✅ |
| **L** Liskov Substitution | Pas de sous-classes prévues ; l'interface est self-contained. | N/A |
| **I** Interface Segregation | L'API publique est minimale : 3 méthodes publiques + `list_sections`. Les helpers sont privés (`_`). | ✅ |
| **D** Dependency Inversion | `SectionAwareEditor` ne dépend d'aucune abstraction interne de `linux_python_utils`. Pas d'injection de dépendance requise (stdlib uniquement). | ✅ |

### `src/linux_python_utils/dotconf/__init__.py`

#### Modification à apporter

Ajouter l'import et l'export de `SectionAwareEditor` :

```python
from linux_python_utils.dotconf.line_editor import SectionAwareEditor

__all__ = [
    # ... existants ...
    "SectionAwareEditor",
]
```

---

## Checklist d'implémentation

### Code

- [ ] Créer `src/linux_python_utils/dotconf/line_editor.py` — classe `SectionAwareEditor`
- [ ] Mettre à jour `src/linux_python_utils/dotconf/__init__.py` — ajouter export

### Tests (pytest)

- [ ] Créer `tests/test_dotconf_line_editor.py`

Tests à implémenter :

```
TestIsBlockPresent
  test_retourne_false_si_fichier_absent
  test_retourne_true_si_bloc_actif_sans_section
  test_retourne_true_si_bloc_actif_dans_section
  test_retourne_false_si_bloc_absent
  test_retourne_false_si_bloc_commente

TestIsBlockCommented
  test_retourne_true_si_bloc_commente_sans_section
  test_retourne_true_si_bloc_commente_dans_section
  test_retourne_false_si_bloc_actif
  test_retourne_false_si_fichier_absent

TestEnsureBlock
  test_cree_fichier_si_absent_sans_section
  test_cree_fichier_si_absent_avec_section
  test_retourne_false_si_bloc_deja_present
  test_decommente_bloc_commente
  test_insere_dans_section_existante
  test_cree_section_si_absente
  test_appende_sans_section
  test_inclut_commentaire_avant_bloc
  test_cree_dossier_parent_si_absent
  test_bloc_multiligne_detecte_present
  test_bloc_multiligne_insere_complet

TestListSections
  test_retourne_sections_dans_ordre
  test_retourne_liste_vide_si_fichier_absent
  test_retourne_liste_vide_si_pas_de_sections
```

- [ ] `pytest tests/test_dotconf_line_editor.py -v --cov=linux_python_utils.dotconf.line_editor --cov-fail-under=90`

### Documentation

- [ ] Docstrings PEP 257 sur toutes les méthodes (déjà inclus dans les signatures ci-dessus)
- [ ] Mettre à jour la docstring du module `dotconf/__init__.py` pour mentionner `SectionAwareEditor`

---

## Points d'attention

- **Fichiers plats sans section** : les lignes comme `--rm-cache-dir` n'ont pas de `=`.
  `_is_active_line` doit comparer `line.strip() == target` sans parsing clé/valeur.
- **Décommentage partiel** : si un bloc multilignes est partiellement commenté,
  `is_block_commented` retourne `False`. `ensure_block` traitera ce cas comme
  une insertion normale (le bloc partiellement commenté sera laissé tel quel
  et les lignes manquantes seront ajoutées).
- **Préservation du `\n` final** : `_write_lines()` ne doit pas ajouter de `\n`
  supplémentaire si le fichier se termine déjà par une ligne vide.
- **`configparser` forçage minuscules** : `SectionAwareEditor` est case-sensitive
  pour les noms de sections et les valeurs, contrairement à `LinuxIniConfigManager`.

---

## ⏸ Validation requise

**Ce plan doit être validé explicitement avant toute modification du code source.**
Répondre **"OK"** pour démarrer l'implémentation.
