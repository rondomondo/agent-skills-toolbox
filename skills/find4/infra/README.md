# find4 infra

OpenTofu configuration for the find4 static webapp on S3.

## What this creates

| Resource | Name |
|---|---|
| S3 website bucket | `find4-webapp` |
| S3 state bucket | `find4-terraform-state` |
| IAM user | `find4-webapp-deployer` |
| IAM policy | `find4-webapp-deploy` (least-privilege sync only) |

All resources are in `us-east-1`.

## Prerequisites

- [OpenTofu](https://opentofu.org/docs/intro/install/) >= 1.6
- AWS CLI configured with credentials that have permission to create S3 buckets and IAM users
- The state bucket (`find4-terraform-state`) must exist before `tofu init` - see step 1 below

## First-time setup

### 1. Create the remote state bucket

This is a one-time manual step. The bucket must exist before OpenTofu can store state in it.

```bash
make state-bucket
```

Or combined with init:

```bash
make setup
```

### 2. Initialise and apply

```bash
make init
make plan
make apply
```

### 3. Add credentials to GitHub

After `apply`, retrieve the deployer credentials:

```bash
make show-credentials
```

Go to your GitHub repo: **Settings > Secrets and variables > Actions > New repository secret**

Add two secrets:

| Secret name | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | printed by `make show-credentials` |
| `AWS_SECRET_ACCESS_KEY` | printed by `make show-credentials` |

The website URL is available via:

```bash
make show-url
```

## Day-to-day

```bash
make plan      # preview changes
make apply     # apply changes
make fmt       # format .tf files
make validate  # validate without hitting AWS
```

## CI/CD

The GitHub Actions workflow at `.github/workflows/deploy-find4-webapp.yml` triggers on any push to
`main` that changes files under `skills/find4/webapp/`. It runs `make deploy-webapp` to build the
webapp, then syncs the result to `s3://find4-webapp`.

The workflow uses the `find4-webapp-deployer` IAM user. That user has only the minimum permissions
needed to sync files - `s3:ListBucket`, `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` - scoped
to the `find4-webapp` bucket.
