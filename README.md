# 🚀 Proyecto ETL con Airflow, GCP, Terraform, DBT y Secret Manager

## 🧠 Descripción general

Este proyecto implementa una **ETL moderna en Google Cloud Platform (GCP)** que extrae datos de una **API pública (Rick & Morty)**, los transforma y los carga en **BigQuery** siguiendo el **modelo Medallion (bronze → silver → gold)**.  

El flujo combina diversas herramientas de ingeniería de datos:  

- **Airflow** (orquestación)  
- **Cloud Function** (procesamiento en GCS)  
- **BigQuery** (almacenamiento estructurado)  
- **Terraform** (infraestructura como código)  
- **DBT** (transformaciones SQL)  
- **Secret Manager** (manejo seguro de credenciales)  
- **Docker + WSL** (entorno de desarrollo local)

---

## 🏗️ Arquitectura general

```
                +------------------+
                |    Rick & Morty  |
                |       API        |
                +--------+---------+
                         |
                         v
                 +-------+--------+
                 |   GCS Bucket   |
                 |     raw/       |
                 +-------+--------+
                         |
                         | (disparo manual o programado)
                         v
                 +-------+--------+
                 |  Cloud Function|
                 |  (Python / BQ) |
                 +-------+--------+
                         |
                +--------+--------+
                |   GCS Bucket    |
                |   processed/    |
                +--------+--------+
                         |
                         v
              +----------+-----------+
              |     BigQuery          |
              | bronze → silver → gold|
              +----------+-----------+
                         |
                         v
                +--------+--------+
                |   GCS Bucket    |
                |   historic/     |
                +-----------------+

```

📁 Además, existe una carpeta `schema/` en el bucket donde se almacena el **esquema JSON** de la tabla bronze de BigQuery, lo que permite mantener control de versiones sobre la estructura de los datos.

---

## 🧩 Componentes principales

### 🌀 1. Airflow (Docker + WSL)
- Configurado mediante `docker-compose.yaml`.  
- Orquesta los DAGs que coordinan el flujo de extracción, carga y verificación. 
- Usa un operador personalizado que consume la api y de inmediato almacena en GCS. 
- El DAG principal es `dag_rick_and_morty_with_operator.py`, que:
  1. Llama a la API pública y almacena los datos en un archivo JSON.   
  2. Envía el archivo JSON al bucket `raw/`.  
  3. Llama a la Cloud Function encargada de procesarlo y generar el archivo Parquet.  
  4. Inserta los datos en BigQuery (bronze).  
  5. Mueve los datos a la carpeta `historic/`.  

### ☁️ 2. Cloud Function
- Desplegada con **Terraform** (automatización total).  
- Procesa los archivos del bucket `raw/`:  
  - Convierte JSON → Parquet.  
  - Escribe en `processed/`.  
  - Inserta datos en BigQuery.  
- Usa **Service Account** con permisos mínimos: lectura de GCS, escritura en BigQuery.

### 🗃️ 3. BigQuery (modelo Medallion)
Organiza los datasets en tres capas:

| Capa | Descripción |
|------|--------------|
| **bronze** | Datos crudos directamente del Parquet procesado por la Cloud Function. |
| **silver** | Limpieza, tipificación y enriquecimiento con DBT. |
| **gold** | Agregaciones o vistas finales para análisis y dashboards. |

### 🧱 4. Terraform
- Despliega la **Cloud Function**, las **Service Accounts** y los permisos IAM necesarios.  
- Facilita la recreación del entorno sin pasos manuales.

### 🧮 5. DBT
- Se usa para aplicar transformaciones SQL dentro de BigQuery.  
- Configurado con `profiles.yml` y modelo Medallion.  
- Ejecutado manualmente o mediante Airflow.

### 🔒 6. Secret Manager
- Gestiona variables sensibles (claves, IDs de proyecto, tokens API).  
- Evita incluir credenciales en el código fuente o archivos `.env`.

### 🐳 7. WSL + Docker
- Entorno local reproducible para ejecutar Airflow y DBT.  
- Permite simular el flujo completo antes de desplegar en GCP.

---

## 📂 Estructura del repositorio

```
data_engineering_project/
│
├── airflow/
│   ├── docker-compose.yaml
│   ├── config/airflow.cfg
│   ├── dags/
│   │   ├── dag_rick_and_morty_with_operator.py
│   │   ├── dag_prueba.py
│   │   └── __pycache__/
│   └── logs/
│
├── terraform/
│   ├── cloud_functions_source/
│   │   ├── main.py
│   │   ├── requirements.txt
│   ├── modules/
│       ├── cloud_function/
│       │   ├── main.py
│       |   |── variables.tf
│       |   └── outputs.tf
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
│
├── dbt/
│   ├── dbt_data_engineering_project/
│   |  ├── macros/
│   |  ├── models/
|   |      ├──bronze
|   |      └──silver
│   |      ├──gold
│   └── dbt_project.yml
│
└── README.md   ← este archivo
```

---

## ⚙️ Configuración inicial

1. **Clonar el repositorio**  
   ```bash
   git clone https://github.com/tu_usuario/data_engineering_project.git
   cd data_engineering_project
   ```

2. **Configurar .yml airflow**  
Airflow se configura directamente en el archivo `docker-compose.yml`.  
Allí se definen las variables necesarias para la conexión con GCP y el uso de **Secret Manager**.  

Ejemplo de variables clave:

```yaml
environment:
  AIRFLOW__API_AUTH__JWT_SECRET: "supersecretjwt"
  GOOGLE_APPLICATION_CREDENTIALS: "/opt/keys/gcp_service_account.json"
  AIRFLOW__SECRETS__BACKEND: "airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend"
  AIRFLOW__SECRETS__BACKEND_KWARGS: '{"connections_prefix": "airflow-connections", "variables_prefix": "airflow-variables", "project_id": "data-engineering-dev-464423"}'
```

Además, se monta la clave del **Service Account** de GCP con el siguiente volumen:
```yaml
volumes:
  - ${AIRFLOW_PROJ_DIR:-.}/../keys/gcp_service_account.json:/opt/keys/gcp_service_account.json
```

Esto permite que Airflow acceda a los secretos y credenciales almacenados en GCP sin necesidad de exponerlas en texto plano ni usar archivos `.env`.

---

3. **Levantar Airflow en WSL/Docker**  
   ```bash
   cd airflow
   docker-compose up -d
   ```

4. **Desplegar Cloud Function con Terraform**
   ```bash
   cd cloud_function/terraform
   terraform init
   terraform apply
   ```

5. **Configurar DBT**
   ```bash
   cd dbt
   dbt run
   ```

---

## ▶️ Ejecución del flujo ETL

1. Airflow ejecuta el DAG `dag_rick_and_morty_with_operator.py`.  
2. Se obtiene el JSON desde la API y se guarda en `raw/`.  
3. La Cloud Function procesa el archivo y genera un Parquet en `processed/`.  
4. Los datos se cargan en BigQuery (tabla bronze).  
5. DBT transforma los datos hasta la capa gold.  
6. El archivo original pasa a `historic/`.  

---

## 🔍 Monitoreo y mantenimiento

- **Airflow UI:** Verifica la ejecución y logs de tareas.  
- **GCP Console:** Monitorea la Cloud Function y BigQuery.  
- **DBT logs:** Para transformaciones SQL.  
- **Secret Manager:** Revisa versiones de credenciales.

---

## 💡 Buenas prácticas aplicadas

- Infraestructura como código (Terraform).  
- Separación de capas en BigQuery (modelo Medallion).  
- Seguridad con Secret Manager.  
- Formato **Parquet** para eficiencia y bajo costo.  
- Procesamiento **event-driven** (basado en archivos).  
- Modularidad: cada componente puede evolucionar de forma independiente.

---

## ✨ Autor

**Juan Guillermo Quintero**  
Ingeniero de Datos | Proyecto ETL con GCP, Airflow, DBT, Terraform y Secret Manager  
