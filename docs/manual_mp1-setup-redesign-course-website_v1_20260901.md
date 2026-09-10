# Mini-Project #1: Re-Design a Website with AI — Self-Guided Manual

**Course:** IPHS 400: Frontiers in AI
**Version:** v1, 2026-09-01
**Audience:** You do not need a CS or STEM background for this. If you can install an app, use a terminal to type commands someone gives you, and follow numbered steps carefully, you can complete this project. Every command below is written to be copy-pasted exactly as shown.

## What you're building

You'll take this course's own website (this repository) and use an AI coding agent — Claude Code — to critique it, plan a revision, and then actually make the revisions, testing as you go. By the end you'll have a working copy of the site running on your own laptop, with a documented set of improvements you made yourself (with AI doing the typing, and you doing the judgment calls).

This manual is long because it explains *everything*, including things a CS major would skip past. Read it in order. Don't skip ahead — later steps assume earlier ones worked.

## How to use this manual with an AI assistant

You are encouraged to have an AI assistant (Claude Code, ChatGPT, whatever you have open) alongside you *while reading this manual* to explain any single term or error message you don't understand. That is a normal, expected way to use this document — the manual gives you the map and the exact commands; use AI for "what does this error mean" or "explain what a terminal is" in the moment. What you should *not* do is skip a whole numbered step because "AI will figure it out" — each step exists because a specific thing needs to be true before the next step works.

---

## Part A. Before You Start: What You're Installing and Why

You'll install four things:

| Tool | What it is | Why you need it |
|---|---|---|
| `git` + `gh` | Version control + GitHub's command-line tool | Lets you download ("clone") the course repo and save your own copy on GitHub |
| `uv` | A fast Python package/environment manager | The site's test suite is written in Python; `uv` sets up an isolated Python environment so it doesn't interfere with anything else on your computer |
| Claude Code CLI | Anthropic's AI coding agent, run from the terminal | This is the AI that reads, critiques, and edits the website code for you |
| VS Code | A code editor | Where you'll look at files, watch the AI make edits, and browse the site's code visually |

You'll also need:
- A **GitHub.com account** (free) — this is where your personal copy of the site will live.
- A **Claude subscription** (the $20/month "Pro" tier is sufficient) — this is what powers Claude Code.

**A note on cost:** the $20/month Claude subscription is a real cost. If your institution provides free or discounted access to Claude Code (check with your instructor first), use that instead of a personal subscription.

---

## Part B. Standardize Your Setup

Before installing anything, make two decisions so everyone in the class is working the same way (this avoids "it works on my machine" problems when asking classmates or the instructor for help):

1. **Browser: use Google Chrome only** for anything web-based in this project (GitHub.com, viewing the running site, Claude's web login). If you don't have Chrome, install it first from google.com/chrome. Other browsers will probably work too, but troubleshooting help in this course assumes Chrome.
2. **AI model: use "Sonnet" as your default**, not the more expensive "Opus"/"Fable" tier models. Inside Claude Code, you can check or change this at any time by typing `/model` and picking the Sonnet option. The cheaper/faster model is the right default for this project — it's plenty capable for the tasks here, and using a heavier model will burn through your usage budget much faster for no benefit on this project.

---

## Part C. Install and Connect Your Tools

### If you're on macOS

**C.1 — Install a package manager (Homebrew), if you don't have one:**

Open the **Terminal** app (search for it with Spotlight: Cmd+Space, type "Terminal"). Paste this and press Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow any on-screen instructions it gives you (it may ask for your Mac password — that's normal, it's installing system-level software).

**C.2 — Install git, gh, and uv:**

```bash
brew install git gh uv
```

Verify each installed correctly:

```bash
git --version
gh --version
uv --version
```

Each command should print a version number, not an error. If any says "command not found," the install didn't finish — stop here and ask for help rather than continuing.

**C.3 — Install the Claude Code CLI:**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Verify:

```bash
claude --version
```

### If you're on Windows 11 (using WSL2)

Windows users will do almost everything **inside WSL2** (Windows Subsystem for Linux), not directly in Windows. This matters: your files, your terminal commands, and your code editor's connection to those files all need to agree on which "filesystem" they're using. Follow this carefully.

**C.1 — Install WSL2, if you don't have it:**

Open **PowerShell as Administrator** (right-click the Start button → "Terminal (Admin)" or "PowerShell (Admin)") and run:

```powershell
wsl --install
```

This installs WSL2 with Ubuntu Linux by default. Restart your computer when prompted. After restart, an Ubuntu terminal window should open automatically and ask you to create a Linux username and password — these are separate from your Windows login, and it's fine if they don't match. Remember them.

**C.2 — Open your WSL2 (Ubuntu) terminal for everything from here on.**

From now on, whenever this manual says "open a terminal," it means the **Ubuntu/WSL2 terminal**, not PowerShell or Command Prompt. You can find it by searching "Ubuntu" in the Start menu.

**C.3 — Update Ubuntu and install git, gh, uv:**

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git
```

Install GitHub CLI:

```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install -y gh
```

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close and reopen your Ubuntu terminal so the new tools are recognized, then verify:

```bash
git --version
gh --version
uv --version
```

**C.4 — Install the Claude Code CLI (inside WSL2):**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Verify:

```bash
claude --version
```

**Important WSL2 rule:** do all your work (cloning the repo, running commands) inside your Linux home directory (`~`, i.e. `/home/yourusername/...`), never under `/mnt/c/...`. `/mnt/c/` is how WSL2 sees your Windows `C:` drive, and running dev tools against it is slow and can cause confusing file-permission bugs. Everything in this manual assumes you're working in your Linux home directory.

### For everyone: create accounts and log in

**Create a GitHub account** (skip if you already have one): go to github.com in Chrome and sign up. Use a personal email address, not a school email tied to an account you might lose access to after graduating.

**Log in to GitHub in Chrome:** go to github.com and sign in, so your browser session is authenticated. You'll need this in Part E.

**Authenticate the GitHub CLI from your terminal:**

```bash
gh auth login
```

Choose: GitHub.com → HTTPS → "Login with a web browser." It will show you a one-time code and open Chrome — paste the code there and approve.

**Authenticate Claude Code:**

```bash
claude
```

The first run will prompt you to log in via your browser. Follow the prompt — it opens Chrome, you log into your Anthropic account (the one with your $20/month subscription attached), and approve. Once you see a prompt inside the terminal that looks like a chat interface, it worked. Type `/exit` to leave for now.

---

## Part C continued. Install and Configure VS Code

**Install VS Code:**

- **macOS:** download from code.visualstudio.com and drag it to Applications — a normal Mac app install, nothing special.
- **Windows/WSL2:** download and install VS Code **on Windows** (the normal Windows installer, not inside WSL2) from code.visualstudio.com. VS Code itself runs on Windows, but it connects *into* your WSL2 Linux filesystem via an extension (next step) — this is the correct setup and is not the same as opening files through `\\wsl$\...` in File Explorer.

**Install two extensions** (click the Extensions icon in the left sidebar — four squares icon — and search for each by name):

1. **"Python"** by Microsoft
2. **"Claude Code for VS Code"** by Anthropic

**Windows/WSL2 only — connect VS Code to your Linux filesystem:** install the **"WSL"** extension by Microsoft as well (search "WSL" in Extensions). Once installed, click the small green icon in VS Code's bottom-left corner and choose "Connect to WSL" — this reopens VS Code operating on your Linux files, which is what you want for every step from here on.

**Connect VS Code to your GitHub account:** click the Accounts icon (bottom-left, person-shaped icon) → "Sign in with GitHub" → follow the browser prompt. This lets VS Code show things like pull request status later, though for this project you'll do almost everything from the terminal.

---

## Part D. Set Up Your Local Code Folder

In your terminal (Ubuntu terminal if on Windows), create a folder to hold your coding projects, if you don't already have one:

```bash
mkdir -p ~/code
cd ~/code
```

`mkdir -p` won't complain or overwrite anything if `~/code` already exists — it's safe to run even if you've done this before.

---

## Part E. Fork and Clone Your Own Copy of the Website

"Forking" means making your own personal copy of a GitHub repository under your own account, which you can freely edit without affecting the original. "Cloning" means downloading that copy onto your laptop.

Ask your instructor for the exact URL of the course website repository (it will look like `https://github.com/<instructor-username>/<repo-name>`). Then, from `~/code`:

```bash
gh repo fork <instructor-username>/<repo-name> --clone=true
cd <repo-name>
```

This creates a fork under **your** GitHub account and downloads it directly into `~/code/<repo-name>`. Confirm it worked:

```bash
git remote -v
```

You should see two remotes: `origin` (your fork) and possibly `upstream` (the original course repo). If you only see `origin`, that's fine too — it points to your fork.

**A note on naming:** this manual and the tech-spec both assume the folder is called `theailab-net` (matching this repo). If `gh repo fork` names your local folder differently, either rename it to match (`mv <repo-name> theailab-net`) or just remember your own folder's actual name and substitute it wherever this manual says `theailab-net`.

---

## Part F. Create a Python Virtual Environment

The website itself is plain HTML/CSS with no build step — you don't need Python to *view* it. But the repo's **test suite** (which checks that every page's links work, every page has the right structure, etc.) is written in Python, so you need an isolated Python environment to run it.

From inside `~/code/theailab-net`:

```bash
uv venv --python=3.12
source .venv/bin/activate
```

You'll know it worked because your terminal prompt will now show `(.venv)` at the start of the line. This environment is isolated — installing test dependencies here won't affect any other Python project on your computer.

Install the test dependencies:

```bash
uv pip install -r tests/requirements.txt
```

**Note:** every time you close and reopen your terminal, you'll need to run `source .venv/bin/activate` again before running tests (but not before running Claude Code — that works regardless).

---

## Part G. Open Claude Code

From inside `~/code/theailab-net`:

```bash
claude --dangerously-skip-permissions
```

**Stop and read this before you run that command.** The `--dangerously-skip-permissions` flag tells Claude Code to make file edits and run terminal commands *without asking you to approve each one first*. It's genuinely convenient — you won't be interrupted every few seconds — but it also means Claude can, in principle, run a destructive command (delete a file, overwrite something) without a checkpoint where you could have said no.

For this project, that risk is low: you're working inside a disposable fork of a small course website, not production infrastructure or anything irreplaceable. If something goes badly wrong, you can always re-clone a fresh copy from Part E. That's *why* this flag is acceptable here — not because it's always safe. In any other context (a job, a personal project with data you haven't backed up), don't reach for this flag by default; use it deliberately, the way this manual does, only when the blast radius of a mistake is genuinely small and recoverable.

If you'd rather stay cautious for your first time using Claude Code, you can instead just run `claude` (without the flag) and approve each action as it's proposed — it'll be slower but you'll see exactly what's happening at each step, which can also be a good way to learn.

---

## Part H. Step 0 (Prerequisite) — Strip Netlify/CI, Then Critique the Site

Do these as two separate prompts to Claude Code, in order. Paste each one as-is into the Claude Code prompt.

### H.0 — Simplify to a standalone local site

```
Strip all code and files associated with Netlify and GitHub Actions CI/CD from
this repo (netlify.toml, .github/workflows/, and any Netlify-specific headers
or redirects). The goal is a simple, standalone static website that runs via a
local test webserver only (e.g. `python3 -m http.server`) — no deploy
pipeline, no external hosting config. Update the README to match: remove
deployment instructions and replace them with instructions for running the
site locally. Do not change any of the site's actual page content.
```

Read what Claude changed before moving on — ask it to summarize the diff if you're not sure what happened (`what did you just change and why?` is a perfectly good follow-up prompt).

### H.1 — Critique the codebase

```
Analyze the course website code in this repo and critique it for errors,
omissions, missing best practices, etc. Save your results in a complete,
clear, and well-structured report in docs/report_web-revision_v1_<YYYYMMDD>.md
```

(Replace `<YYYYMMDD>` with today's actual date, e.g. `20260915`.)

### H.2 — Turn the critique into a ranked tech-spec

```
Synthesize the critique in docs/report_web-revision_v1_<YYYYMMDD>.md into a
complete, clear, concrete, and well-structured tech-spec of all suggested
revisions, detailed as coherent specific tasks ranked by estimated criticality
in ['high','medium','low'], each with a concise description, justification,
and detailed step-by-step instructions on how to implement it. Save it in
docs/tech-spec_website-revision_v1_<YYYYMMDD>.md
```

Read the resulting tech-spec fully before moving to Part I. This is the plan you're about to execute — you should understand and agree with every task in it. If something in it seems wrong, unclear, or like a bad idea, say so to Claude now and ask it to revise that section — don't just implement something you don't understand or disagree with.

---

## Part I. Implement the Revisions

### I.1 — Work through the tech-spec task by task

```
Iterate over each of the tasks in
docs/tech-spec_website-revision_v1_<YYYYMMDD>.md, highest criticality first.
For each task: write or extend a test that captures what "done" means for
that task, implement the change, run the test suite, and if any test fails,
debug and revise until the entire suite passes before moving to the next
task. Tell me briefly after each task what changed and confirm tests are
green before continuing to the next one.
```

Watch what happens for at least the first two or three tasks rather than walking away — this is where you'll catch anything that looks off (an edit that seems too broad, a test that got deleted rather than fixed, etc.) before it compounds across the rest of the list. If Claude Code asks you a clarifying question at any point, that's normal — answer it based on your own judgment about what the site should do; the tech-spec is a plan, not a contract that removes your say.

### I.2 — Serve the finished site and view it

```
Now that all tech-spec tasks are complete and the test suite passes, serve
the revised website in this repo on an open localhost port and give me the
exact URL to open in my browser.
```

Open the URL it gives you in **Chrome**. Click through every page — Home, Syllabus, Schedule, Assignments, Policies, About, and at least two or three week pages — and confirm the site looks right and nothing is broken. This manual check matters: passing tests confirm the code is *structurally* correct, not that the page actually looks and reads the way you want. Only a human looking at the rendered page can confirm that.

---

## Part J. What Was Wrong With the Original Steps (and Why This Manual Is Different)

If you compare this manual against the raw step list some earlier version of this project was based on, here's what changed and why — useful context if you're ever handed a similarly terse instruction set in the future and need to judge it yourself:

- **Order of operations was fixed.** The original had "create a GitHub account" and "connect VS Code to GitHub" scattered after tool installation instead of grouped with authentication; this manual groups all account creation and login together (Part C) so you do it once, in a sensible order, instead of jumping back and forth.
- **WSL2 and macOS were fully separated, not interleaved.** Giving a Windows user and a Mac user the same paragraph with "(on Win)" parentheticals invites mistakes — a Windows user running a macOS-only Homebrew command, for instance. This manual gives each platform its own complete track.
- **The risky flag (`--dangerously-skip-permissions`) is explained, not just handed over.** The original instructions used it with no comment. Skipping every permission check is a real trade-off, not a neutral default — this manual tells you what it costs, why it's an acceptable trade *for this specific low-stakes project*, and gives you a slower-but-safer alternative if you'd rather not use it, especially your first time.
- **"Source a venv" was explained, not assumed.** Someone who has never used Python won't know what "activate" means or that it needs to be re-run every new terminal session — that's spelled out here.
- **Date placeholders were made explicit.** The original tech-spec/report filenames hardcoded a single date (`v1_20260901`); this manual uses `<YYYYMMDD>` placeholders and tells you to substitute today's actual date, since you'll be running this weeks or months after this manual was written.
- **A "read before you proceed" checkpoint was added after the tech-spec step (end of Part H).** The original flow went straight from "generate a tech-spec" to "implement every task in it" with no instruction to actually read and sanity-check the plan first. Blindly executing an AI-generated plan without reading it defeats the point of having a human in the loop — this manual makes that pause explicit.
- **"Watch the first few tasks" guidance was added to Part I.** The original just said iterate through all tasks until done. For a first-time user, walking away entirely during an unattended multi-task AI implementation run is how small mistakes (an overly broad edit, a test quietly weakened instead of fixed) go unnoticed until much later. Staying engaged for the first few tasks calibrates your trust in the rest of the run.
- **A manual visual check was added at the end (Part I.2).** Automated tests passing does not mean a page looks or reads correctly — someone has to actually look at it in a browser. The original implicitly treated "tests pass" as equivalent to "done."
- **Clarified that AI-assisted reading of this manual is expected, not a shortcut around it.** Non-STEM students in particular may feel like asking "what does this term mean" mid-task is cheating or a sign they're behind — it's normal and expected here, as long as it's used to understand each step rather than to skip evaluating it.

---

## Troubleshooting Quick Reference

| Symptom | Likely cause | Fix |
|---|---|---|
| `command not found: git` / `gh` / `uv` / `claude` | Install didn't finish, or terminal wasn't restarted | Close and reopen your terminal; re-run the install command; re-check with `--version` |
| `gh auth login` doesn't open a browser | Running in an environment without a display, or Chrome isn't your default browser | Use the code it prints and open the URL manually in Chrome |
| `pytest` says "command not found" | Virtual environment isn't activated | Run `source .venv/bin/activate` from inside `~/code/theailab-net` first |
| Site pages look unstyled (no CSS) when opened via `file://` | Some browsers block local stylesheet loading for files opened directly | Always view the site through the localhost URL Claude gives you (Part I.2), not by double-clicking the HTML file |
| WSL2: everything feels slow or file changes don't show up in VS Code | You're working under `/mnt/c/...` instead of your Linux home directory | Move the project into `~/code` inside WSL2 (see the WSL2 note in Part C) |
| Claude Code seems to be doing something you didn't expect | — | You can always interrupt it (Ctrl+C or just type a message) and ask it to explain or undo. Nothing it does is unrecoverable as long as you're working in your own fork with git history intact (`git status` / `git diff` will show you exactly what changed) |
