# Installing Git and Pushing to GitHub

## Quick Setup Guide

### Option 1: Install Git (Recommended for Command Line)

1. **Download Git:**
   - Go to: https://git-scm.com/download/win
   - Click "Download for Windows"
   - The download will start automatically

2. **Install Git:**
   - Run the downloaded installer
   - Click "Next" through the installation wizard
   - **Important:** Keep default settings (they're fine)
   - Click "Install"
   - Wait for installation to complete
   - Click "Finish"

3. **Restart Your Terminal:**
   - Close PowerShell/Command Prompt
   - Open a new PowerShell/Command Prompt window

4. **Verify Installation:**
   ```bash
   git --version
   ```
   You should see something like: `git version 2.x.x`

5. **Run the Push Script:**
   - Double-click `push_to_github.bat` in your project folder
   - OR run it from terminal: `.\push_to_github.bat`
   - Follow the prompts

---

### Option 2: Use GitHub Desktop (Easier - No Command Line!)

1. **Download GitHub Desktop:**
   - Go to: https://desktop.github.com/
   - Click "Download for Windows"
   - Run the installer

2. **Sign In:**
   - Open GitHub Desktop
   - Sign in with your GitHub account
   - If you don't have an account, create one at https://github.com

3. **Add Your Project:**
   - Click "File" → "Add Local Repository"
   - Click "Choose..." and select your project folder: `C:\Users\tejas\OneDrive\Desktop\Project`
   - Click "Add Repository"

4. **Create Repository on GitHub:**
   - Click "Publish repository" button (top right)
   - Repository name: `GLAMORA`
   - Description: "Django web application for GLAMORA beauty salon"
   - Choose Public or Private
   - **Uncheck** "Keep this code private" if you want it public
   - Click "Publish Repository"

5. **Done!** Your code is now on GitHub!

---

## After Installation - Manual Steps (If Using Command Line)

If you prefer to do it manually instead of using the batch script:

### Step 1: Initialize Git
```bash
git init
```

### Step 2: Add All Files
```bash
git add .
```

### Step 3: Create First Commit
```bash
git commit -m "Initial commit: GLAMORA Django application"
```

### Step 4: Create Repository on GitHub
1. Go to https://github.com
2. Click "+" → "New repository"
3. Name: `GLAMORA`
4. **DO NOT** check "Initialize with README"
5. Click "Create repository"

### Step 5: Connect and Push
```bash
git remote add origin https://github.com/YOUR_USERNAME/GLAMORA.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

## Troubleshooting

### "git is not recognized"
- Git is not installed or not in PATH
- Restart terminal after installing Git
- Make sure you selected "Git from the command line" during installation

### Authentication Failed
- GitHub no longer accepts passwords
- Use a Personal Access Token:
  1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. Generate new token with `repo` permissions
  3. Use this token as your password when pushing

### "Repository not found"
- Check repository name matches exactly
- Verify you have write access
- Make sure repository exists on GitHub

---

## Which Method Should I Use?

- **GitHub Desktop**: Easier, visual interface, no command line needed
- **Command Line**: More control, professional workflow, better for learning Git

Both methods work perfectly! Choose what you're comfortable with.

---

**Need Help?** Check `GITHUB_SETUP.md` for more detailed instructions.

