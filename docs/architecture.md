# Initial architecture

ADORA-AEGIS is organized as independently owned modules. The initial
integration boundary is a JSON sensor record and a small HTTP API. The folders
are intentionally separated so six contributors can build and test modules
without coupling implementation details.

```text
Synthetic fixtures
       |
       v
Data engine ---> Backend API ---> Frontend
       |                |
       v                +-------> Digital twin
    ML engine ---> AI assistant / explanations
```

The arrows show planned data flow, not implemented services. At this stage the
backend provides only `GET /health`; no modules exchange live data.

## Module responsibilities

- **Data engine:** Synthetic generation, input validation, and preprocessing.
- **Backend:** HTTP interface, request/response validation, and future
  integration points.
- **ML engine:** Model experiments and evaluation; no operational decisions.
- **AI assistant:** Explanations and safety boundaries for prototype outputs.
- **Frontend:** User interaction and presentation through documented APIs.
- **Digital twin:** Visualization of data supplied through shared interfaces.

The shared record format is described in
[`data-schema.md`](./data-schema.md), and the current API surface in
[`api-contracts.md`](./api-contracts.md). Agree on contract changes before
integrating work across module owners. Keep generated data identifiable as
synthetic and avoid committing secrets or real personal health data.
