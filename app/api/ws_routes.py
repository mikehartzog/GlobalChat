from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict
import json
from app.services.translation import translate_text
from app import models, auth
from app.database import get_db
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.auth import SECRET_KEY, ALGORITHM  # Import these from your auth module

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected. Total connections: {len(self.active_connections)}")  # Debug log

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")  # Debug log

    async def broadcast(self, message: dict, sender_id: int):
        # Add debug logging
        print(f"Broadcasting message from user {sender_id} to {len(self.active_connections)-1} other users")
        for user_id, connection in self.active_connections.items():
            if user_id != sender_id:  # Don't send to self
                try:
                    await connection.send_json(message)
                    print(f"Message sent to user {user_id}")
                except Exception as e:
                    print(f"Error sending to user {user_id}: {str(e)}")

manager = ConnectionManager()

async def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return None
        user = db.query(models.User).filter(models.User.email == email).first()
        return user
    except JWTError:
        return None



@router.websocket("/ws/{token}")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: str,
    db: Session = Depends(get_db)
):
    user = await get_user_from_token(token, db)
    if not user:
        await websocket.close(code=4001)
        return

    await manager.connect(user.id, websocket)
    print(f"User {user.username} (ID: {user.id}) connected with preferred language {user.preferred_language}")
    
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received message from {user.username}")
            
            # Get translations
            translations = {}
            recipient_id = data.get('recipient_id')
            
            if recipient_id:
                # Private message - only translate for recipient
                recipient = db.query(models.User).filter(models.User.id == recipient_id).first()
                if recipient and recipient.auto_translate and recipient.preferred_language != data["original_language"]:
                    translated = translate_text(data["content"], recipient.preferred_language)
                    translations[recipient.preferred_language] = translated
            else:
                # Broadcast message - translate for all users
                for conn_id in manager.active_connections:
                    if conn_id != user.id:
                        recipient = db.query(models.User).filter(models.User.id == conn_id).first()
                        if recipient and recipient.auto_translate and recipient.preferred_language != data["original_language"]:
                            if recipient.preferred_language not in translations:
                                translated = translate_text(data["content"], recipient.preferred_language)
                                translations[recipient.preferred_language] = translated

            # Create message in database
            message = models.Message(
                content=data["content"],
                original_language=data["original_language"],
                sender_id=user.id,
                recipient_id=recipient_id,
                translations=json.dumps(translations)
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            # Prepare message for sending
            message_data = {
                "id": message.id,
                "content": message.content,
                "original_language": message.original_language,
                "sender_id": user.id,
                "sender": {
                    "username": user.username,
                    "preferred_language": user.preferred_language
                },
                "created_at": message.created_at.isoformat(),
                "translations": translations,
                "private": recipient_id is not None
            }

            if recipient_id:
                # Send private message only to recipient
                if recipient_id in manager.active_connections:
                    await manager.active_connections[recipient_id].send_json(message_data)
            else:
                # Broadcast to all except sender
                await manager.broadcast(message_data, user.id)

    except WebSocketDisconnect:
        manager.disconnect(user.id)
        print(f"User {user.username} disconnected")
    except Exception as e:
        print(f"Error in websocket: {str(e)}")
        manager.disconnect(user.id)
        await websocket.close(code=1001)