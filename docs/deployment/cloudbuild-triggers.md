# Cloud Build Trigger Configuration

## Overview

The platform has four Cloud Build pipeline files. Each can be run independently
or in combination via the main `cloudbuild.yaml`:

| File | Purpose | When to use |
|---|---|---|
| `cloudbuild.yaml` | Full pipeline with `_DEPLOY_*` flags | Manual runs, one-off deployments |
| `cloudbuild.terraform.yaml` | Terraform only | Any change to `terraform/**` |
| `cloudbuild.backend.yaml` | Backend only | Any change to `backend/**` |
| `cloudbuild.frontend.yaml` | Frontend only | Any change to `frontend/**` |

---

## Recommended Trigger Setup (GCP Console or gcloud)

Create one trigger per pipeline file. Path filters ensure each trigger only
fires when its relevant files change.

### Trigger 1 — Terraform (plan on PRs, apply on main)

```bash
gcloud builds triggers create github \
  --name="terraform-plan-dev" \
  --repo-name="enterprise-ai-platform" \
  --repo-owner="YOUR_GITHUB_ORG" \
  --branch-pattern=".*" \
  --build-config="cloudbuild.terraform.yaml" \
  --included-files="terraform/**" \
  --substitutions="_ENV=dev,_REGION=us-central1,_APPLY_INFRA=false"
```

For the **main branch apply** trigger (separate trigger, same file):

```bash
gcloud builds triggers create github \
  --name="terraform-apply-dev" \
  --repo-name="enterprise-ai-platform" \
  --repo-owner="YOUR_GITHUB_ORG" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.terraform.yaml" \
  --included-files="terraform/**" \
  --substitutions="_ENV=dev,_REGION=us-central1,_APPLY_INFRA=true"
```

### Trigger 2 — Backend

```bash
gcloud builds triggers create github \
  --name="backend-deploy-dev" \
  --repo-name="enterprise-ai-platform" \
  --repo-owner="YOUR_GITHUB_ORG" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.backend.yaml" \
  --included-files="backend/**" \
  --substitutions="_ENV=dev,_REGION=us-central1"
```

### Trigger 3 — Frontend

```bash
gcloud builds triggers create github \
  --name="frontend-deploy-dev" \
  --repo-name="enterprise-ai-platform" \
  --repo-owner="YOUR_GITHUB_ORG" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.frontend.yaml" \
  --included-files="frontend/**" \
  --substitutions="_ENV=dev,_REGION=us-central1"
```

---

## Manual `gcloud` Runs (no trigger needed)

Run any combination on demand using `gcloud builds submit`:

```bash
# Terraform plan only (safe — no infra changes)
gcloud builds submit . \
  --config=cloudbuild.terraform.yaml \
  --substitutions=_ENV=dev,_APPLY_INFRA=false

# Terraform apply (provisions infra)
gcloud builds submit . \
  --config=cloudbuild.terraform.yaml \
  --substitutions=_ENV=dev,_APPLY_INFRA=true

# Backend only
gcloud builds submit . \
  --config=cloudbuild.backend.yaml \
  --substitutions=_ENV=dev,_REGION=us-central1

# Frontend only
gcloud builds submit . \
  --config=cloudbuild.frontend.yaml \
  --substitutions=_ENV=dev,_REGION=us-central1

# Full deploy — all components
gcloud builds submit . \
  --config=cloudbuild.yaml \
  --substitutions=_DEPLOY_TERRAFORM=true,_APPLY_INFRA=true,_DEPLOY_BACKEND=true,_DEPLOY_FRONTEND=true

# Terraform + backend only (skip frontend)
gcloud builds submit . \
  --config=cloudbuild.yaml \
  --substitutions=_DEPLOY_TERRAFORM=true,_APPLY_INFRA=true,_DEPLOY_BACKEND=true,_DEPLOY_FRONTEND=false

# Frontend only via main file
gcloud builds submit . \
  --config=cloudbuild.yaml \
  --substitutions=_DEPLOY_TERRAFORM=false,_DEPLOY_BACKEND=false,_DEPLOY_FRONTEND=true
```

---

## Decision Matrix

| Scenario | Pipeline file | Key flags |
|---|---|---|
| PR opened — validate terraform | `cloudbuild.terraform.yaml` | `_APPLY_INFRA=false` |
| Merged to main — apply infra | `cloudbuild.terraform.yaml` | `_APPLY_INFRA=true` |
| Backend bug fix | `cloudbuild.backend.yaml` | defaults |
| Frontend UI change | `cloudbuild.frontend.yaml` | defaults |
| Full release | `cloudbuild.yaml` | all `_DEPLOY_*=true`, `_APPLY_INFRA=true` |
| Rollback backend | `cloudbuild.backend.yaml` | override image tag manually |

---

## Path Filter Behaviour

Cloud Build `includedFiles` uses glob patterns. When a push touches only
`frontend/src/App.tsx`, only the frontend trigger fires — terraform and backend
triggers are not invoked. This keeps build minutes low and CI fast.

```
Push to: frontend/src/pages/Chat.tsx
  ✅ frontend-deploy-dev  (includedFiles: frontend/**)
  ⬜ backend-deploy-dev   (includedFiles: backend/**)  — skipped
  ⬜ terraform-plan-dev   (includedFiles: terraform/**) — skipped
```
