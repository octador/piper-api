import subprocess
import uuid
import os
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, constr

# --- NOUVEAU : Définition des voix disponibles ---
# On utilise une Enum pour que FastAPI puisse valider automatiquement
# que la voix demandée fait partie de cette liste. C'est très propre !
class VoiceName(str, Enum):
    siwis = "siwis"
    upmc = "upmc"
    tom = "tom"

# --- MODIFIÉ : Le modèle de requête accepte maintenant une voix ---
class TTSRequest(BaseModel):
    text: constr(min_length=1, max_length=1000)
    # Le champ 'voice' est optionnel. S'il n'est pas fourni,
    # on utilisera la voix par défaut 'siwis'.
    voice: VoiceName = VoiceName.siwis

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API Piper TTS est en ligne. Plusieurs voix sont disponibles."}

# --- MODIFIÉ : La logique de la fonction principale ---
@app.post("/tts")
def text_to_speech(request: TTSRequest):
    output_filename = f"{uuid.uuid4()}.wav"
    output_path = f"/tmp/{output_filename}"

    # --- Logique de sélection de la voix ---
    # On construit le nom du fichier modèle à partir de la voix choisie.
    # request.voice.value nous donne la chaîne de caractères ("siwis", "tom", etc.)
    voice_model_name = f"fr_FR-{request.voice.value}-medium.onnx"
    model_path = f"/models/{voice_model_name}"

    # --- Sécurité : Vérification de l'existence du fichier ---
    # Même si l'Enum valide l'entrée, cette vérification garantit que le fichier
    # a bien été copié dans l'image Docker. C'est une double sécurité.
    if not os.path.exists(model_path):
        # Cette erreur ne devrait jamais se produire si le Dockerfile est correct,
        # mais c'est une bonne pratique de la prévoir.
        raise HTTPException(
            status_code=500,
            detail=f"Fichier modèle non trouvé sur le serveur pour la voix '{request.voice.value}'. Contactez l'administrateur."
        )

    command = [
        "piper",
        "--model", model_path,
        "--output_file", output_path
    ]

    try:
        process = subprocess.run(
            command,
            input=request.text,
            encoding='utf-8',
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        error_message_from_piper = e.stderr.strip()
        print(f"Erreur interne lors de l'appel à Piper: {error_message_from_piper}")
        raise HTTPException(
            status_code=503,
            detail=f"Le service de synthèse vocale a rencontré une erreur. Détail: {error_message_from_piper}"
        )
    except Exception as e:
        print(f"Une erreur inattendue est survenue: {e}")
        raise HTTPException(
            status_code=500,
            detail="Une erreur inattendue est survenue sur le serveur."
        )

    return FileResponse(path=output_path, media_type="audio/wav", filename="output.wav")