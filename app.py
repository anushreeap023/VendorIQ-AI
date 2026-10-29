"""
app.py
------
VendorIQ AI - Smart Vendor Proposal Comparison Agent
Main Streamlit entry point.

Run with:
    streamlit run app.py
"""

import os
import streamlit as st
import pandas as pd

from utils import pdf_extractor, gemini_client, scoring, charts, export

# --------------------------------------------------------------------------
# PAGE CONFIG (must be first Streamlit call)
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="VendorIQ AI | Smart Vendor Proposal Comparison",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# SESSION STATE INIT
# --------------------------------------------------------------------------
defaults = {
    "theme": "dark",
    "vendors": [],              # list of extracted+scored vendor dicts
    "risk_by_vendor": {},       # {vendor_name: risk_detection_result}
    "recommendation": {},
    "executive_summary": {},
    "health": {},
    "processed": False,
    "uploaded_names": [],
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


# --------------------------------------------------------------------------
# THEME / CSS
# --------------------------------------------------------------------------
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    dark = st.session_state.theme == "dark"
    bg = "#0E1117" if dark else "#F5F7FB"
    text = "#E6E6E6" if dark else "#1A1A1A"
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: {bg}; color: {text}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


load_css()


# --------------------------------------------------------------------------
# SIDEBAR
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📊 VendorIQ AI")
    st.caption("Smart Vendor Proposal Comparison Agent")
    st.divider()

    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        value=st.session_state.get("api_key", ""),
        help="Get a key from Google AI Studio. Leave blank to explore the app in offline demo mode.",
    )
    st.session_state.api_key = api_key_input

    theme_choice = st.radio("Appearance", ["Dark", "Light"], horizontal=True,
                             index=0 if st.session_state.theme == "dark" else 1)
    st.session_state.theme = theme_choice.lower()

    st.divider()
    page = st.radio(
        "Navigate",
        [
            "🏠 Upload & Overview",
            "📋 Comparison Table",
            "🏆 Scoring & Leaderboard",
            "🎯 AI Recommendation",
            "⚠️ Risk Detection",
            "📈 Analytics",
            "🧾 Executive Summary",
            "💰 Negotiation & Savings",
            "⬇️ Export",
        ],
    )

    st.divider()
    if not st.session_state.api_key:
        st.info("Running in **offline demo mode**. Add a Gemini API key above for full AI analysis.")
    if st.session_state.vendors:
        if st.button("🔄 Reset session", use_container_width=True):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()

load_css()  # re-apply after theme radio may have changed


# --------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------
def metric_card(label, value, col):
    with col:
        st.markdown(
            f"""<div class="viq-card"><h3>{label}</h3>
            <div class="viq-value">{value}</div></div>""",
            unsafe_allow_html=True,
        )


def severity_badge(severity):
    cls = {"Low": "viq-badge-low", "Medium": "viq-badge-medium", "High": "viq-badge-high"}.get(severity, "viq-badge-low")
    return f'<span class="viq-badge {cls}">{severity}</span>'


def process_uploaded_files(files):
    """Full pipeline: extract text -> Gemini extraction -> risk -> scoring."""
    api_key = st.session_state.api_key
    extracted_texts = pdf_extractor.extract_all(files)

    vendors = []
    progress = st.progress(0.0, text="Extracting text from PDFs...")
    for i, item in enumerate(extracted_texts):
        progress.progress((i + 1) / (len(extracted_texts) * 2), text=f"Reading {item['filename']}...")
        if item.get("error") and not item.get("text"):
            st.warning(f"⚠️ Could not extract text from **{item['filename']}**: {item['error']}")
            continue
        vendor_data = gemini_client.extract_vendor_data(item["text"], item["filename"], api_key)
        vendors.append(vendor_data)

    risk_by_vendor = {}
    for i, v in enumerate(vendors):
        progress.progress(
            0.5 + (i + 1) / (len(vendors) * 2) if vendors else 1.0,
            text=f"Assessing risk for {v.get('vendor_name')}...",
        )
        risk_by_vendor[v["vendor_name"]] = gemini_client.detect_risks(v, api_key)

    progress.progress(1.0, text="Scoring vendors...")
    scored_vendors = scoring.compute_scores(vendors, risk_by_vendor)
    health = scoring.procurement_health_score(scored_vendors)

    progress.empty()

    st.session_state.vendors = scored_vendors
    st.session_state.risk_by_vendor = risk_by_vendor
    st.session_state.health = health
    st.session_state.processed = True
    st.session_state.recommendation = {}
    st.session_state.executive_summary = {}


# ==========================================================================
# PAGE: UPLOAD & OVERVIEW
# ==========================================================================
if page == "🏠 Upload & Overview":
    st.markdown(
        """<div class="viq-hero">
        <h1 style="margin-bottom:0.2rem;">Welcome to VendorIQ AI</h1>
        <p style="opacity:0.8;margin:0;">Upload vendor proposal PDFs and let AI extract, compare,
        score, and recommend the best procurement decision — in minutes, not days.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="viq-section-title">Upload Vendor Proposals</div>', unsafe_allow_html=True)
    st.caption("Upload up to 5 PDF vendor proposals to begin analysis.")

    uploaded_files = st.file_uploader(
        "Drop PDF files here",
        type=["pdf"],
        accept_multiple_files=True,
        help="Maximum 5 files.",
    )

    if uploaded_files and len(uploaded_files) > 5:
        st.error("Please upload a maximum of 5 vendor proposals.")
        uploaded_files = uploaded_files[:5]

    if uploaded_files:
        st.write("**Uploaded files:**")
        for f in uploaded_files:
            st.write(f"📄 {f.name} — {f.size / 1024:.1f} KB")

        if st.button("🚀 Analyze Proposals with AI", type="primary", use_container_width=True):
            with st.spinner("VendorIQ AI is analyzing your proposals..."):
                process_uploaded_files(uploaded_files)
            st.success("Analysis complete! Explore the results using the sidebar navigation.")
            st.balloons()

    if st.session_state.processed and st.session_state.vendors:
        st.markdown('<div class="viq-section-title">Quick Overview</div>', unsafe_allow_html=True)
        vendors = st.session_state.vendors
        health = st.session_state.health
        best_value = scoring.best_value_badge(vendors)

        c1, c2, c3, c4 = st.columns(4)
        metric_card("Vendors Analyzed", len(vendors), c1)
        metric_card("Top Vendor", vendors[0]["vendor_name"], c2)
        metric_card("Top Score", f"{vendors[0]['overall_score']}/100", c3)
        metric_card("Health Score", f"{health.get('score', 0)}/100 ({health.get('label', '')})", c4)

        st.markdown(f'<span class="viq-best-value">🏅 Best Value for Money: {best_value}</span>', unsafe_allow_html=True)

        st.markdown('<div class="viq-section-title">Vendor Snapshot</div>', unsafe_allow_html=True)
        cols = st.columns(len(vendors))
        for col, v in zip(cols, vendors):
            with col:
                st.markdown(
                    f"""<div class="viq-card">
                    <h3>{v['vendor_name']}</h3>
                    <div class="viq-value">{v['overall_score']}/100</div>
                    <div>{severity_badge(v.get('overall_risk_level','Low'))}</div>
                    <p style="font-size:0.8rem;opacity:0.75;margin-top:0.4rem;">{v.get('total_cost','N/A')}</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
    else:
        st.info("👆 Upload vendor proposals above to get started.")


# ==========================================================================
# PAGE: COMPARISON TABLE
# ==========================================================================
elif page == "📋 Comparison Table":
    st.markdown('<div class="viq-section-title">Smart Comparison Engine</div>', unsafe_allow_html=True)
    if not st.session_state.vendors:
        st.warning("No vendors analyzed yet. Go to **Upload & Overview** first.")
    else:
        df = export.build_comparison_dataframe(st.session_state.vendors)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown('<div class="viq-section-title">Full Feature Breakdown</div>', unsafe_allow_html=True)
        for v in st.session_state.vendors:
            with st.expander(f"📄 {v['vendor_name']} — Full Details"):
                colA, colB = st.columns(2)
                with colA:
                    st.write(f"**Total Cost:** {v.get('total_cost','N/A')}")
                    st.write(f"**Delivery Timeline:** {v.get('delivery_timeline','N/A')}")
                    st.write(f"**Warranty:** {v.get('warranty_period','N/A')}")
                    st.write(f"**Payment Terms:** {v.get('payment_terms','N/A')}")
                with colB:
                    st.write(f"**Support Details:** {v.get('support_details','N/A')}")
                    st.write("**Key Features:**")
                    for feat in v.get("key_features", []):
                        st.write(f"- {feat}")
                st.write("**Risks Mentioned:**")
                for r in v.get("risks_mentioned", []):
                    st.write(f"- {r}")


# ==========================================================================
# PAGE: SCORING & LEADERBOARD
# ==========================================================================
elif page == "🏆 Scoring & Leaderboard":
    st.markdown('<div class="viq-section-title">Vendor Scoring System</div>', unsafe_allow_html=True)
    if not st.session_state.vendors:
        st.warning("No vendors analyzed yet. Go to **Upload & Overview** first.")
    else:
        vendors = st.session_state.vendors
        best_value = scoring.best_value_badge(vendors)

        st.markdown('<div class="viq-section-title">Leaderboard</div>', unsafe_allow_html=True)
        for i, v in enumerate(vendors, start=1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
            badge = f'<span class="viq-best-value">🏅 Best Value</span>' if v["vendor_name"] == best_value else ""
            st.markdown(
                f"""<div class="viq-card">
                <h3>{medal} {v['vendor_name']} {badge}</h3>
                <div class="viq-value">{v['overall_score']} / 100</div>
                </div>""",
                unsafe_allow_html=True,
            )
            st.progress(min(1.0, v["overall_score"] / 100))

        st.markdown('<div class="viq-section-title">Score Breakdown</div>', unsafe_allow_html=True)
        breakdown_rows = []
        for v in vendors:
            row = {"Vendor": v["vendor_name"]}
            row.update({charts.CRITERIA_LABELS[k]: s for k, s in v.get("scores", {}).items()})
            breakdown_rows.append(row)
        st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True, hide_index=True)

        st.plotly_chart(charts.ranking_chart(vendors, st.session_state.theme), use_container_width=True)


# ==========================================================================
# PAGE: AI RECOMMENDATION
# ==========================================================================
elif page == "🎯 AI Recommendation":
    st.markdown('<div class="viq-section-title">AI Recommendation Engine</div>', unsafe_allow_html=True)
    if not st.session_state.vendors:
        st.warning("No vendors analyzed yet. Go to **Upload & Overview** first.")
    else:
        if st.button("✨ Generate AI Recommendation", type="primary"):
            with st.spinner("Analyzing trade-offs across all vendors..."):
                st.session_state.recommendation = gemini_client.generate_recommendation(
                    st.session_state.vendors, st.session_state.api_key
                )

        rec = st.session_state.recommendation
        if rec:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(
                    f"""<div class="viq-hero">
                    <h2>🏆 Recommended Vendor: {rec.get('recommended_vendor','N/A')}</h2>
                    <p>{rec.get('reasoning','')}</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.write("**Trade-offs to consider:**")
                for t in rec.get("trade_offs", []):
                    st.write(f"- {t}")
                st.write(f"**Runner-up:** {rec.get('runner_up', 'N/A')}")
            with c2:
                metric_card("Confidence Score", f"{rec.get('confidence_score', 0)}%", c2)
        else:
            st.info("Click the button above to generate an AI-backed recommendation.")


# ==========================================================================
# PAGE: RISK DETECTION
# ==========================================================================
elif page == "⚠️ Risk Detection":
    st.markdown('<div class="viq-section-title">Risk Detection Module</div>', unsafe_allow_html=True)
    if not st.session_state.vendors:
        st.warning("No vendors analyzed yet. Go to **Upload & Overview** first.")
    else:
        risk_map = st.session_state.risk_by_vendor
        c1, c2, c3 = st.columns(3)
        total_risks = sum(len(r.get("risks", [])) for r in risk_map.values())
        high_risks = sum(1 for r in risk_map.values() for x in r.get("risks", []) if x["severity"] == "High")
        metric_card("Total Risks Flagged", total_risks, c1)
        metric_card("High-Severity Risks", high_risks, c2)
        metric_card("Vendors Assessed", len(risk_map), c3)

        st.plotly_chart(charts.risk_severity_chart(risk_map, st.session_state.theme), use_container_width=True)

        st.markdown('<div class="viq-section-title">Contract Risk Alert System</div>', unsafe_allow_html=True)
        for vendor_name, info in risk_map.items():
            with st.expander(f"⚠️ {vendor_name} — Overall Risk: {info.get('overall_risk_level','Low')}"):
                for r in info.get("risks", []):
                    st.markdown(
                        f"{severity_badge(r['severity'])} **{r['category']}** — {r['description']}",
                        unsafe_allow_html=True,
                    )


# ==========================================================================
# PAGE: ANALYTICS
# ==========================================================================
elif page == "📈 Analytics":
    st.markdown('<div class="viq-section-title">Interactive Analytics</div>', unsafe_allow_html=True)
    if not st.session_state.vendors:
        st.warning("No vendors analyzed yet. Go to **Upload & Overview** first.")
    else:
        vendors = st.session_state.vendors
        theme = st.session_state.theme
        tab1, tab2, tab3, tab4 = st.tabs(["Radar Chart", "Score Comparison", "Ranking", "Cost Comparison"])
        with tab1:
            st.plotly_chart(charts.radar_chart(vendors, theme), use_container_width=True)
        with tab2:
            st.plotly_chart(charts.score_bar_chart(vendors, theme), use_container_width=True)
        with tab3:
            st.plotly_chart(charts.ranking_chart(vendors, theme), use_container_width=True)
        with tab4:
            st.plotly_chart(charts.cost_comparison_chart(vendors, theme), use_container_width=True)


# ==========================================================================
# PAGE: EXECUTIVE SUMMARY
# ==========================================================================
elif page == "🧾 Executive Summary":
    st.markdown('<div class="viq-section-title">AI Executive Summary</div>', unsafe_allow_html=True)
    if not st.session_state.vendors:
        st.warning("No vendors analyzed yet. Go to **Upload & Overview** first.")
    else:
        if st.button("📝 Generate Executive Summary", type="primary"):
            with st.spinner("Drafting procurement report..."):
                st.session_state.executive_summary = gemini_client.generate_executive_summary(
                    st.session_state.vendors, st.session_state.api_key
                )

        summ = st.session_state.executive_summary
        if summ:
            st.markdown('<div class="viq-section-title">Overview</div>', unsafe_allow_html=True)
            st.write(summ.get("overview", ""))

            st.markdown('<div class="viq-section-title">Strengths & Weaknesses</div>', unsafe_allow_html=True)
            for name in summ.get("strengths_by_vendor", {}).keys():
                st.markdown(f"**{name}**")
                st.write(f"✅ Strength: {summ['strengths_by_vendor'].get(name,'')}")
                st.write(f"⚠️ Weakness: {summ.get('weaknesses_by_vendor', {}).get(name,'')}")
                st.divider()

            st.markdown('<div class="viq-section-title">Final Recommendation</div>', unsafe_allow_html=True)
            st.success(summ.get("final_recommendation", ""))
        else:
            st.info("Click the button above to generate the executive summary.")


# ==========================================================================
# PAGE: NEGOTIATION & SAVINGS (Hackathon differentiator)
# ==========================================================================
elif page == "💰 Negotiation & Savings":
    st.markdown('<div class="viq-section-title">AI Negotiation Suggestions & Estimated Savings</div>', unsafe_allow_html=True)
    if not st.session_state.vendors:
        st.warning("No vendors analyzed yet. Go to **Upload & Overview** first.")
    else:
        vendors = st.session_state.vendors
        costs = [v.get("total_cost_numeric", 0) for v in vendors if v.get("total_cost_numeric")]
        pool_avg = {"avg_cost": sum(costs) / len(costs) if costs else 0}

        for v in vendors:
            with st.expander(f"💬 Negotiation Strategy — {v['vendor_name']}"):
                if st.button(f"Generate suggestions for {v['vendor_name']}", key=f"negotiate_{v['vendor_name']}"):
                    with st.spinner("Building negotiation strategy..."):
                        neg = gemini_client.generate_negotiation_suggestions(v, pool_avg, st.session_state.api_key)
                        st.session_state[f"neg_{v['vendor_name']}"] = neg

                neg = st.session_state.get(f"neg_{v['vendor_name']}")
                if neg:
                    c1, c2 = st.columns(2)
                    metric_card("Estimated Savings %", f"{neg.get('estimated_savings_pct', 0)}%", c1)
                    metric_card("Estimated Savings Amount", neg.get("estimated_savings_amount", "N/A"), c2)
                    st.write("**Negotiation Talking Points:**")
                    for p in neg.get("negotiation_points", []):
                        st.write(f"- {p}")


# ==========================================================================
# PAGE: EXPORT
# ==========================================================================
elif page == "⬇️ Export":
    st.markdown('<div class="viq-section-title">Export Options</div>', unsafe_allow_html=True)
    if not st.session_state.vendors:
        st.warning("No vendors analyzed yet. Go to **Upload & Overview** first.")
    else:
        vendors = st.session_state.vendors
        df = export.build_comparison_dataframe(vendors)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📄 CSV Summary")
            csv_bytes = export.dataframe_to_csv_bytes(df)
            st.download_button(
                "⬇️ Download CSV Summary",
                data=csv_bytes,
                file_name="vendoriq_comparison_summary.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with c2:
            st.markdown("### 📑 PDF Report")
            if st.button("Generate PDF Report", use_container_width=True):
                with st.spinner("Building PDF report..."):
                    pdf_bytes = export.build_pdf_report(
                        vendors,
                        st.session_state.recommendation,
                        st.session_state.executive_summary,
                        st.session_state.health,
                    )
                    st.session_state["pdf_report_bytes"] = pdf_bytes

            if st.session_state.get("pdf_report_bytes"):
                st.download_button(
                    "⬇️ Download PDF Report",
                    data=st.session_state["pdf_report_bytes"],
                    file_name="vendoriq_procurement_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        st.info("💡 Tip: Generate the AI Recommendation and Executive Summary first for a richer PDF report.")


# --------------------------------------------------------------------------
# FOOTER
# --------------------------------------------------------------------------
st.markdown(
    '<div class="viq-footer-note">VendorIQ AI — Built for the AI Product Buildathon · '
    'Powered by Gemini, Streamlit & Plotly</div>',
    unsafe_allow_html=True,
)
