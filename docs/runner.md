# Runner

## Pipeline

```text
line
↓
parse_line
↓
resolve_arg_variables
↓
dispatch_parsed
↓
run_*
↓
use_cases / queries
```

## Rôle de chaque étape

- `line`
  - une ligne brute du scénario DSL
- `parse_line`
  - analyse syntaxique minimale
  - ignore lignes vides et commentaires
  - produit un `ParsedLine`
- `resolve_arg_variables`
  - remplace les références `$name` dans les arguments à partir de la table de variables du runner
- `dispatch_parsed`
  - choisit l’adaptateur `run_*` à partir de `command` et du type command/query
- `run_*`
  - adapte le DSL vers les appels applicatifs
  - convertit au besoin les `items` texte en `RequestItem` ou `ReportItem`
- `use_cases / queries`
  - exécution réelle du comportement métier existant

## Intention

Le runner ne porte pas la logique métier.

Il orchestre seulement :

1. lecture de ligne
2. parsing
3. résolution des variables
4. dispatch
5. appel des use cases et queries existants

## Fichiers principaux

- [runner/parser.py](../runner/parser.py)
- [runner/validate.py](../runner/validate.py)
- [runner/dispatch.py](../runner/dispatch.py)
- [runner/engine.py](../runner/engine.py)
- [run_scenario.py](../run_scenario.py)
