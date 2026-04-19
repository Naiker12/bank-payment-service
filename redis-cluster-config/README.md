#  Redis Cluster Configuration

Este repositorio centraliza la infraestructura de ElastiCache (Redis) que sirve como el motor de estado en tiempo real (Real-time State Engine) para el banco digital.

##  Propósito: Base de Datos vs Redis

| Característica | Base de Datos (DynamoDB) | Redis (In-Memory) |
| :--- | :--- | :--- |
| **Uso** | Auditoría y Auditoría final | Polling de estado y Catálogo |
| **Velocidad** | Milisegundos | Microsegundos |
| **Costo** | Basado en lectura/escritura | Reservado por nodo |

##  Contenido
- `redis.tf`: Definición de recursos de AWS ElastiCache.
- `security_groups.tf`: Reglas de red para acceso seguro desde las Lambdas.

---
*Infraestructura Core de Digital Bank.*
