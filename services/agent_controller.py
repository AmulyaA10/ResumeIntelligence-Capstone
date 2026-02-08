from services.resume_quality_graph import build_resume_quality_graph
from services.skill_gap_graph import build_skill_gap_graph
from services.linkedin_resume_graph import build_linkedin_resume_graph

_quality_graph = build_resume_quality_graph()

def run_resume_pipeline(task: str, resumes: list):
    if task == "score":
        return _quality_graph.invoke(
            {"resumes": resumes}
        )

    raise ValueError(f"Unknown task: {task}")



from services.langgraph_workflow import build_resume_graph

graph = build_resume_graph()

_skill_gap_graph = build_skill_gap_graph()

def run_resume_pipeline(task, resumes=None, query=None):
    if task == "skill_gap":
        return _skill_gap_graph.invoke({
            "resume_text": resumes[0],
            "jd_text": query
        })
    

    # services/agent_controller.py


_linkedin_graph = build_linkedin_resume_graph()

def generate_resume_from_linkedin(url: str):
    return _linkedin_graph.invoke({
        "linkedin_url": url
    })




