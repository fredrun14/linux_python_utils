# TESTS MANQUANTS — CliCommand ET CliApplication
> **Date :** 2026-05-17 à 12:00
> **Complexité estimée :** Faible

---

## Contexte

### Problématique
`tests/test_cli.py` couvre partiellement `CliCommand` et `CliApplication` :
- **`TestCliCommand`** : 2 tests — instanciation de l'ABC et lecture du `name`. Ni
  `register()` ni `execute()` ne sont vérifiés en isolation.
- **`TestCliApplication`** : 4 tests — dispatch, passage d'args, absence de commande,
  commande inconnue. Cas limites non couverts : liste vide, une seule commande, valeur
  par défaut d'un flag, vérification que `execute()` reçoit le bon `args.command`.

### Solution technique retenue
Compléter `tests/test_cli.py` avec des tests ciblés, pattern AAA, sans dépendance
externe — `monkeypatch` pour `sys.argv`, classe `ConcreteCommand` déjà présente réutilisée.
Pas de nouveau fichier : les tests s'ajoutent dans l'existant.

### Fichiers impactés
- `tests/test_cli.py` — ajout de tests dans les deux classes existantes

---

## Évolutions à mettre en place (Détail Junior)

### `tests/test_cli.py`

#### Imports à ajouter/modifier
Aucun import supplémentaire — tout est déjà importé.

#### Tests à ajouter dans `TestCliCommand`

| # | Méthode de test | Ce qu'elle vérifie |
|---|---|---|
| 1 | `test_register_enregistre_la_commande_dans_subparsers` | Après `register()`, le subparser contient bien la commande |
| 2 | `test_execute_est_appele_avec_le_namespace_correct` | `execute()` reçoit un `argparse.Namespace` |
| 3 | `test_concrete_command_sans_register_ne_peut_etre_instanciee` | ABC rejette toute sous-classe n'implémentant pas `register` |
| 4 | `test_concrete_command_sans_execute_ne_peut_etre_instanciee` | ABC rejette toute sous-classe n'implémentant pas `execute` |

**Logique détaillée :**

1. **test_register_enregistre_la_commande_dans_subparsers**
   - Arrange : créer un `ArgumentParser` + `add_subparsers()`, instancier `ConcreteCommand("sync")`
   - Act : appeler `cmd.register(subparsers)`
   - Assert : `parser.parse_args(["sync"])` ne lève pas d'exception → commande reconnue

2. **test_execute_est_appele_avec_le_namespace_correct**
   - Arrange : `ConcreteCommand`, créer un `Namespace(command="test-cmd")`
   - Act : `cmd.execute(namespace)`
   - Assert : `cmd.execute_called is True` et `cmd.last_args is namespace`

3. **test_concrete_command_sans_register_ne_peut_etre_instanciee**
   - Arrange : définir `BadCommand(CliCommand)` qui implémente `name` et `execute` mais
     pas `register`
   - Act/Assert : `pytest.raises(TypeError)` à l'instanciation

4. **test_concrete_command_sans_execute_ne_peut_etre_instanciee**
   - Arrange : définir `BadCommand(CliCommand)` qui implémente `name` et `register` mais
     pas `execute`
   - Act/Assert : `pytest.raises(TypeError)` à l'instanciation

#### Tests à ajouter dans `TestCliApplication`

| # | Méthode de test | Ce qu'elle vérifie |
|---|---|---|
| 5 | `test_run_avec_liste_vide_leve_system_exit` | `CliApplication` sans commandes → `SystemExit` |
| 6 | `test_run_avec_une_seule_commande_dispatche_correctement` | Une seule commande dans la liste |
| 7 | `test_run_flag_avec_valeur_par_defaut` | `args.flag` vaut `"default"` quand non fourni |
| 8 | `test_run_args_command_contient_le_nom_de_la_commande` | `args.command` correspond au nom de la commande exécutée |
| 9 | `test_run_toutes_les_commandes_sont_enregistrees` | Avec 3 commandes, chacune est dispatchable |

**Logique détaillée :**

5. **test_run_avec_liste_vide_leve_system_exit**
   - Arrange : `app = CliApplication("test", "desc", [])`, `monkeypatch sys.argv = ["test", "inexistant"]`
   - Act/Assert : `pytest.raises(SystemExit)`

6. **test_run_avec_une_seule_commande_dispatche_correctement**
   - Arrange : `cmd = ConcreteCommand("solo")`, `app = CliApplication(...)`, `sys.argv = ["test", "solo"]`
   - Act : `app.run()`
   - Assert : `cmd.execute_called is True`

7. **test_run_flag_avec_valeur_par_defaut**
   - Arrange : `cmd = ConcreteCommand("cmd-a")`, `sys.argv = ["test", "cmd-a"]` (pas de `--flag`)
   - Act : `app.run()`
   - Assert : `cmd.last_args.flag == "default"`

8. **test_run_args_command_contient_le_nom_de_la_commande**
   - Arrange : `cmd = ConcreteCommand("cmd-a")`, `sys.argv = ["test", "cmd-a"]`
   - Act : `app.run()`
   - Assert : `cmd.last_args.command == "cmd-a"`

9. **test_run_toutes_les_commandes_sont_enregistrees**
   - Arrange : 3 commandes (`"alpha"`, `"beta"`, `"gamma"`)
   - Act : boucle sur chaque nom, `monkeypatch sys.argv`, `app.run()`
   - Assert : seule la commande ciblée a `execute_called is True`

#### Conventions PEP
- [x] PEP 8  — Imports ordonnés : stdlib → third-party → local
- [x] PEP 8  — Nommage : `snake_case` fonctions, `PascalCase` classes
- [x] PEP 8  — Lignes ≤ 79 caractères
- [x] PEP 257 — Docstring sur chaque classe et méthode de test
- [x] PEP 484 — Type hints sur les fixtures
- [x] PEP 20  — Cas simples, pas d'abstraction prématurée

#### Principes SOLID
| Principe | Question clé | Statut |
|---|---|---|
| **S** | Tests ciblés, une assertion par test | [x] |
| **O** | `ConcreteCommand` existante réutilisée sans modification | [x] |
| **D** | Fixtures injectées via `monkeypatch` et paramètres | [x] |

---

## Checklist d'implémentation

### Tests (pytest)
- [ ] Ajouter 4 tests dans `TestCliCommand`
- [ ] Ajouter 5 tests dans `TestCliApplication`
- [ ] Exécuter `pytest tests/test_cli.py -v` → tous verts
- [ ] Vérifier couverture `cli/base.py` → ≥ 95 %

---

## Points d'attention

- `ConcreteCommand` est déjà définie en tête du fichier — ne pas la redéfinir.
- Pour les tests 3 et 4 (ABC partielle), définir les classes `Bad*` localement dans
  le corps du test (pas au niveau module) pour éviter toute pollution.
- Le test 9 (boucle sur 3 commandes) recrée l'app à chaque itération car `execute_called`
  est muable sur l'instance.

---

## ⏸ Validation requise

**Ce plan doit être validé explicitement avant toute modification du code source.**
Répondre **"OK"** pour démarrer l'implémentation.
