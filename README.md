# Snowflake Summit Demo - Air Quality Analysis

## Overview
This project analyzes historical air quality data across United States avaialable via the [Snowflake marketplace](https://app.snowflake.com/marketplace/listing/GZSTZL7M0KK/snowflake-virtual-hands-on-labs-air-quality-data-united-states?lang=j), focusing on various pollutants and atmospheric parameters. The purpose is to highlight the use of `querychat` as an innovative and intuitive way to interact safely with SQL powered dashboards using natural language. Ultimately, the expectation is that `querychat` enables the following workflow:
  - A user connects to the dashboard and begins submitting natural language requests to the chat interface
  - The chat interface itself is powered by Claude 3.5 via Snowflake Cortex
  - The result of a chat interaction is SQL that is executed against a Snowflake table to filter the data based on the natural language query
  - The dashboard updates to reflect the filtered data

This sort of workflow enables natural language interaction with data **without** requiring a foundational LLM to interpret raw data. Instead, the LLM is only used for creating SQL to respond to filtering and aggregation reguests. The SQL is auditable and, most importantly, does not require the LLM to be exposed to any of the actual data. Once the data has been filtered, the rest of the dashboard reflects the filtered data. Effectively, many UI controls can be replaced with a single chat panel. 

**In this specific example, both the underlying LLM and the SQL execution are powered by Snowflake.**

## Data Description
The data includes aggregations of observed air quality measurements from various observations sites across the United States from 1980-2000. The dataset includes many features, but the main feature is `PARAMETERNAME`, which contains unique parameters measured including:
  - Total Suspended Particles (TSP)
  - Various metals in TSP (Lead, Chromium, Arsenic, etc.)
  - PM10 measurements
  - Volatile Organic Compounds (Benzene, Toluene, etc.)
  - Atmospheric conditions (Temperature, Pressure)

These values were measured over a 24 period of time and then columns like `ARITHMETICMEAN` contain the average value of the resulting data collection. The data is not very granular and specific dates of collection are not included, but this still provides a valid base for rudimentary analysis of air quality by location and over 

## Dashboard
Eventually, two dashboards will be included in this repository: one writted in Shiny for R, the other in Shiny for Python. For now, a single dashbard writtin in Shiny for Python is found at [`dashboard/python/app.py`](dashboard/python/app.py). A virtualenvironment is created using the modules described in [`requirements.txt`](requirements.txt).