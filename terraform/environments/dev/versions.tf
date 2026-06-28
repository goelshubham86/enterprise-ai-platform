# ─────────────────────────────────────────────────────────────────────────────
# versions.tf
#
# Terraform core version constraint + provider source and version pins.
# Keeping these here (separate from main.tf) makes provider audits and
# upgrades a one-file operation.
#
# Upgrade guide:
#   1. Bump required_version and/or the google provider version below.
#   2. Run: terraform init -upgrade
#   3. Commit the updated .terraform.lock.hcl alongside this file.
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  # ~> 1.9 allows patch releases (1.9.x) but blocks 2.x.
  # Matches the hashicorp/terraform:1.9 image used in Cloud Build.
  required_version = "~> 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    # google-beta will be needed for Vertex AI Vector Search (Phase 5).
    # Uncomment and add `provider "google-beta"` in providers.tf when required.
    # google-beta = {
    #   source  = "hashicorp/google-beta"
    #   version = "~> 6.0"
    # }
  }

  backend "gcs" {
    # State bucket is created once manually before first `terraform init`.
    # See docs/deployment/terraform-bootstrap.md for setup steps.
    bucket = "enterprise-ai-tfstate-dev"
    prefix = "terraform/state"
  }
}
