import streamlit as st
from config import BACKGROUNDS, PHASE_SHARED, PARTICIPANT_TOKENS
from data import generate_anonymous_id, save_identity_mapping


def run():
    st.title("Home")
    st.markdown("---")

    token = st.text_input("Enter your participant token to begin", type="password")

    if not token:
        st.info("You need a participant token to access this workshop. If you don't have one, contact your facilitator.")
        return

    if token not in PARTICIPANT_TOKENS:
        st.error("Invalid token. Please check with your facilitator.")
        return

    st.success("Token accepted.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ## What are we doing?

        We're testing whether AI image generation systems represent your
        community authentically and respectfully. You'll compare 4
        systems built by different companies from the US and China.
        You won't know which company made which system.

        **Your role:** Use your lived experience as an expert to uncover biases these systems have.

        ### Why your perspective matters
        - You know what authentic representation looks like for your community
        - You can spot stereotypes that algorithms miss
        - You understand the cultural significance of bias
        """)

    with col2:
        st.markdown("""
        ## How it works (3 hours)

        1. **Orientation** (30 min) — You're here now
        2. **Shared prompts** (15 min) — Everyone rates the same 5 prompts (for comparison)
        3. **Free exploration** (75 min) — You write your own prompts and judge the outputs
        4. **Group discussion** (60 min) — We identify patterns together

        ### What you'll do
        - Write test prompts for the image systems
        - Generate images from those prompts
        - Rate images on authenticity, diversity, and respectfulness
        - Explain why the bias matters in your own words
        """)

    st.markdown("---")
    st.subheader("Register to begin")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your name (stored securely, not linked to your ratings)")
    with col2:
        options = [""] + BACKGROUNDS + ["Other"]
        background = st.selectbox("Your background / community", options, index=0)

    if background == "Other":
        background = st.text_input("Please describe your background / community")

    st.markdown("---")
    st.markdown("""
    ### Consent

    By checking the box below, you agree to the following:
    - Your ratings and written responses will be used in academic research
    - Your identity will be anonymized — your name is stored separately from your data
    - You can withdraw at any time by telling the facilitator
    - Generated images may contain stereotypical or offensive content — this is what we're testing
    - If you feel uncomfortable at any point, you can take a break or stop
    """)

    consent = st.checkbox("I understand the above and consent to participate")

    if st.button("Start Red Teaming", use_container_width=True, type="primary"):
        if not name:
            st.error("Please enter your name")
        elif not background:
            st.error("Please select your background / community")
        elif not consent:
            st.error("Please read and accept the consent statement")
        else:
            anon_id = generate_anonymous_id()
            save_identity_mapping(anon_id, name, background)
            st.session_state.participant_id = anon_id
            st.session_state.participant_display_name = name.split()[0]
            st.session_state.participant_background = background
            st.session_state.participant_token = token
            st.session_state.current_phase = PHASE_SHARED
            st.rerun()
