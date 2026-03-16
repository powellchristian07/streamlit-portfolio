import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ─────────────────────────────────────────────
# 1. PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Alex Morgan | Portfolio",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Portfolio v3 — Built with Streamlit",
    },
)

# ─────────────────────────────────────────────
# 2. CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --primary: #e94560;
    --secondary: #0f3460;
    --accent: #533483;
    --bg-dark: #1a1a2e;
    --bg-card: #16213e;
    --text-muted: #a0a0b0;
}

/* Hide default Streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* Gradient hero name */
.hero-name {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #e94560, #533483);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
    margin-bottom: 0.5rem;
}

/* Sidebar avatar circle */
.avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #e94560, #533483);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    font-weight: 700;
    color: white;
    margin: 0 auto 1rem auto;
    letter-spacing: 2px;
}

/* Section header style */
.section-header {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}
.section-subtitle {
    color: var(--text-muted);
    margin-bottom: 1.5rem;
}

/* Tech badge pill */
.tech-badge {
    display: inline-block;
    background: rgba(83, 52, 131, 0.25);
    border: 1px solid rgba(83, 52, 131, 0.5);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.75rem;
    margin: 2px;
}

/* Contact info row */
.contact-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. CONTENT DATA
# ─────────────────────────────────────────────
PERSONAL = {
    "name": "Alex Morgan",
    "initials": "AM",
    "title": "Senior Data Scientist & ML Engineer",
    "tagline": "Turning raw data into production-grade intelligence",
    "bio": (
        "I'm a data scientist and ML engineer with 7+ years of experience building "
        "end-to-end machine learning systems — from exploratory analysis to deployed "
        "production pipelines. I specialize in NLP, recommendation systems, and MLOps. "
        "Passionate about open source, clean code, and making complex models explainable."
    ),
    "email": "alex.morgan@example.com",
    "location": "San Francisco, CA",
    "github": "https://github.com",
    "linkedin": "https://linkedin.com",
    "twitter": "https://twitter.com",
    "resume_url": "#",
    "years_experience": 7,
    "projects_shipped": 24,
    "open_source_stars": "1.2k",
    "availability": "Open to new opportunities",
}

SKILLS = {
    "Languages": [
        {"name": "Python", "level": 95, "icon": "🐍"},
        {"name": "SQL", "level": 90, "icon": "🗄️"},
        {"name": "R", "level": 75, "icon": "📊"},
        {"name": "JavaScript", "level": 65, "icon": "🌐"},
        {"name": "Bash / Shell", "level": 80, "icon": "💻"},
    ],
    "ML / AI": [
        {"name": "scikit-learn", "level": 92, "icon": "🤖"},
        {"name": "PyTorch", "level": 85, "icon": "🔥"},
        {"name": "TensorFlow", "level": 78, "icon": "🧠"},
        {"name": "HuggingFace", "level": 80, "icon": "🤗"},
        {"name": "LangChain", "level": 70, "icon": "⛓️"},
    ],
    "Data & Viz": [
        {"name": "Pandas / NumPy", "level": 95, "icon": "🐼"},
        {"name": "Plotly / Dash", "level": 88, "icon": "📈"},
        {"name": "Streamlit", "level": 90, "icon": "🎈"},
        {"name": "dbt", "level": 72, "icon": "🔧"},
        {"name": "Apache Spark", "level": 68, "icon": "⚡"},
    ],
    "Infrastructure": [
        {"name": "Docker / K8s", "level": 80, "icon": "🐳"},
        {"name": "AWS", "level": 82, "icon": "☁️"},
        {"name": "GCP", "level": 70, "icon": "🌥️"},
        {"name": "FastAPI", "level": 85, "icon": "⚡"},
        {"name": "Git / CI-CD", "level": 88, "icon": "🔀"},
    ],
}

PROJECTS = [
    {
        "title": "LLM-Powered Document Q&A",
        "description": "RAG pipeline using LangChain, FAISS, and GPT-4 to answer questions over 10k+ internal documents. Reduced analyst research time by 60%.",
        "tech": ["Python", "LangChain", "FAISS", "FastAPI", "React"],
        "category": "AI / LLM",
        "github": "https://github.com",
        "demo": "https://streamlit.io",
        "metrics": {"Accuracy": "94%", "Latency": "<2s", "Docs": "10k+"},
        "featured": True,
    },
    {
        "title": "Real-Time Fraud Detection",
        "description": "Gradient boosting model served via FastAPI with sub-50ms latency. Deployed on AWS with Kafka for streaming inference on 1M+ transactions/day.",
        "tech": ["Python", "XGBoost", "Kafka", "FastAPI", "AWS"],
        "category": "ML Pipeline",
        "github": "https://github.com",
        "demo": None,
        "metrics": {"Precision": "97%", "Latency": "<50ms", "TPD": "1M+"},
        "featured": True,
    },
    {
        "title": "Executive Analytics Dashboard",
        "description": "Interactive Plotly Dash dashboard with drill-down capabilities. Aggregates data from 5 sources and serves 200+ daily active users.",
        "tech": ["Python", "Plotly Dash", "PostgreSQL", "Redis"],
        "category": "Dashboard",
        "github": "https://github.com",
        "demo": "https://streamlit.io",
        "metrics": {},
        "featured": False,
    },
    {
        "title": "Open-Source NLP Toolkit",
        "description": "Python library for text preprocessing and feature extraction. 1.2k GitHub stars, 50k+ monthly PyPI downloads.",
        "tech": ["Python", "spaCy", "NLTK", "PyPI"],
        "category": "Open Source",
        "github": "https://github.com",
        "demo": None,
        "metrics": {},
        "featured": False,
    },
    {
        "title": "Recommendation Engine",
        "description": "Collaborative filtering + content-based hybrid recommender for an e-commerce platform. Improved CTR by 23% over rule-based baseline.",
        "tech": ["Python", "PyTorch", "Redis", "FastAPI"],
        "category": "ML Pipeline",
        "github": "https://github.com",
        "demo": None,
        "metrics": {},
        "featured": False,
    },
    {
        "title": "Data Quality Monitor",
        "description": "Automated pipeline health checks using Great Expectations + Slack alerting. Catches schema drift, null anomalies, and distribution shifts.",
        "tech": ["Python", "Great Expectations", "Airflow", "Slack API"],
        "category": "Data Engineering",
        "github": "https://github.com",
        "demo": None,
        "metrics": {},
        "featured": False,
    },
]

EXPERIENCE = [
    {
        "role": "Senior Data Scientist",
        "company": "TechCorp Inc.",
        "period": "2022 – Present",
        "location": "San Francisco, CA",
        "description": "Lead a team of 4 data scientists building production ML systems for a fintech platform serving 5M+ customers.",
        "achievements": [
            "Built real-time fraud detection model saving $2M+/year in prevented losses",
            "Reduced model training time by 70% via distributed Spark on AWS EMR",
            "Established internal ML platform adopted by 3 product teams",
            "Mentored 2 junior data scientists to senior-level promotions",
        ],
        "tech_used": ["Python", "Spark", "AWS", "MLflow", "FastAPI"],
    },
    {
        "role": "Data Scientist",
        "company": "DataWave Analytics",
        "period": "2019 – 2022",
        "location": "New York, NY",
        "description": "Built NLP models and data pipelines for a SaaS analytics product used by Fortune 500 clients.",
        "achievements": [
            "Shipped sentiment analysis API processing 500k documents/day",
            "Automated ETL pipeline reducing manual data prep from 8h to 20min",
            "Delivered churn prediction model with 89% AUC for key enterprise client",
        ],
        "tech_used": ["Python", "spaCy", "Airflow", "GCP", "BigQuery"],
    },
    {
        "role": "Machine Learning Engineer",
        "company": "StartupAI",
        "period": "2017 – 2019",
        "location": "Boston, MA",
        "description": "Early ML hire at a computer vision startup. Built data pipelines and trained CNN models for defect detection.",
        "achievements": [
            "Trained ResNet-based defect detection model achieving 96% accuracy",
            "Reduced labeling cost by 40% via active learning strategy",
            "Containerized model serving infrastructure using Docker + Kubernetes",
        ],
        "tech_used": ["Python", "PyTorch", "OpenCV", "Docker", "GCP"],
    },
]

EDUCATION = [
    {
        "degree": "M.S. Computer Science (ML Specialization)",
        "school": "Stanford University",
        "year": "2017",
        "gpa": "3.9 / 4.0",
    },
    {
        "degree": "B.S. Statistics",
        "school": "UC Berkeley",
        "year": "2015",
        "gpa": "3.8 / 4.0",
    },
]

CERTIFICATIONS = [
    {"name": "AWS Certified ML Specialist", "issuer": "Amazon", "year": "2023"},
    {"name": "Google Professional Data Engineer", "issuer": "Google", "year": "2022"},
    {"name": "Deep Learning Specialization", "issuer": "Coursera / deeplearning.ai", "year": "2021"},
]

# ─────────────────────────────────────────────
# 4. SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div class="avatar">{PERSONAL["initials"]}</div>', unsafe_allow_html=True)
    st.markdown(f"### {PERSONAL['name']}")
    st.caption(PERSONAL["title"])
    st.divider()

    section = st.radio(
        "Navigate",
        options=["About", "Skills", "Projects", "Experience", "Contact"],
        label_visibility="collapsed",
    )

    st.divider()

    col_gh, col_li = st.columns(2)
    with col_gh:
        st.link_button("GitHub", PERSONAL["github"], use_container_width=True)
    with col_li:
        st.link_button("LinkedIn", PERSONAL["linkedin"], use_container_width=True)

    st.link_button(
        "Download Resume",
        PERSONAL["resume_url"],
        type="primary",
        use_container_width=True,
    )

    st.divider()
    st.caption("v3.0 · Built with Streamlit")

# ─────────────────────────────────────────────
# 5. SECTION RENDERERS
# ─────────────────────────────────────────────

def render_about():
    col_text, col_visual = st.columns([3, 2], gap="large")

    with col_text:
        st.markdown(f'<div class="hero-name">{PERSONAL["name"]}</div>', unsafe_allow_html=True)
        st.markdown(f"#### {PERSONAL['tagline']}")
        st.write("")
        st.write(PERSONAL["bio"])
        st.write("")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.link_button("GitHub", PERSONAL["github"], use_container_width=True)
        with c2:
            st.link_button("LinkedIn", PERSONAL["linkedin"], use_container_width=True)
        with c3:
            st.link_button("Email Me", f"mailto:{PERSONAL['email']}", use_container_width=True)

    with col_visual:
        with st.container(border=True):
            m1, m2, m3 = st.columns(3)
            m1.metric("Experience", f"{PERSONAL['years_experience']}y")
            m2.metric("Projects", PERSONAL["projects_shipped"])
            m3.metric("Stars", PERSONAL["open_source_stars"])

        # Radar chart
        categories = ["ML / AI", "Data Eng", "Backend", "Cloud", "Visualization", "Research"]
        values = [92, 85, 78, 80, 88, 75]
        fig = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(233, 69, 96, 0.15)",
            line=dict(color="#e94560", width=2),
            name="Competency",
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
                angularaxis=dict(tickfont=dict(size=11)),
            ),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=280,
            margin=dict(l=40, r=40, t=30, b=10),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.divider()

    # "What I Do" cards
    st.markdown("### What I Do")
    cards = [
        {"icon": "🤖", "title": "Machine Learning", "desc": "Design, train, and deploy ML models from proof-of-concept to production at scale."},
        {"icon": "📊", "title": "Data Engineering", "desc": "Build robust pipelines, data warehouses, and real-time streaming architectures."},
        {"icon": "☁️", "title": "MLOps & Cloud", "desc": "Containerize, automate, and monitor ML systems on AWS and GCP."},
    ]
    c1, c2, c3 = st.columns(3, gap="medium")
    for col, card in zip([c1, c2, c3], cards):
        with col:
            with st.container(border=True):
                st.markdown(f"## {card['icon']}")
                st.markdown(f"**{card['title']}**")
                st.caption(card["desc"])


def render_skills():
    st.markdown('<div class="section-header">Skills</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Technologies and tools I work with</div>', unsafe_allow_html=True)

    tabs = st.tabs(list(SKILLS.keys()))
    for tab, (category, skills) in zip(tabs, SKILLS.items()):
        with tab:
            for skill in skills:
                col_label, col_bar = st.columns([1, 3])
                with col_label:
                    st.markdown(f"{skill['icon']} **{skill['name']}**")
                with col_bar:
                    st.progress(skill["level"] / 100, text=f"{skill['level']}%")

    st.write("")
    with st.expander("View all skills chart", expanded=False):
        rows = []
        for cat, skills in SKILLS.items():
            for s in skills:
                rows.append({"Category": cat, "Skill": s["name"], "Level": s["level"]})
        df = pd.DataFrame(rows).sort_values("Level", ascending=True)
        fig = px.bar(
            df, x="Level", y="Skill", color="Category", orientation="h",
            range_x=[0, 100], height=480,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Proficiency (%)",
            yaxis_title="",
            legend_title="Category",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.divider()
    st.markdown("### Certifications")
    c1, c2, c3 = st.columns(3, gap="medium")
    for col, cert in zip([c1, c2, c3], CERTIFICATIONS):
        with col:
            with st.container(border=True):
                st.markdown(f"🏅 **{cert['name']}**")
                st.caption(f"{cert['issuer']} · {cert['year']}")


def render_projects():
    st.markdown('<div class="section-header">Projects</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">A selection of things I\'ve built</div>', unsafe_allow_html=True)

    categories = ["All"] + sorted(set(p["category"] for p in PROJECTS))
    selected_cat = st.pills(
        "Filter",
        categories,
        default="All",
        label_visibility="collapsed",
    )

    filtered = PROJECTS if selected_cat == "All" else [p for p in PROJECTS if p["category"] == selected_cat]
    featured = [p for p in filtered if p.get("featured")]
    regular = [p for p in filtered if not p.get("featured")]

    # Featured projects
    for project in featured:
        with st.container(border=True):
            st.markdown("⭐ **FEATURED**")
            col_info, col_metrics = st.columns([2, 1], gap="large")
            with col_info:
                st.markdown(f"### {project['title']}")
                badge_html = " ".join(
                    f'<span class="tech-badge">{t}</span>' for t in project["tech"]
                )
                st.markdown(badge_html, unsafe_allow_html=True)
                st.write("")
                st.write(project["description"])
                btn_col1, btn_col2, _ = st.columns([1, 1, 2])
                with btn_col1:
                    st.link_button("GitHub", project["github"], use_container_width=True)
                with btn_col2:
                    if project.get("demo"):
                        st.link_button("Live Demo", project["demo"], type="primary", use_container_width=True)
            with col_metrics:
                if project["metrics"]:
                    st.write("")
                    for label, value in project["metrics"].items():
                        st.metric(label=label, value=value)

    # Regular project grid
    if regular:
        st.write("")
        cols = st.columns(3, gap="medium")
        for i, project in enumerate(regular):
            with cols[i % 3]:
                with st.container(border=True, height=300):
                    st.markdown(f"#### {project['title']}")
                    st.caption(f"_{project['category']}_")
                    st.write(project["description"])
                    badge_html = " ".join(
                        f'<span class="tech-badge">{t}</span>' for t in project["tech"]
                    )
                    st.markdown(badge_html, unsafe_allow_html=True)
                    st.write("")
                    b1, b2 = st.columns(2)
                    with b1:
                        st.link_button("GitHub", project["github"], use_container_width=True)
                    with b2:
                        if project.get("demo"):
                            st.link_button("Demo", project["demo"], type="primary", use_container_width=True)


def render_experience():
    st.markdown('<div class="section-header">Experience</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">My professional journey</div>', unsafe_allow_html=True)

    tab_work, tab_edu = st.tabs(["Work Experience", "Education & Certifications"])

    with tab_work:
        for i, job in enumerate(EXPERIENCE):
            with st.container(border=True):
                col_meta, col_content = st.columns([1, 3], gap="large")
                with col_meta:
                    st.markdown(f"**{job['period']}**")
                    st.caption(job["location"])
                    st.write("")
                    for tech in job["tech_used"]:
                        st.markdown(
                            f'<span class="tech-badge">{tech}</span>',
                            unsafe_allow_html=True,
                        )
                with col_content:
                    st.markdown(f"### {job['role']}")
                    st.markdown(f"**{job['company']}**")
                    st.write(job["description"])
                    with st.expander("Key Achievements", expanded=(i == 0)):
                        for achievement in job["achievements"]:
                            st.markdown(f"- ✅ {achievement}")

    with tab_edu:
        col_deg, col_cert = st.columns(2, gap="large")

        with col_deg:
            st.markdown("#### Education")
            for edu in EDUCATION:
                with st.container(border=True):
                    st.markdown(f"🎓 **{edu['degree']}**")
                    st.markdown(f"_{edu['school']} · {edu['year']}_")
                    st.metric(label="GPA", value=edu["gpa"])

        with col_cert:
            st.markdown("#### Certifications")
            for cert in CERTIFICATIONS:
                with st.container(border=True):
                    st.markdown(f"🏅 **{cert['name']}**")
                    st.caption(f"{cert['issuer']} · {cert['year']}")


def render_contact():
    st.markdown('<div class="section-header">Contact</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Let\'s build something together</div>', unsafe_allow_html=True)

    col_info, col_form = st.columns([2, 3], gap="large")

    with col_info:
        st.success(f"🟢 {PERSONAL['availability']}")
        st.write("")

        with st.container(border=True):
            st.markdown("**📍 Location**")
            st.caption(PERSONAL["location"])

        with st.container(border=True):
            st.markdown("**✉️ Email**")
            st.caption(PERSONAL["email"])

        st.write("")
        st.markdown("**Find me online**")
        st.link_button("GitHub", PERSONAL["github"], use_container_width=True)
        st.link_button("LinkedIn", PERSONAL["linkedin"], use_container_width=True)
        st.link_button("Twitter", PERSONAL["twitter"], use_container_width=True)

        st.write("")
        # Work preference chart
        fig = px.pie(
            values=[80, 15, 5],
            names=["Remote", "Hybrid", "On-site"],
            title="Work Preference",
            color_discrete_sequence=["#e94560", "#533483", "#0f3460"],
            hole=0.4,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=240,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            title_font_size=13,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_form:
        with st.form("contact_form", clear_on_submit=True):
            st.markdown("#### Send a Message")
            name = st.text_input("Your Name *", placeholder="Jane Smith")
            email_input = st.text_input("Email Address *", placeholder="jane@example.com")
            subject = st.selectbox(
                "Subject",
                [
                    "Job Opportunity",
                    "Freelance Project",
                    "Open Source Collaboration",
                    "Speaking Engagement",
                    "Other",
                ],
            )
            message = st.text_area(
                "Message *",
                placeholder="Tell me about your project or opportunity...",
                height=160,
            )
            submitted = st.form_submit_button(
                "Send Message", type="primary", use_container_width=True
            )

        if submitted:
            if name and email_input and message:
                st.toast("Message sent! I'll get back to you soon. ✅")
                st.success("Thanks for reaching out! Expect a reply within 24–48 hours.")
            else:
                st.error("Please fill in all required fields (marked with *).")

        st.info(
            "ℹ️ This demo form doesn't connect to a backend. "
            "For production use, integrate with EmailJS, Formspree, or a FastAPI endpoint."
        )

# ─────────────────────────────────────────────
# 6. MAIN ROUTER
# ─────────────────────────────────────────────
if section == "About":
    render_about()
elif section == "Skills":
    render_skills()
elif section == "Projects":
    render_projects()
elif section == "Experience":
    render_experience()
elif section == "Contact":
    render_contact()
