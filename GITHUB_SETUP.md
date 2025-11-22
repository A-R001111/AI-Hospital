# 🔗 راهنمای اتصال به GitHub و مدیریت Repository

## مرحله 1: ایجاد Repository در GitHub

### 1.1 ورود به GitHub
1. به https://github.com بروید
2. وارد حساب کاربری خود شوید

### 1.2 ایجاد Repository جدید
1. روی آیکون "+" در گوشه بالا سمت راست کلیک کنید
2. "New repository" را انتخاب کنید
3. تنظیمات:
   ```
   Repository name: AI-Hospital
   Description: سامانه گزارش‌نویسی پرستاران با هوش مصنوعی
   Visibility: Private (توصیه می‌شود) یا Public
   ✅ Add a README file: NO (چون خودمان داریم)
   .gitignore: None (چون خودمان داریم)
   License: MIT (اختیاری)
   ```
4. روی "Create repository" کلیک کنید

## مرحله 2: راه‌اندازی Git در Local

### 2.1 نصب Git (اگر نصب نیست)

**ویندوز:**
```bash
# دانلود از: https://git-scm.com/download/win
# سپس نصب با Next, Next, ...
```

**macOS:**
```bash
brew install git
```

**لینوکس (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install git
```

### 2.2 تنظیم اولیه Git
```bash
# تنظیم نام کاربری
git config --global user.name "Your Name"

# تنظیم ایمیل
git config --global user.email "your.email@example.com"

# بررسی تنظیمات
git config --list
```

## مرحله 3: اتصال پروژه به GitHub

### 3.1 Initialize کردن Git Repository
```bash
# رفتن به دایرکتوری پروژه
cd /path/to/AI-Hospital

# Initialize کردن git
git init

# بررسی وضعیت
git status
```

### 3.2 افزودن فایل‌ها
```bash
# افزودن تمام فایل‌ها (به جز موارد در .gitignore)
git add .

# بررسی فایل‌هایی که اضافه شده‌اند
git status

# اولین commit
git commit -m "Initial commit: Project structure and core modules"
```

### 3.3 اتصال به GitHub Remote
```bash
# افزودن remote (آدرس repository GitHub خود را جایگزین کنید)
git remote add origin https://github.com/YOUR-USERNAME/AI-Hospital.git

# بررسی remote
git remote -v

# Push کردن کد به GitHub
git branch -M main
git push -u origin main
```

**نکته:** اگر از حساب Private استفاده می‌کنید، باید Authentication انجام دهید.

## مرحله 4: Authentication با GitHub

### روش 1: Personal Access Token (توصیه می‌شود)

1. به GitHub Settings بروید
2. Developer settings > Personal access tokens > Tokens (classic)
3. "Generate new token" را کلیک کنید
4. تنظیمات:
   ```
   Note: AI-Hospital Development
   Expiration: 90 days (یا بیشتر)
   Scopes:
   ✅ repo (full control)
   ✅ workflow
   ```
5. "Generate token" را کلیک کنید
6. **Token را کپی کنید** (فقط یکبار نمایش داده می‌شود!)

استفاده از Token:
```bash
# وقتی Git از شما Username و Password می‌خواهد:
Username: YOUR-GITHUB-USERNAME
Password: <Token شما را paste کنید>

# برای ذخیره Token:
git config --global credential.helper store
```

### روش 2: SSH Key

1. تولید SSH Key:
```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
# Enter را چند بار فشار دهید
```

2. کپی کردن Public Key:
```bash
# ویندوز:
type %USERPROFILE%\.ssh\id_ed25519.pub

# macOS/Linux:
cat ~/.ssh/id_ed25519.pub
```

3. افزودن به GitHub:
   - Settings > SSH and GPG keys > New SSH key
   - کلید را paste کنید
   - "Add SSH key" را کلیک کنید

4. تغییر Remote به SSH:
```bash
git remote set-url origin git@github.com:YOUR-USERNAME/AI-Hospital.git
```

## مرحله 5: کار با Git - دستورات روزمره

### 5.1 بررسی وضعیت
```bash
# دیدن فایل‌های تغییر یافته
git status

# دیدن تفاوت‌ها
git diff

# دیدن history
git log
git log --oneline --graph --all
```

### 5.2 Commit کردن تغییرات
```bash
# افزودن فایل‌های خاص
git add file1.py file2.py

# افزودن همه تغییرات
git add .

# افزودن با pattern
git add *.py

# Commit با پیام
git commit -m "feat: Add user authentication"

# تغییر آخرین commit
git commit --amend -m "feat: Update authentication module"
```

### 5.3 Push و Pull
```bash
# Push به GitHub
git push origin main

# Pull از GitHub (دریافت تغییرات)
git pull origin main

# Force push (⚠️ خطرناک!)
git push -f origin main
```

### 5.4 Branch Management
```bash
# ساخت branch جدید
git branch feature/voice-to-text

# تغییر به branch
git checkout feature/voice-to-text

# ساخت و تغییر همزمان
git checkout -b feature/new-feature

# لیست branch ها
git branch -a

# حذف branch
git branch -d feature/old-feature

# Merge کردن branch
git checkout main
git merge feature/voice-to-text
```

## مرحله 6: Best Practices

### 6.1 قوانین Commit Messages
```bash
# فرمت استاندارد:
# <type>: <subject>
#
# <body>
#
# <footer>

# انواع type:
feat:     ویژگی جدید
fix:      رفع باگ
docs:     تغییرات مستندات
style:    فرمت کد
refactor: بازنویسی کد
test:     تست‌ها
chore:    کارهای maintenance

# مثال‌ها:
git commit -m "feat: Add voice recording feature"
git commit -m "fix: Resolve database connection issue"
git commit -m "docs: Update README with deployment guide"
```

### 6.2 Gitflow Workflow
```
main          ────●────●────●────> (Production)
               ↗      ↑
develop    ───●──●──●─┴──●────> (Development)
            ↗     ↗  ↗
feature/x  ─●──●─┘  /  (Features)
feature/y  ────●───┘
```

### 6.3 فایل .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
venv/
.env

# IDE
.vscode/
.idea/

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# Uploads
uploads/
```

## مرحله 7: GitHub Actions (CI/CD)

### 7.1 ایجاد Workflow
ایجاد فایل `.github/workflows/main.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to Parspack
      run: |
        echo "Deploying to Parspack..."
        # دستورات deploy
```

## مرحله 8: Collaboration

### 8.1 دعوت همکاران
1. Settings > Collaborators
2. "Add people" را کلیک کنید
3. Username یا Email را وارد کنید

### 8.2 Pull Request
```bash
# ساخت branch جدید
git checkout -b feature/new-feature

# انجام تغییرات و commit
git add .
git commit -m "feat: Add new feature"

# Push به GitHub
git push origin feature/new-feature

# در GitHub:
# 1. روی "Compare & pull request" کلیک کنید
# 2. توضیحات را بنویسید
# 3. "Create pull request" را کلیک کنید
```

## مرحله 9: رفع مشکلات رایج

### 9.1 Merge Conflict
```bash
# وقتی conflict رخ می‌دهد:
git pull origin main

# فایل‌های conflict را باز کنید و ویرایش کنید
# <<<<<<< HEAD
# کد شما
# =======
# کد دیگران
# >>>>>>> branch-name

# بعد از حل conflict:
git add .
git commit -m "fix: Resolve merge conflict"
```

### 9.2 Undo Changes
```bash
# لغو تغییرات یک فایل
git checkout -- file.py

# لغو آخرین commit (نگه داشتن تغییرات)
git reset --soft HEAD~1

# لغو آخرین commit (حذف تغییرات)
git reset --hard HEAD~1

# برگشت به commit قبلی
git revert <commit-hash>
```

### 9.3 فایل بزرگ Push شد
```bash
# استفاده از Git LFS
git lfs install
git lfs track "*.wav"
git lfs track "*.mp3"
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

## مرحله 10: Backup و Clone

### 10.1 Clone کردن پروژه
```bash
# Clone از GitHub
git clone https://github.com/YOUR-USERNAME/AI-Hospital.git

# Clone با SSH
git clone git@github.com:YOUR-USERNAME/AI-Hospital.git

# Clone یک branch خاص
git clone -b develop https://github.com/YOUR-USERNAME/AI-Hospital.git
```

### 10.2 Fork کردن
در GitHub روی دکمه "Fork" کلیک کنید.

## منابع مفید

- Git Documentation: https://git-scm.com/doc
- GitHub Guides: https://guides.github.com
- Interactive Git: https://learngitbranching.js.org
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf

---

**یادآوری:** همیشه قبل از push کردن، `git status` و `git diff` را بررسی کنید!
