# GitHub Actions CI/CD Setup Guide

## Overview

This project uses GitHub Actions to automatically:
1. Run tests on every push and pull request
2. Build and push Docker images to Docker Hub when tests pass

## Required Secrets Configuration

To enable the CI/CD pipeline, you need to configure the following secrets in your GitHub repository:

### Step 1: Create Docker Hub Access Token

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Click on your username → **Account Settings**
3. Go to **Security** → **New Access Token**
4. Set description: `github-actions-websearch-mcp`
5. Set permissions: **Read, Write, Delete**
6. Click **Generate** and copy the token (you won't be able to see it again!)

### Step 2: Add Secrets to GitHub Repository

1. Go to your GitHub repository: `https://github.com/Kvmyk/WebSearchMCPServer`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

   **Secret 1:**
   - Name: `DOCKERHUB_USERNAME`
   - Value: Your Docker Hub username (e.g., `kuba7331`)
   
   **Secret 2:**
   - Name: `DOCKERHUB_TOKEN`
   - Value: The access token you generated in Step 1

### Step 3: Verify Setup

1. Push code to the `main` branch or create a pull request
2. Go to **Actions** tab in your repository
3. You should see the workflow running
4. After successful completion, the Docker image will be available at:
   `docker pull <your-username>/web-search-mcp:latest`

## Workflow Behavior

### Test Job
- **Runs on**: Every push and PR to `main`
- **Steps**:
  - Checkout code
  - Setup Python 3.12
  - Install dependencies
  - Run pytest with coverage
  - Upload coverage reports

### Build and Push Job
- **Runs on**: Push to `main` only (after tests pass)
- **Steps**:
  - Checkout code
  - Setup Docker Buildx
  - Login to Docker Hub
  - Build multi-platform image (amd64 + arm64)
  - Push with multiple tags:
    - `latest`
    - `main-<commit-sha>`
    - Semver tags (if release)

## Troubleshooting

### Error: "denied: requested access to the resource is denied"
- Check that `DOCKERHUB_USERNAME` matches your actual Docker Hub username exactly
- Verify `DOCKERHUB_TOKEN` is a valid access token (not your password)
- Make sure the token has "Write" permissions

### Error: "invalid reference format"
- Ensure your Docker Hub username in secrets doesn't have spaces or special characters
- The image name should be lowercase

### Tests failing locally but passing in CI (or vice versa)
- Check Python version (CI uses 3.12)
- Ensure all dependencies in `requirements.txt` and `tests/requirements-test.txt` are up to date
- Check if there are environment-specific issues

## Modifying the Workflow

The workflow configuration is located at:
`.github/workflows/ci-cd.yml`

Key customization points:
- **Change Docker image name**: Modify `DOCKER_IMAGE_NAME` environment variable
- **Add more platforms**: Edit `platforms` in build step
- **Change test commands**: Modify the pytest command in test job
- **Adjust triggers**: Edit `on:` section to change when workflow runs
