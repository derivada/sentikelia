from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
from gpt import chat_interaction, generate_diary_summary
from analisis_sentimental import classify_enneagram, classify_big5
from mongo_client import mongo_client
from datetime import date
from model import *
app = FastAPI()

# Config de CORS
origins = [
    "http://localhost:3000",  # React app URL
    "http://localhost:8000",  # Add your backend URL here if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


#########################################
###########       RUTAS       ###########
#########################################

# Ruta de login
@app.post("/login/")
async def login(req: RequestWithUsername):
    if mongo_client.get_user(req.username) is not None:
        return JSONResponse(content={"message": "true"})
    else:
        return JSONResponse(content={"message": "false"})

# Ruta de nuevo mensaje de chat
@app.post("/chats/")
async def send_chat_message(chat_req: ChatRequest):
    gpt_response = chat_interaction(chat_req)
    return JSONResponse(content={"message": gpt_response})

# Ruta de formulario de registro
@app.post("/loginform/")
async def login_form(user_data: UserData):
    # solo puede fallar si el usuario ya existe
    if mongo_client.insertar_usuario_inicial(user_data) is not None:
        return JSONResponse(content={"message" : "true"})
    else:
        return JSONResponse(content={"message" : "false"})

# Nueva entrada en el diario, argumentos to be decided (imagen vs texto, a lo mejor hacen falta 2 rutas)

# Ruta para obtener entradas de diario
@app.get("/diary")
async def get_diary(username: str = Query(..., description="The username to fetch diary entries for")):
    user_diaries = mongo_client.get_diary_entries(username)
    return JSONResponse(content=user_diaries)

# Ruta para añadir entrada de diario
@app.post("/diary")
async def new_diary_entry(diary_req: DiaryRequest):
    username = diary_req.username
    diary_entry = diary_req.entry
    diary_entry.summary = generate_diary_summary(username, diary_entry.entry)
    diary_entry
    # TODO importance and other analysis of the diary contents
    if mongo_client.insert_diary_entry(username, diary_entry) is not None:
        return JSONResponse(content={"message" : "true"})
    else:
        return JSONResponse(content={"message": "false"})

# Ruta para modificar el modo del chat, TODO
@app.post("/chatmode")
async def modify_chat_mode(chat_mode):
    pass

# Ruta para modificar el modo del chat, TODO
@app.get("/tone")
async def get_tone(username: str = Query(..., description="The username to fetch diary entries for")):
    user = mongo_client.get_user(username)
    if user is not None and "chat_tone" in user:
        return JSONResponse(content={"message": user["chat_tone"]})
    else:
        return JSONResponse(content={"message": 0})

# Ruta para modificar el modo del chat, TODO
@app.post("/tone")
async def update_tone(tone_req: ToneChangeRequest):
    user = mongo_client.get_user(tone_req.username)
    if user is not None and mongo_client.update_tone(tone_req):
        return JSONResponse(content={"message": "true"})
    else:
        return JSONResponse(content={"message": "false"})

@app.post("/personality")
async def update_personality(personality_req: PersonalityChangeRequest):
    text = personality_req.input
    enneagram_result = classify_enneagram(text)
    big5_result = classify_big5(text)
    return JSONResponse(content={"enneagram_result": enneagram_result, "big5_result": big5_result})