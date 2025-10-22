# Deploying to Streamlit Community Cloud

This guide walks you through deploying the H001 Support Level Analyzer to Streamlit Community Cloud so anyone can access it without installing Python.

## Prerequisites

- GitHub account (free)
- Streamlit account (free)

## Step-by-Step Deployment

### Step 1: Create a GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Create a new repository called `StockPriceStats` (or your preferred name)
3. Set it to **Public** (required for free Streamlit Cloud)
4. Click "Create repository"

### Step 2: Push Your Code to GitHub

On your local machine (in `/home/gustaf/StockPriceStats/`):

```bash
# Initialize git (if not already done)
git init

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/StockPriceStats.git

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Stock price statistics and H001 support analysis"

# Push to GitHub
git branch -M main
git push -u origin main
```

**Note:** If the parquet files are too large (>100MB), GitHub might reject them. If you get an error about file size:
- GitHub allows files up to 100MB
- The parquet files (~27MB total) should be fine
- If you hit limits, you can use `git lfs` (Git Large File Storage)

### Step 3: Set Up Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign in" → "Sign in with GitHub"
3. Authorize Streamlit to access your GitHub account

### Step 4: Deploy Your App

1. Click "Create app" on the Streamlit Cloud dashboard
2. Fill in:
   - **Repository:** YOUR_USERNAME/StockPriceStats
   - **Branch:** main
   - **Main file path:** `hypotheses/h001_multi_period_low_support/streamlit_app_lite.py`
3. Click "Deploy"

Streamlit Cloud will:
- Clone your repository
- Install dependencies from `requirements.txt`
- Launch your app
- Assign you a public URL like: `https://yourname-stockpricestats.streamlit.app`

### Step 5: Share the Link

Your app is now live! Share the URL with anyone:
- No Python installation needed
- No setup required
- Works on desktop, tablet, and mobile

## Updating Your App

After you make changes locally:

```bash
git add .
git commit -m "Update: description of changes"
git push origin main
```

Streamlit Cloud will automatically detect the change and redeploy your app (within a few seconds).

## Troubleshooting

### "File too large" error when pushing to GitHub

The parquet data files are large (~27MB total). If you hit GitHub's upload limits:

**Option A: Use Git LFS**
```bash
# Install git lfs
git lfs install

# Track parquet files
git lfs track "*.parquet"
git add .gitattributes

# Now push
git add .
git commit -m "Add large files with LFS"
git push
```

**Option B: Download data after deployment**
- Store data on cloud storage (AWS S3, etc.)
- App downloads it at runtime
- More complex but avoids GitHub limits

### App is slow to load

- First load takes longer as Streamlit downloads your data files
- Subsequent loads are cached
- Consider splitting data if it becomes a bottleneck

### "Module not found" errors

Ensure all packages are listed in `requirements.txt`. Common ones for this app:
- streamlit
- pandas
- plotly
- pyarrow (for parquet support)

All should be in the file already.

## App URL Examples

- **Local:** `http://localhost:8501`
- **Streamlit Cloud:** `https://gustafsmith-stockpricestats.streamlit.app`
- **Custom domain:** You can add a custom domain (paid feature)

## Managing Your Deployment

Dashboard at: https://share.streamlit.io/apps

From here you can:
- ✅ View logs
- ✅ Monitor usage
- ✅ Pause/restart your app
- ✅ Configure secrets (if needed later)
- ✅ Delete the app

## File Structure on GitHub

Your repository should look like:

```
StockPriceStats/
├── .streamlit/
│   └── config.toml
├── .gitignore
├── requirements.txt
├── CLAUDE.md
├── README.md
├── DEPLOYMENT.md (this file)
├── price_data_all.parquet
├── price_data_filtered.parquet
├── nasdaq_options_available.csv
├── filter_relevant_stocks.py
├── example_analysis.py
└── hypotheses/
    └── h001_multi_period_low_support/
        ├── streamlit_app_lite.py (your app)
        ├── STREAMLIT_LITE_README.md
        ├── [analysis results and other files]
```

## Performance Notes

**Streamlit Cloud Free Tier:**
- ✅ Unlimited apps
- ✅ Up to 3 apps
- ✅ 1 GB of storage per app
- ✅ Shared CPU
- ✅ No credit card required

**Limitations:**
- App goes to sleep after 7 days of inactivity
- Shared resources (slower under load)
- Monthly limit on compute hours

This is perfect for a personal analysis tool. If you need production-grade performance, consider Streamlit Cloud's paid plans.

## Next Steps

After successful deployment:

1. **Test the app** - Visit your URL and verify everything works
2. **Share with colleagues** - Send them the link
3. **Monitor usage** - Check the Streamlit Cloud dashboard
4. **Make updates** - Push to GitHub, automatic redeployment
5. **Add more analyses** - Extend with H002, H003, etc. (same deployment)

## Support

- Streamlit Docs: https://docs.streamlit.io
- Streamlit Community Cloud: https://docs.streamlit.io/streamlit-community-cloud
- GitHub Pages: https://docs.github.com
