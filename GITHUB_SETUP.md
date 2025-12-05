# Push to GitHub - Quick Guide

Everything is ready! Just follow these simple steps:

## Step 1: Create the Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `YTVidDownloader`
3. Description: `Lightweight YouTube video downloader with GUI and multiple quality options`
4. Choose: **Public** (or Private if you prefer)
5. **DO NOT** check "Initialize this repository with a README" (we already have one!)
6. Click **Create repository**

## Step 2: Push Your Code

After creating the repo, GitHub will show you some commands. **Ignore those** and use these instead:

```bash
cd /mnt/ext4gamedrive/projects/YTVidDownloader

git remote add origin https://github.com/jj-repository/YTVidDownloader.git

git push -u origin main
```

That's it! Your project will be on GitHub.

## Step 3: (Optional) Create a Release

To share the compiled executable:

1. Go to your repo: https://github.com/jj-repository/YTVidDownloader
2. Click on "Releases" → "Create a new release"
3. Tag: `v1.0.0`
4. Title: `YTVidDownloader v1.0.0`
5. Upload the file: `YTVidDownloader-Linux.tar.gz` (from your project folder)
6. Click "Publish release"

Now anyone can download the ready-to-use version!

---

## Git Commands Reference

If you need to make changes later:

```bash
# Make your changes to files, then:
git add .
git commit -m "Your commit message"
git push
```

## Troubleshooting

**If push asks for credentials:**
- Use your GitHub username: `jj-repository`
- Password: Use a Personal Access Token (not your GitHub password)
  - Create one at: https://github.com/settings/tokens
  - Select "repo" scope
  - Copy and use it as your password

**Or use SSH instead:**
```bash
git remote set-url origin git@github.com:jj-repository/YTVidDownloader.git
```
(Requires SSH keys set up on GitHub)
