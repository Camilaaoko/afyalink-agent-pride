import os
import asyncio
import litellm
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

# ── LOAD ENV ──
load_dotenv()
os.environ["CREWAI_DISABLE_PROMPT_CACHING"] = "true"

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

# ── LLM ──
groq_key = os.getenv("GROQ_API_KEY")

llm = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=groq_key,
    temperature=0.2
)

# ── SCOUT AGENT ──
scout = Agent(
    role="Community Health Companion",
    goal="Provide daily check-ins, medication reminders, and detect health stress signals using stigma-safe communication",
    backstory="""You are a caring community health companion for AfyaLink HIV Support patients 
    in rural Kenya and Uganda. You understand maize planting cycles (March/April, Aug/Sept), 
    school fee seasons (January, May, September), and the distance barriers patients face.
    You NEVER mention HIV, AIDS, or ARV directly in messages without patient opt-in for direct language.
    You send maximum 2 messages per day per patient.
    If a patient mentions transport costs, food insecurity, or fear, you output a clear escalation alert.
    DO NOT attempt to call any external tools or delegate work.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ── GUARDIAN AGENT ──
guardian = Agent(
    role="Clinical Triage Coordinator",
    goal="Assess missed appointments, process transport support, reschedule appointments aligned with harvest cycles",
    backstory="""You are a clinical triage coordinator for AfyaLink. 
    You can reschedule appointments and process transport vouchers via M-PESA.
    You NEVER access viral load data without explicit clinician authorisation.
    You consider agricultural calendars and school fee seasons before rescheduling.
    You NEVER stigmatise patients — avoid words like 'defaulter', 'non-compliant', or 'failure'.
    Your sole task is to write down the triage assessment and pass it forward.
    DO NOT attempt to call tools, call functions, or execute manual delegations.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ── HUNTER AGENT ──
hunter = Agent(
    role="Human-Care Coordinator",
    goal="Coordinate CHW home visits and prepare dignified clinical briefing packets for nurses",
    backstory="""You coordinate between AI triage and human Community Health Workers at AfyaLink.
    You NEVER make clinical decisions yourself.
    You only prepare clear, empathetic briefing packets for CHWs and nurses.
    You match patients to CHWs with relevant expertise and language skills.
    You always frame patients with dignity — never using words like 'risky', 'unreliable', or 'defaulter'.
    You alert the assigned CHW within 4 hours of receiving an escalation.
    DO NOT attempt to call tools or delegate.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ── TASKS ──
scout_task = Task(
    description="""A patient named Mary, 34, subsistence farmer in Busia has sent this message:
    'I cannot come to the clinic this month. No money for transport. My children need food.'

    1. Identify her health stress signal — what barriers is she facing?
    2. Note the current season (August — maize planting season) and its impact on her availability
    3. Check if this needs to be escalated to the Guardian Agent
    4. Draft a stigma-safe, supportive response in simple English (max 2 sentences)
       — do NOT mention HIV, AIDS, or medication directly""",
    agent=scout,
    expected_output="Health stress analysis and stigma-safe response draft with escalation recommendation"
)

guardian_task = Task(
    description="""Mary has missed her last 3 consecutive ART pickups.
    Patient profile:
    - Name: Mary Adhiambo, 34, subsistence farmer, Busia
    - Distance from clinic: 18km
    - Transport cost: KES 200 round trip
    - Current season: August — maize planting (peak farm workload)
    - School fee season: September upcoming
    - Last viral load: Suppressed (June 2025)
    - Transaction history: Regular M-PESA activity showing income shocks in Aug/Sept
    - Risk flags: 3 consecutive missed pickups, transport barrier, food insecurity signal

    Using only text, execute these steps:
    1. Assess the missed appointments against the agricultural and school fee calendar
    2. Identify all risk flags — distinguish between clinical risk and barrier-driven absence
    3. Propose a transport support amount via M-PESA (KES 200) and a rescheduled appointment
    4. Since 3+ consecutive pickups missed, prepare the full assessment to escalate to Hunter Agent""",
    agent=guardian,
    expected_output="Barrier-aware triage assessment with transport support proposal and escalation packet"
)

hunter_task = Task(
    description="""Prepare a CHW briefing packet for a home visit to Mary.
    Context from Guardian Agent:
    - Patient: Mary Adhiambo, 34, subsistence farmer, Busia
    - Missed 3 consecutive ART pickups — barrier-driven, not behavioural
    - Last viral load: Suppressed (June 2025) — no clinical deterioration indicated
    - Transport barrier: 18km distance, KES 200 round trip
    - Current season: August planting — high farm workload
    - School fee season: September — income pressure compounding
    - Transport voucher: KES 200 M-PESA support approved by Guardian
    - Recommended CHW: Mama Akinyi (Dholuo speaker, Busia district specialist)

    1. Write a dignified, empathetic briefing packet for Mama Akinyi
    2. Suggest a home delivery option for Mary's 2-month medication supply
    3. Propose a harvest-aligned rescheduled clinic appointment (November — post-harvest)
    4. Note any cross-support opportunities (e.g., food security referral, NHIF registration)
    5. Confirm human CHW visit is required — no AI clinical decision to be made""",
    agent=hunter,
    expected_output="Complete CHW briefing packet with home delivery plan, rescheduled appointment, and dignity-centred framing"
)

# ── CREW ──
afyalink_crew = Crew(
    agents=[scout, guardian, hunter],
    tasks=[scout_task, guardian_task, hunter_task],
    verbose=True
)

# ── RUN ──
print("=" * 60)
print("AFYALINK HIV SUPPORT ECOSYSTEM")
print("Scout -> Guardian -> Hunter Handoff Simulation")
print("=" * 60)

try:
    result = afyalink_crew.kickoff()
    print("\n" + "=" * 60)
    print("FINAL OUTPUT:")
    print("=" * 60)
    print(result)
except Exception as e:
    print(f"\nExecution Failed: {e}")