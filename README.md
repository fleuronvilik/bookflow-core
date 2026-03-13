README.en.md

# Bookflow

Bookflow models the core domain of a book consignment distribution system.

It explores how delivery requests, sales reports, and business rules interact in a small backend system.

The project focuses on **domain modeling**, **scenario execution**, and **policy enforcement**, rather than on building a full production application.

---

## Core Concepts

Bookflow models the following systems:

| System | Type | Role |
|------|------|------|
| `DeliveryRequest` | Workflow | Lifecycle of a book delivery request |
| `SalesReport` | Entity | Sales report submitted by a partner |
| `ReportRequired` | Policy | Ensures a report is submitted after delivery |
| `ActiveRequestExists` | Policy | Prevents multiple active delivery requests |
| `Audit` | Cross-cutting | Records system events |
| `ProjectionStock` | Projection | Computes stock from deliveries and sales |

---

## Use Cases

Bookflow currently supports these use cases:

`CreateDR` · `SubmitDR` · `ApproveDR` · `RejectDR` · `DeliverDR` · `SubmitSR` · `VoidSR` · `GetDR` · `GetSR`

---

## Running a Scenario

Scenarios simulate interactions between partners and administrators.

Example:

```bash
python run_scenario.py -p luigi dr_happy_path
```

Other examples:

```bash
python run_scenario.py -p mario single_active_dr_constraint
python run_scenario.py -p peach sales_report_required_between_deliveries
python run_scenario.py -p yoshi sales_report_void_updates_stock
```

Scenarios are located in the `scenarios/` directory.

## Example scenario

```
P create items=b1*2 -> dr1
P submit dr=$dr1
A approve dr=$dr1
A deliver dr=$dr1

P report items=b1*2 -> sr1
show sr=$sr1
stock partner=P
```

## Running Tests

Create a virtual environment and run the tests:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Stack

Python · Pytest · SQLite · sans framework

## Project Scope

Bookflow intentionally focuses on a limited domain.

Included:

- Delivery request lifecycle
- Sales reports
- Business policies
- Stock projections
- Scenario execution

Out of scope:
- revenue sharing
- book returns
- full API layer
- production infrastructure

## Purpose

Bookflow is a learning project exploring backend system modeling through a small, self-contained domain.

It demonstrates how domain concepts, policies, and projections can be implemented in a minimal Python backend.