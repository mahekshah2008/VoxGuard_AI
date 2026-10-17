# 🎙️ VoxGuard AI
### Explainable Audio-Quality Screening & Anomaly Detection for Secure Voice Operations

**Making voice-driven workflows safer through explainable acoustic analysis.**

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![NumPy](https://img.shields.io/badge/Scientific%20Computing-NumPy-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![SciPy](https://img.shields.io/badge/Signal%20Processing-SciPy-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![Testing](https://img.shields.io/badge/Testing-30%20Unit%20Tests-success)](#-testing--quality-assurance)
[![Status](https://img.shields.io/badge/Status-Prototype-orange)](#-limitations--responsible-use)
[![License](https://img.shields.io/badge/License-Add%20Your%20License-lightgrey)](#-license)

---

## 🌟 Project at a Glance

| Project Detail | Information |
|---|---|
| **Project Name** | VoxGuard AI |
| **Category** | Artificial Intelligence · Audio Analytics · Cybersecurity |
| **Made for** | TECHTREK Hackathon , Technosphinx 2026 |
| **Made by** | Mahek Shah , Team name - Dodo |
| **Deployed Link** | [Launch VoxGuard AI](https://voxguardai-hnuxy4bm9rjgqprpphb2u9.streamlit.app/#home) |
| **Source Code** | [View on GitHub](https://github.com/mahekshah2008/VoxGuard_AI) |
| **Core Technologies** | Python, Streamlit, NumPy, SciPy, unittest |

> **The challenge:** Voice recordings can contain clipping, unusual silence patterns, signal distortions, or other acoustic irregularities. These characteristics may warrant further inspection in sensitive voice-driven workflows.
>
> **Our approach:** VoxGuard AI transforms measurable audio characteristics into transparent, rule-based findings that help users understand potential recording-quality issues before taking action.

## 🎯 The Problem

Voice-based communication is increasingly used in customer support, identity verification, remote collaboration, and operational workflows. However, a recording may have quality issues or suspicious acoustic characteristics that are difficult to identify through casual listening alone.

Existing black-box solutions can make it difficult for developers and reviewers to understand why a sample was flagged.

**VoxGuard AI addresses this challenge with a lightweight, explainable screening pipeline** that extracts acoustic features, evaluates configurable detection rules, and presents understandable findings through an interactive dashboard.

## 💡 Our Solution

VoxGuard AI is a Python-based audio analysis prototype built to make initial voice-recording screening accessible, interpretable, and easy to test.

Users can upload a WAV recording, inspect its waveform and playback, review extracted signal characteristics, and understand which detection rules were triggered.

### ✨ Key Features

- 🎚️ **Multi-Metric Acoustic Analysis** — Measures RMS energy, peak amplitude, silence ratio, clipping ratio, zero-crossing rate, and spectral characteristics.
- 🔎 **Explainable Rule Engine** — Connects measurable acoustic properties to explicit, traceable detection rules.
- 📊 **Interactive Dashboard** — Presents recording playback, waveform visualization, feature measurements, and analysis findings.
- 🛡️ **Input Validation & Error Handling** — Handles invalid, corrupted, or unsupported inputs gracefully.
- 🧪 **Automated Unit Testing** — Includes a reported suite of 30 unit tests covering detector behavior and edge cases.
- ⚡ **Lightweight Architecture** — Uses familiar Python scientific-computing libraries without requiring a deep-learning model for the current baseline.

## 🧠 How It Works

```text
        WAV Audio Upload
               │
               ▼
     Input Validation & Loading
               │
               ▼
       Acoustic Feature Extraction
               │
               ▼
        Deterministic Rule Engine
               │
               ▼
       Explainable Findings
               │
               ▼
     Streamlit Results Dashboard
               │
               ▼
      Human Review & Verification
```

### The Analysis Pipeline

**01 — Audio Ingestion**

Accepts WAV recordings and validates the input before processing.

**02 — Feature Extraction**

Computes signal-level measurements that characterize recording amplitude, silence, clipping, and spectral behavior.

**03 — Rule-Based Screening**

Evaluates extracted measurements against predefined thresholds and detection conditions.

**04 — Explainable Reporting**

Displays measured values alongside triggered rules, helping reviewers understand the basis of each finding.

**05 — Safety-Oriented Decision Support**

Encourages independent verification when a recording is used in a sensitive workflow.

## 🔬 Acoustic Features Analyzed

| Feature | What It Measures | Why It Matters |
|---|---|---|
| RMS Energy | Average signal magnitude | Helps identify unusually weak or strong audio |
| Peak Amplitude | Highest absolute sample amplitude | Helps identify extreme peaks |
| Silence Ratio | Proportion of samples or frames classified as silent | Helps identify extended silence or recording gaps |
| Clipping Ratio | Proportion of samples near the clipping threshold | Helps identify possible amplitude distortion |
| Zero-Crossing Rate | Frequency of signal sign changes | Describes aspects of signal texture |
| Spectral Features | Frequency-domain characteristics | Helps characterize the audio signal |

*Interpretation depends on the implementation, recording conditions, and configured thresholds. No individual feature establishes whether a voice is genuine or synthetic.*

## 🏗️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web interface |
| NumPy | Numerical operations and signal measurements |
| SciPy | Scientific and signal-processing utilities |
| Python `unittest` | Automated testing and regression checks |
| Git & GitHub | Version control and project collaboration |

## 📁 Project Structure

```text
VoxGuard_AI/
│
├── app.py               # Streamlit dashboard and user interface
├── detector.py          # Feature extraction and rule engine
├── test_detector.py     # Automated unit tests
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- pip
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/mahekshah2008/VoxGuard_AI.git
cd VoxGuard_AI
```

### 2. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Launch the Dashboard

```bash
streamlit run app.py
```

Open the local URL printed in your terminal and upload a WAV recording to explore the analysis.

### 4. Run the Test Suite

```bash
python -m unittest -v test_detector
```

The project documentation reports **30 passing unit tests**. Run the suite in your current environment to verify the result.

## 🧪 Testing & Quality Assurance

Reliability is an important part of VoxGuard AI's design.

The automated test suite is intended to verify core detector behavior and help identify regressions when the analysis pipeline changes.

Quality considerations include:

- Valid and invalid audio input handling.
- Acoustic feature extraction behavior.
- Rule-engine conditions and threshold boundaries.
- Edge cases and unexpected input conditions.
- Repeatable verification through automated tests.

**Engineering note:** Passing unit tests demonstrate expected software behavior under tested conditions. They do not, by themselves, establish deepfake detection accuracy or real-world security effectiveness.

## 🔐 Security, Explainability & Responsible Use

VoxGuard AI is designed as a **decision-support tool, not an automated authenticity authority**.

Its current rule-based architecture identifies acoustic patterns and recording-quality anomalies. These patterns can arise in genuine recordings as well as synthetic or manipulated audio.

Consequently, VoxGuard AI does not currently claim to:

- Reliably distinguish every genuine voice from an AI-generated voice.
- Prove speaker identity or establish the origin of a recording.
- Detect every form of voice cloning, replay attacks, or audio manipulation.
- Replace human review, identity verification, or forensic investigation.

> **Security principle:** Never authorize a sensitive financial transaction, change account credentials, or perform a high-privilege operation based on a voice recording alone. Use independent verification channels and appropriate multi-factor authentication.

## 🚧 Current Limitations

- **Rule-based baseline:** The current detector uses deterministic rules rather than a trained deepfake classifier.
- **Threshold sensitivity:** Detection outcomes depend on configured thresholds and recording characteristics.
- **Environmental variability:** Microphones, background noise, compression, and different speakers can affect extracted features.
- **No validated authenticity benchmark yet:** Detection precision, recall, false-positive rates, false-negative rates, and ROC-AUC have not been established by the project description.

These limitations define the next stage of development rather than being hidden behind unsupported accuracy claims.

## 🔮 Future Roadmap

- [ ] **Labeled Dataset Integration** — Evaluate genuine and synthetic speech using documented datasets and reproducible splits.
- [ ] **Deepfake Detection Models** — Integrate and evaluate suitable pretrained audio anti-spoofing architectures.
- [ ] **Performance Benchmarking** — Measure precision, recall, F1-score, false-positive rate, false-negative rate, and ROC-AUC where appropriate.
- [ ] **Robustness Testing** — Evaluate background noise, compression, unseen speakers, and recording-device variation.
- [ ] **REST API** — Expose the detection pipeline through FastAPI.
- [ ] **Containerization** — Package the application and dependencies with Docker.
- [ ] **Model Explainability** — Provide interpretable model outputs alongside the existing rule-based evidence.
- [ ] **Security Hardening** — Review file-handling safeguards, upload limits, privacy, logging, and deployment configuration.

## 🏆 Why VoxGuard AI?

**For hackathon judges**
- Tackles a relevant trust and security challenge involving voice-driven workflows.
- Demonstrates a complete prototype, from audio input to explainable output.
- Emphasizes transparent reasoning instead of unsupported black-box claims.
- Includes automated testing and a practical development roadmap.

**For recruiters and engineering teams**
- Demonstrates Python application development and scientific computing.
- Applies signal-processing concepts to a practical problem.
- Shows modular architecture, input validation, and unit-testing practices.
- Establishes a foundation for future ML integration and API deployment.
- Communicates technical limitations and security responsibilities clearly.

## 👥 Project Credits

- **Made for:** TECHTREK Hackathon , Technosphinx 2026
- **Made by:** Mahek Shah / Dodo
- **Role:** Team Lead
- **Deployed Link:** [https://voxguardai-hnuxy4bm9rjgqprpphb2u9.streamlit.app/#home]
- **GitHub Repository:** https://github.com/mahekshah2008/VoxGuard_AI

## 📜 License

Add your chosen open-source license and include its corresponding license file before describing this project as open source. Until then, the repository's license status should be treated as unspecified.

---

### 🚀 VoxGuard AI — Analyze the Signal. Explain the Findings. Verify Before You Trust.

*Built as a hackathon prototype exploring explainable audio analysis, software reliability, and safer voice-driven operations.*
