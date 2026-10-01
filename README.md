# 🌤️ NOAA Weather Radio Simulator

A Python-based simulation of NOAA Weather Radio broadcasts, 
featuring 300+ real stations across all 50 US states.

## 🎙️ Features

- **300+ NOAA stations** across all 50 US states
- **4 authentic SAPI voices:** Tom, Paul, Harry, Donna
- **Real local time** for every station (Arizona/Hawaii DST exception)
- **Priority-based alert system** (Emergency > Warning > Watch > Advisory > Statement)
- **Region-specific content:**
  - Marine forecast (coastal only)
  - Hazardous outlook (region + season based)
  - Hourly roundup with regional extra stations
- **Authentic 2010s format:**
  - 8-day zone forecast
  - Climate summary with normals and records
  - Varied sentence structures (no repetition)
- **EAS Details Channel:** scrolling ticker, 1050/853 Hz tone
- **5-language support:** English, Turkish, German, Spanish, French
- **Continuous broadcast loop** (manually started/stopped)

## 📥 Installation

```bash
pip install -r requirements.txt
python Main.py
