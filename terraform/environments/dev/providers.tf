# ─────────────────────────────────────────────────────────────────────────────
# providers.tf
#
# Provider configuration. Keeping provider blocks here makes it easy to add
# aliases (e.g. a second region, or google-beta) without touching module code.
# ─────────────────────────────────────────────────────────────────────────────

provider "google" {
  project = var.project_id
  region  = var.region

  # Default labels applied to every resource created by this provider.
  # Individual modules merge additional labels on top of these.
  default_labels = {
    env        = local.env
    managed-by = "terraform"
    project    = "enterprise-ai-platform"
  }
}

# Uncomment when Phase 5 (Vertex AI Vector Search) is implemented.
# google-beta is required for preview features not yet in the GA provider.
# provider "google-beta" {
#   project = var.project_id
#   region  = var.region
#
#   default_labels = {
#     env        = local.env
#     managed-by = "terraform"
#     project    = "enterprise-ai-platform"
#   }
# }
