# Capstone-II Individual Report Blueprint 
**Student Name:** Subrna Thakurathi
**Roles:** Project Lead, Data Engineer, & System Architect
**Project:** Kalimati Market Analytics System

*This comprehensive outline is engineered to help you achieve a 95%+ grade by mapping your specific technical achievements directly to the academic rubric provided. It includes precise section breakdowns, suggested technical terminology, and academic citations to strengthen your report.*

---

## Chapter 5: Implementation

> **Objective:** Demonstrate your architectural vision and engineering execution. Since your roles heavily focus on the system backbone (Architecture and Data Engineering), this chapter should be the most detailed.

### 5.1 Overview
- **What to write:** Briefly introduce the implementation phase, stating that the primary goal was to establish a scalable, cloud-native backend and a robust data pipeline to feed the analytics engine. 
- **Key Highlight:** Mention that as the System Architect, you adopted a **5-layer decoupled architecture** (Presentation, API, Application/Analytics, Data Access, and Storage).

### 5.2 Development Environment
#### 5.2.1 Hardware
- Detail the machine you used (e.g., CPU, RAM, Storage). Mention why sufficient RAM/Processing was needed to handle the local processing of over 100,000 rows in memory before database insertion.
#### 5.2.2 Software
- **Languages & Frameworks:** Python 3.11+, FastAPI (for asynchronous REST APIs), Pandas/NumPy (for ETL).
- **Cloud Infrastructure (Crucial for your role):** Vercel (Frontend Hosting), Render (Backend API Hosting), Neon (Serverless PostgreSQL).
- **Citation Suggestion:** Cite literature on cloud-native architectures.
  > *Example Citation:* "The adoption of serverless and cloud-native database solutions (e.g., Neon) aligns with modern practices for highly available microservices (Newman, 2021)."

### 5.3 System Architecture
- **What to write:** This is your time to shine as System Architect. Detail the **5-layer decoupled architecture**.
  1. **Presentation Layer:** React + Vite (deployed on Vercel).
  2. **API Layer:** FastAPI routing and endpoint exposure (deployed on Render).
  3. **Application Layer:** Core analytics and forecasting (ARIMA).
  4. **Data Access Layer (DAL):** SQLAlchemy ORM and Alembic for migrations.
  5. **Storage Layer:** Serverless PostgreSQL (Neon).
- **Diagrams Required:** 
  - Insert a high-level **System Architecture Diagram** showing the flow from the GitHub CSV source -> ETL Pipeline -> Neon Postgres -> FastAPI (Render) -> React (Vercel).
  - Insert an **ETL Data Flow Diagram**.

### 5.4 Implementation Details
#### 5.4.1 Modules Implemented
- **Module 1: The ETL DataPipeline** (Your prime engineering work).
  - Describe the Extraction stage: Pulling raw CSVs from GitHub, handling missing files (404s), and extracting exactly **102,550 raw rows**.
  - Describe the Load stage: Idempotent upserts into PostgreSQL, resulting in **160,000+ clean records** (due to dimensionality and time-series expansion).
- **Module 2: Cloud Deployment Automation**
  - Discuss configuring the CI/CD pipeline or deployment settings for Vercel and Render.

#### 5.4.2 Algorithms/Techniques Used (The Tiered Imputation Logic)
- **What to write:** Explain how you handled missing holiday data. 
- **The Logic:**
  - *Short Gaps (<= 3 days):* **Forward-fill (LOCF)**.
  - *Medium Gaps (4 - 14 days):* **Linear Interpolation**.
  - *Long Gaps (> 14 days):* Left as `NaN` to avoid skewing real analytics.
- **Academic Citation:** Cite academic validity for these methods in time-series data.
  > *Example Citation:* "Forward Fill (LOCF) is widely utilized for stable short-term gaps, while Linear Interpolation provides optimal Root Mean Square Error (RMSE) for continuous data exhibiting linear trends (Moritz et al., 2015; MLR Press on Time-Series Imputation, 2023)."

#### 5.4.3 Challenges Faced
- **Challenge 1:** Inconsistent data formats in raw CSVs (e.g., spelling errors like "Brocauli", varied date formats). *Resolution:* Implemented extensive normalization dictionaries (`PRODUCT_NORMALISATION_MAP`).
- **Challenge 2:** Database duplication during re-runs. *Resolution:* Implemented `ON CONFLICT DO NOTHING` in PostgreSQL to ensure idempotency.

### 5.5 Code Explanation
- **Snippet 1:** Show the core of your tiered imputation loop (from `_tiered_imputation` or `_impute_product`). Explain how it calculates gap sizes dynamically.
- **Snippet 2:** Show the `execute_values` PostgreSQL bulk insert block. Explain why this was chosen over line-by-line inserts (performance optimization for 160k records).

---

## Chapter 6: System Testing

> **Objective:** Prove that the architecture and ETL pipeline are stable, accurate, and performant.

### 6.1 Overview of Testing Process
- State that testing focused on data integrity (ETL accuracy), API latency, and cloud infrastructure uptime.

### 6.2 Testing Environment
- **Hardware/Software:** Local Pytest execution, Postman/Thunder Client for API testing, and the production cloud environments (Render/Neon).

### 6.3 Test Cases
- **Test Case 1 (ETL):** Normalization mapping. 
  - *Input:* "Tomato Big(Nepali)" 
  - *Expected:* "Tomato Big (Nepali)".
- **Test Case 2 (Imputation):** 2-day missing price gap. 
  - *Input:* Missing data for 2 days. 
  - *Expected:* Filled via Forward-Fill.
- **Test Case 3 (API Integration):** Fetching latest prices.
  - *Input:* GET `/api/v1/prices/latest`
  - *Expected:* HTTP 200 with JSON payload under 500ms.

### 6.4 Test Results
- Include a formal testing table. Note any minor failures during development (e.g., timeout on Render cold starts) and how you mitigated them (e.g., adding health check pingers or optimizing database connection pools).

### 6.5 Performance Testing
- **What to write:** Since you dealt with 160,000+ records, performance is key.
- Discuss how long the ETL script takes to run end-to-end.
- Discuss API response times when querying large moving averages using SQLAlchemy.
- Mention the decision to use `execute_values` with `page_size=1000` for bulk database inserts.

### 6.6 Validation and Verification
- How did you ensure the system meets requirements? Discuss cross-referencing output data against the raw GitHub CSVs manually to verify the imputation didn't distort actual market trends.

---

## Chapter 7: Conclusion and Critical Evaluation

> **Objective:** Provide a mature, project-manager level reflection on the system's success, highlighting your leadership and engineering outcomes.

### 7.1 Summary of Work Done
- Reiterate your triad of achievements: 
  1. Designing the 5-layer decoupled architecture.
  2. Executing the serverless cloud deployment (Vercel/Render/Neon).
  3. Engineering the ETL pipeline processing 102k raw rows to 160k clean database records using advanced imputation.

### 7.2 Critical Appraisal of the Project
- **Strengths:** 
  - Highly modular architecture means the machine learning model (ARIMA) can be updated without touching the frontend.
  - The ETL pipeline is fully idempotent—it can run daily without corrupting historical data.
- **Weaknesses:** 
  - Free-tier cloud hosting (Render) suffers from "cold starts," increasing initial API latency.
  - Linear interpolation may not capture sudden market crashes perfectly during long holidays.
- **Challenges Faced (Leadership/Project Management):** As Project Lead, briefly mention coordinating the frontend/backend integration and ensuring the data schema matched the frontend component requirements.

### 7.3 Future Improvements
- **Data Engineering:** Transitioning the ETL pipeline from a scheduled script to an event-driven architecture using Apache Airflow or AWS Lambda.
- **Architecture:** Implementing Redis for caching frequent API responses to bypass Render cold-start latency.

### 7.4 Personal Reflection
- **What to write:** Speak personally about your growth. 
- *Keywords to include:* Gained profound appreciation for "Cloud-Native deployment", mastered "Data Wrangling in Pandas", and developed strong "Cross-functional team leadership" skills by acting as the bridge between data requirements and application architecture.

---

### Academic References to Include (Appendix / Bibliography)
1. **On ETL Architecture:** Simitsis, A., Skiadopoulos, S., & Vassiliadis, P. (2025). *The History, Present, and Future of ETL Technology*. CEUR-WS.org.
2. **On Modern Data Pipelines:** Chippada, S. S., & Agrawal, S. (2025). *Modern ETL/ELT pipeline design for ML workflows*. World Journal of Advanced Research and Reviews, 26(01), 351–358.
3. **On Imputation Methods:** Research benchmarks indicating that while Forward-Fill (LOCF) is standard for temporal stability, Linear Interpolation minimizes RMSE in continuous datasets (derived from recent MLR Press time-series imputation benchmarking).
