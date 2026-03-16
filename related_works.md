# Related Works: Participatory Red Teaming for Bias in Image Generation

## Most Directly Relevant: Participatory Red Teaming

### [Dark and Bright Side of Participatory Red-Teaming with Targets of Stereotyping](https://arxiv.org/abs/2602.19124) (CHI 2026, very recent)
- Empirical study of participatory red-teaming with people targeted by stereotypes
- Key finding: Participants transformed discrimination into expertise for identifying biases
- **Critical caveat:** Single 45-min session caused psychological harm—weakened critical thinking, internalized new stereotypes
- Implications: Your workshops need careful design around psychological safety, debriefing, and duration
- Suggests need for participant support/debriefing protocols

### [AI red-teaming is a sociotechnical problem: on values, labor, and harms](https://arxiv.org/abs/2412.09751)
- Frames red-teaming as labor, not just methodology
- Raises questions about: Who performs red-teaming? What are the labor conditions? What are the ethical implications?
- Directly relevant to your design—how will you structure participation to be ethical?

### [Ask What Your Country Can Do For You: Towards a Public Red Teaming Model](https://arxiv.org/abs/2510.20061)
- Proposes public, jurisdiction-based red teaming (open to all residents 18+)
- Could inform your model for Oxford-based recruitment

### [UNESCO Red Teaming Playbook](https://globalteacherprize.org/news/community-news/1946/1946-New-UNESCO-Playbook-Helps-Communities-Red-Team-AI-for-Social-Good)
- Hands-on guide for testing generative AI for bias/stereotypes
- Designed for civil society, educators, policymakers
- May provide structured methodology you can adapt

---

## Bias in Image Generation: Specific to Your Models

### [A Large Scale Analysis of Gender Biases in Text-to-Image Generative Models](https://arxiv.org/abs/2503.23398) (2025)
- Tests Flux, Stable Diffusion 3.5, and others
- Proposes automatic evaluation protocols
- Results show: gender stereotypes in professions, gendered attribute associations

### [Easily Accessible Text-to-Image Generation Amplifies Demographic Stereotypes at Large Scale](https://arxiv.org/abs/2211.03759)
- Broad analysis of stereotyping across multiple models
- Documents racial homogenization (e.g., "Middle Eastern man" → always bearded, brown-skinned, traditional dress)
- Shows stereotypes emerge from ordinary prompts, not just adversarial ones

### [New Job, New Gender? Measuring Social Bias in Image Generation Models](https://arxiv.org/abs/2401.00763)
- Specifically tests profession-based gender stereotyping
- Directly relevant to your "professional roles" category of prompts

### [Can we Debias Social Stereotypes in AI-Generated Images?](https://arxiv.org/abs/2505.20692)
- Recent study examining user perceptions of bias
- Tests whether debiasing strategies actually work from user perspective

### [Auditing and Instructing Text-to-Image Generation Models on Fairness](https://link.springer.com/content/pdf/10.1007/s43681-024-00-531-5.pdf) (AIES 2024)
- Proposes Fair Diffusion framework (deployable without retraining)
- Relevant if you want to test mitigation strategies

### [Data Bias Mitigation and Evaluation Framework for Diffusion Models](https://openaccess.thecvf.com/content/ICCV2025W/STREAM/papers/Yu_Data_Bias_Mitigation_and_Evaluation_Framework_for_Diffusion-based_Generative_Face_ICCVW_2025_paper.pdf) (ICCV 2025 Workshop)
- Recent technical approach to bias evaluation in facial generation

---

## Participatory Auditing & Cross-Cultural Approaches

### [Algorithmic Auditing and Social Justice: Lessons from Audit Study History](https://dl.acm.org/doi/fullHtml/10.1145/3465416.3483294)
- Frames algorithmic auditing within social justice history
- Shows how non-experts identify novel bias dimensions (e.g., teens noticed "age" bias via wrinkles/gray hair that professionals missed)
- **Key insight:** Participatory auditing adds construct validity

### [Bias in AI Systems: Integrating Formal and Socio-Technical Approaches](https://pmc.ncbi.nlm.nih.gov/articles/PMC12823528/)
- Shows bias magnitude varies by jurisdiction and local marginalization history
- **Critical for your cross-cultural framing:** U.S. findings don't generalize globally; you need localized audits

### [Cultural Diversity and AI: Toward a Pluralistic Framework](https://www.ojed.org/STEM/article/view/9644)
- Proposes co-creating datasets with language communities
- Culturally grounded governance model
- Relevant to how you frame "authentic" vs. "stereotyped" representation

---

## Red-Teaming LLMs (Methodological Reference)

### [STAR: Sociotechnical Approach to Red Teaming Language Models](https://arxiv.org/abs/2406.11757)
- Frameworks for structured red-teaming (methodology you could adapt for images)
- Discusses how to recruit diverse red teamers

### [The Human Factor in AI Red Teaming](https://arxiv.org/abs/2407.07786)
- Perspective on social/collaborative computing in red-teaming
- Relevant for designing workshop dynamics

---

## What Your Project Should Contribute

Based on this review, **your unique angle is:**

1. **Image-specific + cross-cultural participatory approach** — Most bias eval in image generation is either:
   - Automated metrics (misses lived experience)
   - Ad-hoc audits (not systematic or rigorous)
   - LLM red-teaming (not images)
   - Single-culture datasets

2. **Ethical design around psychological safety** — The CHI 2026 paper flagged harms; you could design around this (longer engagement, better debriefing, support structures)

3. **Experiential vs. technical bias framing** — Your paper could argue: "Bias isn't just statistical skew; it's how marginalized communities experience the system"

4. **Cross-regional findings** — Pakistan + Iran + Turkey perspectives on representation in Western-trained models (fills the gap in current "US-centric bias research")

---

## Key Recommendations for Your Design

Based on this literature:

- **Psychological safety is critical.** Don't run single, intense sessions. Build in debriefing, ongoing support.
- **Frame it as collaborative expertise, not exploitation.** Compensate well, give participants co-authorship options, make the work visible.
- **Test multiple systems.** Compare how bias manifests differently across DALL-E, Stable Diffusion, Midjourney.
- **Go beyond gender/race.** Disability, age, class, religion—what's missing?
- **Localize bias definitions.** What counts as "stereotyped" varies by culture and community.
- **Document the process transparently.** The sociotechnical aspects (who participated, how they were recruited, what labor was involved) is as important as the findings.

---

## Suggested Citation Strategy

Your paper could position itself as:

> "Building on participatory red-teaming work (X, Y, Z) and cross-cultural algorithmic auditing (A, B), we conduct the first participatory evaluation of image diffusion models with communities from Pakistan and Iran, revealing how algorithmic bias is experienced differently across cultures and proposed frameworks for localized fairness."
