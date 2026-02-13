# Repository Migration Guide

This document provides instructions for migrating the Sovereignty-AI-Studio repository from the old organization to the new organization.

## Migration Steps

Follow these steps to migrate the repository from `Appel420` organization to `sovereignty-one` organization:

### 1. Clone the Repository

```bash
git clone https://github.com/Appel420/Sovereignty-AI-Studio.git
```

### 2. Navigate to the Repository

```bash
cd Sovereignty-AI-Studio
```

### 3. Update Remote URL

Change the remote URL to point to the new organization:

```bash
git remote set-url origin https://github.com/sovereignty-one/Sovereignty-AI-Studio.git
```

### 4. Push to New Repository

Push all branches and tags to the new repository:

```bash
# Push the main branch with upstream tracking
git push -u origin main

# Push all other branches
# Note: This will push all local branches. If you need to migrate remote branches
# that don't exist locally, first fetch them with: git fetch --all
git push --all

# Push all tags
git push --tags
```

## Verification

After completing the migration, verify that:
- All branches have been pushed to the new repository
- All tags have been transferred
- The remote URL is correctly set to the new organization

You can verify the remote URL with:
```bash
git remote -v
```

## Notes

- Ensure you have proper permissions to push to the new repository before starting the migration
- The `git push --all` command only pushes branches that exist in your local repository. If the old repository has remote branches that you haven't checked out locally, they won't be automatically migrated. To migrate all remote branches, you may need to check them out locally first or use a more comprehensive migration tool
- The `git push -u origin main` command is included to set up tracking for the main branch before pushing all branches. While `git push --all` will also push main, the initial command with `-u` ensures proper upstream tracking is configured
- This process will not delete the old repository; you'll need to archive or delete it separately if needed
- Update any CI/CD pipelines, webhooks, or external integrations to point to the new repository URL
