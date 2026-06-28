# ─────────────────────────────────────────────────────────────────────────────
# locals.tf
#
# Derived values and constants used across this environment's module calls.
# Using locals (rather than repeating literals) means a single edit here
# propagates everywhere: rename the environment, change the label set, or
# adjust the naming prefix without touching every module block in main.tf.
# ─────────────────────────────────────────────────────────────────────────────

locals {
  # Canonical environment name — passed to every module so bucket names,
  # resource labels, and lifecycle rules are automatically scoped.
  env = "dev"

  # Shared labels applied to all resources in this environment.
  # Modules merge additional purpose-specific labels on top of these.
  common_labels = {
    env        = local.env
    team       = "ai-platform"
    managed-by = "terraform"
  }
}
