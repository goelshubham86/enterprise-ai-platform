# ─── Required ─────────────────────────────────────────────────────────────────


variable "project_id" {
  description = "GCP project ID in which all resources are created."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be 6-30 lowercase letters, numbers, or hyphens, starting with a letter."
  }
}

# ─── Regional ─────────────────────────────────────────────────────────────────

variable "region" {
  description = "Primary GCP region for all resources."
  type        = string
  default     = "us-central1"

  validation {
    condition = contains([
      "us-central1", "us-east1", "us-east4", "us-west1", "us-west2",
      "europe-west1", "europe-west2", "europe-west3", "europe-west4",
      "asia-east1", "asia-northeast1", "asia-southeast1",
    ], var.region)
    error_message = "region must be a supported GCP region."
  }
}

# ─── Phase 2: IAM + CORS ──────────────────────────────────────────────────────

variable "backend_sa_email" {
  description = <<-EOT
    Email of the Cloud Run backend service account.
    Granted roles/storage.objectAdmin on document and artifact buckets.
    Set to null to skip IAM binding (safe before the SA is created in Phase 3).
  EOT
  type        = string
  default     = null
}

variable "frontend_origin" {
  description = <<-EOT
    Frontend origin URL for CORS on the documents bucket
    (e.g. https://enterprise-ai-frontend-abc123-uc.a.run.app).
    Required only when the browser uploads directly to GCS.
    Set to null to disable CORS.
  EOT
  type        = string
  default     = null
}
