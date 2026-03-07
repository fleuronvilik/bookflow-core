# Runner mini spec

Ce document doit maintenant décrire surtout le DSL et ses règles d’usage.

Le détail du moteur interne est documenté séparément dans [docs/runner.md](runner.md).

## Positionnement

Le runner exécute des scénarios texte ligne par ligne en réutilisant les use cases et queries existants.

Contraintes conservées :

- pas de framework CLI
- pas de parser complexe
- stop on first error
- commentaires `#` et lignes vides ignorés
- variables via `-> name` et `$name`
- pas de logique métier déplacée dans le runner

## DSL

Une ligne non vide est soit :

- une `command`
- une `query`

## Commands

Acteurs :

- `P` : partner
- `A` : admin

Commandes supportées :

- `create`
- `submit`
- `approve`
- `deliver`
- `report`
- `void`

Formes supportées :

```text
P create items=b1*1;b2*1 -> dr1
P submit dr=$dr1
A approve dr=$dr1
A deliver dr=$dr1
P report items=b1*2 -> sr1
A void sr=$sr1 reason=mistake
```

Règles utiles :

- `create` attend `items=...`
- `submit` attend `dr=...`
- `approve` attend `dr=...`
- `deliver` attend `dr=...`
- `report` attend `items=...`
- `void` attend `sr=...` et `reason=...`

## Queries

Queries supportées :

- `show`
- `stock`

Formes supportées :

```text
show dr=$dr1
show sr=$sr1
show dr=$dr1 partner=P
stock partner=P
```

Règles utiles :

- `show` attend `dr=...` ou `sr=...`
- `show` tolère aujourd’hui des arguments additionnels comme `partner=P`
- `stock` attend `partner=P`
- dans l’état actuel, `stock` utilise le partner fixé par le runtime du runner

## Variables

Capture :

```text
P create items=b1*1;b2*1 -> dr1
```

Référence :

```text
P submit dr=$dr1
show dr=$dr1
```

Règles :

- `-> name` stocke l’`id` du résultat dans la table de variables du runner
- `$name` remplace une valeur d’argument par la variable correspondante
- si la variable n’existe pas, l’exécution échoue
- l’assignation est autorisée sur les commandes qui retournent un `id`
- l’assignation n’est pas autorisée sur les queries

## Items

Les items restent du texte au niveau du parsing :

```text
items=b1*2;b2*1
```

Règles :

- `;` sépare les items
- `*` sépare `book_id` et `quantity`
- la conversion en `RequestItem` ou `ReportItem` se fait dans les adaptateurs `run_*`

## Commentaires et lignes vides

Règles :

- une ligne vide est ignorée
- une ligne commençant par `#` est ignorée

Exemple :

```text
# create and submit a delivery request

P create items=b1*1;b2*1 -> dr1
P submit dr=$dr1
```

## Validation DSL

Le runner valide le contrat DSL avant résolution et dispatch.

Exemples rejetés :

```text
A submit dr=$dr1
P approve dr=$dr1
P submit items=b1*2
show
stock
```

Exemples tolérés volontairement :

```text
P submit dr=$dr1 -> submitted
A approve dr=$submitted -> approved
show dr=$dr1 partner=P
```

## Exécution

Ordre d’exécution :

1. lecture ligne par ligne
2. `parse_line`
3. validation DSL
4. `resolve_arg_variables`
5. `dispatch_parsed`
6. adaptateur `run_*`
7. appel des use cases / queries
8. stockage éventuel de l’assignation

Pour le détail du pipeline interne, voir [docs/runner.md](/home/vilfleur/python_playground/book_depot/docs/runner.md).

## Résultat d’exécution

Chaque ligne exécutée retourne un résultat minimal :

```python
{"ok": bool, "id": int | None, "msg": str}
```

Exemples :

```python
{"ok": True, "id": 1, "msg": "created dr 1"}
{"ok": True, "id": 1, "msg": "DR#1 status=DRAFT"}
{"ok": False, "id": None, "msg": "line 9: active delivery request already exists for partner p1"}
```

## Scénarios

Des scénarios DSL d’exemple existent dans [scenarios/basic.txt](scenarios/basic.txt), [scenarios/active_dr.txt](scenarios/active_dr.txt), [scenarios/report_required.txt](scenarios/report_required.txt) et [scenarios/transversal.txt](scenarios/transversal.txt).
