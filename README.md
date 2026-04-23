# bank-payment-service

Repositorio de soporte para la capa de estado del flujo de pagos.

## Alcance

- Contiene utilidades Python compartidas para trabajar con Redis y el flujo de pagos.
- La infraestructura real de Redis vive en [`redis-cluster-config`](./redis-cluster-config).
- No expone catálogo ni orquesta pagos por si solo.

## Responsabilidad principal

Redis se usa para almacenar y consultar el estado de las transacciones de forma rapida mientras el flujo avanza por SQS.

## Infraestructura

Para desplegar el cluster:

```bash
cd redis-cluster-config
terraform init
terraform apply -auto-approve
```

## Archivos relevantes

- [`app/utils/redis_client.py`](./app/utils/redis_client.py)
- [`app/services/payment_service.py`](./app/services/payment_service.py)
- [`redis-cluster-config/redis.tf`](./redis-cluster-config/redis.tf)
