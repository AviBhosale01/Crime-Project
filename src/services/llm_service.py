"""
Multi-Provider LLM Integration Service (Gemini, OpenAI, Groq, OpenRouter, NVIDIA NIM)
Text-to-SQL Engine and Intelligence Synthesis
"""
import re
from datetime import datetime
import pandas as pd
import database

def generate_sql_query(prompt_text: str, provider: str, model_name: str, api_key: str):
    """
    Generate a read-only SQLite query from natural language question.
    """
    now_dt = datetime.now()
    live_datetime_str = now_dt.strftime("%A, %d %B %Y, %I:%M:%S %p IST")
    live_date_iso = now_dt.strftime("%Y-%m-%d")

    sql_system = f"""You are an expert SQL assistant for a Crime Analytics platform in Pune, Maharashtra.
CURRENT REAL-TIME SYSTEM DATE: {live_date_iso} ({live_datetime_str}).
The database is SQLite. The schema has 4 tables:
1. districts (id, name, unemployment_rate, poverty_index, median_income, education_index, population_density, center_lat, center_lon)
2. suspects (id, name, age, gang_affiliation, priors_count, risk_score)
3. crimes (id, timestamp, district_id, crime_type, severity, latitude, longitude, status, suspect_id)
4. suspect_connections (suspect_a, suspect_b, relation_type, strength)

Your task is to translate the user's natural language question into a single valid SQLite SELECT query.
Return ONLY the SQL query inside a markdown code block starting with ```sql and ending with ```.
Do not write any explanation or intro/outro. Only SELECT queries are permitted.

If the question is a greeting, time/date query, general conversational message, or cannot be answered by querying the database, respond with exactly:
NO_SQL
"""
    extra_headers = {}
    if provider == "OpenRouter":
        extra_headers = {
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
            "X-Title": "Antigravity Crime Command Center"
        }

    response_text = ""
    if provider == "Gemini":
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name, system_instruction=sql_system)
        response_text = model.generate_content(prompt_text).text
    else:
        from openai import OpenAI
        base_urls = {
            "OpenAI": None,
            "OpenRouter": "https://openrouter.ai/api/v1",
            "Groq": "https://api.groq.com/openai/v1",
            "NVIDIA NIM": "https://integrate.api.nvidia.com/v1"
        }
        client = OpenAI(api_key=api_key, base_url=base_urls.get(provider))
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": sql_system},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.0,
            extra_headers=extra_headers
        )
        response_text = resp.choices[0].message.content

    response_text = response_text.strip()
    if "NO_SQL" in response_text:
        return None

    # Robust regex extraction of SQL inside ```sql ... ``` or ``` ... ``` code blocks
    code_block_match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", response_text, re.IGNORECASE)
    if code_block_match:
        sql_query = code_block_match.group(1).strip()
    else:
        # Fallback: Find where SELECT or WITH begins
        select_match = re.search(r"(SELECT[\s\S]*|WITH[\s\S]*)", response_text, re.IGNORECASE)
        if select_match:
            sql_query = select_match.group(1).strip()
        else:
            sql_query = response_text

    # Clean any trailing markdown or quotes
    sql_query = sql_query.strip("` \n\r;") + ";"

    # Self-healing if first character 'S' was somehow dropped by model or prefix
    if sql_query.upper().startswith("ELECT "):
        sql_query = "S" + sql_query

    return sql_query

def execute_safe_query(sql_query: str):
    """
    Safely execute a read-only SQL query against the SQLite database.
    """
    if not sql_query or sql_query == "NO_SQL":
        return None, None, None

    cleaned_sql = sql_query.upper().strip()
    forbidden_words = ["DROP ", "DELETE ", "UPDATE ", "INSERT ", "ALTER ", "TRUNCATE ", "CREATE ", "REPLACE "]
    if any(w in cleaned_sql for w in forbidden_words) or not (cleaned_sql.startswith("SELECT") or cleaned_sql.startswith("WITH")):
        return None, None, "Security Policy Error: Non-read-only query blocked."

    try:
        conn = database.get_connection()
        df_result = pd.read_sql_query(sql_query, conn)
        conn.close()
        query_df_json = df_result.to_json(orient="records")
        return df_result, query_df_json, None
    except Exception as e:
        return None, None, str(e)

def synthesize_briefing(prompt_text: str, sql_query: str, query_df_json: str, sql_error: str, provider: str, model_name: str, api_key: str):
    """
    Synthesize natural language intelligence response from database results.
    """
    now_dt = datetime.now()
    live_datetime_str = now_dt.strftime("%A, %d %B %Y, %I:%M:%S %p IST")
    live_date_iso = now_dt.strftime("%Y-%m-%d")

    explain_system = f"""You are the AI Intelligence Briefing Officer for Pune Police Command Center.
CURRENT REAL-TIME SYSTEM CLOCK: {live_datetime_str} (Date: {live_date_iso}).
IMPORTANT INSTRUCTION ON TIME/DATE: You HAVE direct access to the live system clock ({live_datetime_str}). If the user asks for today's date, current time, or live system status, state the exact date and time immediately and accurately. NEVER say "I do not have access to real-time system clocks".

Interpret database results clearly and professionally for police commanders.
Keep responses concise, factual, and formatted with clean Markdown bullet points. Refer to Pune, Maharashtra context.
"""
    prompt = f"User Question: {prompt_text}\n\n"
    if sql_query:
        prompt += f"Executed SQL Query:\n{sql_query}\n\n"
        if sql_error:
            prompt += f"SQL Error:\n{sql_error}\n\n"
        else:
            prompt += f"Raw DB Results:\n{query_df_json}\n\n"
    else:
        prompt += "(No SQL query was run for this request.)\n\n"

    extra_headers = {}
    if provider == "OpenRouter":
        extra_headers = {
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
            "X-Title": "Antigravity Crime Command Center"
        }

    final_answer = ""
    if provider == "Gemini":
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model2 = genai.GenerativeModel(model_name, system_instruction=explain_system)
        final_answer = model2.generate_content(prompt).text
    else:
        from openai import OpenAI
        base_urls = {
            "OpenAI": None,
            "OpenRouter": "https://openrouter.ai/api/v1",
            "Groq": "https://api.groq.com/openai/v1",
            "NVIDIA NIM": "https://integrate.api.nvidia.com/v1"
        }
        client = OpenAI(api_key=api_key, base_url=base_urls.get(provider))
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": explain_system},
                {"role": "user", "content": prompt}
            ],
            extra_headers=extra_headers
        )
        final_answer = resp.choices[0].message.content

    return final_answer
