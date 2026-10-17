"""
VoxGuard AI - Premium Cybersecurity Dashboard

A polished cybersecurity SaaS dashboard for audio authenticity analysis.
Uses rule-based audio forensics via the AudioAuthenticator API.
All processing is local; no audio is uploaded to external services.
"""

import os
import tempfile

import streamlit as st

from detector import AudioAuthenticator, VoxGuardError

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="VoxGuard AI",
    page_icon=":material/shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme: deep navy, cyan/teal accents, glass cards
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
    /* Smooth scrolling for anchor navigation */
    html {
        scroll-behavior: smooth;
    }

    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #060d1a 0%, #0a1628 40%, #0d1b2e 100%);
        color: #e0e6f0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1628 0%, #060d1a 100%);
        border-right: 1px solid #1a2d4a;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #00d4aa !important;
        font-weight: 600;
    }

    /* Primary button */
    .stButton > button {
        background: linear-gradient(135deg, #00d4aa 0%, #00b894 100%);
        color: #060d1a;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #00ffcc 0%, #00d4aa 100%);
        box-shadow: 0 0 25px rgba(0, 212, 170, 0.5);
        transform: translateY(-2px);
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(13, 27, 46, 0.6);
        border: 2px dashed #1a2d4a;
        border-radius: 16px;
        padding: 2rem;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #00d4aa;
        background: rgba(13, 27, 46, 0.9);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(13, 27, 46, 0.6);
        color: #00d4aa;
        font-weight: 600;
        border-radius: 10px;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: rgba(13, 27, 46, 0.6);
        border: 1px solid #1a2d4a;
        border-radius: 12px;
        padding: 1rem;
    }
    [data-testid="stMetricLabel"] {
        color: #8892b0;
    }
    [data-testid="stMetricValue"] {
        color: #00d4aa;
    }

    /* Alerts */
    .stAlert {
        border-radius: 10px;
    }

    /* Checkbox */
    .stCheckbox > label {
        color: #e0e6f0;
    }

    /* Audio player */
    .stAudio {
        background: rgba(13, 27, 46, 0.6);
        border-radius: 10px;
        padding: 0.5rem;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(13, 27, 46, 0.6);
        color: #8892b0;
        border-radius: 10px 10px 0 0;
        padding: 0.5rem 1rem;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(0, 212, 170, 0.15);
        color: #00d4aa;
    }

    /* Glass card */
    .glass-card {
        background: rgba(13, 27, 46, 0.6);
        border: 1px solid #1a2d4a;
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
    }

    /* Gradient text */
    .gradient-text {
        background: linear-gradient(135deg, #00d4aa 0%, #00ffcc 50%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Audio wave animation */
    @keyframes wave {
        0%, 100% { height: 20%; }
        50% { height: 80%; }
    }
    .wave-bar {
        width: 4px;
        background: linear-gradient(180deg, #00d4aa, #7c3aed);
        border-radius: 2px;
        animation: wave 1.2s ease-in-out infinite;
    }

    /* Glow effect */
    .glow {
        box-shadow: 0 0 20px rgba(0, 212, 170, 0.15);
    }

    /* Feature card hover */
    .feature-card {
        background: rgba(13, 27, 46, 0.6);
        border: 1px solid #1a2d4a;
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    .feature-card:hover {
        border-color: #00d4aa;
        box-shadow: 0 0 20px rgba(0, 212, 170, 0.2);
        transform: translateY(-2px);
    }

    /* Navigation link styling */
    .nav-link {
        display: block;
        padding: 0.5rem 0.75rem;
        margin: 0.15rem 0;
        border-radius: 8px;
        color: #8892b0;
        text-decoration: none;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }
    .nav-link:hover {
        background: rgba(0, 212, 170, 0.1);
        color: #00d4aa;
    }
    .nav-link:focus {
        outline: 2px solid #00d4aa;
        outline-offset: -2px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLASSIFICATION_COLORS = {
    "Likely Genuine": "#00d4aa",
    "Suspicious": "#ff6b6b",
    "Inconclusive": "#ffd93d",
}

RISK_COLORS = {
    "Low": "#00d4aa",
    "Medium": "#ffd93d",
    "High": "#ff6b6b",
    "Unknown": "#8892b0",
}

MAX_UPLOAD_MB = 20


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classification_color(value: str) -> str:
    return CLASSIFICATION_COLORS.get(value, "#8892b0")


def _risk_color(value: str) -> str:
    return RISK_COLORS.get(value, "#8892b0")


# ---------------------------------------------------------------------------
# Sidebar with functional navigation
# ---------------------------------------------------------------------------

with st.sidebar:
    # Logo treatment with inline SVG shield
    st.markdown(
        """
    <div style="text-align: center; padding: 1rem 0 0.75rem 0;">
        <div style="
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, #00d4aa 0%, #7c3aed 100%);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5rem;
            box-shadow: 0 0 25px rgba(0, 212, 170, 0.3);
        ">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L3 7V12C3 17.55 6.84 22.74 12 24C17.16 22.74 21 17.55 21 12V7L12 2Z" fill="#060d1a"/>
                <path d="M9 12L11 14L15 10" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <h2 style="margin: 0; color: #00d4aa; font-size: 1.4rem;">VoxGuard AI</h2>
        <p style="color: #8892b0; font-size: 0.8rem; margin: 0.15rem 0 0 0;">
            Listen. Analyse. Stay Safer.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Navigation sections - functional anchor links
    st.markdown("### :material/menu: Navigation")
    st.markdown(
        """
    <a href="#home" class="nav-link" role="link" tabindex="0">
        <span style="display: flex; align-items: center; gap: 0.5rem;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 20V14H14V20H19V12H22L12 3L2 12H5V20H10Z" fill="currentColor"/>
            </svg>
            Home
        </span>
    </a>
    <a href="#how-it-works" class="nav-link" role="link" tabindex="0">
        <span style="display: flex; align-items: center; gap: 0.5rem;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M9.09 9C9.3251 8.33167 9.78915 7.76811 10.4 7.4C11.0108 7.03189 11.7339 6.87932 12.475 7.00539C13.2161 7.13147 13.8928 7.52643 14.355 8.105C14.8172 8.68357 15.0316 9.41112 15 10.15C15 11.5 12.5 12 12.5 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M12 17H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            How It Works
        </span>
    </a>
    <a href="#results" class="nav-link" role="link" tabindex="0">
        <span style="display: flex; align-items: center; gap: 0.5rem;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
            </svg>
            Example Results
        </span>
    </a>
    <a href="#safety" class="nav-link" role="link" tabindex="0">
        <span style="display: flex; align-items: center; gap: 0.5rem;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 9V13M12 17H12.01M10.29 3.86L1.82 18C1.64 18.37 1.64 18.82 1.82 19.19C2 19.57 2.37 19.78 2.77 19.78H21.23C21.63 19.78 22 19.57 22.18 19.19C22.36 18.82 22.36 18.37 22.18 18L13.71 3.86C13.53 3.48 13.16 3.25 12.76 3.25C12.36 3.25 11.99 3.48 11.81 3.86H10.29Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Safety Tips and Limitations
        </span>
    </a>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Amber disclaimer card with inline SVG warning icon
    st.markdown(
        """
    <div style="
        background: rgba(255, 193, 7, 0.08);
        border: 1px solid rgba(255, 193, 7, 0.3);
        border-radius: 12px;
        padding: 0.9rem;
    ">
        <p style="color: #ffc107; font-weight: 600; margin: 0 0 0.4rem 0; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 9V13M12 17H12.01M10.29 3.86L1.82 18C1.64 18.37 1.64 18.82 1.82 19.19C2 19.57 2.37 19.78 2.77 19.78H21.23C21.63 19.78 22 19.57 22.18 19.19C22.36 18.82 22.36 18.37 22.18 18L13.71 3.86C13.53 3.48 13.16 3.25 12.76 3.25C12.36 3.25 11.99 3.48 11.81 3.86H10.29Z" stroke="#ffc107" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Important Disclaimer
        </p>
        <p style="color: #e0e6f0; font-size: 0.78rem; margin: 0; line-height: 1.35;">
            This is <strong>NOT</strong> a validated AI-generated voice detector.
            It performs rule-based audio-quality analysis only.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Privacy card with inline SVG lock icon
    st.markdown(
        """
    <div style="
        background: rgba(0, 212, 170, 0.08);
        border: 1px solid rgba(0, 212, 170, 0.3);
        border-radius: 12px;
        padding: 0.9rem;
    ">
        <p style="color: #00d4aa; font-weight: 600; margin: 0 0 0.4rem 0; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" stroke="#00d4aa" stroke-width="2"/>
                <path d="M7 11V7C7 4.24 9.24 2 12 2C14.76 2 17 4.24 17 7V11" stroke="#00d4aa" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Privacy
        </p>
        <p style="color: #e0e6f0; font-size: 0.78rem; margin: 0; line-height: 1.35;">
            All processing happens <strong>locally</strong>. Audio files are never
            uploaded to external services.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Home section (hero)
# ---------------------------------------------------------------------------

st.markdown('<div id="home"></div>', unsafe_allow_html=True)

st.markdown(
    """
<div style="text-align: center; padding: 0.5rem 0 0.75rem 0;">
    <h1 class="gradient-text" style="font-size: 2.5rem; margin-bottom: 0; font-weight: 700;">
        VoxGuard AI
    </h1>
    <p style="color: #8892b0; font-size: 1.1rem; margin: 0.25rem 0 0 0;">
        AI-Powered Voice Authenticity Analysis
    </p>
    <p style="color: #6b7a99; font-size: 0.9rem; margin: 0.5rem auto 0 auto; max-width: 550px;">
        Analyse audio recordings for authenticity indicators using advanced rule-based
        audio forensics. Upload a WAV file to get started.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# Feature cards with inline SVG icons
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
    <div class="feature-card" style="text-align: center;">
        <div style="
            width: 48px;
            height: 48px;
            background: rgba(0, 212, 170, 0.15);
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5rem;
        ">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="2" y="3" width="20" height="14" rx="2" stroke="#00d4aa" stroke-width="2"/>
                <path d="M8 21H16M12 17V21" stroke="#00d4aa" stroke-width="2" stroke-linecap="round"/>
            </svg>
        </div>
        <h4 style="margin: 0 0 0.4rem 0; color: #00d4aa; font-size: 0.95rem;">Local Processing</h4>
        <p style="color: #8892b0; font-size: 0.8rem; margin: 0;">
            All analysis runs on your device. No data leaves your machine.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
    <div class="feature-card" style="text-align: center;">
        <div style="
            width: 48px;
            height: 48px;
            background: rgba(0, 212, 170, 0.15);
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5rem;
        ">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 11L12 14L22 4" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 12V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19V5C3 3.9 3.9 3 5 3H16" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <h4 style="margin: 0 0 0.4rem 0; color: #00d4aa; font-size: 0.95rem;">Rule-Based Analysis</h4>
        <p style="color: #8892b0; font-size: 0.8rem; margin: 0;">
            Transparent audio-quality metrics and anomaly detection.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
    <div class="feature-card" style="text-align: center;">
        <div style="
            width: 48px;
            height: 48px;
            background: rgba(0, 212, 170, 0.15);
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5rem;
        ">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 1V23M17 5H9.5C8.12 5 7 6.12 7 7.5C7 8.88 8.12 10 9.5 10H14.5C15.88 10 17 11.12 17 12.5C17 13.88 15.88 15 14.5 15H7" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <h4 style="margin: 0 0 0.4rem 0; color: #00d4aa; font-size: 0.95rem;">Financial Safety</h4>
        <p style="color: #8892b0; font-size: 0.8rem; margin: 0;">
            Guardrails for sensitive financial instructions.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# Audio wave visual (illustrative)
st.markdown(
    """
<div style="text-align: center; padding: 0.25rem 0;">
    <div style="display: inline-flex; align-items: flex-end; gap: 3px; height: 30px;">
        <div class="wave-bar" style="animation-delay: 0s;"></div>
        <div class="wave-bar" style="animation-delay: 0.1s;"></div>
        <div class="wave-bar" style="animation-delay: 0.2s;"></div>
        <div class="wave-bar" style="animation-delay: 0.3s;"></div>
        <div class="wave-bar" style="animation-delay: 0.4s;"></div>
        <div class="wave-bar" style="animation-delay: 0.5s;"></div>
        <div class="wave-bar" style="animation-delay: 0.6s;"></div>
        <div class="wave-bar" style="animation-delay: 0.7s;"></div>
        <div class="wave-bar" style="animation-delay: 0.8s;"></div>
        <div class="wave-bar" style="animation-delay: 0.9s;"></div>
        <div class="wave-bar" style="animation-delay: 1.0s;"></div>
        <div class="wave-bar" style="animation-delay: 1.1s;"></div>
    </div>
    <p style="color: #6b7a99; font-size: 0.7rem; margin: 0.25rem 0 0 0;">
        Illustrative audio wave visualization
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# How It Works section
# ---------------------------------------------------------------------------

st.markdown('<div id="how-it-works"></div>', unsafe_allow_html=True)

st.markdown("## :material/help: How It Works")

st.markdown(
    """
<div class="glass-card" style="padding: 0.8rem 1.2rem;">
    <p style="color: #8892b0; font-size: 0.85rem; margin: 0; line-height: 1.4;">
        VoxGuard AI analyses audio recordings using a transparent, rule-based pipeline.
        Here is what happens when you upload a WAV file and click <strong>Analyse Audio</strong>:
    </p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
    <div class="feature-card" style="text-align: center;">
        <div style="
            width: 48px;
            height: 48px;
            background: rgba(0, 212, 170, 0.15);
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5rem;
        ">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 15V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19V15" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 10L12 15L17 10" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 15V3" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <h4 style="margin: 0 0 0.4rem 0; color: #00d4aa; font-size: 0.9rem;">1. Upload</h4>
        <p style="color: #8892b0; font-size: 0.78rem; margin: 0; line-height: 1.4;">
            WAV file is read and validated locally. Format, size, and integrity are checked.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
    <div class="feature-card" style="text-align: center;">
        <div style="
            width: 48px;
            height: 48px;
            background: rgba(0, 212, 170, 0.15);
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5rem;
        ">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2V6M12 18V22M4.93 4.93L7.76 7.76M16.24 16.24L19.07 19.07M2 12H6M18 12H22M4.93 19.07L7.76 16.24M16.24 7.76L19.07 4.93" stroke="#00d4aa" stroke-width="2" stroke-linecap="round"/>
                <circle cx="12" cy="12" r="3" stroke="#00d4aa" stroke-width="2"/>
            </svg>
        </div>
        <h4 style="margin: 0 0 0.4rem 0; color: #00d4aa; font-size: 0.9rem;">2. Analyse</h4>
        <p style="color: #8892b0; font-size: 0.78rem; margin: 0; line-height: 1.4;">
            14 acoustic features extracted: RMS energy, spectral centroid, SNR, clipping ratio, and more.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
    <div class="feature-card" style="text-align: center;">
        <div style="
            width: 48px;
            height: 48px;
            background: rgba(0, 212, 170, 0.15);
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5rem;
        ">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 11L12 14L22 4" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 12V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19V5C3 3.9 3.9 3 5 3H16" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <h4 style="margin: 0 0 0.4rem 0; color: #00d4aa; font-size: 0.9rem;">3. Classify</h4>
        <p style="color: #8892b0; font-size: 0.78rem; margin: 0; line-height: 1.4;">
            Transparent rules produce a classification with explanation and limitations.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Upload section
# ---------------------------------------------------------------------------

st.markdown("## :material/upload: Upload Audio")

with st.container(border=True):
    uploaded_file = st.file_uploader(
        "Choose a WAV file",
        type=["wav"],
        help=f"Upload a WAV audio file for analysis (max {MAX_UPLOAD_MB} MB)",
    )

    is_financial = False
    analyze_clicked = False

    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)

        if file_size_mb > MAX_UPLOAD_MB:
            st.error(
                f"File too large ({file_size_mb:.1f} MB). "
                f"Maximum allowed: {MAX_UPLOAD_MB} MB."
            )
        else:
            st.success(f"Uploaded: **{uploaded_file.name}** ({file_size_mb:.2f} MB)")

            # Audio playback
            st.audio(uploaded_file, format="audio/wav")

            # Financial instruction checkbox
            is_financial = st.checkbox(
                "This recording relates to a sensitive financial instruction",
                help="Check if the audio contains financial instructions that require verification",
            )

            # Analyze button
            analyze_clicked = st.button("Analyse Audio", type="primary")
    else:
        st.info("Upload a WAV file to begin analysis")

# ---------------------------------------------------------------------------
# Results section
# ---------------------------------------------------------------------------

st.markdown('<div id="results"></div>', unsafe_allow_html=True)

st.markdown("## :material/analytics: Analysis Results")

if not analyze_clicked or uploaded_file is None:
    st.info("Upload a WAV file and click **Analyse Audio** to see results.")
else:
    # Save uploaded file to a temporary location for the detector
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        authenticator = AudioAuthenticator()
        result = authenticator.analyze(tmp_path)

        # -------------------------------------------------------------------
        # Result variables
        # -------------------------------------------------------------------

        classification = result["classification"]
        risk = result["risk_indicator"]
        explanation = result["explanation"]
        limitations = result["limitations"]
        audio_quality = result["audio_quality"]
        features = result["measured_features"]
        triggered_rules = result["triggered_rules"]
        financial_rec = result["financial_verification_recommendation"]

        # -------------------------------------------------------------------
        # KPI cards
        # -------------------------------------------------------------------

        with st.container(horizontal=True):
            st.metric("Classification", classification, border=True)
            st.metric("Risk Indicator", risk, border=True)
            quality_label = (
                "Adequate" if audio_quality["adequate_for_assessment"] else "Insufficient"
            )
            st.metric("Assessment Quality", quality_label, border=True)
            st.metric("Duration", f"{audio_quality['duration_seconds']:.2f}s", border=True)

        st.markdown("---")

        # -------------------------------------------------------------------
        # Results tabs
        # -------------------------------------------------------------------

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                ":material/lightbulb: Key Findings",
                ":material/high_quality: Audio Health Report",
                ":material/bar_chart: Measured Features",
                ":material/flag: Triggered Rules",
                ":material/payments: Financial Safety",
                ":material/info: Limitations",
            ]
        )

        # --- Tab 1: Key Findings ---
        with tab1:
            st.markdown("### Explanation")
            st.info(explanation)

            if triggered_rules:
                st.markdown("### Triggered Rules")
                for rule in triggered_rules:
                    st.markdown(f"- `{rule}`")

        # --- Tab 2: Audio Health Report ---
        with tab2:
            # Plain-English issue descriptions
            ISSUE_DESCRIPTIONS = {
                "DURATION_TOO_SHORT": "Recording is too short — less than half a second is not enough for reliable analysis",
                "SAMPLE_RATE_TOO_LOW": "Recording quality is below standard (sample rate is low)",
                "ENTIRELY_SILENT": "Recording appears to be completely silent",
                "EXCESSIVE_SILENCE": "Recording contains too much silence",
                "LOW_SNR": "Background noise may be affecting the recording",
                "HEAVY_CLIPPING": "Recording may be distorted (clipping detected)",
                "UNUSUAL_SPECTRAL_FLATNESS": "Unusual frequency distribution detected",
                "LOW_DYNAMIC_RANGE": "Recording has limited volume variation",
            }

            # Transparent quality score rubric (out of 10)
            RULE_PENALTIES = {
                "ENTIRELY_SILENT": 5,
                "DURATION_TOO_SHORT": 3,
                "EXCESSIVE_SILENCE": 3,
                "SAMPLE_RATE_TOO_LOW": 2,
                "LOW_SNR": 2,
                "HEAVY_CLIPPING": 2,
                "UNUSUAL_SPECTRAL_FLATNESS": 1,
                "LOW_DYNAMIC_RANGE": 1,
            }

            quality_score = 10
            for rule in triggered_rules:
                quality_score -= RULE_PENALTIES.get(rule, 0)
            quality_score = max(0, quality_score)

            # Quality score display
            col1, col2 = st.columns([1, 2])

            with col1:
                if quality_score >= 7:
                    score_color = "#00d4aa"
                    score_label = "Good"
                elif quality_score >= 4:
                    score_color = "#ffd93d"
                    score_label = "Fair"
                else:
                    score_color = "#ff6b6b"
                    score_label = "Poor"

                st.markdown(
                    f"""
                <div style="text-align: center; padding: 1rem;">
                    <div style="
                        width: 80px;
                        height: 80px;
                        background: rgba(13, 27, 46, 0.8);
                        border: 3px solid {score_color};
                        border-radius: 50%;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        margin-bottom: 0.5rem;
                    ">
                        <span style="font-size: 1.8rem; font-weight: 700; color: {score_color};">
                            {quality_score}
                        </span>
                    </div>
                    <p style="color: {score_color}; font-weight: 600; margin: 0;">{score_label}</p>
                    <p style="color: #6b7a99; font-size: 0.7rem; margin: 0.25rem 0 0 0;">
                        Indicative recording-quality score
                    </p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown("#### What this means")
                st.markdown(
                    """
                <div class="glass-card" style="padding: 0.8rem;">
                    <p style="color: #8892b0; font-size: 0.8rem; margin: 0; line-height: 1.4;">
                        <strong>Score rubric:</strong> Starts at 10. Deductions: -5 silent, -3 too short or too much silence,
                        -2 low sample rate, noise, or clipping, -1 unusual frequency or limited volume range.
                        This is a recording-quality score only — it is <strong>not</strong> a voice-authenticity or fraud probability.
                    </p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if audio_quality["issues"]:
                    st.markdown("#### Plain-English summary")
                    for issue in audio_quality["issues"]:
                        description = ISSUE_DESCRIPTIONS.get(issue, issue.replace("_", " ").title())
                        st.warning(f"- {description}")
                else:
                    st.success("No quality issues detected — the recording appears to be of good technical quality.")

            # Important disclaimer
            st.info(
                "**Note:** Good audio quality does not prove a voice is genuine, and poor quality does not prove fraud. "
                "This report assesses signal quality only, not speech intelligibility or speaker identity."
            )

            # Collapsible Technical Details
            with st.expander("View Technical Details"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### Signal Properties")
                    st.markdown(f"- **Sample Rate:** {audio_quality['sample_rate']} Hz")
                    st.markdown(f"- **Duration:** {audio_quality['duration_seconds']:.2f} s")
                    st.markdown(f"- **Bit Depth:** {audio_quality['bit_depth']}-bit")
                    st.markdown(f"- **Channels:** {audio_quality['num_channels']}")

                with col2:
                    st.markdown("#### Measured Features")
                    st.markdown(f"- **RMS Energy:** {features['rms_energy']:.6f}")
                    st.markdown(f"- **Peak Amplitude:** {features['peak_amplitude']:.6f}")
                    st.markdown(f"- **Clipping Ratio:** {features['clipping_ratio']:.6f}")
                    st.markdown(f"- **Silence Ratio:** {features['silence_ratio']:.4f}")
                    st.markdown(f"- **SNR:** {features['snr_db']:.1f} dB")
                    st.markdown(f"- **Dynamic Range:** {features['dynamic_range_db']:.1f} dB")

        # --- Tab 3: Measured Features ---
        with tab3:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### Energy")
                st.markdown(f"- **RMS Energy:** {features['rms_energy']:.6f}")
                st.markdown(f"- **Peak Amplitude:** {features['peak_amplitude']:.6f}")
                st.markdown(
                    f"- **Dynamic Range:** {features['dynamic_range_db']:.1f} dB"
                )

            with col2:
                st.markdown("#### Spectral")
                st.markdown(
                    f"- **Centroid:** {features['spectral_centroid_hz']:.1f} Hz"
                )
                st.markdown(
                    f"- **Bandwidth:** {features['spectral_bandwidth_hz']:.1f} Hz"
                )
                st.markdown(
                    f"- **Rolloff:** {features['spectral_rolloff_hz']:.1f} Hz"
                )
                st.markdown(
                    f"- **Flatness:** {features['spectral_flatness']:.4f}"
                )

            with col3:
                st.markdown("#### Other")
                st.markdown(
                    f"- **Zero-Crossing Rate:** {features['zero_crossing_rate']:.4f}"
                )
                st.markdown(
                    f"- **Clipping Ratio:** {features['clipping_ratio']:.6f}"
                )
                st.markdown(
                    f"- **Silence Ratio:** {features['silence_ratio']:.4f}"
                )
                st.markdown(f"- **SNR:** {features['snr_db']:.1f} dB")
                st.markdown(
                    f"- **Noise Floor:** {features['noise_floor_db']:.1f} dB"
                )

        # --- Tab 4: Triggered Rules ---
        with tab4:
            if triggered_rules:
                for rule in triggered_rules:
                    st.markdown(f"- `{rule}`")
            else:
                st.success("No rules triggered")

        # --- Tab 5: Financial Safety ---
        with tab5:
            if is_financial:
                st.error(
                    "**IMPORTANT: Sensitive Financial Instruction Detected**\n\n"
                    "This recording relates to a sensitive financial instruction. "
                    "Regardless of the analysis result, you should verify the instruction "
                    "through a separate, trusted channel before taking any action."
                )

            st.info(financial_rec)

        # --- Tab 6: Limitations ---
        with tab6:
            for limitation in limitations:
                st.markdown(f"- {limitation}")

        # -------------------------------------------------------------------
        # Final disclaimer
        # -------------------------------------------------------------------

        st.markdown("---")
        st.warning(
            "**Disclaimer:** This tool uses rule-based audio forensics, not a validated "
            "AI deepfake detection model. Results should not be used as the sole basis "
            "for security decisions. Audio analysis cannot establish the identity of "
            "the speaker."
        )

    except VoxGuardError as e:
        st.error(f"Analysis failed: {str(e)}")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
    finally:
        # Clean up temporary file
        os.unlink(tmp_path)

# ---------------------------------------------------------------------------
# Safety Tips and Limitations section
# ---------------------------------------------------------------------------

st.markdown('<div id="safety"></div>', unsafe_allow_html=True)

st.markdown("## :material/tips_and_updates: Safety Tips and Limitations")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Safety Tips")
    st.markdown(
        """
    <div class="glass-card">
        <ul style="color: #e0e6f0; font-size: 0.85rem; margin: 0; padding-left: 1.2rem; line-height: 1.6;">
            <li>Always verify sensitive financial instructions through a separate, trusted channel.</li>
            <li>Do not rely solely on audio analysis for security decisions.</li>
            <li>Be cautious of unsolicited audio messages requesting money or personal information.</li>
            <li>When in doubt, contact the supposed sender using a known, independent contact method.</li>
            <li>Report suspected fraud to your local authorities or financial institution.</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown("### Limitations")
    st.markdown(
        """
    <div class="glass-card">
        <ul style="color: #e0e6f0; font-size: 0.85rem; margin: 0; padding-left: 1.2rem; line-height: 1.6;">
            <li>This tool uses rule-based audio forensics, not a validated AI deepfake detection model.</li>
            <li>Audio analysis cannot establish the identity of the speaker.</li>
            <li>Acoustic features alone cannot distinguish genuine from synthetic speech.</li>
            <li>Results should not be used as the sole basis for security decisions.</li>
            <li>A "Likely Genuine" result does not guarantee the audio is authentic.</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )
