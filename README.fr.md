# bookflow-core

Modélisation d'un système de dépôt-vente pour la distribution de livres.

## Systèmes

| Système | Type | Rôle |
|---|---|---|
| `DeliveryRequest` | Workflow | Cycle de vie d'une demande de livraison |
| `SalesReport` | Entité | Rapport de ventes soumis par un partenaire |
| `ReportRequired` | Policy | Détermine si un rapport est obligatoire |
| `ActiveRequestExists` | Policy | Détermine si une demande est déjà en cours de traitement |
| `Audit` | Transversal | Trace les événements système |
| `ProjectionStock` | Projection | État du stock à partir des livraisons et ventes |

Pour une description détaillée de chaque bounded context — invariants, règles métier, objets clés et dépendances — voir **[CONTEXTS.md](CONTEXTS.md)**.

## Use cases

`CreateDR` · `SubmitDR` · `ApproveDR` · `RejectDR` · `DeliverDR` · `SubmitSR` · `VoidSR` · `GetDR` · `GetSR`

## Lancer un scénario

```bash
python run_scenario.py -p <partner-id> <scenario-path-or-name> # partner_id=luigi|mario|peach|yoshi|p1|p2
```

Quatre scénarios sont dans le dossier `scenarios/`.
1. `dr_happy_path`
2. `single_active_dr_constraint`
3. `sales_report_required_between_deliveries`
4. `sales_report_void_updates_stock`

Recommandation: expérimenter avec un partenaire par scénario.

## Lancer les tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Stack

Python · Pytest · sans framework
