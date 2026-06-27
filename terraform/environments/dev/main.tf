/*
  Environment: dev
  ----------------
  Instantiates all platform infrastructure modules for the dev environment.
  Add or uncomment modules as each phase is implemented.

  State backend: GCS bucket 'enterprise-ai-tfstate-dev'
  (Create this bucket manually once before first `terraform init`)
*/

terraform {
  required_version = ">= 1.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    bucket = "enterprise-ai-tfstate-dev"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── Phase 2: Document Storage Bucket ─────────────────────────
#
# Stores uploaded PDFs before they are parsed, chunked, and embedded.
# The backend Cloud Run service account is granted objectAdmin so it
# can upload, read, and delete documents via the service layer.

module "documents_bucket" {
  source = "../../modules/cloud-storage"

  project_id = var.project_id
  name       = "documents"
  env        = "dev"
  location   = var.region

  storage_class      = "STANDARD"
  versioning_enabled = true
  force_destroy      = true   # safe for dev; always false in prod

  # Grant the backend service account full object access
  object_admins = var.backend_sa_email != "" ? [
    "serviceAccount:${var.backend_sa_email}"
  ] : []

  # Allow direct browser uploads from the dev frontend (optional)
  cors_origins = var.frontend_origin != "" ? [var.frontend_origin] : []

  labels = {
    team    = "ai-platform"
    purpose = "document-storage"
  }
}

# ─── Phase 2: Model / Embedding Artifacts Bucket ─────────────
# Uncomment when embedding artifacts need to be persisted.

# module "artifacts_bucket" {
#   source = "../../modules/cloud-storage"
#
#   project_id         = var.project_id
#   name               = "artifacts"
#   env                = "dev"
#   location           = var.region
#   versioning_enabled = true
#   force_destroy      = true
#
#   object_admins = var.backend_sa_email != "" ? [
#     "serviceAccount:${var.backend_sa_email}"
#   ] : []
# }

# ─── Future: Cloud Run, Vertex AI, Networking ─────────────────
# module "networking" { ... }
# module "cloud_run_backend" { ... }
# module "vertex_ai" { ... }
