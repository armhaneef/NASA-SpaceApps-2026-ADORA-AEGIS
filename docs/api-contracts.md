# Initial API contracts

The backend currently exposes one endpoint. Future module integrations should
be added here before implementation so independently developed clients and
services share stable request and response shapes.

## `GET /health`

Indicates whether the API process is responding. This is a service health check;
it does not indicate astronaut or system health.

**Success — `200 OK`**

```json
{
  "status": "ok"
}
```

There are no request parameters or request body. Future sensor ingestion and
module-output endpoints are not implemented yet; use the shared field and unit
conventions in [`data-schema.md`](./data-schema.md).

FastAPI's interactive development documentation is available at `/docs` while
the local server is running.
