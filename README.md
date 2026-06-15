# Chanua Chess ♟️

An interactive data-driven dashboard designed to parse, analyze, and transform thousands of fast-paced online chess games into beautiful, insights-rich scoresheets and performance metrics. 

---

## 🚀 Architecture & Tech Stack

Chanua Chess uses a modern, decoupled client-server architecture built entirely with Python ecosystems:

*   **Frontend UI:** Built with **Streamlit** for a reactive, state-managed analytics interface. Deployed seamlessly via **Streamlit Community Cloud**.
*   **Backend API:** High-performance REST API built with **FastAPI** to process heavy validation logic, PGN extraction, and computational tasks. 
*   **Production Hosting:** Containerized via a custom **Dockerfile** and hosted on **Hugging Face Spaces** (providing high-compute CPU environments entirely serverless).
*   **Database:** Cloud-hosted **MongoDB Atlas** for persistent storage of game histories, historical trends, and metadata records.

