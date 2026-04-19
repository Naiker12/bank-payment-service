# bank-payment-service

Microservicio de pagos para Digital Bank. Gestiona el catálogo de servicios y procesa pagos mediante una cadena de Lambdas orquestada por SQS.

## 📋 Resumen de Arquitectura

Siguiendo la **Guía Definitiva de Arquitectura EDA**, este servicio se integra de la siguiente manera:

| Servicio | Rol Principal | Tecnología | Enlace con Datos |
|---|---|---|---|
| **Payment Service** | API Gateway / Orquestador | Python / Lambda | Redis (Catálogo) / DynamoDB (Pagos) |
| **Notification Service** | Procesador de Colas (Workers) | Python / Lambda | SQS (start, check, transaction) |
| **Card Transaction** | Core Bancario / Débito | Java / Spring Boot | DynamoDB (Tarjetas) |

## Arquitectura Detallada

```
POST /catalog/update → catalog_update (S3 + Redis)
GET  /catalog        → get_catalog (Redis)
POST /payment        → payment_initiator → SQS → start_payment → SQS → check_balance → SQS → transaction
GET  /payment/status/{traceId} → get_payment_status (DynamoDB)
```

## Stack

- **Runtime**: Python 3.11 (AWS Lambda)
- **Base de datos**: DynamoDB (tabla `payment`)
- **Cache**: Redis (ElastiCache) para catálogo de servicios
- **Colas**: 3 colas SQS (start-payment, check-balance, transaction)
- **Almacenamiento**: S3 para respaldo de CSVs del catálogo
- **IaC**: Terraform

## Lambdas

| Lambda | Trigger | Descripción |
|--------|---------|-------------|
| `catalog_update` | API Gateway POST | Recibe CSV, sube a S3, sincroniza Redis |
| `get_catalog` | API Gateway GET | Lee catálogo desde Redis |
| `payment_initiator` | API Gateway POST | Valida tarjeta, crea registro, inicia cadena SQS |
| `start_payment` | SQS | Confirma estado INITIAL, encola check-balance |
| `check_balance` | SQS | Verifica saldo, decide IN_PROGRESS o FAILED |
| `transaction` | SQS | Ejecuta débito vía Card Service, marca FINISH |
| `get_payment_status` | API Gateway GET | Consulta estado del pago por traceId |

## Estados del pago

`INITIAL` → `IN_PROGRESS` → `FINISH` (éxito) o `FAILED` (saldo insuficiente)

## Variables de entorno

| Lambda | Variable | Descripción |
|--------|----------|-------------|
| catalog_update | `REDIS_HOST`, `REDIS_PORT`, `CATALOG_BUCKET` | Redis + S3 |
| get_catalog | `REDIS_HOST`, `REDIS_PORT` | Redis |
| payment_initiator | `CARD_API_URL`, `START_PAYMENT_QUEUE_URL`, `PAYMENT_TABLE` | Card API + SQS + DynamoDB |
| start_payment | `CHECK_BALANCE_QUEUE_URL`, `PAYMENT_TABLE` | SQS + DynamoDB |
| check_balance | `TRANSACTION_QUEUE_URL`, `CARD_API_URL`, `PAYMENT_TABLE` | SQS + Card API + DynamoDB |
| transaction | `CARD_API_URL`, `PAYMENT_TABLE` | Card API + DynamoDB |
| get_payment_status | `PAYMENT_TABLE` | DynamoDB |

## Despliegue

```bash
cd terraform
terraform init
terraform plan
terraform apply
```
