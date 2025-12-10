# GitHub Setup Guide for GLAMORA Project

## Prerequisites

1. **Install Git** (if not already installed):
   - Download from: https://git-scm.com/download/win
   - Follow the installation wizard
   - Restart your terminal/PowerShell after installation

2. **Create GitHub Account** (if you don't have one):
   - Go to: https://github.com
   - Sign up for a free account

## Step-by-Step Instructions to Push to GitHub

### Step 1: Initialize Git Repository (if not already initialized)

Open PowerShell or Command Prompt in your project directory and run:

```bash
git init
```

### Step 2: Check Git Status

```bash
git status
```

This will show you all files that will be committed.

### Step 3: Add All Files to Git

```bash
git add .
```

**Important:** Make sure `.env` file is NOT added. Check `.gitignore` includes `.env` (it should already be there).

### Step 4: Create Initial Commit

```bash
git commit -m "Initial commit: GLAMORA Django application"
```

### Step 5: Create Repository on GitHub

1. Go to https://github.com
2. Click the **"+"** icon in the top right corner
3. Select **"New repository"**
4. Repository name: `GLAMORA`
5. Description: "Django web application for GLAMORA beauty salon"
6. Choose **Public** or **Private** (your choice)
7. **DO NOT** initialize with README, .gitignore, or license (we already have these)
8. Click **"Create repository"**

### Step 6: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
git remote add origin https://github.com/YOUR_USERNAME/GLAMORA.git
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### Step 7: Push to GitHub

```bash
git branch -M main
git push -u origin main
```

You may be prompted for your GitHub username and password (or personal access token).

### Step 8: Verify Upload

Go to your GitHub repository page and verify all files are uploaded correctly.

## Important Notes

### Files That Should NOT Be Committed

- `.env` - Contains sensitive database credentials
- `.venv/` or `venv/` - Virtual environment folder
- `__pycache__/` - Python cache files
- `*.pyc` - Compiled Python files
- `media/` - User uploaded media files
- `*.log` - Log files

All these should already be in `.gitignore`.

### If You Need to Update Later

After making changes:

```bash
git add .
git commit -m "Description of your changes"
git push
```

### Authentication Issues

If you get authentication errors:

1. **Use Personal Access Token** instead of password:
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` permissions
   - Use this token as password when pushing

2. **Or use SSH** (more secure):
   - Generate SSH key: `ssh-keygen -t ed25519 -C "your_email@example.com"`
   - Add SSH key to GitHub account
   - Use SSH URL: `git@github.com:YOUR_USERNAME/GLAMORA.git`

## Troubleshooting

### "git is not recognized"
- Git is not installed or not in PATH
- Install Git from https://git-scm.com/download/win
- Restart terminal after installation

### "Permission denied"
- Check your GitHub credentials
- Use personal access token instead of password

### "Repository not found"
- Verify repository name matches exactly
- Check you have write access to the repository

### Large Files Warning
- If you have large image files, consider using Git LFS
- Or optimize images before committing

## Quick Reference Commands

```bash
# Check status
git status

# Add all files
git add .

# Commit changes
git commit -m "Your commit message"

# Push to GitHub
git push

# View remote URL
git remote -v

# Change remote URL (if needed)
git remote set-url origin https://github.com/YOUR_USERNAME/GLAMORA.git
```

---

**Ready to push?** Follow the steps above, and your GLAMORA project will be on GitHub!

