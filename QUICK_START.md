# Quick Start Guide - JD-Resume Matching

## 🚀 Get Started in 5 Minutes

### Step 1: Configure API Key

Edit `.env` file and add your OpenRouter API key:

```bash
OPEN_ROUTER_KEY=sk-or-v1-your-actual-key-here
```

Don't have an API key? Get one at: https://openrouter.ai/

**Alternative**: Use OpenAI directly by modifying `services/jd_parser.py` and `services/resume_enricher.py`:

```python
# Change this:
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPEN_ROUTER_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# To this:
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)
```

---

### Step 2: Test the Implementation

Run the test script to validate everything works:

```bash
cd /Users/amulyaalva/Documents/Documents-\ Feb\ 2026/MVP\ -\ Resume\ Intelligence/ResumeIntelligence
python3 test_matching.py
```

**Expected Output:**
```
================================================================================
TESTING JD-RESUME MATCHING WORKFLOW
================================================================================

📋 Job Description: Senior DevOps Engineer (5+ years)
📄 Candidates: 3 resumes

🔍 Parsing job description...
📄 Processing 3 resumes...
  Processing candidate 1/3...
  Processing candidate 2/3...
  Processing candidate 3/3...
📊 Ranking candidates...

================================================================================
RESULTS
================================================================================

🎯 JD Requirements:
   Must-have skills: AWS, Docker, Kubernetes, CI/CD, Terraform...
   Years required: 5
   Seniority: Senior

🏆 Candidate Ranking:

  ✅ Rank #1: Candidate_1
     Score: 85.0/100 | Recommendation: Shortlist
     Summary: 9/10 skills matched, 6 years experience
     Skills: 9 matched, 1 missing
     Penalty: -8 points

  ⚠️ Rank #2: Candidate_2
     Score: 68.0/100 | Recommendation: Review
     Summary: 6/10 skills matched, 4 years experience
     Skills: 6 matched, 4 missing
     Penalty: -6 points

  ❌ Rank #3: Candidate_3
     Score: 32.0/100 | Recommendation: Reject
     Summary: 4/10 skills matched, 2 years experience
     Skills: 4 matched, 6 missing
     Penalty: -19 points

================================================================================
TEST COMPLETED
================================================================================
```

---

### Step 3: Launch the Dashboard

Start Streamlit:

```bash
streamlit run app.py
```

Navigate to: **"🎯 JD-Resume Matching"** in the sidebar

---

### Step 4: Try a Quick Example

#### Option A: Use Sample Data (Paste Text)

1. **Paste this JD:**

```
Senior Software Engineer - Backend

Requirements:
- 5+ years of backend development experience
- Expert in Python, Django/Flask, and REST APIs
- Strong SQL database skills (PostgreSQL, MySQL)
- Experience with AWS or GCP
- Docker and Kubernetes
- CI/CD pipelines (Jenkins, GitHub Actions)
- Microservices architecture
- Redis/Memcached caching

Nice to have:
- GraphQL
- Message queues (RabbitMQ, Kafka)
- Terraform

Domain: SaaS, Fintech
```

2. **Paste 2 resumes** (use "Paste Text (Multiple)" option):

**Resume 1 (Strong):**
```
ALEX CHEN
Senior Backend Engineer

EXPERIENCE
Senior Backend Engineer | TechStartup Inc. | 2020-2024 (4 years)
- Built RESTful APIs using Python/Django serving 1M+ requests/day
- Optimized PostgreSQL queries, reducing response time by 55%
- Deployed microservices on AWS ECS using Docker/Kubernetes
- Implemented Redis caching, improving latency by 40%
- Saved $80K/year by migrating from EC2 to Lambda for batch jobs

Backend Engineer | WebCorp | 2018-2020 (2 years)
- Developed Flask APIs for e-commerce platform
- Built CI/CD pipelines using Jenkins
- Managed MySQL databases with 10M+ records

SKILLS
Python, Django, Flask, PostgreSQL, MySQL, AWS, Docker, Kubernetes,
Redis, Jenkins, GitHub Actions, REST APIs, Microservices

EDUCATION
BS Computer Science | 2018
```

**Resume 2 (Weak):**
```
JORDAN SMITH
Software Developer

PROFILE
Passionate and motivated software developer with proven track record.
Dynamic team player committed to delivering innovative solutions.

EXPERIENCE
Software Developer | OldCompany | 2016-2018
- Worked on various backend projects
- Collaborated with cross-functional teams
- Implemented best practices
- Delivered high-quality code

Junior Developer | StartupXYZ | 2015-2016
- Assisted in software development
- Maintained existing codebase

SKILLS
Python, Java, SQL, AWS, Docker, Agile, Leadership, Innovation
```

3. **Click "🚀 Run Matching & Ranking"**

4. **View Results:**
   - Alex Chen: ~75-85 score (Shortlist)
   - Jordan Smith: ~35-45 score (Reject)

---

#### Option B: Upload Resume Files

If you have PDF/DOCX resumes:

1. Paste JD text (or upload JD file)
2. Select "Upload Files" for resumes
3. Upload multiple PDF/DOCX files
4. Run matching

---

### Step 5: Explore Features

#### Filter Results
- **Minimum Score**: Move slider to show only high-scoring candidates
- **Recommendation Filter**: Show only "Shortlist" to see top candidates

#### View Detailed Reports
- Click on any candidate's expandable row
- See full markdown explanation
- View score breakdown chart

#### Export Data
- **Download Ranking Table (CSV)**: All candidates with metrics
- **Download Shortlist (CSV)**: Only top candidates

---

## 📊 Understanding the Scores

### Score Components

| Component | Max Points | What It Measures |
|-----------|-----------|------------------|
| **Skill Coverage** | 30 | How many required skills are matched |
| **Experience Depth** | 20 | Years of experience + seniority match |
| **Domain Relevance** | 15 | Industry/domain match |
| **Evidence Quality** | 15 | Projects + skill context |
| **Quantification** | 10 | Measurable outcomes (%, $, numbers) |
| **Recency** | 10 | How recent is the experience |
| **Penalties** | -0 to -20 | Buzzwords, vague claims, outdated |

### Recommendations

- **Shortlist (>=75)**: Strong candidates → proceed to interview
- **Review (60-74)**: Potential fits → phone screen
- **Reject (<60)**: Poor fits → decline

---

## 🔍 What to Look For

### Good Resume Signals ✅
- **Specific projects**: "Built payment gateway processing 10K transactions/day"
- **Quantified achievements**: "Reduced deployment time by 65%"
- **Recent experience**: 2022-2024 roles
- **Context for skills**: "Python - Built REST APIs using FastAPI"

### Red Flags 🚩
- **Vague claims**: "Worked on various projects"
- **Buzzwords only**: "Synergy, leverage, disrupt, innovative"
- **No numbers**: No %, $, or metrics
- **Outdated**: No recent (2022+) experience
- **Missing context**: Lists "Docker" without explaining usage

---

## 🐛 Troubleshooting

### Issue: API Authentication Error

**Error Message:**
```
openai.AuthenticationError: Error code: 401
```

**Solution:**
Check your `.env` file and ensure `OPEN_ROUTER_KEY` or `OPENAI_API_KEY` is set correctly.

---

### Issue: Import Error

**Error Message:**
```
ModuleNotFoundError: No module named 'langgraph'
```

**Solution:**
Install dependencies:
```bash
pip install -r requirements.txt
```

---

### Issue: No Results Showing

**Solution:**
1. Check that you provided both JD and resumes
2. Lower the "Minimum Score Filter" slider
3. Enable all recommendation types (Shortlist/Review/Reject)

---

### Issue: Slow Processing

**Reason:** LLM API calls take time (~5-10 seconds per resume)

**Tips:**
- Start with 2-5 resumes for testing
- Increase batch size for production
- Consider caching JD parsing (same JD, multiple batches)

---

## 📝 Demo Script (7-Minute Walkthrough)

### Minute 0-1: Introduction
"This is the Resume Intelligence MVP implementing the PRD requirements. It provides explainable, evidence-based candidate screening using a 100-point rubric."

### Minute 1-2: JD Upload
"First, we paste a Senior DevOps Engineer job description requiring AWS, Kubernetes, Docker, etc."

### Minute 2-3: Resume Upload
"Next, we upload 5 candidate resumes using the file upload feature."

### Minute 3-4: Run Matching
"We click 'Run Matching & Ranking' and wait ~30 seconds for processing..."

### Minute 4-5: View Rankings
"Here's the ranking table. Notice candidate #1 scored 85/100 and is recommended for shortlist. Candidate #5 scored 35/100 and is rejected. The table shows matched skills, experience years, and penalties."

### Minute 5-6: Detailed Breakdown
"Let's expand candidate #1. We see a full explanation with 6 score components:
- Skill Coverage: 27/30 (9/10 skills matched)
- Experience Depth: 18/20 (6 years, exceeds requirement)
- Domain Relevance: 15/15 (all domains matched)
- Evidence Quality: 13/15 (4 projects with strong context)
- Quantification: 10/10 (6 measurable outcomes like 'Reduced latency by 60%')
- Recency: 10/10 (most recent role: 2024)

The system detected 2 minor risk flags for -8 penalty points."

### Minute 6-7: Export & Summary
"We can export the ranking table as CSV or download just the shortlisted candidates. The system provides clear recommendations: Shortlist, Review, or Reject. This is production-ready for recruiter workflows."

---

## 🎯 Next Steps

1. **Test with Real Data**: Upload 10-20 actual resumes from your hiring pipeline
2. **Calibrate Thresholds**: Adjust recommendation thresholds if needed (currently 75/60)
3. **Validate Accuracy**: Compare system rankings to human recruiter judgments
4. **Customize Rubric**: Modify scoring weights in `scoring_engine.py` if needed
5. **Integrate**: Connect to your ATS or workflow tools

---

## 📚 Documentation

- **IMPLEMENTATION_SUMMARY.md**: Full feature list and technical details
- **ARCHITECTURE.md**: System design and data flow diagrams
- **test_matching.py**: Sample test script with 3 resumes

---

## 💡 Tips for Best Results

### Write Better JDs
- Clearly specify "must-have" vs "nice-to-have" skills
- Include experience requirements (e.g., "5+ years")
- Mention domain/industry (e.g., "fintech", "healthcare")

### Improve Resume Quality
- Encourage candidates to include specific projects
- Ask for quantified achievements (%, $, scale)
- Request recent experience dates

### Tune Scoring
- If too many rejections: Lower thresholds (e.g., 70/55 instead of 75/60)
- If too many false positives: Increase penalty weights in `risk_detector.py`

---

**Quick Start Version**: 1.0
**Last Updated**: February 8, 2026
**Status**: ✅ Ready to Use
