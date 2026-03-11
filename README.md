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

## Use cases

`CreateDR` · `SubmitDR` · `ApproveDR` · `RejectDR` · `DeliverDR` · `SubmitSR` · `VoidSR` · `GetDR` · `GetSR`

## Lancer un scénario

```bash
python run_scenario.py <partner-id> <scenario-path-or-name>
```

Les scénarios sont dans le dossier `scenarios/`.

## Lancer les tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Stack

Python · Pytest · sans framework
