import streamlit as st
import os
from dotenv import load_dotenv
from services.candidate_service import CandidateService
from services.interview_service import InterviewService
from services.llama_service import LlamaService
from database.connection import get_database
import streamlit as st
from database.connection import get_database

# Import interview service last, passing dependencies
def init_services():
    db = get_database()
    
    # Initialize services in correct order
    candidate_service = CandidateService(db)
    llama_service = LlamaService()
    
    # Import interview service here to avoid circular import
    from services.interview_service import InterviewService
    interview_service = InterviewService(db, llama_service, candidate_service)
    
    return candidate_service, interview_service
# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Technical Interview Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Initialize services
@st.cache_resource
def init_services():
    db = get_database()
    llama_service = LlamaService()
    candidate_service = CandidateService(db)
    interview_service = InterviewService(db, llama_service, candidate_service)
    return candidate_service, interview_service

candidate_service, interview_service = init_services()

def main():
    st.title("🤖 AI Technical Interview Assistant")
    st.write("Welcome to your personalized technical interview experience!")
    
    # Initialize session state
    if "step" not in st.session_state:
        st.session_state.step = "registration"
    if "candidate_id" not in st.session_state:
        st.session_state.candidate_id = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Navigation
    if st.session_state.step == "registration":
        show_registration_form()
    elif st.session_state.step == "tech_stack":
        show_tech_stack_form()
    elif st.session_state.step == "interview":
        show_interview_interface()
    elif st.session_state.step == "completed":
        show_completion_page()

def show_registration_form():
    st.header("📋 Candidate Information")
    
    with st.form("candidate_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name *", 
                                    placeholder="John Doe")
            email = st.text_input("Email Address *", 
                                placeholder="john.doe@example.com")
            phone = st.text_input("Phone Number *", 
                                placeholder="+1-555-123-4567")
        
        with col2:
            years_exp = st.number_input("Years of Experience *", 
                                      min_value=0, max_value=50, value=0)
            location = st.text_input("Current Location *", 
                                   placeholder="San Francisco, CA, USA")
            
        # Desired positions (multi-select)
        positions = st.multiselect(
            "Desired Position(s) *",
            options=[
                "Software Engineer", "Senior Software Engineer", "Lead Developer",
                "Full Stack Developer", "Frontend Developer", "Backend Developer",
                "DevOps Engineer", "Data Scientist", "ML Engineer", 
                "Product Manager", "Engineering Manager"
            ],
            help="Select all positions you're interested in"
        )
        
        submitted = st.form_submit_button("Continue to Tech Stack")
        
        if submitted:
            # Validation
            errors = []
            if not full_name or len(full_name.split()) < 2:
                errors.append("Full name must contain at least 2 words")
            if not email or "@" not in email or "." not in email:
                errors.append("Valid email address is required")
            if not phone:
                errors.append("Phone number is required")
            if not location:
                errors.append("Current location is required")
            if not positions:
                errors.append("At least one desired position must be selected")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Save candidate data
                candidate_data = {
                    "full_name": full_name,
                    "email": email,
                    "phone_number": phone,
                    "years_experience": years_exp,
                    "desired_positions": positions,
                    "current_location": location,
                    "tech_stack": []
                }
                
                try:
                    candidate_id = candidate_service.create_candidate(candidate_data)
                    st.session_state.candidate_id = candidate_id
                    st.session_state.step = "tech_stack"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating candidate: {e}")

def show_tech_stack_form():
    st.header("⚡ Technical Skills Assessment")
    st.write("Please specify your technical proficiencies:")
    
    # Tech categories with comprehensive options
    tech_categories = {
        "Programming Languages": [
            "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", 
            "TypeScript", "Swift", "Kotlin", "PHP", "Ruby", "Scala", "R"
        ],
        "Frontend Technologies": [
            "React", "Vue.js", "Angular", "Svelte", "HTML/CSS", "Bootstrap", 
            "Tailwind CSS", "Material-UI", "jQuery", "Next.js", "Nuxt.js"
        ],
        "Backend Frameworks": [
            "Django", "Flask", "FastAPI", "Express.js", "Spring Boot", 
            "ASP.NET", "Laravel", "Ruby on Rails", "Gin", "Echo"
        ],
        "Databases": [
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", 
            "Oracle", "Cassandra", "DynamoDB", "Elasticsearch"
        ],
        "Cloud Platforms": [
            "AWS", "Google Cloud", "Azure", "Digital Ocean", "Heroku", 
            "Vercel", "Netlify", "Firebase"
        ],
        "DevOps & Tools": [
            "Docker", "Kubernetes", "Jenkins", "GitHub Actions", "GitLab CI", 
            "Terraform", "Ansible", "Prometheus", "Grafana"
        ],
        "Data Science & ML": [
            "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", 
            "Keras", "Apache Spark", "Jupyter", "Tableau", "Power BI"
        ],
        "Mobile Development": [
            "React Native", "Flutter", "Swift (iOS)", "Kotlin (Android)", 
            "Xamarin", "Ionic", "Cordova"
        ]
    }
    
    selected_skills = {}
    
    for category, technologies in tech_categories.items():
        st.subheader(category)
        
        # Multi-select for technologies in this category
        selected_techs = st.multiselect(
            f"Select {category.lower()}:",
            options=technologies,
            key=f"select_{category}"
        )
        
        if selected_techs:
            category_skills = []
            for tech in selected_techs:
                proficiency = st.select_slider(
                    f"Proficiency in {tech}:",
                    options=["Beginner", "Intermediate", "Advanced"],
                    value="Intermediate",
                    key=f"prof_{category}_{tech}"
                )
                category_skills.append({
                    "name": tech,
                    "proficiency": proficiency
                })
            
            selected_skills[category] = category_skills
        
        st.divider()
    
    if st.button("Start Technical Interview", type="primary"):
        if not selected_skills:
            st.error("Please select at least one technology to proceed.")
        else:
            # Update candidate's tech stack
            tech_stack_data = []
            for category, skills in selected_skills.items():
                tech_stack_data.append({
                    "category": category,
                    "technologies": skills
                })
            
            try:
                candidate_service.update_tech_stack(
                    st.session_state.candidate_id, 
                    tech_stack_data
                )
                
                # Start interview session
                session_id = interview_service.start_interview(st.session_state.candidate_id)
                st.session_state.session_id = session_id
                st.session_state.step = "interview"
                session = interview_service.get_session(session_id)
                st.session_state.chat_history = [msg.model_dump() for msg in session.conversation_history]

                st.rerun()
            except Exception as e:
                st.error(f"Error updating tech stack: {e}")

def show_interview_interface():
    st.header("💬 Technical Interview Session")
    
    # Chat interface
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])
    
    # User input
    if prompt := st.chat_input("Type your response here..."):
        # Add user message to chat
        st.session_state.chat_history.append({
            "role": "user", 
            "content": prompt
        })
        
        # Get AI response
        try:
            # Fix: Use 'prompt' instead of undefined 'user_input'
            response = interview_service.process_user_input(st.session_state.session_id, prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            st.rerun()
        except Exception as e:
            st.error(f"Error processing input: {e}")
    
    # Interview controls
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Pause Interview"):
            st.info("Interview paused. You can resume anytime.")
    
    with col2:
        if st.button("End Interview"):
            st.session_state.step = "completed"
            st.rerun()
    
    with col3:
        if st.button("Get Help"):
            st.info("If you need clarification on a question, just ask!")

def show_completion_page():
    st.header("✅ Interview Completed")
    st.success("Thank you for completing the technical interview!")
    
    st.write("""
    ### Next Steps:
    1. **Review Process**: Our technical team will review your responses within 2-3 business days
    2. **Follow-up**: You'll receive an email with feedback and next steps
    3. **Questions**: Contact hr@company.com for any inquiries
    
    ### What Happens Next:
    - Technical assessment review
    - Potential follow-up technical discussion
    - Cultural fit interview
    - Final decision and offer discussion
    """)
    
    if st.button("Start New Interview"):
        # Reset session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
