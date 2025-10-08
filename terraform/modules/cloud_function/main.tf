# 1. Bucket temporal para el código (Staging)
resource "google_storage_bucket" "source_bucket" {
  name          = "${var.project_id}-source" 
  location      = var.region
  force_destroy = true 
}

# 2. Compresión y Subida del código
data "archive_file" "source_zip" {
  type        = "zip"
  source_dir  = var.source_path
  output_path = "function_code.zip"
}

resource "google_storage_bucket_object" "archive" {
  name   = "source-${data.archive_file.source_zip.output_md5}.zip"
  bucket = google_storage_bucket.source_bucket.name
  source = data.archive_file.source_zip.output_path 
  depends_on = [google_storage_bucket.source_bucket]
}

# 3. Definición de la Cloud Function
resource "google_cloudfunctions_function" "data_processor_function" {
  name                  = var.function_name
  runtime               = "python310" 
  entry_point           = var.function_entry_point
  trigger_http          = true 
  available_memory_mb   = 256
  
  source_archive_bucket = google_storage_bucket.source_bucket.name
  source_archive_object = google_storage_bucket_object.archive.name
  
  depends_on = [google_storage_bucket_object.archive]
}