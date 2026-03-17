# Red Team Image Bias Evaluation

AI image generators have biases. The people most affected by those biases should be the ones evaluating them. This tool lets you run a workshop where participants from any community can test how current image generation systems see them, flag what's wrong, and explain why it matters.

## Background

This tool grows out of work on [Humane Intelligence's](https://humane-intelligence.org/) public red teaming exercises and the [IMDA Singapore AI Safety Red Teaming Challenge](https://airedteaming.sg/). Those projects demonstrated the value of participatory red teaming - bringing affected communities into the evaluation process - but were focused on text-based LLMs, ran as one-off events, and used proprietary platforms.

This app fills the gap: an open-source, self-hostable tool purpose-built for **image generation** bias, designed to be reused by any facilitator with any community.

## What this is

A workshop-in-a-box for evaluating bias in AI image generation. A facilitator brings together 12-18 participants from any community, and participants use their lived experience to probe how current systems depict their cultures, identities, and daily lives. The app captures both quantitative scores and qualitative written observations, producing data suitable for academic publication.

### Systems under test

The app evaluates 4 commercial image generation models from major US and Chinese technology companies. Models span a range of architectures and training approaches, including both diffusion and autoregressive methods. Participants see randomized blind names instead of real model names to prevent brand bias from influencing their ratings.

### Workshop flow

1. **Welcome & consent** (30 min) -- Orientation, registration, informed consent
2. **Shared prompts** (15 min) -- All participants rate the same 5 prompts (so you can compare how different people experience the same images)
3. **Free exploration** (75 min) -- Participants write their own prompts and judge the outputs
4. **Group discussion** (60 min) -- Identify patterns together (in-person, not in the app)

### What participants do

1. Enter a passcode you give them to access the workshop
2. Write prompts that test how the models represent their community (e.g. "A successful Pakistani businesswoman giving a keynote speech")
3. See images from all 4 systems side by side
4. **Triage** each system: "Looks fine", "Problematic", or "Nonsensical"
5. Write detailed explanations for the problematic ones -- what they expected, whether it feels authentic, and what the real-world impact of any bias is
6. When a model refuses to generate, they explain why that erasure matters

### What you get as a facilitator

- A live dashboard showing participant progress, emerging patterns, and alerts
- Anonymized data (real names stored separately from ratings)
- Summary statistics by model, bias category, and community
- Inter-rater reliability from the shared prompts
- One-click export to JSON, CSV, or a formatted Markdown report

## What you need

- A GitHub account (free)
- API keys from 3 providers (see below)
- About $80-150 for API costs
- A laptop to manage the workshop

No programming or server experience is required if you use the recommended deployment option (Streamlit Community Cloud).

## Setting up (step by step)

### 1. Fork the repository

Go to this project's GitHub page and click **Fork** in the top right. This creates your own copy that you can customize.

### 2. Get API keys

You need to create accounts with 3 providers and get an API key from each. This takes about 15 minutes.

**OpenAI** -- [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- You'll need to add a credit card
- Go to Settings > Billing and set a monthly limit of $60 to avoid surprises
- Create a new API key and copy it somewhere safe

**Replicate** -- [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens) (powers 2 of the 4 models)
- Sign up with GitHub
- Add $20 of credit under Billing
- Copy your API token from the account page

**Google AI Studio** -- [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- Sign in with a Google account
- Click "Create API key" -- no credit card needed for the free tier
- If you hit the free tier limit during the workshop, you can add billing later

**DashScope** (optional) -- [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/)
- Only needed if you enable the optional Qwen model
- Skip this for your first workshop

### 3. Estimate costs

With 15 participants, each generating ~10 prompts with 2 images per system:

| Provider | Approx. cost per image | Est. workshop total |
|----------|----------------------|---------------------|
| OpenAI | $0.04 | ~$50 |
| Replicate (x2 models) | $0.01-0.05 | ~$30-60 |
| Google | Free tier or ~$0.02 | ~$0-25 |

**Budget roughly $80-150 for a full workshop.** Start with the amounts above and top up if needed during the session.

### 4. Create passcodes

Create one passcode per participant, plus one for yourself as facilitator. These can be any words -- keep them short and easy to type, since participants will enter them on their phones or laptops (e.g. `sunrise`, `river`, `mountain`).

Write them down or print them on slips of paper to hand out at the start of the workshop.

### 5. Deploy the app

#### Recommended: Streamlit Community Cloud (free, no server needed)

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account
2. Click **New app** and select your forked repository
3. Set the main file to `app.py`
4. Click **Advanced settings** and paste your secrets in this format:

```
OPENAI_API_KEY = "sk-..."
REPLICATE_API_TOKEN = "r8_..."
GOOGLE_API_KEY = "AI..."
PARTICIPANT_TOKENS = "sunrise,river,mountain,forest,ocean"
FACILITATOR_TOKEN = "your-facilitator-passcode"
```

5. Click **Deploy**. In a few minutes you'll get a public URL (e.g. `https://your-app.streamlit.app`) that participants can open in any browser.

That's it. No terminal, no server, no installation.

> **Note:** The free tier works well for workshops up to ~15 people. If images are slow to generate, it's usually the API providers, not Streamlit.

#### Alternative: self-hosted

If you prefer to run the app on your own server (for more control or to keep data on your own infrastructure), see the [self-hosting guide](#self-hosting) at the bottom of this page.

### 6. Do a dry run

Before the workshop, open your app URL and test the full flow yourself:

1. Enter a participant passcode and register
2. Complete one shared prompt (generate images, triage, rate)
3. Write one free prompt and go through the same flow
4. Log out, then enter your facilitator passcode and check the dashboard shows your test data
5. Try the export buttons

This takes 10 minutes and will catch any API key problems before workshop day.

## During the workshop

- Open the app in your browser and enter your **facilitator passcode** to see the live dashboard
- The dashboard auto-refreshes every 30 seconds (toggle in sidebar)
- Watch for **alerts**: models with many refusals, very low scores, or high disagreement between raters
- If a participant's images fail to generate, ask them to click "Generate" again -- the app retries automatically
- Participants can take breaks at any time; their progress is saved after each rating
- If a participant accidentally closes their browser, they'll need to re-register with a new passcode (their previous ratings are still saved on the server)

## After the workshop

Use the **Data Export** section on the facilitator dashboard:

- **JSON** -- all raw data, suitable for analysis in Python, R, or any tool that reads JSON
- **CSV** -- summary statistics table, opens directly in Excel or Google Sheets
- **Markdown report** -- a formatted summary with findings, quotes, and statistics, ready to paste into a paper draft

You can also click **Preview Report** on the dashboard to see the report before downloading.

## Adapting for your own workshop

To customize the app for a different community, set of models, or research question, you'll need to edit a configuration file called `config.py`. If you deployed on Streamlit Cloud, you can edit this file directly on GitHub (click the file, then the pencil icon).

Things you can change:

- **Models** -- swap in different image generation systems (you'll also need to add code for new APIs in `data.py` -- this part requires Python knowledge)
- **Shared prompts** -- change the 5 prompts everyone rates. Pick prompts relevant to your participants' communities.
- **Bias categories** -- add or rename the categories participants choose from (e.g. profession, appearance, cultural, religious)
- **Participant communities** -- update the list of backgrounds in the registration form
- **Scoring rubric** -- modify the rating scales, labels, or add new dimensions
- **Prompt target** -- change the suggested number of free prompts per participant (default: 8)

## Data and privacy

- Participant names are stored separately from their ratings
- Ratings use anonymous IDs only (e.g. `P-a3f8b2c1`)
- All data stays on your server (or Streamlit's servers if using Community Cloud)
- Participants can download their own data from the results page
- The app blocks search engine indexing

## Troubleshooting

**"Invalid token" when entering a passcode**
Check that your passcodes in the secrets/`.env` file match exactly what you're typing. They are case-sensitive. Make sure there are no extra spaces around the commas in `PARTICIPANT_TOKENS`.

**Images fail to generate for one system**
That system's API may be temporarily overloaded or the API key may be invalid. Ask the participant to try again. If one system consistently fails, check your API key and billing for that provider. The other systems will still work -- a failed system shows an error message but doesn't block the rest.

**Dashboard shows no participants**
Make sure you're entering the facilitator passcode, not a participant passcode. Participant data appears on the dashboard only after they complete at least one rating.

**App is slow or unresponsive**
Image generation takes 5-30 seconds per system depending on the API. This is normal. If the app itself is unresponsive (not just waiting for images), try refreshing the browser. On Streamlit Community Cloud, the app may "sleep" after inactivity -- just reload and it restarts in about 30 seconds.

---

## Self-hosting

If you need more control over the deployment, here are two options for running the app on your own server.

### Prerequisites

- A server or VPS (DigitalOcean, Hetzner, AWS, etc.)
- Basic comfort with a terminal (SSH, running commands)
- Python 3.10+ installed on the server

### Option A: Run directly (simplest)

```bash
git clone <your-repo-url>
cd image-eval-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys and passcodes

# Run in the background
nohup streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true &
```

The app runs at `http://your-server-ip:8501`. For HTTPS, put it behind a reverse proxy like Caddy or nginx.

### Option B: Docker (auto-restarts on crash)

Install [Docker](https://docs.docker.com/get-docker/) on your server, then:

```bash
docker build -t image-eval-app .
docker run -d --name image-eval-app --restart always \
  -p 8501:8501 \
  --env-file .env \
  -v /path/to/persistent/data:/app/red_team_data \
  image-eval-app
```

The container includes a health check and restarts automatically if Streamlit stops responding. For HTTPS, add a reverse proxy. Streamlit requires WebSocket support:

```nginx
location / {
    proxy_pass http://localhost:8501;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

## Project structure

```
app.py              Entry point, routing, session state, sidebar
config.py           Models, blind names, rubric, shared prompts, tokens
data.py             Annotations, identity, image generation APIs, retry logic
components.py       Scoring forms, image grid, validation
analysis.py         Aggregation, inter-rater reliability, report generation
views/
  _1_welcome.py     Passcode gate, registration, informed consent
  _2_shared_prompts.py  Shared prompts for inter-rater reliability
  _3_explore.py     Free exploration (participant-driven prompts)
  _4_annotate.py    Deep-dive scoring for problematic systems
  _5_results.py     Per-participant results and data download
  _6_gallery.py     Triage page (Looks fine / Problematic / Nonsensical)
  _7_facilitator.py Facilitator dashboard
tests/
  test_data.py      Data layer tests
  test_analysis.py  Analysis function tests
```

## Running tests

```bash
python -m pytest tests/ -v
```

## License

MIT

---

A project of [Future Ethics](https://futureethics.ai).
