# API Swagger Documentation

This `docs` folder contains Swagger/OpenAPI reference documentation for the REST API services in this repository.

## Available API docs

- `factory-app`: `docs/factory-app-swagger.md`
- `provider-app`: `docs/provider-app-swagger.md`

## Interactive Swagger UI

Each FastAPI application also exposes interactive Swagger documentation at runtime:

- `factory-app`: `http://localhost:8000/docs`
- `provider-app`: `http://localhost:8001/docs`

Use the `OpenAPI` schema endpoints if you want to generate client libraries or import the API definition into tools such as Postman.

- `factory-app`: `http://localhost:8000/openapi.json`
- `provider-app`: `http://localhost:8001/openapi.json`
