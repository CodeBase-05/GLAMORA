# Push Project to GLAMORA Repository

Your GitHub repository: **https://github.com/CodeBase-05/GLAMORA**

## Quick Steps to Push Your Code

### Option 1: Using GitHub Desktop (EASIEST - Recommended!)

1. **Download GitHub Desktop:**
   - Go to: https://desktop.github.com/
   - Download and install GitHub Desktop

2. **Sign In:**
   - Open GitHub Desktop
   - Sign in with your GitHub account (CodeBase-05)

3. **Add Your Project:**
   - Click "File" → "Add Local Repository"
   - Click "Choose..." 
   - Select: `C:\Users\tejas\OneDrive\Desktop\Project`
   - Click "Add Repository"

4. **Publish to Existing Repository:**
   - Click "Publish repository" button (top right)
   - **Uncheck** "Keep this code private" (if you want it public)
   - Repository name: `GLAMORA`
   - Click "Publish Repository"
   - OR if it asks to connect to existing repo, select "CodeBase-05/GLAMORA"

5. **Done!** Your code is now on GitHub!

---

### Option 2: Using Command Line

#### Step 1: Install Git
- Download from: https://git-scm.com/download/win
- Install Git (keep default settings)
- **Restart PowerShell/Terminal after installation**

#### Step 2: Run These Commands

Open PowerShell in your project folder and run:

```bash
# Initialize Git repository
git init

# Add all files
git add .

# Create commit
git commit -m "Initial commit: Complete GLAMORA project"

# Connect to your GitHub repository
git remote add origin https://github.com/CodeBase-05/GLAMORA.git

# Set main branch
git branch -M main

# Push to GitHub
git push -u origin main
```

**Note:** When prompted for credentials:
- Username: `CodeBase-05`
- Password: Use a **Personal Access Token** (not your GitHub password)
  - Get token from: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  - Generate new token with `repo` permissions

---

## What Will Be Pushed

✅ All your project files
✅ README.md (with setup instructions)
✅ requirements.txt
✅ database_queries.sql
✅ All templates and static files
✅ Service images from Assets folder

❌ `.env` file (will NOT be pushed - it's in .gitignore)
❌ `.venv` folder (will NOT be pushed - it's in .gitignore)
❌ `__pycache__` folders (will NOT be pushed)

---

## After Pushing

Your repository will be available at:
**https://github.com/CodeBase-05/GLAMORA**

Anyone can now:
1. Clone your repository
2. Follow the README.md instructions
3. Set up their own database
4. Run the application

---

## Need Help?

- **GitHub Desktop:** Easiest option, no command line needed
- **Command Line:** More control, professional workflow

Choose whichever you're comfortable with!

