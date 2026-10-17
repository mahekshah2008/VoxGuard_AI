# VoxGuard AI 🎙️

**Explainable audio-quality screening to support safer decisions involving voice messages.**

VoxGuard AI is a lightweight Python and Streamlit prototype that analyses WAV recordings, extracts acoustic features, identifies audio-quality anomalies, and provides explainable findings and safety recommendations.

## 🚀 Features

- WAV audio upload and playback
- Audio validation and error handling
- Acoustic feature extraction
- Rule-based audio-quality analysis
- Display of measured features and triggered rules
- Qualitative findings and limitations
- Financial safety recommendations for sensitive instructions

## ⚙️ How It Works

1. **Upload:** The user uploads a WAV recording.
2. **Validate:** The application checks whether the file can be processed.
3. **Extract:** The detector calculates acoustic features, including RMS energy, peak amplitude, silence ratio, clipping ratio, zero-crossing rate, and spectral characteristics.
4. **Analyse:** Predefined rules evaluate selected audio characteristics.
5. **Explain:** The interface presents findings and relevant limitations.
6. **Verify:** For sensitive financial instructions, the application recommends independent verification through a trusted channel.

## 🛠️ Tech Stack

- Python
- Streamlit
- NumPy
- SciPy

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/mahekshah2008/VoxGuard_AI.git
cd VoxGuard_AI
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the application:

```bash
python -m streamlit run app.py
```

Open the local URL displayed in your terminal.

## 📁 Project Structure

```text
VoxGuard_AI/
├── app.py
├── detector.py
├── requirements.txt
├── test_detector.py
└── README.md
```

## 🧪 Testing

Run the unit tests with:

```bash
python -m unittest -v test_detector
```

The project has had 30 unit tests reported as passing. This indicates that the tested software behaviours passed; it does not establish voice-detection accuracy.

## ⚠️ Limitations

- This prototype uses rule-based acoustic analysis, not a trained deepfake classifier.
- Audio-quality anomalies do not prove that speech is AI-generated.
- Results are not a scientifically calibrated probability of authenticity.
- False positives and false negatives are possible.
- Performance has not been established through a representative, labelled voice-authenticity benchmark.

## 🔮 Future Improvements

- Evaluate suitable labelled genuine and synthetic speech datasets.
- Integrate and validate a suitable pretrained voice-spoofing detector.
- Evaluate performance on unseen speakers, synthesis methods, codecs, and recording conditions.
- Measure precision, recall, false-positive rate, false-negative rate, and ROC-AUC.
- Expand robustness testing and document reproducible results.

## 🔐 Safety Principle

**Never approve a sensitive financial transaction based on a voice recording alone.** Verify the request through an independently trusted channel and follow the relevant approval procedures.

---

Built as a hackathon prototype. VoxGuard AI supports human judgment; it does not establish forensic authenticity or authorize financial transactions.
