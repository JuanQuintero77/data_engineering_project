variable "project_id" {
  description = "ID del proyecto de Google Cloud."
  type        = string
}

variable "region" {
  description = "Región donde se desplegará la función."
  type        = string
}

variable "function_name" {
  description = "Nombre exacto de la Cloud Function (clave para Airflow)."
  type        = string
}

variable "function_entry_point" {
  description = "Nombre de la función en tu código (ej: 'process_json_data')."
  type        = string
}

variable "source_code_path" {
  description = "Ruta local donde se encuentra el código (ej: './cloud_function_source')."
  type        = string
}