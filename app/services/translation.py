from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

LANGUAGE_CODES = {
    'spanish': 'es',
    'french': 'fr',
    'german': 'de',
    'italian': 'it',
    'portuguese': 'pt',
    'russian': 'ru',
    'japanese': 'ja',
    'korean': 'ko',
    'chinese': 'zh',
}

def translate_text(text: str, target_language: str) -> str:
    try:
        lang_code = LANGUAGE_CODES.get(target_language.lower(), target_language.lower())
        
        prompt = (
            f"Translate this text to {target_language} ({lang_code}).\n"
            f"Original text: {text}\n"
            "Translate directly without quotes or additional text."
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a translator. Respond with only the translation, no quotes, no explanations, no additional text."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        translated = response.choices[0].message.content.strip()
        # Remove any kind of quotes (single, double, or smart quotes)
        translated = translated.strip("'").strip('"').strip('"').strip('"')
        return translated

    except Exception as e:
        print(f"Translation error: {str(e)}")
        return f"Translation error: {text}"


async def detect_language(text: str) -> str:
    """
    Detect the language of the input text
    """
    try:
        prompt = f"What is the language of this text? Respond with only the ISO language code (e.g., 'en', 'es', 'fr'): {text}"
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a language detection expert. Respond only with language codes."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Language detection error: {str(e)}")
        return "en"  # Default to English if detection fails