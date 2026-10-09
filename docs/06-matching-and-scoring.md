# 06. Matching and Scoring
 
The score is a decision aid, not a probability of being hired. Every point can be traced to a rule in `config/scoring.yaml`, and the breakdown is stored with each job.
 
## Step 1. Hard filters (before scoring)
A job that fails is excluded, logged with a reason and never notified.
 
| Filter | Examples |
|---|---|
| Region restriction | "US residents only", "must be authorized to work in the US/UK/EU", "must reside in Canada" (pattern list in config) |
| Expired | Deadline earlier than today |
| Scam patterns | "registration fee", "pay to apply", "commission only", "MLM", "training fee", messaging-app-only applications |
| Excluded titles | Telemarketer, pure sales roles (configurable) |
| Off-topic | No support-related keyword in title, and none in the first 300 characters of the description |
| Age | Posted more than 30 days ago (unless deadline is still ahead) |
 
Restricted-region wording is the most common time-waster for Kenya-based applicants, so it runs first.
 
## Step 2. Score (100 points)
 
| Factor | Max | Rule |
|---|---|---|
| Title relevance | 25 | Strong-list exact match 25. Strong fuzzy (similarity 85 or more) 22. Potential-list exact 18, fuzzy 15. Stretch-list 10, fuzzy 8. Other support keyword in title 5 |
| Skills overlap | 25 | 25 x (matched weight / total weight). Required skills weight 2, preferred weight 1. Partial skills count 0.5. If the job lists no skills, 12 points and a "skills not listed" note |
| Location and eligibility | 20 | Remote open to Kenya, Africa or worldwide 20. Nairobi on-site or hybrid 20. Other Kenyan city 16. Remote with EAT-compatible timezone 16. Remote with region unstated 10 (flag "eligibility unconfirmed"). East Africa on-site (relocation) 8. Other international on-site 4. Restricted: excluded by filter |
| Experience level | 10 | Job asks 3 to 8 years 10. Asks 1 to 3 years or entry 8. Not stated 7. Senior or lead 6. Manager or director 2 |
| Salary | 10 | Listed and at or above floor 10. Listed below floor 2. Unlisted, or no floor set 5. (Floor is currently unset, so salary is neutral. Salary is still displayed) |
| Freshness | 5 | Posted 3 days or less 5, 7 days 4, 14 days 3, 30 days 1, older 0 |
| Industry | 5 | Preferred industry 5, neutral 3, avoided 0 |
 
**Tiers**
| Tier | Score | Meaning |
|---|---|---|
| Top | 85 or more | Apply first |
| Strong | 75 to 84 | Good fit, apply |
| Potential | 50 to 74 | Worth a look, check gaps |
| Weak | under 50 | Stored, not notified |
 
The digest shows Top and Strong, plus up to 5 Potential jobs.
 
## Skills extraction (v1, no machine learning)
- A dictionary of canonical skills and tools with synonyms in `scoring.yaml` (for example "customer relationship management" maps to CRM; "help desk" and "service desk" map to ticketing).
- Sections headed "requirements", "must have" or "qualifications" mark required skills. "Nice to have" and "preferred" mark preferred ones. With no section headings, all are treated as required.
- The candidate side comes from `profile.yaml`. Partial skills are declared there (for example networking basics from the Cisco certificate).
- An optional LLM-assisted extractor may be added later. It is off by default and would treat scraped text strictly as untrusted data.
## Gaps and recommendations
Each scored job gets:
- **Skills matched** and **skills missing**, from the extraction above.
- **Transferable strengths**, using a mapping such as: payment follow-up to collections and billing support; dispatch coordination to order and logistics support; cash and POS handling to billing and finance support; Cisco certificate to technical aptitude; WhatsApp support to chat support.
- **Recommended action**, chosen by rule:
  - Top or Strong and deadline within 3 days: "Apply now".
  - Top or Strong: "Tailor CV to matched skills, apply within 3 days".
  - Missing tool is a common one (Freshdesk, Intercom, Salesforce): "Add a line on similar tool experience; consider a free course".
  - Eligibility unconfirmed: "Check country eligibility before applying".
  - Potential: "Review gaps, apply if the role appeals".
## Worked examples (using the current profile)
 
**Example A. Customer Support Specialist, remote SaaS, open to Africa**
Requires Zendesk, Freshdesk, ticketing, English; prefers CRM and live chat. Salary 800 to 1,200 USD. Posted 2 days ago. Asks 3+ years.
| Factor | Points | Why |
|---|---|---|
| Title | 25 | Strong-list exact |
| Skills | 17.5 | Required weight 8, matched 6 (Zendesk, ticketing, English). Preferred weight 2, matched 1 (CRM). 7 of 10 |
| Location | 20 | Remote, Africa-eligible |
| Experience | 10 | 3+ years |
| Salary | 5 | Listed, no floor set |
| Freshness | 5 | 2 days |
| Industry | 3 | Neutral |
| **Total** | **85.5** | **Top.** Missing: Freshdesk, live chat. Action: tailor CV around Zendesk and ticketing, apply within 3 days |
 
**Example B. Customer Care Representative, Nairobi bank, on-site**
Requires complaint handling, CRM, Swahili, customer service; 2 years. No salary. Posted 5 days ago, deadline in 12 days.
Title 25, skills 25 (all matched), location 20, experience 8, salary 5, freshness 4, industry 3 = **90, Top.** Action: apply this week.
 
**Example C. Customer Support Agent, "US residents only"**
Hard filter: region restriction. **Excluded**, logged with the matched phrase.
 
**Example D. Technical Support Engineer, remote worldwide**
Requires Linux, scripting, networking, ticketing; 3+ years.
Title 10 (stretch), skills 9.4 (ticketing matched 2, networking partial 1, total 3 of 8), location 20, experience 10, salary 5, freshness 5, industry 3 = **62.4, Potential.** Missing: Linux, scripting. Action: review gaps, apply only if the role appeals.
 
## Calibration and versioning
1. In Phase 4, the owner labels about 30 real jobs (apply, maybe, skip).
2. Compare labels with tiers. Target at least 80% agreement between Top/Strong and "apply".
3. Adjust weights only in `scoring.yaml`, and increment `scoring_version`. Stored breakdowns include the version so old scores stay explainable.
## Known limitations
Keyword extraction misses unusual phrasing. Eligibility text can be ambiguous, hence the "unconfirmed" flag. Salary in mixed currencies is not compared. The score cannot judge employer quality or scams beyond the pattern list, so always read the posting.
 
