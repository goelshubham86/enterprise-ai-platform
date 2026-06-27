variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "Primary GCP region for all resources."
  type        = string
  default     = "us-central1"
}

variable "backend_sa_email" {
  description = <<-EOT
    Email of the Cloud Run backend service account.
    Granted roles/storage.objectAdmin on all document buckets.
    Leave empty to skip IAM binding (useful before the SA exists).
  EOT
  type    = string
  default = ""
}

variable "frontend_origin" {
  description = <<-EOT
    Frontend origin URL for CORS (e.g. https://my-app-abc123-uc.a.run.app).
    Required only if the browser uploads directly to GCS.
    Leave empty to disable CORS on the bucket.
  EOT
  type    = string
  default = ""
}

variable "backend_image" {
  description = "Backend Docker image URI (Artifact Registry). Used by Cloud Run module (Phase 3)."
  type        = string
  default     = ""
}

variable "frontend_image" {
  description = "Frontend Docker image URI (Artifact Registry). Used by Cloud Run module (Phase 3)."
  type        = string
  default     = ""
}
