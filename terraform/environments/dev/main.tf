# ─────────────────────────────────────────────────────────────────────────────
# main.tf — dev environment
#
# Instantiates platform infrastructure modules.
# Add or uncomment modules as each phase is implemented.
#
# Provider config  → providers.tf
# Version pins     → versions.tf
# Shared locals    → locals.tf
# Input variables  → variables.tf
# Outputs          → outputs.tf
# ─────────────────────────────────────────────────────────────────────────────

# ─── Phase 2: Document Storage Bucket ─────────────────────────────────────────
#
# Stores uploaded PDFs before they are parsed, chunked, and embedded.
# The backend Cloud Run service account is granted objectAdmin so it can
# upload, read, and delete documents via the storage service layer.

module "documents_bucket" {
  source = "../../modules/cloud-storage"

  project_id = var.project_id
  name       = "documents"
  env        = local.env
  location   = var.region

  storage_class      = "STANDARD"
  versioning_enabled = true
  force_destroy      = true # safe for dev; always false in staging and prod

  # Grant the default Cloud Run compute service account object-level access.
  # Set backend_sa_email in terraform.tfvars or pass as a Cloud Build variable.
  object_admins = var.backend_sa_email != null ? [
    "serviceAccount:${var.backend_sa_email}"
  ] : []

  cors_origins = var.frontend_origin != null ? [var.frontend_origin] : []

  labels = merge(local.common_labels, {
    purpose = "document-storage"
  })
}

# ─── Phase 2: Embedding Artifacts Bucket ──────────────────────────────────────
# Stores FAISS index files and embedding cache produced by the backend.
# Uncomment when the embedding pipeline is implemented.

# module "artifacts_bucket" {
#   source = "../../modules/cloud-storage"
#
#   project_id         = var.project_id
#   name               = "artifacts"
#   env                = local.env
#   location           = var.region
#   versioning_enabled = true
#   force_destroy      = true
#
#   object_admins = var.backend_sa_email != null ? [
#     "serviceAccount:${var.backend_sa_email}"
#   ] : []
#
#   labels = merge(local.common_labels, {
#     purpose = "embedding-artifacts"
#   })
# }

# ─── Phase 4: Networking ───────────────────────────────────────────────────────
# module "networking" {
#   source  = "../../modules/networking"
#   project_id = var.project_id
#   env        = local.env
#   region     = var.region
# }

# ─── Phase 3: Cloud Run — Backend ─────────────────────────────────────────────
# module "cloud_run_backend" {
#   source  = "../../modules/cloud-run"
#   project_id = var.project_id
#   env        = local.env
#   region     = var.region
#   image      = var.backend_image
# }

# ─── Phase 3: Cloud Run — Frontend ────────────────────────────────────────────
# module "cloud_run_frontend" {
#   source  = "../../modules/cloud-run"
#   project_id = var.project_id
#   env        = local.env
#   region     = var.region
#   image      = var.frontend_image
# }

# ─── Phase 5: Vertex AI ───────────────────────────────────────────────────────
# module "vertex_ai" {
#   source  = "../../modules/vertex-ai"
#   project_id = var.project_id
#   env        = local.env
#   region     = var.region
# }
