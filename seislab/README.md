<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:020818,40:061428,100:0a2040&height=200&section=header&text=SeisLab&fontSize=90&fontColor=38bdf8&fontAlignY=42&desc=Seismic%20Analysis%20%26%20Attribute%20Extraction%20Toolkit&descAlignY=64&descColor=4a7090&animation=fadeIn&fontFamily=Trebuchet+MS" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-11557c?style=for-the-badge)](https://matplotlib.org)
[![License](https://img.shields.io/badge/License-MIT-f0c040?style=for-the-badge)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-In_Development-f87171?style=for-the-badge)]()

<br/>

> *A personal project in active development — building a seismic data visualization and attribute analysis tool from the ground up as part of my Applied Geophysics journey at IIT (ISM) Dhanbad.*

<br/>

</div>

---

<br/>

## 🔭 &nbsp; About This Project

**SeisLab** is a Python-based seismic data visualization and attribute extraction toolkit that I am building as part of my learning in Applied Geophysics. The goal is to create an interactive desktop application that can load seismic data, display it visually, and compute common seismic attributes used in exploration workflows.

This is a **first-build, work-in-progress** — I am learning and improving it continuously.

<br/>

---

## ✨ &nbsp; Current Features

<br/>

### 🖥️ &nbsp; GUI (PyQt5)
- Basic desktop application layout
- Modular tab-based interface
- Seismic viewer panel with matplotlib integration
- Attribute selection and basic statistics panel

### 📊 &nbsp; Seismic Attribute Computation
Currently implemented attributes:

| Attribute | Description |
|:---|:---|
| **RMS Amplitude** | Root-mean-square energy of the seismic trace |
| **Instantaneous Amplitude** | Envelope of the analytic signal |
| **Instantaneous Phase** | Phase of the analytic signal |
| **Instantaneous Frequency** | Time derivative of instantaneous phase |

### 📁 &nbsp; Data Handling
- Synthetic seismic data generation for testing
- NumPy array-based internal data representation
- SEG-Y file support *(planned — in progress)*

<br/>

---

## 🛠️ &nbsp; Tech Stack

<br/>

| Technology | Purpose |
|:---|:---|
| `Python 3.9+` | Core language |
| `PyQt5` | Desktop GUI framework |
| `Matplotlib` | Seismic data visualization |
| `NumPy` | Numerical computation & attribute algorithms |
| `Pandas` | Data handling and tabular output |
| `segyio` *(planned)* | SEG-Y file reading |
| `CuPy` *(planned)* | GPU acceleration for large datasets |

<br/>

---

## 📂 &nbsp; Project Structure

```
SeisLab/
│
├── main.py                  ← Launch the application
│
├── gui/
│   ├── main_window.py       ← Main window layout
│   ├── seismic_viewer.py    ← Seismic display widget
│   └── stats_tab.py         ← Statistics panel
│
├── core/
│   ├── seismic_loader.py    ← Data loading logic
│   └── attributes.py        ← Attribute computation
│
├── assets/
│   └── seislab.png          ← App icon
│
└── README.md
```

<br/>

---

## 🚀 &nbsp; Getting Started

<br/>

**1. Clone the repository**
```bash
git clone https://github.com/ashraf-iit-ism/seislab.git
cd seislab
```

**2. Install dependencies**
```bash
pip install numpy pandas matplotlib pyqt5
```

**3. Run the application**
```bash
python main.py
```

<br/>

---

## 🗺️ &nbsp; Roadmap

What I am planning to build next:

```
  ✅  Core GUI layout (PyQt5)
  ✅  Basic seismic attribute computation
  ✅  Matplotlib seismic viewer

  🔧  SEG-Y file loader (in progress)
  🔲  2D seismic section viewer
  🔲  More seismic attributes
  🔲  Seismic attribute maps
  🔲  Well log integration
  🔲  Machine learning — facies classification
  🔲  GPU acceleration (CuPy)
  🔲  Export to PNG / PDF
```

<br/>

---

## 👤 &nbsp; Author

<br/>

<div align="center">

### Md Ashraf

**M.Sc (Tech) Applied Geophysics**
*Indian Institute of Technology (ISM) Dhanbad*

<br/>

`Geophysical Data Analysis` &nbsp;·&nbsp; `Seismic Interpretation` &nbsp;·&nbsp; `Python` &nbsp;·&nbsp; `ML in Geoscience`

<br/>

[![GitHub](https://img.shields.io/badge/GitHub-ashraf--iit--ism-181717?style=for-the-badge&logo=github)](https://github.com/ashraf-iit-ism)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit_Site-0a66c2?style=for-the-badge&logo=google-chrome&logoColor=white)](https://your-portfolio-link.com)

</div>

<br/>

---

## 📄 &nbsp; License

Released under the **MIT License** — see [`LICENSE`](./LICENSE) for details.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0a2040,50:061428,100:020818&height=100&section=footer" width="100%"/>

<br/>

*Built from scratch · Learning in public · IIT (ISM) Dhanbad*

</div>
