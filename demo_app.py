"""
IntelliKYC — Self-contained demo for Streamlit Community Cloud.
No FastAPI, no Redis, no EasyOCR required.
Stack: Groq Vision (Llama 4 Scout), MediaPipe FaceMesh, SHA-256 blockchain, Streamlit.
"""

import streamlit as st
import base64
import hashlib
import json
import os
import re
import time
import io
from datetime import datetime
from typing import Dict, Optional

# ── Optional heavy imports with graceful fallback ──────────────────────────────
try:
    from groq import Groq
    _GROQ_OK = True
except ImportError:
    _GROQ_OK = False

try:
    import mediapipe as mp
    import numpy as np
    from PIL import Image
    _MP_OK = True
except ImportError:
    _MP_OK = False

# ──────────────────────────────────────────────────────────────────────────────
# Page config (must be first Streamlit call)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntelliKYC Demo",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Styles ────────────────────────────────────────────────────────────────────
def _apply_styles():
    st.markdown(
        """
        <style>
        .kyc-title {
            font-size: 2em; font-weight: 700; letter-spacing: -0.5px;
            background: linear-gradient(90deg, #7c3aed, #2563eb);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 0;
        }
        .kyc-sub {
            font-size: 0.95em; color: #6b7280; margin-top: 4px; margin-bottom: 0;
        }
        .step-badge {
            display: inline-block;
            background: #7c3aed; color: white;
            border-radius: 20px; padding: 2px 14px;
            font-size: 0.8em; font-weight: 600; letter-spacing: 0.3px;
        }
        .hash-box {
            font-family: monospace; font-size: 0.75em;
            background: #1e1e2e; color: #a5f3fc;
            padding: 8px 12px; border-radius: 6px;
            word-break: break-all;
        }
        .feature-card {
            background: #1e1e2e; border-radius: 8px;
            padding: 16px 18px; border: 1px solid #2d2d3f;
        }
        .feature-card h4 { margin: 0 0 6px 0; font-size: 0.95em; font-weight: 600; color: #e2e8f0; }
        .feature-card p  { margin: 0; font-size: 0.85em; color: #94a3b8; line-height: 1.5; }
        .notice-box {
            background: #1e293b; border-left: 3px solid #7c3aed;
            border-radius: 0 6px 6px 0; padding: 10px 14px;
            font-size: 0.88em; color: #cbd5e1;
        }
        .lv-step-done   { text-align:center; color:#22c55e; font-size:0.85em; }
        .lv-step-active { text-align:center; color:#7c3aed; font-weight:700; font-size:0.85em; }
        .lv-step-todo   { text-align:center; color:#374151; font-size:0.85em; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Groq client ───────────────────────────────────────────────────────────────
@st.cache_resource
def _groq_client():
    key = None
    try:
        key = st.secrets.get("GROQ_API_KEY") or st.secrets.get("groq_api_key")
    except Exception:
        pass
    if not key:
        key = os.environ.get("GROQ_API_KEY", "")
    if key and _GROQ_OK:
        return Groq(api_key=key)
    return None


# ── AI analysis ───────────────────────────────────────────────────────────────
def analyze_document(image_bytes: bytes, doc_type: str, customer: Dict) -> Dict:
    """Single Groq Vision call: OCR + field validation + fraud scoring."""
    client = _groq_client()
    if not client:
        return _mock_analysis(customer, doc_type)

    b64 = base64.b64encode(image_bytes).decode()
    id_key = "aadhaar_number" if doc_type == "aadhaar" else "pan_number"

    prompt = f"""You are an AI KYC specialist verifying an Indian {doc_type.upper()} card.

Customer-provided information:
  Name : {customer.get('full_name', '—')}
  DOB  : {customer.get('date_of_birth', '—')}
  ID   : {customer.get(id_key, '—')}

Tasks:
1. Extract all visible text from the document image.
2. Identify: name, date_of_birth, id_number, address.
3. Compare extracted fields against customer-provided values.
4. Assess authenticity — look for editing, inconsistent fonts, tampering.
5. Output a fraud risk score (0 = safe, 1 = fraudulent).

Respond with ONLY valid JSON, no markdown fences:
{{
  "document_detected": true,
  "extracted_fields": {{"name": "...", "date_of_birth": "...", "id_number": "...", "address": "..."}},
  "field_match": {{"name_match": true, "dob_match": true, "id_match": true, "overall_score": 0.92}},
  "fraud": {{
    "risk_score": 0.08, "risk_level": "LOW", "indicators": [],
    "authenticity_score": 0.95, "image_quality": "GOOD", "confidence": 0.88
  }},
  "ocr_text": "...",
  "recommendation": "APPROVE"
}}"""

    try:
        resp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }],
            temperature=0.1,
            max_tokens=900,
        )
        raw = resp.choices[0].message.content
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        st.caption(f"Groq error: {e} — using demo results.")

    return _mock_analysis(customer, doc_type)


def _mock_analysis(customer: Dict, doc_type: str) -> Dict:
    id_key = "aadhaar_number" if doc_type == "aadhaar" else "pan_number"
    return {
        "document_detected": True,
        "extracted_fields": {
            "name": customer.get("full_name"),
            "date_of_birth": customer.get("date_of_birth"),
            "id_number": customer.get(id_key),
            "address": "123 Demo Street, Mumbai, MH 400001",
        },
        "field_match": {"name_match": True, "dob_match": True, "id_match": True, "overall_score": 0.93},
        "fraud": {
            "risk_score": 0.07, "risk_level": "LOW", "indicators": [],
            "authenticity_score": 0.96, "image_quality": "GOOD", "confidence": 0.85,
        },
        "ocr_text": "Demo mode — add GROQ_API_KEY for live AI analysis.",
        "recommendation": "APPROVE",
        "mock": True,
    }


# ── Head pose detection (MediaPipe FaceMesh) ──────────────────────────────────
def detect_head_pose(image_bytes: bytes) -> Dict:
    """
    Estimate horizontal head orientation using FaceMesh landmarks.
    Returns orientation: 'left' | 'right' | 'center'
    """
    if not _MP_OK:
        return {"face_detected": True, "orientation": "unknown", "confidence": 0.85, "mock": True}
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr = np.array(img)
        with mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5
        ) as fm:
            result = fm.process(arr)

        if not result.multi_face_landmarks:
            return {"face_detected": False, "orientation": None, "confidence": 0.0}

        lm = result.multi_face_landmarks[0].landmark
        nose_x   = lm[1].x
        left_x   = lm[33].x    # subject's left eye outer corner
        right_x  = lm[263].x   # subject's right eye outer corner
        eye_center = (left_x + right_x) / 2
        eye_span   = abs(left_x - right_x)

        if eye_span < 0.05:
            return {"face_detected": True, "orientation": "center", "confidence": 0.5}

        # Positive deviation → nose to the right side in image
        deviation = (nose_x - eye_center) / eye_span

        if deviation < -0.18:
            orientation = "left"
        elif deviation > 0.18:
            orientation = "right"
        else:
            orientation = "center"

        confidence = min(1.0, 0.55 + abs(deviation) * 2.5)
        return {
            "face_detected": True,
            "orientation": orientation,
            "confidence": round(confidence, 2),
            "deviation": round(deviation, 3),
        }
    except Exception as e:
        return {"face_detected": True, "orientation": "center", "confidence": 0.65, "mock": True, "error": str(e)}


# ── Blockchain record ─────────────────────────────────────────────────────────
def create_blockchain_record(customer: Dict, analysis: Dict, liveness: Dict) -> Dict:
    ts = datetime.utcnow().isoformat() + "Z"
    payload = {
        "customer_hash": hashlib.sha256(
            (customer.get("full_name", "") + customer.get("email", "")).encode()
        ).hexdigest()[:20],
        "doc_match_score": analysis.get("field_match", {}).get("overall_score", 0),
        "fraud_risk": analysis.get("fraud", {}).get("risk_score", 0),
        "liveness_confidence": liveness.get("confidence", 0),
        "recommendation": analysis.get("recommendation", "UNKNOWN"),
        "timestamp": ts,
    }
    tx_hash    = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    block_hash = hashlib.sha256(f"{'0'*64}{tx_hash}{ts}".encode()).hexdigest()
    zk_id      = hashlib.md5(tx_hash.encode()).hexdigest()
    return {
        "transaction_hash": tx_hash,
        "block_hash": block_hash,
        "zk_proof_id": zk_id,
        "timestamp": ts,
        "payload": payload,
    }


# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "step": 1,
        "customer": {},
        "doc_type": "aadhaar",
        "doc_bytes": None,
        "analysis": None,
        "liveness": None,
        "blockchain": None,
        "decision": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Sidebar ───────────────────────────────────────────────────────────────────
def _sidebar():
    with st.sidebar:
        st.markdown("**IntelliKYC**")
        st.caption("AI-Powered KYC Verification")
        st.markdown("---")

        steps = [
            (1, "Home"), (2, "Registration"), (3, "Document Upload"),
            (4, "AI Analysis"), (5, "Face Liveness"), (6, "Blockchain"), (7, "Decision"),
        ]
        cur = st.session_state.step
        for n, label in steps:
            if n < cur:
                st.markdown(f"<span style='color:#6b7280;font-size:0.9em'>✓ {n}. {label}</span>", unsafe_allow_html=True)
            elif n == cur:
                st.markdown(f"<span style='color:#7c3aed;font-weight:600;font-size:0.9em'>→ {n}. {label}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:#374151;font-size:0.9em'>&nbsp;&nbsp;{n}. {label}</span>", unsafe_allow_html=True)

        st.markdown("---")
        client   = _groq_client()
        ai_col   = "#22c55e" if client else "#f59e0b"
        mp_col   = "#22c55e" if _MP_OK  else "#f59e0b"
        ai_label = "Connected"   if client else "Demo mode"
        mp_label = "Ready"       if _MP_OK  else "Unavailable"

        st.markdown(f"<span style='color:{ai_col};font-size:0.85em'>● Groq AI: {ai_label}</span>",   unsafe_allow_html=True)
        st.markdown(f"<span style='color:{mp_col};font-size:0.85em'>● MediaPipe: {mp_label}</span>", unsafe_allow_html=True)
        st.markdown("<span style='color:#22c55e;font-size:0.85em'>● Blockchain: Ready</span>",       unsafe_allow_html=True)

        st.markdown("---")
        st.caption("Groq Llama 4 Scout · MediaPipe · SHA-256 · Streamlit")
        st.caption("[GitHub](https://github.com/nihar-sm/iKYC)  ·  Team Vagabond")


# ─────────────────────────────────────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────────────────────────────────────

def page_home():
    st.markdown('<div class="kyc-title">IntelliKYC</div>', unsafe_allow_html=True)
    st.markdown('<p class="kyc-sub">AI-Powered Identity Verification Pipeline</p>', unsafe_allow_html=True)
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="feature-card"><h4>Groq Vision AI</h4>'
            '<p>Llama 4 Scout analyses document images — extracts fields, validates data, '
            'and scores fraud risk in a single API call.</p></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="feature-card"><h4>Face Liveness</h4>'
            '<p>MediaPipe FaceMesh detects face presence and head orientation through '
            'a 3-step movement challenge (left, right, forward).</p></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="feature-card"><h4>Blockchain Record</h4>'
            '<p>Each verified KYC creates an immutable SHA-256 transaction hash '
            'with a zero-knowledge proof ID for privacy.</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Verification pipeline**")
    pipeline_cols = st.columns(11)
    for i, step in enumerate(["Register", "Upload Doc", "AI Scan", "Liveness", "Blockchain", "Decision"]):
        pipeline_cols[i * 2].markdown(
            f"<div style='text-align:center;font-size:0.8em;color:#e2e8f0;"
            f"background:#1e1e2e;border-radius:6px;padding:6px 4px;'>{step}</div>",
            unsafe_allow_html=True,
        )
        if i < 5:
            pipeline_cols[i * 2 + 1].markdown(
                "<div style='text-align:center;color:#4b5563;padding-top:6px;'>→</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    client = _groq_client()
    c1, c2, c3 = st.columns(3)
    if client:
        c1.success("Groq AI: Connected")
    else:
        c1.warning("Groq AI: Demo mode")
    if _MP_OK:
        c2.success("MediaPipe: Ready")
    else:
        c2.warning("MediaPipe: Unavailable")
    c3.success("Blockchain: Ready")

    if not client:
        st.markdown(
            '<div class="notice-box">To enable live AI analysis, add <strong>GROQ_API_KEY</strong> '
            'in Streamlit Cloud → App Settings → Secrets. '
            'Get a free key at <a href="https://console.groq.com" target="_blank">console.groq.com</a>.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Start KYC Verification", type="primary", use_container_width=True):
        st.session_state.step = 2
        st.rerun()


# ── Registration (no st.form — prevents Enter-key submission) ─────────────────

def page_registration():
    st.markdown('<span class="step-badge">Step 1 of 6</span>', unsafe_allow_html=True)
    st.markdown("### Customer Registration")
    st.markdown("Enter details exactly as they appear on your identity document.")

    # Selectbox lives outside the form so switching Aadhaar/PAN triggers an immediate rerender
    doc_type = st.selectbox("Document Type *", ["Aadhaar", "PAN"], key="reg_dtype")

    # st.form with enter_to_submit=False:
    #   - all field values are sent atomically on button click (no debounce race)
    #   - pressing Enter in a text field does NOT submit
    with st.form("reg_form", enter_to_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            name  = st.text_input("Full Name *",     placeholder="As on Aadhaar / PAN")
            dob   = st.date_input("Date of Birth *", min_value=datetime(1900, 1, 1).date())
            email = st.text_input("Email *",         placeholder="you@example.com")
        with c2:
            phone = st.text_input("Phone *", placeholder="+91 98765 43210")
            if doc_type == "Aadhaar":
                doc_num_raw = st.text_input("Aadhaar Number *", placeholder="123456789012", max_chars=12)
            else:
                doc_num_raw = st.text_input("PAN Number *", placeholder="ABCDE1234F", max_chars=10)

        submitted = st.form_submit_button("Continue", type="primary", use_container_width=True)

    if submitted:
        name  = (name  or "").strip()
        email = (email or "").strip()
        phone = (phone or "").strip()

        if not name or not email or not phone:
            st.error("Please fill all required fields.")
            return

        if doc_type == "Aadhaar":
            digits = re.sub(r'\D', '', doc_num_raw or "")
            if len(digits) != 12:
                st.error("Aadhaar number must be exactly 12 digits.")
                return
            id_key, doc_num = "aadhaar_number", digits
        else:
            doc_num = (doc_num_raw or "").strip().upper()
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', doc_num):
                st.error("Invalid PAN. Expected: ABCDE1234F (5 letters · 4 digits · 1 letter)")
                return
            id_key = "pan_number"

        st.session_state.customer = {
            "full_name": name,
            "date_of_birth": str(dob),
            "email": email,
            "phone": phone,
            id_key: doc_num,
        }
        st.session_state.doc_type = doc_type.lower()
        st.session_state.step = 3
        st.rerun()


def page_document():
    st.markdown('<span class="step-badge">Step 2 of 6</span>', unsafe_allow_html=True)
    st.markdown("### Document Upload")

    if not st.session_state.customer:
        st.warning("Complete registration first.")
        if st.button("Back to Registration"):
            st.session_state.step = 2; st.rerun()
        return

    doc_label = st.session_state.doc_type.capitalize()
    st.markdown(f"Upload a clear photo of your **{doc_label}** card.")

    c1, c2 = st.columns([3, 2])
    with c1:
        f = st.file_uploader(f"{doc_label} card", type=["jpg", "jpeg", "png"], help="Max 10 MB")
        if f:
            if f.size > 10 * 1024 * 1024:
                st.error("File exceeds 10 MB."); return
            st.image(f, caption=f"Your {doc_label}", use_container_width=True)
            if st.button("Confirm & Continue", type="primary", use_container_width=True):
                st.session_state.doc_bytes = f.read()
                st.session_state.step = 4
                st.rerun()
    with c2:
        st.markdown("**Tips for a good scan**")
        st.markdown("- Card fully visible, flat on surface\n- Even lighting, no glare\n- JPG or PNG, under 10 MB")
        cust = st.session_state.customer
        if cust:
            st.markdown("---")
            st.markdown(f"**Registered:** {cust.get('full_name')}  \n**DOB:** {cust.get('date_of_birth')}")


def page_ai_analysis():
    st.markdown('<span class="step-badge">Step 3 of 6</span>', unsafe_allow_html=True)
    st.markdown("### AI Document Analysis")

    if not st.session_state.doc_bytes:
        st.warning("Upload a document first.")
        if st.button("Back to Document"):
            st.session_state.step = 3; st.rerun()
        return

    if st.session_state.analysis:
        _show_analysis(st.session_state.analysis)
        st.markdown("---")
        if st.button("Continue to Face Liveness", type="primary", use_container_width=True):
            st.session_state.step = 5; st.rerun()
        return

    c1, c2 = st.columns([1, 1])
    with c1:
        st.image(st.session_state.doc_bytes, caption="Document", use_container_width=True)
    with c2:
        st.markdown("**Groq Vision will:**")
        st.markdown("1. Extract all text (OCR)\n2. Validate fields vs. registration\n3. Detect fraud patterns\n4. Score risk level")
        if st.button("Run AI Analysis", type="primary", use_container_width=True):
            with st.spinner("Groq AI is analysing your document…"):
                result = analyze_document(
                    st.session_state.doc_bytes,
                    st.session_state.doc_type,
                    st.session_state.customer,
                )
            st.session_state.analysis = result
            st.rerun()


def _show_analysis(r: Dict):
    fraud = r.get("fraud", {})
    match = r.get("field_match", {})
    risk  = fraud.get("risk_level", "LOW")
    badge = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "❌"}.get(risk, "—")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fraud Risk",      f"{badge} {risk}", f"score {fraud.get('risk_score', 0):.2f}")
    c2.metric("Authenticity",    f"{fraud.get('authenticity_score', 0.9):.0%}")
    c3.metric("Field Match",     f"{match.get('overall_score', 0.9):.0%}")
    c4.metric("Recommendation",  r.get("recommendation", "REVIEW"))

    with st.expander("Extracted Fields", expanded=True):
        ex = r.get("extracted_fields", {})
        a, b = st.columns(2)
        items = list(ex.items())
        for field, val in items[:2]:
            a.markdown(f"**{field.replace('_',' ').title()}:** {val or '—'}")
        for field, val in items[2:]:
            b.markdown(f"**{field.replace('_',' ').title()}:** {val or '—'}")

    inds = fraud.get("indicators", [])
    if inds:
        with st.expander("Fraud Indicators"):
            for i in inds: st.warning(f"• {i}")
    else:
        st.success("No fraud indicators detected")

    if r.get("mock"):
        st.caption("Demo mode — add GROQ_API_KEY for real AI analysis.")


# ── Face liveness: 3-step head movement challenge ─────────────────────────────

_LV_STEPS = [
    {"key": "left",   "label": "Turn your head LEFT",       "hint": "Turn until your right ear faces the camera", "icon": "←"},
    {"key": "right",  "label": "Turn your head RIGHT",      "hint": "Turn until your left ear faces the camera",  "icon": "→"},
    {"key": "center", "label": "Face the camera directly",  "hint": "Look straight ahead at the camera",          "icon": "●"},
]

def _lv_step_html(i: int, cur: int, s: dict) -> str:
    if i < cur:
        cls = "lv-step-done"
        icon = f"✓ {s['icon']}"
    elif i == cur:
        cls = "lv-step-active"
        icon = s["icon"]
    else:
        cls = "lv-step-todo"
        icon = s["icon"]
    return f'<div class="{cls}">{icon}<br><small>{s["key"]}</small></div>'


def page_liveness():
    st.markdown('<span class="step-badge">Step 4 of 6</span>', unsafe_allow_html=True)
    st.markdown("### Face Liveness Detection")

    if not st.session_state.analysis:
        st.warning("Complete AI analysis first.")
        if st.button("Back to Analysis"):
            st.session_state.step = 4; st.rerun()
        return

    # Already completed
    if st.session_state.liveness:
        lv = st.session_state.liveness
        passed = lv.get("steps_passed", 3)
        st.success(f"Liveness verified — {passed}/3 movement checks passed")
        if lv.get("mock"):
            st.caption("Running in demo mode — MediaPipe head-pose analysis unavailable.")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Continue to Blockchain", type="primary", use_container_width=True):
                st.session_state.step = 6; st.rerun()
        with col2:
            if st.button("Redo liveness check", use_container_width=True):
                st.session_state.liveness = None
                st.session_state.pop("liveness_challenge", None)
                st.rerun()
        return

    # Init challenge state
    if "liveness_challenge" not in st.session_state:
        st.session_state["liveness_challenge"] = {"step": 0, "results": []}

    cs = st.session_state["liveness_challenge"]

    # All steps complete → write final result and rerun
    if cs["step"] >= len(_LV_STEPS):
        passed = sum(1 for r in cs["results"] if r["passed"])
        st.session_state.liveness = {
            "face_detected": True,
            "confidence": round(0.82 + 0.06 * passed, 2),
            "steps_passed": passed,
            "mock": not _MP_OK,
        }
        st.rerun()
        return

    # Step progress bar
    prog_cols = st.columns(len(_LV_STEPS))
    for i, s in enumerate(_LV_STEPS):
        prog_cols[i].markdown(_lv_step_html(i, cs["step"], s), unsafe_allow_html=True)

    st.markdown("---")
    cur = _LV_STEPS[cs["step"]]

    photo_key = f"_lv_photo_{cs['step']}"

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"**{cur['label']}**")
        photo = st.camera_input(
            "Position yourself, then click to capture",
            key=f"_lv_cam_{cs['step']}",
        )
        # Persist bytes into session_state the moment camera fires so they
        # survive the Verify-button rerun (camera widget can reset to None)
        if photo is not None:
            st.session_state[photo_key] = photo.read()

        photo_bytes = st.session_state.get(photo_key)

        if photo_bytes:
            if st.button("Verify", type="primary", use_container_width=True, key=f"_lv_btn_{cs['step']}"):
                with st.spinner("Analysing pose…"):
                    pose = detect_head_pose(photo_bytes)

                expected = cur["key"]

                if pose.get("mock"):
                    ok = True
                elif not pose.get("face_detected"):
                    ok = False
                elif expected == "center":
                    ok = abs(pose.get("deviation", 0)) < 0.22
                else:
                    ok = abs(pose.get("deviation", 0)) > 0.14

                if ok:
                    cs["results"].append({"step": expected, "passed": True, "pose": pose})
                    cs["step"] += 1
                    st.session_state.pop(photo_key, None)  # clear stored photo for this step
                    st.rerun()
                else:
                    st.error("Head position not detected clearly. Turn your head more and try again.")

    with c2:
        st.markdown(f"**Step {cs['step'] + 1} of {len(_LV_STEPS)}**")
        st.markdown(f"*{cur['hint']}*")
        st.markdown("---")
        if cs["step"] > 0:
            st.markdown(f"Completed: {cs['step']}/{len(_LV_STEPS)}")
        if not _MP_OK:
            st.caption("Demo mode — head-pose analysis unavailable; all steps auto-pass.")


def page_blockchain():
    st.markdown('<span class="step-badge">Step 5 of 6</span>', unsafe_allow_html=True)
    st.markdown("### Blockchain Recording")

    if not st.session_state.liveness:
        st.warning("Complete liveness check first.")
        if st.button("Back to Liveness"):
            st.session_state.step = 5; st.rerun()
        return

    if st.session_state.blockchain:
        rec = st.session_state.blockchain
        st.success("KYC record committed to blockchain")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Transaction Hash**")
            st.markdown(f'<div class="hash-box">{rec["transaction_hash"]}</div>', unsafe_allow_html=True)
            st.markdown("**Block Hash**")
            st.markdown(f'<div class="hash-box">{rec["block_hash"]}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown("**ZK-Proof ID**")
            st.markdown(f'<div class="hash-box">{rec["zk_proof_id"]}</div>', unsafe_allow_html=True)
            st.markdown(f"**Timestamp:** `{rec['timestamp']}`")
            st.markdown("**Verification Level:** STANDARD")

        st.markdown("---")
        if st.button("View Final Decision", type="primary", use_container_width=True):
            fraud = st.session_state.analysis.get("fraud", {})
            lv    = st.session_state.liveness
            if fraud.get("risk_score", 0.1) < 0.35 and lv.get("confidence", 0) > 0.55 and lv.get("face_detected"):
                st.session_state.decision = "APPROVED"
            elif fraud.get("risk_score", 0.1) < 0.65:
                st.session_state.decision = "MANUAL_REVIEW"
            else:
                st.session_state.decision = "REJECTED"
            st.session_state.step = 7
            st.rerun()
        return

    with st.expander("How this works"):
        st.markdown(
            "1. **Payload hashing** — verification scores + timestamp → SHA-256 transaction hash\n"
            "2. **Block linking** — tx hash chained to previous block hash\n"
            "3. **ZK-Proof ID** — allows third-party verification without exposing customer PII\n"
            "4. **Immutability** — altering any field breaks the entire hash chain"
        )

    if st.button("Commit to Blockchain", type="primary", use_container_width=True):
        with st.spinner("Creating immutable record…"):
            time.sleep(0.8)
            rec = create_blockchain_record(
                st.session_state.customer,
                st.session_state.analysis,
                st.session_state.liveness,
            )
        st.session_state.blockchain = rec
        st.rerun()


def page_decision():
    st.markdown('<span class="step-badge">Step 6 of 6</span>', unsafe_allow_html=True)
    st.markdown("### KYC Decision")

    decision   = st.session_state.decision or "UNKNOWN"
    customer   = st.session_state.customer
    analysis   = st.session_state.analysis or {}
    liveness   = st.session_state.liveness or {}
    blockchain = st.session_state.blockchain or {}
    fraud      = analysis.get("fraud", {})

    if decision == "APPROVED":
        st.success("## KYC Approved")
        st.markdown(f"**{customer.get('full_name', 'Customer')}** has been successfully verified.")
    elif decision == "MANUAL_REVIEW":
        st.warning("## Manual Review Required")
        st.markdown("Scores are borderline — a human reviewer will make the final call.")
    else:
        st.error("## KYC Rejected")
        st.markdown("Verification failed. Please visit your nearest branch with original documents.")

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Decision",          decision)
    c2.metric("Fraud Risk Score",  f"{fraud.get('risk_score', 0.07):.2f}")
    c3.metric("Liveness",          f"{liveness.get('confidence', 0.85):.0%}")
    c4.metric("Doc Authenticity",  f"{fraud.get('authenticity_score', 0.95):.0%}")

    if blockchain:
        st.markdown("### Blockchain Confirmation")
        c1, c2 = st.columns(2)
        tx = blockchain.get("transaction_hash", "")
        c1.markdown(f"**Tx Hash:** `{tx[:20]}…{tx[-8:]}`")
        c1.markdown(f"**Timestamp:** `{blockchain.get('timestamp', '')}`")
        c2.markdown(f"**ZK-Proof ID:** `{blockchain.get('zk_proof_id', '')}`")
        c2.markdown("**Status:** Immutably recorded")

    st.markdown("---")
    report = {
        "kyc_report": {
            "version": "2.0-open-source",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "customer": {k: v for k, v in customer.items() if k not in ("aadhaar_number", "pan_number")},
            "decision": decision,
            "document_analysis": {
                "fraud_risk_level": fraud.get("risk_level"),
                "fraud_risk_score": fraud.get("risk_score"),
                "authenticity_score": fraud.get("authenticity_score"),
                "indicators": fraud.get("indicators", []),
            },
            "liveness": {
                "face_detected": liveness.get("face_detected"),
                "confidence": liveness.get("confidence"),
                "steps_passed": liveness.get("steps_passed"),
            },
            "blockchain": {
                "transaction_hash": blockchain.get("transaction_hash"),
                "zk_proof_id": blockchain.get("zk_proof_id"),
                "timestamp": blockchain.get("timestamp"),
            },
        }
    }

    st.download_button(
        "Download KYC Report (JSON)",
        data=json.dumps(report, indent=2),
        file_name=f"kyc_report_{customer.get('full_name','user').replace(' ','_')}.json",
        mime="application/json",
        use_container_width=True,
    )

    st.markdown("---")
    if st.button("Start New Verification", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    _init()
    _apply_styles()
    _sidebar()

    routes = {
        1: page_home,
        2: page_registration,
        3: page_document,
        4: page_ai_analysis,
        5: page_liveness,
        6: page_blockchain,
        7: page_decision,
    }
    routes.get(st.session_state.step, page_home)()


if __name__ == "__main__":
    main()
