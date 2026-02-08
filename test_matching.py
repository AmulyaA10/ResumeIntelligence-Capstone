"""
Test script for JD-Resume matching workflow
Quick validation of the complete pipeline
"""

from services.matching_workflow import match_resumes_to_jd

# Sample Job Description
sample_jd = """
Senior DevOps Engineer

We are looking for an experienced DevOps Engineer to join our cloud infrastructure team.

Requirements:
- 5+ years of DevOps/SRE experience
- Strong expertise in AWS (EC2, ECS, Lambda, S3, RDS)
- Expert in Docker and Kubernetes
- CI/CD pipeline design and implementation (Jenkins, GitLab CI)
- Infrastructure as Code (Terraform, CloudFormation)
- Python or Go scripting
- Linux system administration
- Git version control
- Experience with monitoring tools (Prometheus, Grafana, DataDog)
- Agile/Scrum methodology

Nice to have:
- Ansible configuration management
- Microservices architecture
- Security best practices

Industry: SaaS, Cloud Infrastructure
"""

# Sample Resume 1 (Strong candidate)
sample_resume_1 = """
JOHN DOE
Senior DevOps Engineer | Cloud Infrastructure Specialist

EXPERIENCE

Senior DevOps Engineer | TechCorp Inc. | 2021 - Present (3 years)
- Architected and deployed AWS infrastructure for microservices platform using Terraform
- Reduced deployment time by 65% by implementing GitLab CI/CD pipelines
- Managed Kubernetes clusters (EKS) serving 5M+ daily requests with 99.9% uptime
- Built Docker containerization strategy, reducing image sizes by 40%
- Implemented Prometheus/Grafana monitoring stack, decreasing incident response time by 50%
- Led migration from monolith to microservices, saving $100K annually in infrastructure costs

DevOps Engineer | CloudSolutions Ltd. | 2018 - 2021 (3 years)
- Automated infrastructure provisioning using AWS CloudFormation
- Developed Python scripts for log analysis and automation (10K+ lines)
- Managed Jenkins CI/CD pipelines for 20+ microservices
- Administered Linux servers (Ubuntu, CentOS) and performed security hardening

SKILLS
Python, Terraform, AWS (EC2, ECS, Lambda, S3, RDS), Docker, Kubernetes, Jenkins, GitLab CI,
Linux, Git, Prometheus, Grafana, DataDog, Ansible, Bash

EDUCATION
Bachelor of Science in Computer Science | State University | 2018

CERTIFICATIONS
- AWS Certified Solutions Architect - Professional
- Certified Kubernetes Administrator (CKA)
"""

# Sample Resume 2 (Moderate candidate - some gaps)
sample_resume_2 = """
JANE SMITH
DevOps Engineer

EXPERIENCE

DevOps Engineer | StartupXYZ | 2022 - 2024 (2 years)
- Worked on AWS infrastructure
- Deployed Docker containers
- Maintained CI/CD pipelines
- Collaborated with development teams

Junior DevOps Engineer | WebHost Co. | 2020 - 2022 (2 years)
- Assisted in server management
- Created deployment scripts
- Monitored system performance

SKILLS
AWS, Docker, Jenkins, Python, Linux, Git, Terraform

EDUCATION
Bachelor's in Information Technology | 2020
"""

# Sample Resume 3 (Weak candidate - vague, outdated)
sample_resume_3 = """
BOB JOHNSON
IT Professional

PROFILE
Results-oriented and highly motivated team player with proven track record in DevOps.
Dynamic professional passionate about cloud technologies. Self-starter with excellent
communication skills.

EXPERIENCE

DevOps Specialist | Legacy Corp | 2017 - 2019
- Responsible for cloud infrastructure
- Worked with various DevOps tools
- Collaborated with cross-functional teams
- Implemented best practices
- Delivered innovative solutions

System Administrator | OldTech Inc. | 2015 - 2017
- Managed servers
- Performed system maintenance
- Provided technical support

SKILLS
AWS, Docker, Kubernetes, CI/CD, Python, Linux, Agile, Strategic Planning,
Leadership, Innovation, Synergy

EDUCATION
Associate Degree in Computer Science | 2015
"""


def test_matching():
    """Run matching test with sample data"""

    print("=" * 80)
    print("TESTING JD-RESUME MATCHING WORKFLOW")
    print("=" * 80)
    print()

    resume_texts = [sample_resume_1, sample_resume_2, sample_resume_3]

    print(f"📋 Job Description: Senior DevOps Engineer (5+ years)")
    print(f"📄 Candidates: {len(resume_texts)} resumes")
    print()

    result = match_resumes_to_jd(sample_jd, resume_texts)

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    # Display JD requirements
    jd_req = result["jd_requirements"]
    print("🎯 JD Requirements:")
    print(f"   Must-have skills: {', '.join(jd_req['must_have_skills'][:5])}...")
    print(f"   Years required: {jd_req['years_of_experience']['total']}")
    print(f"   Seniority: {jd_req['role_seniority']}")
    print()

    # Display ranking
    print("🏆 Candidate Ranking:")
    print()

    for candidate in result["ranked_candidates"]:
        score = candidate["final_score"]
        recommendation = candidate["recommendation"]

        # Emoji for recommendation
        if recommendation == "Shortlist":
            emoji = "✅"
        elif recommendation == "Review":
            emoji = "⚠️"
        else:
            emoji = "❌"

        print(f"  {emoji} Rank #{candidate['rank']}: {candidate['candidate_id']}")
        print(f"     Score: {score}/100 | Recommendation: {recommendation}")
        print(f"     Summary: {candidate['summary']}")

        # Show matched/missing skills
        breakdown = candidate["score_result"]["breakdown"]
        matched = breakdown["skill_coverage"]["matched_skills"]
        missing = breakdown["skill_coverage"]["missing_skills"]

        print(f"     Skills: {len(matched)} matched, {len(missing)} missing")
        print(f"     Penalty: -{candidate['score_result']['penalty']} points")
        print()

    print("=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    test_matching()
