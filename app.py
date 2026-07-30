import io
import json
import math
import os
import re
import smtplib
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Flowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def rerun_app() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        st.stop()


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --brand-ink: #0F294A;
            --brand-teal: #008080;
            --brand-blue: #2563eb;
            --brand-soft: #f5f9ff;
            --text-muted: #64748b;
            --line: #e2e8f0;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(0, 128, 128, 0.10), transparent 24%),
                linear-gradient(135deg, #f7fbff 0%, #eef4ff 45%, #fdfefe 100%);
        }
        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 2.2rem;
            max-width: 1480px;
        }
        .hero-card {
            background: linear-gradient(135deg, #0F294A 0%, #123d67 38%, #0f766e 100%);
            border-radius: 28px;
            padding: 1.35rem 1.4rem;
            box-shadow: 0 18px 45px rgba(15, 41, 74, 0.22);
            margin-bottom: 1rem;
            border: 1px solid rgba(255,255,255,0.18);
        }
        .hero-chip {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.16);
            color: #e2f4f4;
            font-size: 0.79rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }
        .hero-card h1 {
            color: white;
            margin: 0 0 0.35rem 0;
            font-size: 2.1rem;
            line-height: 1.15;
        }
        .hero-card p {
            color: rgba(255,255,255,0.9);
            margin: 0;
            line-height: 1.55;
            font-size: 1rem;
        }
        .glass-card {
            background: rgba(255,255,255,0.95);
            border: 1px solid rgba(226,232,240,0.95);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
            backdrop-filter: blur(16px);
        }
        .section-title {
            color: var(--brand-ink);
            font-size: 1.04rem;
            font-weight: 800;
            margin-bottom: 0.32rem;
            letter-spacing: -0.01em;
        }
        .section-subtitle {
            color: var(--text-muted);
            font-size: 0.94rem;
            line-height: 1.45;
        }
        .metric-pill {
            display: inline-block;
            padding: 0.38rem 0.72rem;
            background: linear-gradient(135deg, rgba(0,128,128,0.12), rgba(37,99,235,0.12));
            color: var(--brand-teal);
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 800;
            margin-top: 0.45rem;
        }
        .preview-card {
            border-radius: 20px;
            padding: 1rem 1.1rem;
            background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid #dbeafe;
            box-shadow: 0 12px 30px rgba(15, 41, 74, 0.08);
            margin-bottom: 1rem;
        }
        .preview-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--brand-ink);
            margin-bottom: 0.25rem;
        }
        .preview-meta {
            color: var(--text-muted);
            font-size: 0.92rem;
            line-height: 1.45;
        }
        .record-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(245,249,255,0.98) 100%);
            border: 1px solid rgba(226,232,240,0.95);
            border-radius: 18px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.8rem;
            box-shadow: 0 10px 24px rgba(15, 41, 74, 0.06);
        }
        .record-title {
            font-size: 1rem;
            font-weight: 800;
            color: var(--brand-ink);
            margin-bottom: 0.25rem;
        }
        .record-meta {
            color: var(--text-muted);
            font-size: 0.9rem;
            line-height: 1.45;
            margin-bottom: 0.45rem;
        }
        .record-pill {
            display: inline-block;
            padding: 0.32rem 0.6rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            background: rgba(0,128,128,0.10);
            color: var(--brand-teal);
            margin-right: 0.35rem;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            font-size: 0.84rem;
            font-weight: 700;
            animation: fadeIn 0.55s ease;
        }
        .status-good {
            background: #dcfce7;
            color: #166534;
        }
        .status-attention {
            background: #fef3c7;
            color: #92400e;
        }
        .status-risk {
            background: #fee2e2;
            color: #b91c1c;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }
        div[data-testid="stRadio"] label {
            background: linear-gradient(135deg, #f8fafc 0%, #f3f8ff 100%);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 0.58rem 0.75rem;
            margin: 0.2rem 0;
            box-shadow: 0 4px 10px rgba(15, 41, 74, 0.03);
        }
        div[data-testid="stTextInput"] > div > div > input,
        div[data-testid="stTextArea"] > div > div > textarea,
        div[data-testid="stSelectbox"] > div > div > div {
            border-radius: 12px;
            border: 1px solid var(--line);
            box-shadow: inset 0 1px 2px rgba(15, 41, 74, 0.04);
        }
        div[data-testid="stBaseButton-secondary"] button,
        div[data-testid="stBaseButton-primary"] button,
        [data-testid="stFormSubmitButton"] button {
            border-radius: 999px;
            padding: 0.68rem 1.12rem;
            font-weight: 700;
            border: none;
            box-shadow: 0 10px 22px rgba(15, 41, 74, 0.10);
            transition: transform 0.16s ease, box-shadow 0.16s ease;
        }
        div[data-testid="stBaseButton-secondary"] button:hover,
        div[data-testid="stBaseButton-primary"] button:hover,
        [data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(15, 41, 74, 0.14);
        }
        [data-testid="stFormSubmitButton"] button,
        div[data-testid="stBaseButton-primary"] button {
            background: linear-gradient(135deg, #008080 0%, #0F294A 100%);
            color: white;
        }
        div[data-testid="stBaseButton-secondary"] button {
            background: linear-gradient(135deg, #ffffff 0%, #f4f8ff 100%);
            color: var(--brand-ink);
            border: 1px solid var(--line);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


OUTLETS = [
    "Pastry and Bakery",
    "Sole",
    "Nahaam",
    "Lobby Lounge",
    "Jose Pizzaro",
    "Rosewater & IRD",
    "Pool Bar",
    "Sushi Samba",
    "Rays Bar",
    "Production Kitchens",
]

CHECKLIST_ITEMS = [
    "Chiller/Freezer / Hot Cabinet temperature are accurate and monitored regularly",
    "Food arranged properly to prevent cross contamination",
    "Dry store and storage shelves are clean; temperature and humidity controlled",
    "No cardboard / wooden boxes in chillers and preparation areas",
    "No dented or damaged goods are present",
    "Colour coded chopping boards and knives are being used",
    "No raw egg is being used in food cooked below 75°C",
    "High risk foods are cooked above 75°C and randomly monitored",
    "Colleagues are aware of allergen management",
    "Ingredients are clearly mentioned on bottle / packet in English / Arabic",
    "Allergen orders are handled only by the outlet / kitchen in-charge",
    "Chiller, freezer and storage racks are clean, including rubber seal, rack and door handle; no ice formation in freezer",
    "Food and hand contact surfaces are clean and disinfected",
    "Pot wash sink is clean and well stocked with detergent and disinfectant",
    "Dish washing machine is clean and rinse temperature reaches more than 82°C",
    "Garbage bin is pedal operated, clean, bagged and not overfilled",
    "Food handlers hair is protected by hair restraint, wounds are covered if any, and company grooming standard is followed",
    "Hand wash station is well stocked with water, soap and tissue paper, not blocked, and hands are washed frequently",
    "Machines, walls, floors, light fixtures and equipment are in good repair",
    "Calibrated probe thermometer is available in the outlet",
    "Documents are up to date, including chiller, freezer, cooling, cooking, EFST, grooming and first aid kit records",
    "Fly killers are clean and not placed directly above food preparation area",
    "Pest sighting log is up to date and no pest activity is noted",
    "Ice machines and ice scoop are clean and in good condition",
    "Coffee machine is clean and cleaning record is available",
    "Milk for coffee machine is refrigerated, or changed regularly at maximum 4-hour interval",
    "Take away sticker is available and service staff are aware of take away policy",
    "Colleagues are aware of allergen management",
    "Bar and service area are clean with no pest infestation",
    "Mixers and blenders are clean",
    "Menu contains allergen disclaimer",
    "Chiller / Freezer temperature are accurate and monitored regularly",
    "No storage containers are reused from original intended use",
    "Cold holding temperature is maintained while storing high risk beverages such as milk and juice",
    "No expired food is present and foods are labelled appropriately for Culinary",
    "No expired food or beverage is present and foods are labelled appropriately for Service",
    "FIFO system is followed",
    "Items are covered and labelled",
    "Alcohol is segregated from non-alcohols for Service",
]

CHECKLIST_GROUPS = [
    ("Storage", 5),
    ("Preparation and Cooking", 6),
    ("Cleaning", 7),
    ("Maintenance", 2),
    ("Documents", 1),
    ("Pest Control", 2),
    ("Service - Food and Beverage", 11),
    ("Critical Criteria", 5),
]


class SemiCircularGauge(Flowable):
    def __init__(self, value: float, width: float = 3.0 * inch, height: float = 2.2 * inch):
        self.value = max(0.0, min(100.0, value))
        self.width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        x_center = self.width / 2
        y_center = 0.7 * inch
        radius = 0.95 * inch

        canvas.setLineWidth(10)
        canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
        canvas.arc(x_center - radius, y_center - radius, x_center + radius, y_center + radius, startAng=180, extent=-180)

        canvas.setStrokeColor(colors.HexColor("#0F294A"))
        progress_extent = -((self.value / 100) * 180)
        canvas.arc(x_center - radius, y_center - radius, x_center + radius, y_center + radius, startAng=180, extent=progress_extent)

        canvas.setLineWidth(2)
        canvas.setStrokeColor(colors.HexColor("#008080"))
        angle = math.radians(180 - (self.value / 100) * 180)
        pointer_x = x_center + radius * math.cos(angle)
        pointer_y = y_center + radius * math.sin(angle)
        canvas.line(x_center, y_center, pointer_x, pointer_y)

        canvas.setFillColor(colors.HexColor("#0F294A"))
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawCentredString(x_center, y_center + 0.05 * inch, f"{self.value:.1f}%")
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(x_center, y_center - 0.35 * inch, "Average Compliance")

        canvas.roundRect(x_center - 0.82 * inch, 0.1 * inch, 1.64 * inch, 0.3 * inch, 0.08 * inch, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawCentredString(x_center, 0.23 * inch, f"Final Average: {self.value:.1f}%")


def get_downloads_dir() -> Path:
    candidates = [Path.home() / "Downloads", Path.home() / "downloads"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    downloads_dir = candidates[0]
    downloads_dir.mkdir(parents=True, exist_ok=True)
    return downloads_dir


def build_output_path(file_name: str) -> str:
    downloads_dir = get_downloads_dir()
    downloads_dir.mkdir(parents=True, exist_ok=True)
    return str(downloads_dir / file_name)


def send_report_by_email(pdf_path: str, recipient_email: str) -> Tuple[bool, str]:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv("SMTP_FROM_EMAIL")

    if not all([smtp_host, smtp_port, smtp_username, smtp_password, sender_email, recipient_email]):
        return False, "Email delivery is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL to enable this option."

    try:
        msg = EmailMessage()
        msg["Subject"] = "Conrad Abu Dhabi EHS Inspection Report"
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg.set_content("Please find the attached inspection report.")
        with open(pdf_path, "rb") as handle:
            msg.add_attachment(handle.read(), maintype="application", subtype="pdf", filename=Path(pdf_path).name)

        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        return True, f"Report sent to {recipient_email}"
    except Exception as exc:
        return False, f"Email delivery failed: {exc}"


def build_dynamic_output_path(audit_data: Dict[str, object]) -> str:
    outlet_name = str(audit_data.get("outlet", "Outlet")).strip()
    inspection_timestamp = str(audit_data.get("inspection_timestamp", datetime.now().strftime("%Y-%m-%d")))
    try:
        parsed_date = datetime.strptime(inspection_timestamp, "%Y-%m-%d")
    except ValueError:
        try:
            parsed_date = datetime.strptime(inspection_timestamp, "%Y-%m-%d %H:%M")
        except ValueError:
            parsed_date = datetime.now()

    outlet_slug = re.sub(r"[^a-zA-Z0-9]+", " ", outlet_name).strip().lower()
    date_slug = parsed_date.strftime("%m-%d-%Y")
    file_name = f"{outlet_slug}-Food Safety Report {date_slug}.pdf"
    return build_output_path(file_name)


def calculate_score(results: Dict[str, str]) -> Tuple[float, Dict[str, int]]:
    counts = Counter()
    total_items = 0
    for value in results.values():
        if value == "Not Applicable":
            continue
        total_items += 1
        counts[value] += 1

    achieved = counts.get("Achieved", 0)
    partial = counts.get("Partial", 0)
    failed = counts.get("Did Not Achieve", 0)
    score = round((achieved + 0.5 * partial) / total_items * 100, 2) if total_items else 0.0
    return score, {
        "Achieved": achieved,
        "Partial": partial,
        "Did Not Achieve": failed,
        "Rated Items": total_items,
        "Not Applicable": sum(1 for value in results.values() if value == "Not Applicable"),
    }


def get_status(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 80:
        return "Good"
    if score >= 70:
        return "Satisfactory"
    return "Needs Improvement"


def parse_item_comments(raw_text: str) -> Dict[str, str]:
    comments: Dict[str, str] = {}
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key.startswith("item_"):
            comments[key] = value
    return comments


def get_history_storage_path() -> Path:
    data_dir = os.getenv("REPORT_DATA_DIR")
    if data_dir:
        storage_path = Path(data_dir)
    else:
        storage_path = Path(__file__).resolve().parent / "data"
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path / "audit_history.json"


def load_history(path: Optional[str] = None) -> List[Dict]:
    if path:
        history_path = Path(path)
        if not history_path.exists():
            return []
        with open(history_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    backend = os.getenv("REPORT_STORAGE_BACKEND", "local").lower()
    remote_url = os.getenv("REPORT_STORAGE_URL")
    if backend == "remote" and remote_url:
        request = urllib.request.Request(remote_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload) if payload else []

    history_path = get_history_storage_path()
    if not history_path.exists():
        return []
    with open(history_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_history(history: List[Dict], path: Optional[str] = None) -> None:
    if path:
        history_path = Path(path)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(history_path, "w", encoding="utf-8") as handle:
            json.dump(history, handle, indent=2)
        return

    backend = os.getenv("REPORT_STORAGE_BACKEND", "local").lower()
    remote_url = os.getenv("REPORT_STORAGE_URL")
    if backend == "remote" and remote_url:
        payload = json.dumps(history, indent=2).encode("utf-8")
        request = urllib.request.Request(remote_url, data=payload, headers={"Content-Type": "application/json"}, method="PUT")
        with urllib.request.urlopen(request, timeout=10) as _response:
            return

    history_path = get_history_storage_path()
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as handle:
        json.dump(history, handle, indent=2)


def build_records_synopsis(history: List[Dict]) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for entry in reversed(history):
        score = entry.get("score", 0.0)
        try:
            score_value = float(score)
        except (TypeError, ValueError):
            score_value = 0.0
        records.append({
            "date": entry.get("inspection_timestamp") or entry.get("inspection_date") or "N/A",
            "outlet": entry.get("outlet", "N/A"),
            "score": round(score_value, 1),
            "status": get_status(score_value),
            "corrective_actions": entry.get("corrective_actions") or "No corrective action recorded.",
            "observations": entry.get("observations") or "No observations recorded.",
            "notes_guidance": entry.get("notes_guidance") or "No guidance captured.",
            "hotel_name": entry.get("hotel_name", "N/A"),
        })
    return records


def render_records_workspace(history: List[Dict]) -> None:
    st.markdown(
        """
        <div class='glass-card'>
            <div class='section-title'>Records workspace</div>
            <div class='section-subtitle'>Review every daily inspection as a premium synopsis with score, actions, and date in one polished view.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    records = build_records_synopsis(history)
    if not records:
        st.info("No inspection records yet. Submit a daily report to build this workspace.")
        return

    summary_cols = st.columns(3)
    with summary_cols[0]:
        st.metric("Total Records", len(records))
    with summary_cols[1]:
        average_score = round(sum(item["score"] for item in records) / len(records), 1) if records else 0.0
        st.metric("Average Score", f"{average_score:.1f}%")
    with summary_cols[2]:
        last_outlet = records[0]["outlet"] if records else "N/A"
        st.metric("Latest Outlet", last_outlet)

    for record in records:
        st.markdown(
            f"""
            <div class='record-card'>
                <div class='record-title'>{record['outlet']}</div>
                <div class='record-meta'><strong>Date:</strong> {record['date']} · <strong>Hotel:</strong> {record['hotel_name']}</div>
                <div style='margin-bottom:0.45rem;'>
                    <span class='record-pill'>Score: {record['score']:.1f}%</span>
                    <span class='record-pill'>Status: {record['status']}</span>
                </div>
                <div class='record-meta'><strong>Corrective actions:</strong> {record['corrective_actions']}</div>
                <div class='record-meta'><strong>Observations:</strong> {record['observations']}</div>
                <div class='record-meta'><strong>Guidance:</strong> {record['notes_guidance']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_generated_report_card(audit_data: Dict[str, object], output_path: str) -> None:
    score, counts = calculate_score(audit_data["results"])
    status = get_status(score)

    status_class = "status-good" if score >= 80 else "status-attention" if score >= 60 else "status-risk"

    st.markdown(
        """
        <div class='hero-card'>
            <h1>Daily report generated successfully</h1>
            <p>Your inspection packet is ready to review, share, or export.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class='preview-card'>
            <div class='preview-title'>Executive report preview</div>
            <div class='preview-meta'>Outlet: {audit_data.get('outlet', 'N/A')}<br/>Inspection time: {audit_data.get('inspection_timestamp', 'N/A')}<br/>Inspection completed by: {audit_data.get('auditor_name', 'N/A')}</div>
            <div style='margin-top: 0.7rem;'><span class='status-badge {status_class}'>● {status}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class='glass-card'>
                <div class='section-title'>Outlet</div>
                <div class='section-subtitle'>{audit_data.get('outlet', 'N/A')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class='glass-card'>
                <div class='section-title'>Compliance score</div>
                <div class='section-subtitle'>{score:.1f}%</div>
                <span class='metric-pill'>{status}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class='glass-card'>
                <div class='section-title'>Rated items</div>
                <div class='section-subtitle'>{counts['Rated Items']} total</div>
                <span class='metric-pill'>Achieved {counts['Achieved']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with open(output_path, "rb") as handle:
        pdf_bytes = handle.read()

    st.download_button(
        label="Download Daily Report PDF",
        data=pdf_bytes,
        file_name=Path(output_path).name,
        mime="application/pdf",
    )

    recipient_email = st.text_input("Email report to (optional)", key="daily_email_recipient")
    if recipient_email:
        if st.button("Send Daily Report by Email"):
            sent, message = send_report_by_email(output_path, recipient_email)
            st.success(message) if sent else st.warning(message)


def collect_audit_data() -> Dict[str, object]:
    inject_css()
    st.markdown(
        """
        <div class='hero-card'>
            <div class='hero-chip'>Premium compliance operations</div>
            <h1>Conrad Abu Dhabi EHS Inspection Report</h1>
            <p>Capture professional inspection data, add evidence notes, and export polished PDF reports in a single luxury-grade workflow.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='glass-card'>
            <div class='section-title'>Inspection workflow</div>
            <div class='section-subtitle'>Use the guided tabs below to enter audit details, score each checklist item, and attach your final observations before exporting a polished report.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='glass-card'><div class='section-title'>Daily Reporting</div><div class='section-subtitle'>A complete daily inspection packet with executive summary and compliance breakdown.</div><span class='metric-pill'>PDF ready</span></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='glass-card'><div class='section-title'>Monthly Analytics</div><div class='section-subtitle'>Track outlet performance trends and recurring issues across the month.</div><span class='metric-pill'>Leadership view</span></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='glass-card'><div class='section-title'>Professional Output</div><div class='section-subtitle'>Export polished reports with structured commentary and evidence-ready sections.</div><span class='metric-pill'>Executive grade</span></div>", unsafe_allow_html=True)

    with st.form("inspection_form"):
        tab_details, tab_checklist, tab_notes = st.tabs(["Audit Details", "Checklist Assessment", "Notes & Evidence"])

        with tab_details:
            st.markdown("<div class='section-title'>1. Audit Details</div>", unsafe_allow_html=True)
            col_a, col_b, col_c = st.columns(3)
            outlet = col_a.selectbox("Select Outlet", OUTLETS)
            hotel_name = col_b.text_input("Hotel / Property Name", "Conrad Abu Dhabi Etihad Towers")
            inspection_timestamp = col_c.text_input("Inspection Date", datetime.now().strftime("%Y-%m-%d"))

            col_d, col_e, col_f = st.columns(3)
            person_on_duty = col_d.text_input("Person on Duty")
            department = col_e.text_input("Department", "Food & Beverage")
            auditor_name = col_f.text_input("Inspection Done By")

        with tab_checklist:
            st.markdown("<div class='section-title'>2. Checklist Assessment</div>", unsafe_allow_html=True)
            results: Dict[str, str] = {}
            for index, item in enumerate(CHECKLIST_ITEMS, start=1):
                results[f"item_{index}"] = st.radio(
                    f"{index}. {item}",
                    ["Achieved", "Partial", "Did Not Achieve", "Not Applicable"],
                    index=0,
                    key=f"item_{index}",
                )

        with tab_notes:
            st.markdown("<div class='section-title'>3. Notes & Evidence</div>", unsafe_allow_html=True)
            observations = st.text_area("General Observations", height=120)
            corrective_actions = st.text_area("Corrective Actions Taken", height=120)
            notes_guidance = st.text_area("Notes & Guidance", height=120)
            inspector_comments_text = st.text_area("Inspector Comments (optional; format: item_1: comment)", height=120)

        submitted = st.form_submit_button("Generate Daily Report PDF")
        if submitted:
            st.session_state["last_form_submitted"] = True
            st.session_state["last_submission_data"] = {
                "hotel_name": hotel_name,
                "outlet": outlet,
                "inspection_timestamp": inspection_timestamp,
                "person_on_duty": person_on_duty,
                "department": department,
                "auditor_name": auditor_name,
                "results": results,
                "observations": observations,
                "corrective_actions": corrective_actions,
                "notes_guidance": notes_guidance,
                "item_comments": parse_item_comments(inspector_comments_text),
            }

    return {
        "hotel_name": hotel_name,
        "outlet": outlet,
        "inspection_timestamp": inspection_timestamp,
        "person_on_duty": person_on_duty,
        "department": department,
        "auditor_name": auditor_name,
        "results": results,
        "observations": observations,
        "corrective_actions": corrective_actions,
        "notes_guidance": notes_guidance,
        "item_comments": parse_item_comments(inspector_comments_text),
    }


def build_monthly_dashboard(history: List[Dict], selected_month: str) -> Dict[str, object]:
    if not history:
        return {"month": selected_month, "outlet_scores": {}, "recurring_issues": []}

    records = []
    for entry in history:
        if not entry.get("inspection_date"):
            continue
        if entry["inspection_date"].startswith(selected_month):
            records.append(entry)

    if not records:
        return {"month": selected_month, "outlet_scores": {}, "recurring_issues": []}

    df = pd.DataFrame(records)
    outlet_scores: Dict[str, float] = {}
    for outlet in OUTLETS:
        subset = df[df["outlet"] == outlet]
        if not subset.empty:
            outlet_scores[outlet] = round(float(subset["score"].mean()), 2)

    issue_counter = Counter()
    for entry in records:
        for key, value in entry.get("results", {}).items():
            if value != "Achieved" and value != "Not Applicable":
                issue_counter[key] += 1

    recurring_issues = []
    for item_key, count in issue_counter.most_common(5):
        recurring_issues.append({"item": CHECKLIST_ITEMS[int(item_key.split("_")[-1]) - 1], "count": count})

    outlet_trends: Dict[str, List[Dict[str, object]]] = {}
    for outlet in OUTLETS:
        subset = [entry for entry in records if entry.get("outlet") == outlet]
        if not subset:
            outlet_trends[outlet] = []
            continue
        trend_points = []
        for entry in sorted(subset, key=lambda item: item.get("inspection_date", "")):
            trend_points.append({
                "date": entry.get("inspection_date", ""),
                "score": round(float(entry.get("score", 0.0)), 1),
            })
        outlet_trends[outlet] = trend_points

    outlet_recurring_issues: Dict[str, List[Dict[str, object]]] = {}
    for outlet in OUTLETS:
        subset = [entry for entry in records if entry.get("outlet") == outlet]
        issue_counter_for_outlet = Counter()
        for entry in subset:
            for key, value in entry.get("results", {}).items():
                if value != "Achieved" and value != "Not Applicable":
                    issue_counter_for_outlet[key] += 1
        outlet_issues = []
        for item_key, count in issue_counter_for_outlet.most_common(3):
            outlet_issues.append({
                "item": CHECKLIST_ITEMS[int(item_key.split("_")[-1]) - 1],
                "count": count,
            })
        outlet_recurring_issues[outlet] = outlet_issues

    ranked_outlets = sorted(outlet_scores.items(), key=lambda item: (-item[1], item[0]))
    overall_average = round(float(df["score"].mean()), 2) if "score" in df.columns else 0.0

    if len(records) >= 2:
        sorted_records = sorted(records, key=lambda item: item.get("inspection_date", ""))
        midpoint = max(1, len(sorted_records) // 2)
        first_half = sorted_records[:midpoint]
        second_half = sorted_records[midpoint:]
        first_avg = round(float(pd.DataFrame(first_half)["score"].mean()), 2) if first_half else 0.0
        second_avg = round(float(pd.DataFrame(second_half)["score"].mean()), 2) if second_half else 0.0
        delta = round(second_avg - first_avg, 2)
        trend_direction = "improved" if delta >= 0 else "declined"
        trend_text = f"Performance {trend_direction} by {abs(delta):.1f} points from the first to the second half of the month."
    else:
        trend_text = "Performance remained stable across the available inspections this month."

    best_outlet = ranked_outlets[0][0] if ranked_outlets else "N/A"
    best_score = ranked_outlets[0][1] if ranked_outlets else 0.0
    top_risk = recurring_issues[0]["item"] if recurring_issues else "No recurring gaps detected"

    risk_heatmap = []
    for outlet, score in ranked_outlets:
        if score >= 90:
            status = "Excellent"
            tone = "good"
        elif score >= 80:
            status = "Good"
            tone = "good"
        elif score >= 70:
            status = "Watch"
            tone = "attention"
        else:
            status = "Critical"
            tone = "risk"
        risk_heatmap.append({
            "outlet": outlet,
            "score": score,
            "status": status,
            "tone": tone,
        })

    executive_summary = (
        f"Across {len(records)} inspections in {selected_month}, the portfolio averaged {overall_average:.1f}% compliance. "
        f"{best_outlet} led performance at {best_score:.1f}%, while {top_risk} remained the most frequent recurring concern. "
        f"{trend_text}"
    )

    return {
        "month": selected_month,
        "outlet_scores": outlet_scores,
        "ranked_outlets": ranked_outlets,
        "average_score": overall_average,
        "recurring_issues": recurring_issues,
        "outlet_trends": outlet_trends,
        "outlet_recurring_issues": outlet_recurring_issues,
        "risk_heatmap": risk_heatmap,
        "executive_summary": executive_summary,
        "insights": (
            f"Overall monthly compliance averaged {overall_average:.1f}%. "
            f"The strongest outlet was {best_outlet} at {best_score:.1f}%, while the most persistent risk area was {top_risk}. "
            f"{trend_text}"
        ),
        "Recurring issues": recurring_issues,
    }


def build_outlet_bar_chart(outlet_scores: Dict[str, float]):
    ranked = sorted(outlet_scores.items(), key=lambda item: (-item[1], item[0]))
    if not ranked:
        return None

    labels = [name for name, _ in ranked]
    values = [score for _, score in ranked]
    colors_list = ["#8ecae6" if index % 2 == 0 else "#a8dadc" for index in range(len(labels))]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10.5, 4.2), dpi=160)
    bars = ax.bar(labels, values, color=colors_list, edgecolor="#9db2c7", linewidth=0.9, width=0.6)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Average Score (%)", fontsize=8, color="#1E293B")
    ax.set_title("Outlet Ranking by Average Compliance", fontsize=10, color="#0F294A", pad=8)
    ax.set_facecolor("#F8FBFF")
    fig.patch.set_facecolor("#FFFFFF")
    ax.tick_params(axis="x", labelrotation=35, labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.9, alpha=0.8)
    ax.grid(axis="x", visible=False)

    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.7, f"{value:.1f}%", ha="center", va="bottom", fontsize=7, color="#0F294A", fontweight="bold")

    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()


def build_outlet_trend_chart(outlet_trends: Dict[str, List[Dict[str, object]]]):
    visible_trends = {outlet: points for outlet, points in outlet_trends.items() if points}
    if not visible_trends:
        return None

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8.0, 4.2), dpi=160)
    for outlet, points in visible_trends.items():
        x_values = [datetime.strptime(point["date"], "%Y-%m-%d") for point in points]
        y_values = [float(point["score"]) for point in points]
        ax.plot(x_values, y_values, marker="o", linewidth=2.6, label=outlet, color="#0F294A" if outlet == list(visible_trends.keys())[0] else "#008080", markerfacecolor="#ffffff", markeredgewidth=1.1, markersize=4.8)
        ax.fill_between(x_values, y_values, alpha=0.12, color="#008080")

    ax.set_ylim(0, 105)
    ax.set_ylabel("Inspection Score (%)", fontsize=8, color="#1E293B")
    ax.set_title("Outlet Score Trend Across Selected Month", fontsize=10, color="#0F294A", pad=8)
    ax.set_facecolor("#F8FBFF")
    fig.patch.set_facecolor("#FFFFFF")
    ax.tick_params(axis="y", labelsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")
    ax.grid(True, color="#E2E8F0", linewidth=0.9, alpha=0.85)
    ax.legend(loc="best", fontsize=7)

    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()


def generate_pdf_report(audit_data: Dict[str, object], output_path: Optional[str] = None) -> str:
    score, counts = calculate_score(audit_data["results"])
    status = get_status(score)
    output_path = output_path or build_dynamic_output_path(audit_data)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()

    PRIMARY_COLOR = colors.HexColor("#0F294A")
    ACCENT_TEAL = colors.HexColor("#008080")
    BG_LIGHT = colors.HexColor("#F8FAFC")
    TEXT_DARK = colors.HexColor("#1E293B")
    SUCCESS_GREEN = colors.HexColor("#10B981")
    PARTIAL_ORANGE = colors.HexColor("#D97706")
    MUTED_GREY = colors.HexColor("#6B7280")

    styles.add(ParagraphStyle(name="DocTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=PRIMARY_COLOR))
    styles.add(ParagraphStyle(name="Subtitle", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.8, leading=10.8, textColor=MUTED_GREY))
    styles.add(ParagraphStyle(name="CardLabel", fontName="Helvetica-Bold", fontSize=7.8, leading=10, textColor=ACCENT_TEAL))
    styles.add(ParagraphStyle(name="CardValue", fontName="Helvetica", fontSize=9.2, leading=12, textColor=TEXT_DARK))
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=12.5, textColor=PRIMARY_COLOR))
    styles.add(ParagraphStyle(name="SectionBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.6, leading=11.2, textColor=TEXT_DARK))
    styles.add(ParagraphStyle(name="BadgeText", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.2, leading=8.8, alignment=TA_CENTER, textColor=TEXT_DARK))
    styles.add(ParagraphStyle(name="SummaryValue", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=16, leading=18, textColor=PRIMARY_COLOR))
    styles.add(ParagraphStyle(name="SummaryLabel", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.2, leading=10, textColor=MUTED_GREY))
    styles.add(ParagraphStyle(name="CommentText", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=7.4, leading=9.2, textColor=MUTED_GREY, leftIndent=14))

    def build_status_badge(label: str, status_value: str) -> Table:
        if status_value == "Achieved":
            bg = colors.HexColor("#D1FAE5")
            text_color = SUCCESS_GREEN
            border = colors.HexColor("#A7F3D0")
        elif status_value == "Partial":
            bg = colors.HexColor("#FEF3C7")
            text_color = PARTIAL_ORANGE
            border = colors.HexColor("#FCD34D")
        else:
            bg = colors.HexColor("#F3F4F6")
            text_color = MUTED_GREY
            border = colors.HexColor("#D1D5DB")
        badge = Table([[Paragraph(label, styles["BadgeText"])]] , colWidths=[1.05 * inch], hAlign="LEFT")
        badge.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), bg),
                    ("TEXTCOLOR", (0, 0), (-1, -1), text_color),
                    ("GRID", (0, 0), (-1, -1), 0.3, border),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return badge

    def build_card(title: str, value: str) -> Table:
        table = Table([[Paragraph(title, styles["CardLabel"])], [Paragraph(value, styles["CardValue"])]], colWidths=[1.85 * inch], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#E2E8F0")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return table

    def build_box(title: str, body: str) -> Table:
        content = body.strip() or "N/A"
        table = Table([[Paragraph(title, styles["SectionTitle"])], [Paragraph(content, styles["SectionBody"])]], colWidths=[6.25 * inch], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("PADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return table

    def add_page_number(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED_GREY)
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Page {canvas.getPageNumber()}")

    story = []
    story.append(Paragraph("Food Safety Inspection Report", styles["DocTitle"]))
    story.append(Paragraph("Professional inspection report with clear executive score summary.", styles["Subtitle"]))
    story.append(Spacer(1, 0.12 * inch))

    metadata_rows = [
        [
            Paragraph("HOTEL / PROPERTY NAME", styles["CardLabel"]),
            Paragraph("LOCATION / OUTLET", styles["CardLabel"]),
            Paragraph("INSPECTION DATE", styles["CardLabel"]),
        ],
        [
            Paragraph(str(audit_data.get("hotel_name", "Conrad Abu Dhabi Etihad Towers")), styles["CardValue"]),
            Paragraph(str(audit_data.get("outlet", "Pool Bar")), styles["CardValue"]),
            Paragraph(str(audit_data.get("inspection_timestamp", "2026-07-27")), styles["CardValue"]),
        ],
        [
            Paragraph("PERSON ON DUTY", styles["CardLabel"]),
            Paragraph("DEPARTMENT", styles["CardLabel"]),
            Paragraph("INSPECTION DONE BY", styles["CardLabel"]),
        ],
        [
            Paragraph(str(audit_data.get("person_on_duty", "N/A")), styles["CardValue"]),
            Paragraph(str(audit_data.get("department", "Food & Beverage")), styles["CardValue"]),
            Paragraph(str(audit_data.get("auditor_name", "Divya Nath")), styles["CardValue"]),
        ],
    ]
    metadata_table = Table(metadata_rows, colWidths=[1.85 * inch, 1.85 * inch, 1.85 * inch])
    metadata_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(metadata_table)
    story.append(Spacer(1, 0.15 * inch))

    score_header = Paragraph("<b>OVERALL SCORE & METRICS SUMMARY</b>", ParagraphStyle("ScoreHeader", fontName="Helvetica-Bold", fontSize=10, leading=12, textColor=colors.white))
    score_content = Table(
        [
            [Paragraph(f"<b>{score:.0f}%</b><br/><font size=8>Overall Score</font>", ParagraphStyle("BigScore", fontName="Helvetica-Bold", fontSize=18, textColor=PRIMARY_COLOR)), Paragraph(f"<b>Status:</b> {status}", styles["CardValue"])],
            [Paragraph(f"<b>Rated:</b> {counts['Rated Items']}", styles["CardValue"]), Paragraph(f"<b>Achieved:</b> {counts['Achieved']}", styles["CardValue"])],
            [Paragraph(f"<b>Partial:</b> {counts['Partial']}", styles["CardValue"]), Paragraph(f"<b>Did Not Achieve:</b> {counts['Did Not Achieve']}", styles["CardValue"])],
        ],
        colWidths=[2.8 * inch, 2.8 * inch],
    )
    score_table = Table([[score_header], [score_content]], colWidths=[5.9 * inch])
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), PRIMARY_COLOR),
                ("BACKGROUND", (0, 1), (0, 1), BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 1, PRIMARY_COLOR),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(score_table)
    story.append(Spacer(1, 0.15 * inch))

    issues = [str(CHECKLIST_ITEMS[index]) for index, value in enumerate(audit_data.get("results", {}).values()) if value != "Achieved"]
    if issues:
        story.append(Paragraph("Issues Requiring Attention", styles["SectionTitle"]))
        story.append(Paragraph("• " + "<br/>• ".join(issues[:8]), styles["SectionBody"]))
        story.append(Spacer(1, 0.08 * inch))

    story.append(Paragraph("Checklist Review", styles["SectionTitle"]))
    item_index = 0
    for group_name, count in CHECKLIST_GROUPS:
        category_items = []
        achieved_count = 0
        for _ in range(count):
            result_key = f"item_{item_index + 1}"
            selection = audit_data.get("results", {}).get(result_key, "Not answered")
            achieved_count += 1 if selection == "Achieved" else 0
            category_items.append((item_index, result_key, selection))
            item_index += 1
        category_score = round((achieved_count / count) * 100, 0) if count else 0
        category_status = "Good" if category_score >= 90 else "Needs Review" if category_score >= 70 else "Needs Attention"
        cat_header = Table([[Paragraph(group_name, styles["SectionTitle"]), Paragraph(f"{int(category_score)}% - {category_status}", styles["SummaryLabel"])]], colWidths=[4.8 * inch, 1.2 * inch])
        cat_header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        story.append(cat_header)
        story.append(Spacer(1, 0.03 * inch))
        for idx, result_key, selection in category_items:
            item_text = CHECKLIST_ITEMS[idx]
            status_label = selection if selection != "Not answered" else "Not Applicable"
            badge = build_status_badge(status_label, selection if selection != "Not answered" else "Did Not Achieve")
            row_bg = colors.HexColor("#F8FAFC") if idx % 2 == 0 else colors.white
            item_row = Table([[Paragraph(f"{idx + 1}. {item_text}", styles["SectionBody"]), badge]], colWidths=[4.9 * inch, 1.0 * inch], hAlign="LEFT")
            item_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), row_bg), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
            story.append(item_row)
            comment = audit_data.get("item_comments", {}).get(result_key)
            if comment:
                story.append(Paragraph(f"Inspector Comment: {comment}", styles["CommentText"]))
        story.append(Spacer(1, 0.06 * inch))

    story.append(Spacer(1, 0.08 * inch))
    story.append(build_box("General Observation", str(audit_data.get("observations", "") or "N/A")))
    story.append(Spacer(1, 0.08 * inch))
    story.append(build_box("Corrective Action Taken", str(audit_data.get("corrective_actions", "") or "N/A")))
    story.append(Spacer(1, 0.08 * inch))
    story.append(build_box("Notes & Guidance", str(audit_data.get("notes_guidance", "") or "N/A")))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return output_path


def generate_daily_pdf_bytes(audit_data: Dict[str, object], output_path: Optional[str] = None) -> Tuple[bytes, str]:
    output_path = output_path or build_dynamic_output_path(audit_data)
    output_path = generate_pdf_report(audit_data, output_path=output_path)
    with open(output_path, "rb") as handle:
        return handle.read(), output_path


def generate_monthly_pdf_bytes(history: List[Dict], selected_month: str, output_path: Optional[str] = None) -> Tuple[bytes, str]:
    output_path = output_path or build_output_path(f"monthly_summary_{selected_month}.pdf")
    output_path = export_monthly_pdf(history, selected_month, output_path=output_path)
    with open(output_path, "rb") as handle:
        return handle.read(), output_path


def export_monthly_pdf(history: List[Dict], selected_month: str, output_path: Optional[str] = None) -> str:
    summary = build_monthly_dashboard(history, selected_month)
    output_path = output_path or build_output_path(f"monthly_summary_{selected_month}.pdf")
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.65 * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DocTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#0F294A")))
    styles.add(ParagraphStyle(name="Subtitle", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=11, textColor=colors.HexColor("#6B7280")))
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=12.5, textColor=colors.HexColor("#0F294A")))
    styles.add(ParagraphStyle(name="SectionBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.7, leading=11.2, textColor=colors.HexColor("#1E293B")))
    styles.add(ParagraphStyle(name="CardLabel", fontName="Helvetica-Bold", fontSize=7.8, leading=10, textColor=colors.HexColor("#008080")))
    styles.add(ParagraphStyle(name="CardValue", fontName="Helvetica", fontSize=9.2, leading=12, textColor=colors.HexColor("#1E293B")))
    styles.add(ParagraphStyle(name="SummaryValue", fontName="Helvetica-Bold", fontSize=16, leading=18, textColor=colors.HexColor("#0F294A")))

    story = []
    story.append(Paragraph("Monthly Analytics Report", styles["DocTitle"]))
    story.append(Paragraph("Executive performance overview with charts, trend insight, and outlet-level breakdown.", styles["Subtitle"]))
    story.append(Spacer(1, 0.12 * inch))

    metric_rows = [
        [Paragraph("Selected Month", styles["CardLabel"]), Paragraph(selected_month, styles["CardValue"])],
        [Paragraph("Average Compliance", styles["CardLabel"]), Paragraph(f"{summary.get('average_score', 0):.1f}%", styles["SummaryValue"])],
        [Paragraph("Audits Logged", styles["CardLabel"]), Paragraph(str(len(history)), styles["CardValue"])],
        [Paragraph("Best Outlet", styles["CardLabel"]), Paragraph(str(summary.get("ranked_outlets", [["N/A", 0.0]])[0][0] if summary.get("ranked_outlets") else "N/A"), styles["CardValue"])],
    ]
    metric_table = Table(metric_rows, colWidths=[1.7 * inch, 3.7 * inch])
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(metric_table)
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Executive Summary", styles["SectionTitle"]))
    story.append(Paragraph(summary.get("executive_summary", summary.get("insights", "No insights available yet.")), styles["SectionBody"]))
    story.append(Spacer(1, 0.08 * inch))

    hero_rows = [
        [Paragraph("Average Compliance", styles["CardLabel"]), Paragraph(f"{summary.get('average_score', 0):.1f}%", styles["SummaryValue"])],
        [Paragraph("Best Outlet", styles["CardLabel"]), Paragraph(str(summary.get("ranked_outlets", [["N/A", 0.0]])[0][0] if summary.get("ranked_outlets") else "N/A"), styles["CardValue"])],
        [Paragraph("Most Frequent Risk", styles["CardLabel"]), Paragraph(str(summary.get("recurring_issues", [{}])[0].get("item", "No recurring gaps detected") if summary.get("recurring_issues") else "No recurring gaps detected"), styles["CardValue"])],
    ]
    hero_table = Table(hero_rows, colWidths=[2.2 * inch, 3.2 * inch])
    hero_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(hero_table)
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Risk Heatmap by Outlet", styles["SectionTitle"]))
    heatmap_rows = [["Outlet", "Average Score", "Status"]]
    for entry in summary.get("risk_heatmap", []):
        heatmap_rows.append([entry["outlet"], f"{entry['score']:.1f}%", entry["status"]])
    if len(heatmap_rows) == 1:
        heatmap_rows.append(["No data", "0.0%", "No data"])
    heatmap_table = Table(heatmap_rows, colWidths=[2.4 * inch, 1.2 * inch, 1.1 * inch])
    heatmap_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F294A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(heatmap_table)
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Monthly Trends & Insights", styles["SectionTitle"]))
    story.append(Paragraph(summary.get("insights", "No insights available yet."), styles["SectionBody"]))
    story.append(Spacer(1, 0.12 * inch))

    gauge = SemiCircularGauge(summary.get("average_score", 0))
    chart = build_outlet_bar_chart(summary.get("outlet_scores", {}))
    trend_chart = build_outlet_trend_chart(summary.get("outlet_trends", {}))
    if chart or trend_chart:
        visual_row = []
        if chart:
            visual_row.append(Image(io.BytesIO(chart), width=2.4 * inch, height=1.35 * inch))
        if trend_chart:
            visual_row.append(Image(io.BytesIO(trend_chart), width=2.4 * inch, height=1.35 * inch))
        if len(visual_row) == 2:
            visual_table = Table([visual_row], colWidths=[2.4 * inch, 2.4 * inch], hAlign="LEFT")
            visual_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
            story.append(visual_table)
        else:
            story.append(visual_row[0])
    else:
        story.append(Paragraph("No outlet score data available for this period.", styles["SectionBody"]))
    story.append(Spacer(1, 0.14 * inch))

    story.append(Paragraph("Outlet Performance Table", styles["SectionTitle"]))
    table_rows = [["Outlet", "Average Score", "Audits", "Status"]]
    for outlet, score in summary.get("ranked_outlets", []):
        status = "Achieved" if score >= 90 else "Partial" if score >= 70 else "Did Not Achieve"
        table_rows.append([outlet, f"{score:.1f}%", str(len([entry for entry in history if entry.get("outlet") == outlet and entry.get("inspection_date", "").startswith(selected_month)])), status])

    if len(table_rows) == 1:
        table_rows.append(["No data", "0.0%", "0", "Not Applicable"])

    outlet_table = Table(table_rows, repeatRows=1, colWidths=[2.2 * inch, 1.0 * inch, 0.8 * inch, 1.1 * inch])
    outlet_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F294A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(outlet_table)
    story.append(Spacer(1, 0.14 * inch))

    story.append(Paragraph("Outlet Recurring Issues", styles["SectionTitle"]))
    issue_rows = [["Outlet", "Recurring Issues"]]
    for outlet, issues in summary.get("outlet_recurring_issues", {}).items():
        if issues:
            issue_text = "<br/>".join([f"• {issue['item']} ({issue['count']} mentions)" for issue in issues])
        else:
            issue_text = "No recurring gaps detected"
        issue_rows.append([outlet, Paragraph(issue_text, styles["SectionBody"])])
    if len(issue_rows) == 1:
        issue_rows.append(["No data", Paragraph("No recurring risk areas were identified in the current month.", styles["SectionBody"])])
    issue_table = Table(issue_rows, repeatRows=1, colWidths=[1.8 * inch, 4.2 * inch])
    issue_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F294A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(issue_table)
    story.append(Spacer(1, 0.14 * inch))

    story.append(Paragraph("Key Risk Areas", styles["SectionTitle"]))
    if summary.get("recurring_issues"):
        issue_items = []
        for issue in summary["recurring_issues"]:
            issue_items.append(f"• {issue['item']} ({issue['count']} mentions)")
        story.append(Paragraph("<br/>".join(issue_items), styles["SectionBody"]))
    else:
        story.append(Paragraph("No recurring risk areas were identified in the current month.", styles["SectionBody"]))

    doc.build(story)
    return output_path


def main() -> None:
    st.set_page_config(page_title="Conrad Abu Dhabi EHS Inspection Report", layout="wide")
    audit_data = collect_audit_data()
    if st.session_state.get("last_form_submitted", False):
        submitted_data = st.session_state.get("last_submission_data") or audit_data
        score, counts = calculate_score(submitted_data["results"])
        history = load_history()
        history.append(
            {
                "hotel_name": submitted_data["hotel_name"],
                "outlet": submitted_data["outlet"],
                "inspection_date": datetime.now().strftime("%Y-%m-%d"),
                "inspection_timestamp": submitted_data["inspection_timestamp"],
                "person_on_duty": submitted_data["person_on_duty"],
                "department": submitted_data["department"],
                "auditor_name": submitted_data["auditor_name"],
                "score": score,
                "counts": counts,
                "results": submitted_data["results"],
                "observations": submitted_data["observations"],
                "corrective_actions": submitted_data["corrective_actions"],
                "notes_guidance": submitted_data["notes_guidance"],
            }
        )
        save_history(history)
        pdf_bytes, output_path = generate_daily_pdf_bytes(submitted_data)
        st.session_state["last_generated_output_path"] = output_path
        st.session_state["last_daily_pdf_bytes"] = pdf_bytes
        st.session_state["last_daily_report_name"] = Path(output_path).name
        render_generated_report_card(submitted_data, output_path)

    st.markdown(
        """
        <div class='hero-card'>
            <h1>Conrad Abu Dhabi EHS Inspection Report</h1>
            <p>Review insights, ranking, and recurring compliance issues in a more executive-friendly view.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    history = load_history()
    month_options = sorted({entry.get("inspection_date", "")[:7] for entry in history if entry.get("inspection_date")})
    selected_month = st.selectbox("Select Month", month_options or [datetime.now().strftime("%Y-%m")])
    dashboard = build_monthly_dashboard(history, selected_month)

    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric("Selected Month", selected_month)
    with metric_cols[1]:
        st.metric("Average Score", f"{dashboard.get('average_score', 0):.1f}%")
    with metric_cols[2]:
        best_outlet = dashboard.get("ranked_outlets", [("N/A", 0.0)])[0][0] if dashboard.get("ranked_outlets") else "N/A"
        st.metric("Top Outlet", best_outlet)

    st.markdown("<div class='glass-card'><div class='section-title'>Executive summary</div><div class='section-subtitle'>" + dashboard.get("executive_summary", dashboard.get("insights", "No insights available yet.")) + "</div></div>", unsafe_allow_html=True)

    if dashboard.get("risk_heatmap"):
        st.markdown("<div class='glass-card'><div class='section-title'>Outlet risk heatmap</div><div class='section-subtitle'>A traffic-light view of outlet health based on average monthly performance.</div></div>", unsafe_allow_html=True)
        heatmap_cols = st.columns(len(dashboard["risk_heatmap"]))
        for col, entry in zip(heatmap_cols, dashboard["risk_heatmap"]):
            tone_class = "status-good" if entry["tone"] == "good" else "status-attention" if entry["tone"] == "attention" else "status-risk"
            with col:
                st.markdown(
                    f"""
                    <div class='preview-card'>
                        <div class='preview-title'>{entry['outlet']}</div>
                        <div class='preview-meta'>Average score: {entry['score']:.1f}%</div>
                        <div style='margin-top: 0.55rem;'><span class='status-badge {tone_class}'>● {entry['status']}</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    bar_chart = build_outlet_bar_chart(dashboard.get("outlet_scores", {}))
    trend_chart = build_outlet_trend_chart(dashboard.get("outlet_trends", {}))
    chart_cols = st.columns(2)
    with chart_cols[0]:
        if bar_chart:
            st.image(bar_chart, width="stretch")
        else:
            st.info("No outlet score data available for this period.")
    with chart_cols[1]:
        if trend_chart:
            st.image(trend_chart, width="stretch")
        else:
            st.info("No outlet trend data available for this period.")

    history = load_history()
    render_records_workspace(history)

    st.markdown("<div class='glass-card'><div class='section-title'>Monthly report generator</div><div class='section-subtitle'>Create a polished monthly summary and trend pack for leadership review.</div></div>", unsafe_allow_html=True)
    report_actions = st.columns([1.1, 1, 1.4])
    with report_actions[0]:
        if st.button("Generate Monthly Report"):
            monthly_pdf_bytes, output_path = generate_monthly_pdf_bytes(history, selected_month)
            st.session_state["last_monthly_pdf_bytes"] = monthly_pdf_bytes
            st.session_state["last_monthly_output_path"] = output_path
            st.session_state["last_monthly_report_name"] = Path(output_path).name
            st.success(f"Monthly PDF generated and ready to download. Saved to {output_path}")
    with report_actions[1]:
        if st.button("Refresh Trends"):
            rerun_app()
    with report_actions[2]:
        st.caption("The monthly report includes the executive summary, outlet heatmap, trend chart, and recurring issues summary.")

    monthly_pdf_bytes = st.session_state.get("last_monthly_pdf_bytes")
    monthly_report_name = st.session_state.get("last_monthly_report_name")
    if monthly_pdf_bytes and monthly_report_name:
        st.download_button(
            label="Download Monthly Report PDF",
            data=monthly_pdf_bytes,
            file_name=monthly_report_name,
            mime="application/pdf",
        )

    st.markdown("<div class='glass-card'><div class='section-title'>Outlet recurring issues</div></div>", unsafe_allow_html=True)
    for outlet, issues in dashboard.get("outlet_recurring_issues", {}).items():
        if issues:
            issue_text = "; ".join([f"{issue['item']} ({issue['count']})" for issue in issues])
            st.markdown(f"**{outlet}:** {issue_text}")


if __name__ == "__main__":
    main()
