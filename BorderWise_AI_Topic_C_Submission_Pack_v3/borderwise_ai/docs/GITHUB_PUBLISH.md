# Publish the complete BorderWise AI source repository

The project ZIP is not itself a published GitHub repository. The team must create the repository and copy its URL into the submission email/materials.

## 1. Create an empty repository

On GitHub, create a repository named `borderwise-ai`. Do not initialize it with an additional README, license, or `.gitignore`, because this folder already contains those project files. Copy the URL of the repository you created.

## 2. Review the files before publishing

Open a terminal in the extracted `borderwise_ai` folder. Check that no real API key, `.env` file, personal financial information, passport information, or other secrets are present. Never put an API key in the source code, HTML, screenshots, or commit history.

## 3. Commit the complete project

Run these commands in the `borderwise_ai` folder:

```bash
git init
git add .
git status --short
```

Review the staged file list and confirm that it includes the working browser app (`server.py`, `web_server.py`, and `web/index.html`), calculator and assistant code, tests, documentation, launch/test scripts, and presentation files. Confirm that no secret or private file is staged. If anything sensitive appears, unstage it and fix `.gitignore` before continuing.

Then commit and push:

```bash
git commit -m "Initial BorderWise AI Topic C prototype"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/borderwise-ai.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your actual GitHub username and use the exact repository URL you created. If your remote uses a different URL, use that one instead.

## 4. Verify the repository

Open the repository URL in a browser and confirm that the source files and README are visible. If the competition expects public source code, set visibility to public only after the secret/privacy review.

## 5. Include the link in your submission

Copy the actual repository URL into the submission email or form. Do not leave the example URL above in the final submission.
