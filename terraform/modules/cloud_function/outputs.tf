output "function_info" {
  description = "Nombre de la Cloud Function y su región para el operador de Airflow."
  value       = "${google_cloudfunctions_function.data_processor_function.name} en ${google_cloudfunctions_function.data_processor_function.region}"
}