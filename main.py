from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import List
import psycopg2
import os
import uvicorn

# -----------------------------
# Database connection info from environment variables
# -----------------------------
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="Festival Lookup API")

# -----------------------------
# DB connection helper
# -----------------------------
def get_db_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# -----------------------------
# Home page with HTML form
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>Festival Lookup</title>
        </head>
        <body style="font-family: Arial; margin: 40px;">
            <h2>🎉 Festival Lookup</h2>
            <form action="/festivals/" method="get">
                <label for="holidaydate">Enter date (YYYY-MM-DD):</label><br><br>
                <input type="text" id="holidaydate" name="holidaydate" placeholder="e.g., 2025-12-25" required>
                <br><br>
                <label for="district">Enter district name:</label><br><br>
                <input type="text" id="district" name="district" placeholder="e.g., Nellore" required>
                <br><br>
                <button type="submit" style="padding: 5px 15px;">Get Festivals</button>
            </form>
            <p>Example: <code>/festivals/?holidaydate=2025-12-25&district=Nellore</code></p>
        </body>
    </html>
    """

# -----------------------------
# API endpoint - fetch festivals based on date & district
# -----------------------------
@app.get("/festivals/", response_model=List[str])
def get_festivals(
    holidaydate: str = Query(..., description="Holiday date in YYYY-MM-DD format"),
    district: str = Query(..., description="District name")
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Distinct festivals, case-insensitive, include national holidays
        query = """
        SELECT DISTINCT f.holidayname
        FROM festival f
        JOIN india_districts d 
            ON LOWER(TRIM(f.state_name)) = LOWER(TRIM(d.state_name))
               OR LOWER(TRIM(f.state_name)) = 'all india'
        WHERE f.holidaydate = %s
          AND LOWER(TRIM(d.district_name)) = LOWER(TRIM(%s))
        ORDER BY f.holidayname
        """
        cur.execute(query, (holidaydate.strip(), district.strip()))
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    if not rows:
        raise HTTPException(status_code=404, detail="No festivals found for the given date/district")

    festival_names = [row[0] for row in rows]
    return festival_names

# -----------------------------
# Run as Python script
# -----------------------------
if __name__ == "__main__":
    # Use port from Render environment variable or default 8000 locally
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
