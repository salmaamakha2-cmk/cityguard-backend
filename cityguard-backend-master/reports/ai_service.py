import json
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ── Configure Gemini ─────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None
    print("WARNING: GEMINI_API_KEY not found. AI features will use fallback/mock mode.")

MODEL = "gemini-2.5-flash"



# ── 1. Analyze Report Text ───────────────────────────────────────────
def analyze_report_text(title: str, description: str, language: str = 'fr') -> dict:
    prompt = f"""
You are an AI assistant for CityGuard, an urban problem reporting platform in Morocco.
Analyze the following citizen report and respond ONLY with a valid JSON object.

Report Title: {title}
Report Description: {description}
Language: {language}

Return ONLY this JSON (no explanation, no markdown, no extra text):
{{
    "category": "<one of: pothole, lighting, waste, water, other>",
    "severity": "<one of: low, medium, high>",
    "is_critical": <true or false>,
    "is_urgent": <true or false>,
    "suggested_title": "<a clear professional title in the same language as the report>",
    "improved_description": "<a clear structured description for the municipal administration, in the same language>",
    "summary": "<a short 1-sentence summary for the admin dashboard, in the same language>",
    "confidence_score": <float between 0.0 and 1.0>
}}

Rules:
- severity = "high" if dangerous (accident risk, major water leak, blocked road)
- severity = "medium" if important but not immediately dangerous
- severity = "low" if minor inconvenience
- is_critical = true if severity is high OR immediate danger
- is_urgent = true if words like: danger, accident, bloque, fuite importante, urgence
- suggested_title: improve only if original is too short or unclear
- improved_description: reformulate clearly and professionally
- Respond in the same language as the report (French, Arabic, or English)
"""
    if not client:
        return _fallback_text_analysis(title, description, "AI Client not initialized (missing API key)")
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        text = re.sub(r'```json|```', '', response.text).strip()
        result = json.loads(text)
        required = ['category', 'severity', 'is_critical', 'is_urgent',
                    'suggested_title', 'improved_description', 'summary', 'confidence_score']
        for field in required:
            if field not in result:
                result[field] = _default_value(field)
        result['model'] = MODEL
        result['status'] = 'analyzed'
        return result
    except Exception as e:
        return _fallback_text_analysis(title, description, str(e))


# ── 2. Analyze Report Image ──────────────────────────────────────────
def analyze_report_image(image_url: str = None, use_real_model: bool = False) -> dict:
    if not use_real_model or not image_url:
        return _mock_image_analysis()
    if not client:
        return _mock_image_analysis(error="AI Client not initialized (missing API key)")
    try:
        import httpx
        image_data = httpx.get(image_url).content
        prompt = """Analyze this urban problem image for CityGuard platform.
Respond ONLY with valid JSON (no markdown):
{"detected_problem": "...", "category": "pothole|lighting|waste|water|other",
 "severity": "low|medium|high", "is_critical": false, "description": "...", "confidence_score": 0.0}"""
        response = client.models.generate_content(
            model=MODEL,
            contents=[types.Part.from_bytes(data=image_data, mime_type="image/jpeg"), prompt]
        )
        text = re.sub(r'```json|```', '', response.text).strip()
        result = json.loads(text)
        result['model'] = MODEL
        result['status'] = 'analyzed'
        return result
    except Exception as e:
        return _mock_image_analysis(error=str(e))


# ── 3. Chatbot ───────────────────────────────────────────────────────
def chatbot_response(user_message: str, conversation_history: list = None, language: str = 'fr') -> dict:
    system_prompt = """You are CityGuard Assistant, a helpful chatbot for an urban problem reporting platform in Morocco.
Help citizens create reports, choose categories, and understand the platform.
Categories: pothole, lighting, waste, water, other.
Always respond in the same language as the user (French, Arabic, Darija, or English).
Be friendly, professional, and concise."""
    if not client:
        return {'response': _fallback_chatbot_response(language), 'status': 'fallback', 'error': 'AI Client not initialized'}
    try:
        contents = [system_prompt + "\n\n"]
        for h in (conversation_history or []):
            parts = h.get('parts', [''])
            contents.append(parts[0])
        contents.append(user_message)
        full_prompt = "\n".join(contents)
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
        )
        return {'response': response.text, 'status': 'success', 'model': MODEL}
    except Exception as e:
        return {'response': _fallback_chatbot_response(language), 'status': 'fallback', 'error': str(e)}
# ── 4. Full Report Analysis (text + image) ───────────────────────────
def analyze_full_report(title: str, description: str, image_url: str = None, language: str = 'fr') -> dict:
    text_result = analyze_report_text(title, description, language)
    if image_url:
        image_result = analyze_report_image(image_url, use_real_model=True)
        severity_rank = {'low': 1, 'medium': 2, 'high': 3}
        if severity_rank.get(image_result.get('severity', 'low'), 1) > severity_rank.get(text_result.get('severity', 'low'), 1):
            text_result['severity'] = image_result.get('severity')
            text_result['is_critical'] = image_result.get('is_critical', text_result['is_critical'])
        text_result['image_analysis'] = image_result
    return text_result


# ── Helpers ──────────────────────────────────────────────────────────
def _default_value(field):
    return {'category': 'other', 'severity': 'low', 'is_critical': False, 'is_urgent': False,
            'suggested_title': '', 'improved_description': '', 'summary': '', 'confidence_score': 0.5}.get(field)


def _fallback_text_analysis(title, description, error=''):
    text = (title + ' ' + description).lower()
    category = 'other'
    for cat, kws in {'pothole': ['trou', 'nid', 'route'], 'lighting': ['lumiere', 'lampe', 'eclairage'],
                     'waste': ['dechet', 'poubelle', 'ordure'], 'water': ['eau', 'fuite', 'leak']}.items():
        if any(k in text for k in kws):
            category = cat
            break
    is_critical = any(w in text for w in ['danger', 'urgent', 'accident', 'bloque'])
    severity = 'high' if is_critical else 'medium' if len(description) > 50 else 'low'
    return {'category': category, 'severity': severity, 'is_critical': is_critical, 'is_urgent': is_critical,
            'suggested_title': title, 'improved_description': description,
            'summary': f"Signalement {category} — gravité {severity}.",
            'confidence_score': 0.6, 'model': 'fallback', 'status': 'fallback', 'error': error}


def _mock_image_analysis(error=''):
    import random
    return {'detected_problem': 'Urban problem detected (mock mode)',
            'category': random.choice(['pothole', 'waste', 'lighting', 'water', 'other']),
            'severity': random.choice(['low', 'medium', 'high']),
            'is_critical': False, 'description': 'Mock mode — real model not activated.',
            'confidence_score': round(random.uniform(0.6, 0.95), 2),
            'model': 'mock', 'status': 'mock', 'error': error}


def _fallback_chatbot_response(language='fr'):
    return {'fr': "Je suis désolé, difficulté technique. Veuillez réessayer.",
            'ar': "عذراً، مشكلة تقنية. يرجى المحاولة مرة أخرى.",
            'en': "Sorry, technical issue. Please try again."}.get(language, "Veuillez réessayer.")