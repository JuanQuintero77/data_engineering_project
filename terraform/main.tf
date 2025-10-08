# 1. Configuración de Proveedores
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.2"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 2. Habilitación de APIs
resource "google_project_service" "cf_apis" {
  for_each = toset(["cloudfunctions.googleapis.com", "cloudbuild.googleapis.com", "storage.googleapis.com"])
  service            = each.key
  disable_on_destroy = false
}

# 3. LLAMADA AL MÓDULO
module "cloud_function_deployment" {
  source                 = "./modules/cloud_function"
  # Pasamos las variables de la raíz al módulo
  project_id             = var.project_id
  region                 = var.region
  function_name          = var.function_name
  function_entry_point   = var.function_entry_point
  source_path            = "./cloud_function_source" # Ruta relativa a la carpeta del módulo
  
  depends_on             = [google_project_service.cf_apis]
}

# 4. Salida
output "cloud_function_info" {
  description = "Nombre de la Cloud Function y su región."
  value       = module.cloud_function_deployment.function_info
}