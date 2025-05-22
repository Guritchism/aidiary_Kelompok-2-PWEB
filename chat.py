import google.generativeai as genai
from typing import Tuple, Any # For type hints, using built-in list and dict
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Konfigurasi API Gemini
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set or not found in .env file.")

genai.configure(api_key=API_KEY) # Correct way to configure the SDK

# Default generation config for the model
DEFAULT_GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 2048,
}

# System Instruction (Prompt Sistem)
SYSTEM_INSTRUCTION = """Anda adalah seorang terapis berpengalaman yang berdedikasi untuk membantu mahasiswa mengatasi tekanan akademik. Dengan keahlian dalam mendengarkan secara empatik dan memberikan dukungan yang penuh pengertian, Anda membantu mereka menemukan keseimbangan emosional dan mencegah burnout, sehingga mereka dapat mencapai potensi penuh mereka secara akademik dan pribadi. Anda juga memiliki kemampuan mendeteksi ekspresi emosi melalui emoji, dan secara otomatis memberikan tanggapan yang menenangkan dan relevan berdasarkan ekspresi tersebut. 

Ketika mahasiswa mengetik emoji tertentu, Anda langsung merespons dengan dukungan seperti berikut:
😢 → Jangan sedih ya, aku di sini untuk membantu 😊
😎 → Keren banget kamu! Terus semangat 😎
☺️ → Senangnya melihat kamu bahagia! Tetap tersenyum ya 😊
😁 → Wah, kamu kelihatan ceria banget! 😄
🙄 → Kalau ada yang bikin kesal, ceritain aja ya... Aku dengar kok 🙏
😡 → Waduh, kamu marah ya? Yuk tarik napas dulu, kita selesaikan bareng 😌

Anda tidak hanya merespons berdasarkan kata, tetapi juga memahami konteks emosional yang tersirat dalam simbol-simbol kecil itu. Tujuan Anda adalah menjadi teman digital yang suportif, yang hadir setiap saat mahasiswa merasa tertekan, lelah, atau bahkan hanya ingin dihargai dan didengar."""

MODEL_NAME = 'gemini-1.5-flash-latest' # Using a current model name

# Type alias for the chat history structure expected by the API
# Each item is a dict: {'role': 'user'/'model', 'parts': [{'text': '...'}]}
ApiChatHistoryType = list[dict[str, Any]]

def gemini_create(prompt: str, history_for_api: ApiChatHistoryType) -> str:
    try:
        model = genai.GenerativeModel(
            MODEL_NAME,
            system_instruction=SYSTEM_INSTRUCTION,
            generation_config=DEFAULT_GENERATION_CONFIG
        )
        
        current_conversation_content: ApiChatHistoryType = history_for_api + [
            {'role': 'user', 'parts': [{'text': prompt}]}
        ]
        
        response = model.generate_content(
            contents=current_conversation_content
        )
        return response.text
    except Exception as e:
        print(f"Debug - Error detail in gemini_create: {type(e).__name__} - {str(e)}")
        detailed_error_message = str(e)
        if hasattr(e, 'message') and e.message: # type: ignore
            detailed_error_message = e.message # type: ignore
        return f"Maaf, terjadi kesalahan dalam berkomunikasi dengan AI: {detailed_error_message}"

def conversation_history(
    user_input: str, 
    history_tuples: list[Tuple[str, str]] 
) -> Tuple[list[Tuple[str, str]], list[Tuple[str, str]]]:
    
    processed_history_tuples = list(history_tuples or [])
    
    MAX_TURNS = 10 
    if len(processed_history_tuples) > MAX_TURNS:
        processed_history_tuples = processed_history_tuples[-MAX_TURNS:]
    
    api_formatted_history: ApiChatHistoryType = []
    for user_msg, model_msg in processed_history_tuples:
        api_formatted_history.append({'role': 'user', 'parts': [{'text': user_msg}]})
        api_formatted_history.append({'role': 'model', 'parts': [{'text': model_msg}]})
        
    response_text = gemini_create(user_input, api_formatted_history)

    if not response_text.startswith("Maaf, terjadi kesalahan"):
        processed_history_tuples.append((user_input, response_text))
    
    return processed_history_tuples, processed_history_tuples

