/*
  Module: cloud-storage
  ---------------------
  Creates a production-hardened Google Cloud Storage bucket with:
    • Uniform bucket-level access (no legacy ACLs)
    • Public access prevention enforced
    • Versioning + soft-delete for point-in-time recovery
    • Tiered lifecycle rules for cost optimisation
    • Optional CMEK encryption
    • Optional access logging
    • Granular IAM bindings (readers / creators / admins)

  Naming convention: {project_id}-{name}-{env}
  Example:           my-project-documents-dev
*/

terraform {
  required_version = ">= 1.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

locals {
  bucket_name = "${var.project_id}-${var.name}-${var.env}"

  # Merge caller-supplied labels with mandatory standard labels
  labels = merge(
    {
      env        = var.env
      managed-by = "terraform"
      module     = "cloud-storage"
      project    = "enterprise-ai-platform"
    },
    var.labels,
  )
}

# ─── Bucket ───────────────────────────────────────────────────

resource "google_storage_bucket" "this" {
  project  = var.project_id
  name     = local.bucket_name
  location = var.location

  storage_class = var.storage_class
  force_destroy = var.force_destroy

  uniform_bucket_level_access = var.uniform_bucket_level_access
  public_access_prevention    = var.public_access_prevention

  labels = local.labels

  # ── Versioning ────────────────────────────────────────────
  versioning {
    enabled = var.versioning_enabled
  }

  # ── Soft Delete ───────────────────────────────────────────
  # Protects against accidental deletion; objects can be restored
  # within the retention window even after a delete call.
  dynamic "soft_delete_policy" {
    for_each = var.soft_delete_retention_days > 0 ? [1] : []
    content {
      retention_duration_seconds = var.soft_delete_retention_days * 86400
    }
  }

  # ── Lifecycle Rules ───────────────────────────────────────
  dynamic "lifecycle_rule" {
    for_each = var.lifecycle_rules
    content {
      action {
        type          = lifecycle_rule.value.action.type
        storage_class = try(lifecycle_rule.value.action.storage_class, null)
      }
      condition {
        age                   = try(lifecycle_rule.value.condition.age, null)
        num_newer_versions    = try(lifecycle_rule.value.condition.num_newer_versions, null)
        with_state            = try(lifecycle_rule.value.condition.with_state, null)
        matches_storage_class = try(lifecycle_rule.value.condition.matches_storage_class, null)
      }
    }
  }

  # ── CORS ──────────────────────────────────────────────────
  dynamic "cors" {
    for_each = length(var.cors_origins) > 0 ? [1] : []
    content {
      origin          = var.cors_origins
      method          = var.cors_methods
      response_header = ["Content-Type", "Authorization", "x-goog-*"]
      max_age_seconds = var.cors_max_age_seconds
    }
  }

  # ── Encryption (CMEK) ─────────────────────────────────────
  dynamic "encryption" {
    for_each = var.kms_key_name != null ? [1] : []
    content {
      default_kms_key_name = var.kms_key_name
    }
  }

  # ── Access Logging ────────────────────────────────────────
  dynamic "logging" {
    for_each = var.log_bucket_name != null ? [1] : []
    content {
      log_bucket        = var.log_bucket_name
      log_object_prefix = var.log_object_prefix
    }
  }
}

# ─── IAM Bindings ─────────────────────────────────────────────
#
# Using additive bindings (iam_member) rather than authoritative
# (iam_policy / iam_binding) to avoid wiping existing permissions
# set outside Terraform (e.g., by GCS default grants).

resource "google_storage_bucket_iam_member" "object_readers" {
  for_each = toset(var.object_readers)

  bucket = google_storage_bucket.this.name
  role   = "roles/storage.objectViewer"
  member = each.value
}

resource "google_storage_bucket_iam_member" "object_creators" {
  for_each = toset(var.object_creators)

  bucket = google_storage_bucket.this.name
  role   = "roles/storage.objectCreator"
  member = each.value
}

resource "google_storage_bucket_iam_member" "object_admins" {
  for_each = toset(var.object_admins)

  bucket = google_storage_bucket.this.name
  role   = "roles/storage.objectAdmin"
  member = each.value
}
