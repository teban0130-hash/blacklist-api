# API de lista negra de emails

API REST en Flask para administrar la lista negra global de emails de la organización.
Pensada para desplegarse en AWS Elastic Beanstalk (Python en Amazon Linux 2023).

## Endpoints

Todos requieren el header `Authorization: Bearer <AUTH_TOKEN>`.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/blacklists` | Agrega un email a la lista negra |
| GET | `/blacklists/<email>` | Indica si el email está en la lista negra y el motivo |
| GET | `/` | Health check para Beanstalk (sin token) |

### POST /blacklists

```json
{
  "email": "usuario@ejemplo.com",
  "app_uuid": "6f1c2a8e-3b7d-4c55-9a0e-1f2b3c4d5e6f",
  "blocked_reason": "Fraude"
}
```

Respuestas: `201` creado, `400` datos inválidos, `401` token inválido, `409` el email ya existe.
Además del cuerpo, se guardan la IP de origen de la petición y la fecha y hora.

### GET /blacklists/&lt;email&gt;

```json
{ "is_blacklisted": true, "blocked_reason": "Fraude" }
```

## Variables de entorno

| Variable | Uso | Valor por defecto |
|---|---|---|
| `AUTH_TOKEN` | Token estático para el Bearer | `token-local-desarrollo` |
| `RDS_HOSTNAME`, `RDS_PORT`, `RDS_DB_NAME`, `RDS_USERNAME`, `RDS_PASSWORD` | PostgreSQL en RDS (Beanstalk las define si la base está asociada al entorno) | — |
| `DATABASE_URL` | Cadena de conexión alternativa si no hay variables `RDS_*` | `sqlite:///blacklist.db` |

## Ejecución local

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt pytest
pytest
python application.py          # http://localhost:5000
```

```bash
curl -X POST http://localhost:5000/blacklists \
  -H "Authorization: Bearer token-local-desarrollo" \
  -H "Content-Type: application/json" \
  -d '{"email":"usuario@ejemplo.com","app_uuid":"6f1c2a8e-3b7d-4c55-9a0e-1f2b3c4d5e6f","blocked_reason":"Fraude"}'

curl http://localhost:5000/blacklists/usuario@ejemplo.com \
  -H "Authorization: Bearer token-local-desarrollo"
```

## Despliegue en Elastic Beanstalk

1. Comprimir `.ebextensions/`, `application.py`, `models.py` y `requirements.txt` en la raíz de un `.zip`.
2. En el entorno, definir `AUTH_TOKEN` en *Configuration → Updates, monitoring and logging → Environment properties*.
3. Para persistencia real, asociar una base PostgreSQL de RDS. Sin ella se usa SQLite dentro de la instancia y los datos se pierden al reemplazarla.

### Con CloudFormation

`blacklist-stack.yaml` crea todo lo anterior: rol IAM, PostgreSQL en RDS (credenciales en Secrets Manager), grupos de seguridad, aplicación, versión y entorno de Beanstalk con las variables de entorno ya configuradas.

Primero se crea el bucket con `s3-bucket.yaml` (una sola vez) y se sube el zip:

```bash
aws cloudformation deploy --stack-name blacklist-bucket --template-file s3-bucket.yaml

tar -a -c -f app.zip .ebextensions application.py models.py requirements.txt
aws s3 cp app.zip s3://cursodevopsuniandes-equipo-devops-students/app.zip

aws cloudformation deploy \
  --stack-name blacklist-api \
  --template-file blacklist-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      VpcId=<vpc-id> \
      SubnetIds=<subnet-a>,<subnet-b> \
      AuthToken=<token-de-al-menos-16-caracteres>
```

Para una versión nueva del código, sube el zip con otro nombre (por ejemplo `app-v2.zip`) y repite el `deploy` agregando `SourceBundleKey=app-v2.zip`.
