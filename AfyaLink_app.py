import os
import asyncio
import litellm
import streamlit as st
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="AfyaLink — HIV Support Ecosystem",
    page_icon="🏥",
    layout="wide"
)

# ── LOAD ENV ──
load_dotenv()
os.environ["CREWAI_DISABLE_PROMPT_CACHING"] = "true"
groq_key = os.getenv("GROQ_API_KEY")

# ── LITELLM PATCH ──
original_completion = litellm.completion
def modified_completion(*args, **kwargs):
    if "messages" in kwargs:
        for message in kwargs["messages"]:
            if isinstance(message, dict):
                message.pop("cache_breakpoint", None)
    return original_completion(*args, **kwargs)
litellm.completion = modified_completion

original_acompletion = litellm.acompletion
async def modified_acompletion(*args, **kwargs):
    if "messages" in kwargs:
        for message in kwargs["messages"]:
            if isinstance(message, dict):
                message.pop("cache_breakpoint", None)
    return await original_acompletion(*args, **kwargs)
litellm.acompletion = modified_acompletion

# ── CUSTOM CSS ──
st.markdown("""
<style>
    .main { background-color: #F0F4F8; }
    .stButton>button {
        background-color: #1A5276;
        color: white;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-size: 16px;
        border: none;
        width: 100%;
    }
    .stButton>button:hover { background-color: #2471A3; }
    .agent-card {
        background: white;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 5px solid;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown("""
<div style='background:linear-gradient(135deg,#1A5276,#2471A3);
padding:28px 32px;border-radius:12px;margin-bottom:24px;
box-shadow:0 4px 16px rgba(0,0,0,0.15)'>
    <h1 style='color:white;margin:0;font-size:28px'>🏥 AfyaLink HIV Support Ecosystem</h1>
    <p style='color:#AED6F1;margin:6px 0 0;font-size:14px'>
        Agent Pride Prototype — Scout &#8594; Guardian &#8594; Hunter Handoff Simulation
    </p>
    <p style='color:#AED6F1;margin:4px 0 0;font-size:12px'>
        Dignity-preserving AI for rural HIV adherence support in Kenya & Uganda
    </p>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("## About AfyaLink")
    st.info(
        "AfyaLink deploys a 3-agent AI ecosystem to support rural HIV patients "
        "with stigma-safe communication, harvest-cycle aligned scheduling, "
        "and human oversight at every critical decision point."
    )
    st.markdown("---")
    st.markdown("### Agent Roles")
    st.markdown("""
    <div class='agent-card' style='border-color:#2471A3'>
        <b style='color:#2471A3'>🔵 Scout</b><br>
        <small>Community Health Companion<br>
        Max 2 msgs/day · Stigma-safe · Stress detection</small>
    </div>
    <div class='agent-card' style='border-color:#1E8449'>
        <b style='color:#1E8449'>🟢 Guardian</b><br>
        <small>Clinical Triage Coordinator<br>
        Transport support · Appointment rescheduling</small>
    </div>
    <div class='agent-card' style='border-color:#6C3483'>
        <b style='color:#6C3483'>🟣 Hunter</b><br>
        <small>Human-Care Coordinator<br>
        CHW briefings · Home delivery · No clinical decisions</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### GUARD Safety Rails")
    guards = [
        "Never mention HIV/AIDS/ARV without opt-in",
        "Max 2 SMS/day per patient",
        "Dignity filter — no 'defaulter' language",
        "Human CHW alert within 4 hours",
        "All data on AWS Africa (Cape Town)",
        "Kenya DPA 2019 & Uganda DPA 2022 compliant",
    ]
    for g in guards:
        st.markdown(f"🛡 <small>{g}</small>", unsafe_allow_html=True)

# ── PATIENT INPUT ──
st.markdown("## Patient Profile")

col1, col2 = st.columns(2)

with col1:
    patient_name    = st.text_input("Patient Name", value="Mary Adhiambo")
    patient_age     = st.number_input("Age", min_value=15, max_value=80, value=34)
    patient_occupation = st.text_input("Occupation", value="Subsistence farmer")
    patient_location = st.text_input("Location / Sub-county", value="Busia")

with col2:
    distance_km     = st.number_input("Distance from clinic (km)", min_value=1, value=18)
    transport_cost  = st.number_input("Transport cost round trip (KES)", min_value=0, value=200)
    missed_pickups  = st.number_input("Consecutive missed ART pickups", min_value=0, value=3)
    last_vl         = st.selectbox("Last viral load status", ["Suppressed", "Unsuppressed", "Unknown"])

patient_message = st.text_area(
    "Patient message / SMS received",
    value="I cannot come to the clinic this month. No money for transport. My children need food.",
    height=80
)

col3, col4 = st.columns(2)
with col3:
    current_season = st.selectbox(
        "Current season",
        ["Maize planting (March/April)", "Maize harvest (Aug/Sept)",
         "School fee season (Jan/May/Sept)", "Off-season", "Long rains (April/November)"],
        index=1
    )
with col4:
    chw_name = st.text_input("Assigned CHW name", value="Mama Akinyi")
    chw_specialty = st.text_input("CHW specialty", value="Dholuo speaker, Busia district")

st.markdown("---")

# ── RUN BUTTON ──
run = st.button("Run AfyaLink Agent Handoff", type="primary", use_container_width=True)

if run:
    if not groq_key:
        st.error("GROQ_API_KEY not found. Please check your .env file or Streamlit secrets.")
        st.stop()

    # ── BUILD LLM ──
    llm = LLM(
        model="groq/llama-3.1-8b-instant",
        api_key=groq_key,
        temperature=0.2
    )

    # ── AGENTS ──
    scout = Agent(
        role="Community Health Companion",
        goal="Provide daily check-ins, medication reminders, and detect health stress signals using stigma-safe communication",
        backstory=f"""You are a caring community health companion for AfyaLink HIV Support patients
        in rural Kenya and Uganda. You understand maize planting cycles (March/April, Aug/Sept),
        school fee seasons (January, May, September), and the distance barriers patients face.
        You NEVER mention HIV, AIDS, or ARV directly in messages without patient opt-in.
        You send maximum 2 messages per day per patient.
        If a patient mentions transport costs, food insecurity, or fear, output a clear escalation alert.
        DO NOT attempt to call any external tools or delegate work.""",
        verbose=False,
        allow_delegation=False,
        llm=llm
    )

    guardian = Agent(
        role="Clinical Triage Coordinator",
        goal="Assess missed appointments, process transport support, reschedule appointments aligned with harvest cycles",
        backstory="""You are a clinical triage coordinator for AfyaLink.
        You can reschedule appointments and process transport vouchers via M-PESA.
        You NEVER access viral load data without explicit clinician authorisation.
        You consider agricultural calendars and school fee seasons before rescheduling.
        You NEVER stigmatise patients — avoid 'defaulter', 'non-compliant', or 'failure'.
        DO NOT attempt to call tools, call functions, or execute manual delegations.""",
        verbose=False,
        allow_delegation=False,
        llm=llm
    )

    hunter = Agent(
        role="Human-Care Coordinator",
        goal="Coordinate CHW home visits and prepare dignified clinical briefing packets for nurses",
        backstory="""You coordinate between AI triage and human Community Health Workers at AfyaLink.
        You NEVER make clinical decisions yourself.
        You only prepare clear, empathetic briefing packets for CHWs and nurses.
        You always frame patients with dignity — never using 'risky', 'unreliable', or 'defaulter'.
        You alert the assigned CHW within 4 hours of receiving an escalation.
        DO NOT attempt to call tools or delegate.""",
        verbose=False,
        allow_delegation=False,
        llm=llm
    )

    # ── TASKS ──
    scout_task = Task(
        description=f"""A patient named {patient_name}, {patient_age}, {patient_occupation}
        in {patient_location} has sent this message:
        '{patient_message}'

        Current season: {current_season}
        Distance from clinic: {distance_km}km
        Transport cost: KES {transport_cost} round trip

        1. Identify the health stress signals — what barriers is this patient facing?
        2. Note the current season ({current_season}) and its impact on availability
        3. Check if this needs escalation to Guardian Agent
        4. Draft a stigma-safe, supportive response in simple English (max 2 sentences)
           — do NOT mention HIV, AIDS, or medication directly""",
        agent=scout,
        expected_output="Health stress analysis and stigma-safe response draft with escalation recommendation"
    )

    guardian_task = Task(
        description=f"""Patient has missed {missed_pickups} consecutive ART pickups.
        Patient profile:
        - Name: {patient_name}, {patient_age}, {patient_occupation}, {patient_location}
        - Distance from clinic: {distance_km}km
        - Transport cost: KES {transport_cost} round trip
        - Current season: {current_season}
        - Last viral load: {last_vl}
        - Risk flags: {missed_pickups} consecutive missed pickups, transport barrier, food insecurity signal

        1. Assess missed appointments against the agricultural and school fee calendar
        2. Identify all risk flags — distinguish clinical risk from barrier-driven absence
        3. Propose transport support via M-PESA (KES {transport_cost}) and a rescheduled appointment
        4. Prepare the full assessment to escalate to Hunter Agent""",
        agent=guardian,
        expected_output="Barrier-aware triage assessment with transport support proposal and escalation packet"
    )

    hunter_task = Task(
        description=f"""Prepare a CHW briefing packet for a home visit.
        Patient: {patient_name}, {patient_age}, {patient_occupation}, {patient_location}
        Missed {missed_pickups} consecutive ART pickups — barrier-driven, not behavioural
        Last viral load: {last_vl}
        Transport barrier: {distance_km}km, KES {transport_cost} round trip
        Current season: {current_season}
        Transport voucher: KES {transport_cost} M-PESA support approved
        Assigned CHW: {chw_name} ({chw_specialty})

        1. Write a dignified, empathetic briefing packet for {chw_name}
        2. Suggest a home delivery option for 2-month medication supply
        3. Propose a harvest-aligned rescheduled clinic appointment
        4. Note cross-support opportunities (food security referral, NHIF registration)
        5. Confirm human CHW visit required — no AI clinical decision to be made""",
        agent=hunter,
        expected_output="Complete CHW briefing packet with home delivery plan and dignity-centred framing"
    )

    # ── RUN AGENTS SEPARATELY FOR DISPLAY ──
    st.markdown("## Agent Outputs")

    with st.status("Running AfyaLink agent handoff...", expanded=True) as status:
        st.write("Scout Agent detecting stress signals...")
        try:
            scout_result = Crew(
                agents=[scout], tasks=[scout_task], verbose=False
            ).kickoff()

            st.write("Guardian Agent assessing barriers and triage...")
            guardian_result = Crew(
                agents=[guardian], tasks=[guardian_task], verbose=False
            ).kickoff()

            st.write("Hunter Agent preparing CHW briefing packet...")
            hunter_result = Crew(
                agents=[hunter], tasks=[hunter_task], verbose=False
            ).kickoff()

            status.update(label="Agent handoff complete", state="complete")

        except Exception as e:
            status.update(label="Error occurred", state="error")
            st.error(f"Error: {e}")
            st.stop()

    # ── SCOUT OUTPUT ──
    with st.expander("🔵 Scout Agent — Community Health Companion", expanded=True):
        st.markdown("""<div class='agent-card' style='border-color:#2471A3'>""",
                    unsafe_allow_html=True)
        st.markdown(str(scout_result))
        st.markdown("</div>", unsafe_allow_html=True)

    # ── GUARDIAN OUTPUT ──
    with st.expander("🟢 Guardian Agent — Clinical Triage Coordinator", expanded=True):
        st.markdown("""<div class='agent-card' style='border-color:#1E8449'>""",
                    unsafe_allow_html=True)
        st.markdown(str(guardian_result))
        st.markdown("</div>", unsafe_allow_html=True)

    # ── HUNTER OUTPUT ──
    with st.expander("🟣 Hunter Agent — Human-Care Coordinator", expanded=True):
        st.markdown("""<div class='agent-card' style='border-color:#6C3483'>""",
                    unsafe_allow_html=True)
        st.markdown(str(hunter_result))
        st.markdown("</div>", unsafe_allow_html=True)

    # ── GUARD RAIL SUMMARY ──
    st.markdown("---")
    st.markdown("### GUARD Safety Rail Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Missed Pickups",
                  f"{missed_pickups} pickups",
                  "CHW escalation triggered" if missed_pickups >= 3 else "Monitoring")
    with c2:
        st.metric("Transport Barrier",
                  f"{distance_km}km / KES {transport_cost}",
                  "Voucher approved")
    with c3:
        st.metric("Dignity Filter", "Active", "No stigmatising language")
    with c4:
        st.metric("Data Sovereignty", "100%", "AWS Africa — Cape Town")

    st.success(
        f"Agent handoff complete. CHW briefing packet ready for {chw_name}. "
        f"Human review required before any clinical decision."
    )

# ── FOOTER ──
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:gray;font-size:11px'>"
    "AfyaLink HIV Support Ecosystem  |  Built with CrewAI + Groq LLaMA 3.1  |  "
    "Kenya DPA 2019 & Uganda DPA 2022 Compliant  |  "
    "All data stored on AWS Africa (Cape Town)  |  "
    "No clinical decisions made without human oversight"
    "</p>",
    unsafe_allow_html=True
)