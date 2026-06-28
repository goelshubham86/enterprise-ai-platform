# ─────────────────────────────────────────────────────────────────────────────
# TFLint Configuration
#
# Scope: all modules and environments under terraform/
# Run:   tflint --init && tflint --recursive   (from terraform/)
#
# Plugins pinned for reproducible CI. To upgrade:
#   tflint --init          → re-downloads at pinned version
#   Edit version below     → re-run tflint --init to pull new version
#
# Roadmap (add plugins here as the project matures):
#   □ tflint-ruleset-google-beta  — beta resource rules
#   □ tflint-ruleset-azurerm      — if multi-cloud expands
# ─────────────────────────────────────────────────────────────────────────────

config {
  # compact: one line per finding — easier to scan in Cloud Build logs
  format = "compact"

  # Lint module source code referenced via relative paths (our own modules).
  # Does not follow remote registry sources.
  call_module_type = "local"

  # Never suppress non-zero exit for lint errors — let CI fail fast.
  force = false
}

# ─── Built-in Terraform plugin ────────────────────────────────────────────────
# Checks naming conventions, required_version, required_providers, deprecated
# interpolation syntax, and unused declarations.
# No credentials required — pure HCL analysis.
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

# ─── Google Cloud plugin ──────────────────────────────────────────────────────
# Checks GCP-specific rules: invalid resource names, unsupported regions,
# deprecated attributes on google_* resources, and more.
# No GCP credentials required — static analysis only.
#
# Changelog: https://github.com/terraform-linters/tflint-ruleset-google/releases
plugin "google" {
  enabled = true
  version = "0.32.0"
  source  = "github.com/terraform-linters/tflint-ruleset-google"
}
