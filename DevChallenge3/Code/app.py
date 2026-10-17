import streamlit as st
import ollama
import json
import os

# --- PERSISTENT LOCAL STORAGE ---
DB_FILE = "local_tutor_db.json"

def load_profiles():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_profiles(profiles):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4, ensure_ascii=False)

# --- PAGE CONFIG & CUSTOM CSS ---
st.set_page_config(page_title="LocalTutor AI", page_icon="🌍", layout="wide")

st.markdown("""
<style>
    .metric-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #333; }
    .metric-value { font-size: 24px; font-weight: bold; color: #4CAF50; }
    .metric-label { font-size: 14px; color: #888; }
    .vocab-card { background-color: #2b2b2b; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #4CAF50;}
    .native-text { font-size: 22px; font-weight: bold; color: #ffffff; }
    .roman-text { font-size: 16px; color: #aaa; font-style: italic; }
    .english-text { font-size: 18px; color: #ddd; }
    .report-card { background-color: #1a1a2e; padding: 20px; border-radius: 10px; border: 1px solid #16213e; margin-top: 20px;}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'profiles' not in st.session_state:
    st.session_state.profiles = load_profiles()
if 'active_lang' not in st.session_state:
    st.session_state.active_lang = None
if 'view' not in st.session_state:
    st.session_state.view = 'setup'

# --- LLM HELPER FUNCTION ---
def call_tutor(prompt):
    messages = [
        {"role": "system", "content": "You are a precise language tutor. Always respond in valid JSON format ONLY. Do not include markdown code blocks."},
        {"role": "user", "content": prompt}
    ]
    with st.spinner("🧠 Tutor is thinking..."):
        response = ollama.chat(model='llama3.1:8b', messages=messages, format='json')
        raw_json = response['message']['content'].strip()
        
        # Failsafe: Clean markdown wrappers if Llama 3.1 ignores formatting instructions
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:]
        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]
            
        return raw_json.strip()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🌍 LocalTutor AI")
    if st.session_state.profiles:
        langs = list(st.session_state.profiles.keys())
        langs.insert(0, "Select a language...") 
        
        current_index = 0
        if st.session_state.active_lang in langs:
            current_index = langs.index(st.session_state.active_lang)
            
        selected_lang = st.selectbox("Switch Language:", langs, index=current_index)
        
        if selected_lang != "Select a language..." and selected_lang != st.session_state.active_lang:
            st.session_state.active_lang = selected_lang
            st.session_state.view = 'lesson'
            st.rerun()
            
        if st.session_state.active_lang and st.session_state.active_lang != "Select a language...":
            profile = st.session_state.profiles[st.session_state.active_lang]
            progress = min(profile['day'] / profile['days'], 1.0)
            st.progress(progress, text=f"Overall Progress: {int(progress * 100)}%")

            st.divider()
            st.subheader("Navigation")
            
            # Using standard callbacks for stable state routing
            def go_to_lesson(): st.session_state.view = 'lesson'
            def go_to_history(): st.session_state.view = 'history'
            
            st.button("🎓 Current Lesson", on_click=go_to_lesson, use_container_width=True)
            st.button("📖 History / Revisit Lessons", on_click=go_to_history, use_container_width=True)

    st.divider()
    def go_to_setup(): 
        st.session_state.active_lang = None
        st.session_state.view = 'setup'
        
    st.button("➕ Start New Language", on_click=go_to_setup, use_container_width=True)

# --- VIEW 1: SETUP ---
if st.session_state.view == 'setup':
    st.header("Embark on a New Language")
    st.markdown("Your progress will be saved locally to `local_tutor_db.json`.")
    
    col1, col2 = st.columns(2)
    with col1:
        lang = st.text_input("Language to learn (e.g., Korean, Spanish):")
        daily_time = st.slider("Daily time commitment (mins):", 5, 120, 20)
    with col2:
        level = st.selectbox("Current Level:", ["Absolute Beginner", "Beginner", "Intermediate", "Advanced"])
        days = st.slider("Target timeline (days):", 7, 365, 30)
        
    if st.button("🚀 Initialize Tutor", type="primary"):
        if lang:
            if lang not in st.session_state.profiles:
                st.session_state.profiles[lang] = {
                    "level": level, "time": daily_time, "days": days, "day": 1,
                    "lagging": "None (First Day)", "past_questions": [], 
                    "current_lesson": {}, "current_quiz": [], "history": []
                }
            save_profiles(st.session_state.profiles)
            st.session_state.active_lang = lang
            st.session_state.view = 'lesson'
            st.rerun()
        else:
            st.error("Please enter a language.")

# --- MAIN APP LOGIC ---
if st.session_state.active_lang and st.session_state.view != 'setup':
    profile = st.session_state.profiles[st.session_state.active_lang]
    lang = st.session_state.active_lang
    
    if st.session_state.view != 'history':
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f'<div class="metric-card"><div class="metric-value">{lang}</div><div class="metric-label">Language</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><div class="metric-value">Day {profile["day"]}/{profile["days"]}</div><div class="metric-label">Streak</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card"><div class="metric-value">{profile["level"]}</div><div class="metric-label">Level</div></div>', unsafe_allow_html=True)
        col4.markdown(f'<div class="metric-card"><div class="metric-value">{profile["time"]}m</div><div class="metric-label">Daily Goal</div></div>', unsafe_allow_html=True)
        st.write("") 

    # --- VIEW 2: LESSON ---
    if st.session_state.view == 'lesson':
        if not profile.get('current_lesson'):
            
            beginner_instruction = ""
            if profile['level'] == "Absolute Beginner" and profile['day'] <= 2:
                beginner_instruction = "CRITICAL: The user is an Absolute Beginner. You MUST focus strictly on teaching the foundational Alphabet/Letters/Characters today. Fill the 'vocabulary' array with the most important letters and their pronunciations. DO NOT teach full complex sentences yet."

            prompt = f"""
            Create a {lang} lesson for a {profile['level']} student on Day {profile['day']}. 
            {beginner_instruction}
            Lagging topics from yesterday to review: {profile['lagging']}.
            
            Return ONLY a valid JSON object in this exact format:
            {{
                "title": "Lesson Title",
                "introduction": "A brief 2-sentence explanation of today's focus.",
                "vocabulary": [
                    {{"native": "Word/Alphabet in native script", "romanization": "Pronunciation", "english": "Meaning"}}
                ],
                "sentences": [
                    {{"native": "Sentence/Grammar rule in native script", "romanization": "Pronunciation", "english": "Explanation"}}
                ]
            }}
            """
            raw_json = call_tutor(prompt)
            try:
                profile['current_lesson'] = json.loads(raw_json)
                save_profiles(st.session_state.profiles)
            except Exception as e:
                st.error("Failed to parse the lesson from Llama 3.1. Please click refresh to retry.")
                profile['current_lesson'] = {}
        
        lesson_data = profile.get('current_lesson', {})
        if lesson_data:
            st.subheader(lesson_data.get("title", "Today's Lesson"))
            st.write(lesson_data.get("introduction", ""))
            
            st.markdown("### Vocabulary / Characters")
            for item in lesson_data.get("vocabulary", []):
                html_block = (
                    '<div class="vocab-card">'
                    f'<div class="native-text">{item.get("native", "")}</div>'
                    f'<div class="roman-text">{item.get("romanization", "")}</div>'
                    f'<div class="english-text">{item.get("english", "")}</div>'
                    '</div>'
                )
                st.markdown(html_block, unsafe_allow_html=True)
                
            st.markdown("### Grammar / Practice")
            for item in lesson_data.get("sentences", []):
                html_block = (
                    '<div class="vocab-card">'
                    f'<div class="native-text">{item.get("native", "")}</div>'
                    f'<div class="roman-text">{item.get("romanization", "")}</div>'
                    f'<div class="english-text">{item.get("english", "")}</div>'
                    '</div>'
                )
                st.markdown(html_block, unsafe_allow_html=True)
        
        if st.button("📝 Start Today's Assignment", type="primary"):
            st.session_state.view = 'quiz'
            st.rerun()

    # --- VIEW 3: QUIZ ---
    elif st.session_state.view == 'quiz':
        if not profile.get('current_quiz'):
            prompt = f"""
            Generate a 4-question assessment based EXACTLY and ONLY on this lesson data: 
            {json.dumps(profile['current_lesson'])}
            
            CRITICAL INSTRUCTION: Do NOT hallucinate words or letters that were not taught in the lesson above. Create translation, fill-in-the-blank, or meaning-matching questions.
            
            Return ONLY a valid JSON object in this exact format:
            {{"questions": ["Question 1", "Question 2", "Question 3", "Question 4"]}}
            """
            raw_json = call_tutor(prompt)
            try:
                quiz_data = json.loads(raw_json)
                profile['current_quiz'] = quiz_data.get("questions", [])
                profile['past_questions'].extend(profile['current_quiz'])
                save_profiles(st.session_state.profiles)
            except Exception as e:
                st.error("Failed to generate quiz. Retrying...")
                profile['current_quiz'] = []
                st.rerun()

        st.subheader("Daily Assessment")
        st.markdown("Test your knowledge on today's specific topics.")
        
        with st.form("quiz_form"):
            answers = []
            for i, q in enumerate(profile['current_quiz']):
                answers.append(st.text_area(f"**Q{i+1}:** {q}", height=68))
            
            if st.form_submit_button("Submit for Grading", type="primary"):
                st.session_state.current_answers = answers
                st.session_state.view = 'feedback'
                st.rerun()

    # --- VIEW 4: FEEDBACK & REPORT CARD ---
    elif st.session_state.view == 'feedback':
        st.subheader("Performance Report")
        
        qa_pairs = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(profile['current_quiz'], st.session_state.current_answers)])
        
        if 'report_card' not in st.session_state:
            prompt = f"""
            Evaluate these {lang} answers from a {profile['level']} student:
            {qa_pairs}
            
            Generate a structured performance report.
            Return ONLY a valid JSON object in this exact format:
            {{
                "score": "A number out of 100",
                "strengths": "1-2 sentences on what they did well",
                "weaknesses": "1-2 sentences on what needs improvement",
                "detailed_feedback": "Detailed corrections for each question using native characters where appropriate.",
                "lagging_topics": "A very short list of concepts to reteach tomorrow."
            }}
            """
            raw_json = call_tutor(prompt)
            try:
                st.session_state.report_card = json.loads(raw_json)
                profile['lagging'] = st.session_state.report_card.get("lagging_topics", "None")
                save_profiles(st.session_state.profiles)
            except Exception as e:
                st.session_state.report_card = {
                    "score": "N/A", "strengths": "Good effort.", "weaknesses": "Review today's concepts.",
                    "detailed_feedback": "Failed to parse detailed report from AI.", "lagging_topics": "Review"
                }
        
        report = st.session_state.report_card
        
        # Visual Report Card
        st.markdown(f"""
        <div class="report-card">
            <h2 style="text-align: center; color: #4CAF50;">Score: {report.get('score', '100')}/100</h2>
            <hr>
            <p><strong>🌟 Strengths:</strong> {report.get('strengths', '')}</p>
            <p><strong>📉 Weaknesses:</strong> {report.get('weaknesses', '')}</p>
            <hr>
            <p><strong>📝 Detailed Feedback:</strong><br>{report.get('detailed_feedback', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.warning(f"**Focus areas saved for tomorrow:** {profile['lagging']}")
        
        if st.button("⏩ Complete Day & Move to Next", type="primary"):
            if 'history' not in profile:
                profile['history'] = []
            
            profile['history'].append({
                "day": profile['day'],
                "lesson": profile['current_lesson'],
                "report": report
            })
            
            profile['day'] += 1
            profile['current_lesson'] = {}
            profile['current_quiz'] = []
            save_profiles(st.session_state.profiles)
            
            del st.session_state.report_card
            del st.session_state.current_answers
            st.session_state.view = 'lesson'
            st.rerun()

    # --- VIEW 5: HISTORY ---
    elif st.session_state.view == 'history':
        st.header(f"📖 History: {lang}")
        st.markdown("Review your past lessons and report cards.")
        
        if 'history' not in profile or not profile['history']:
            st.info("No past lessons to show yet. Complete a day to see it here!")
        else:
            for past_day in reversed(profile['history']):
                with st.expander(f"Day {past_day['day']}: {past_day['lesson'].get('title', 'Lesson')} (Score: {past_day.get('report', {}).get('score', 'N/A')})"):
                    st.write(past_day['lesson'].get('introduction', ''))
                    
                    st.markdown("**Vocabulary / Characters**")
                    for item in past_day['lesson'].get("vocabulary", []):
                        st.markdown(f"- **{item.get('native', '')}** ({item.get('romanization', '')}) — {item.get('english', '')}")
                        
                    st.markdown("**Grammar / Practice**")
                    for item in past_day['lesson'].get("sentences", []):
                        st.markdown(f"- **{item.get('native', '')}** ({item.get('romanization', '')}) — {item.get('english', '')}")
                    
                    st.markdown("---")
                    st.markdown("**Tutor Feedback:**")
                    st.info(past_day.get('report', {}).get('detailed_feedback', 'No feedback recorded.'))
