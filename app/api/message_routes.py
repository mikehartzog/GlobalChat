from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, auth
from app.database import get_db
import json
from app.services.translation import translate_text

router = APIRouter()

@router.get("/", response_model=List[schemas.MessageResponse])
async def get_messages(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    messages = db.query(models.Message)\
        .order_by(models.Message.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    response_messages = []
    for message in messages:
        # Only process translation if needed
        translations = {}
        if (current_user.auto_translate and 
            message.original_language != current_user.preferred_language):
            
            stored_translations = json.loads(message.translations)
            
            # Check if we already have the translation
            if current_user.preferred_language in stored_translations:
                translations[current_user.preferred_language] = stored_translations[current_user.preferred_language]
            else:
                # Get new translation
                translated = translate_text(message.content, current_user.preferred_language)
                translations[current_user.preferred_language] = translated
                
                # Update stored translations
                stored_translations[current_user.preferred_language] = translated
                message.translations = json.dumps(stored_translations)
                db.commit()
        
        response_messages.append({
            "id": message.id,
            "content": message.content,
            "original_language": message.original_language,
            "sender_id": message.sender_id,
            "sender": message.sender,
            "created_at": message.created_at,
            "translations": translations  # Only includes relevant translation
        })
    
    return response_messages


@router.get("/{message_id}", response_model=schemas.MessageResponse)
async def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    translations = {}
    if (current_user.auto_translate and 
        message.original_language != current_user.preferred_language):
        
        stored_translations = json.loads(message.translations)
        
        if current_user.preferred_language in stored_translations:
            translations[current_user.preferred_language] = stored_translations[current_user.preferred_language]
        else:
            translated = translate_text(message.content, current_user.preferred_language)
            translations[current_user.preferred_language] = translated
            
            stored_translations[current_user.preferred_language] = translated
            message.translations = json.dumps(stored_translations)
            db.commit()
    
    return {
        "id": message.id,
        "content": message.content,
        "original_language": message.original_language,
        "sender_id": message.sender_id,
        "sender": message.sender,
        "created_at": message.created_at,
        "translations": translations
    }


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Query the message
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    
    # Check if message exists
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if current user is the message owner
    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this message"
        )
    
    # Delete the message
    db.delete(message)
    db.commit()
    
    # 204 No Content status code is returned automatically
    
@router.post("/{message_id}/translate")
async def translate_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    translations = json.loads(message.translations)
    target_lang = current_user.preferred_language
    
    # Return cached translation if exists
    if target_lang in translations:
        return {"translated_text": translations[target_lang]}
        
    # Get new translation
    translated = translate_text(message.content, target_lang)
    translations[target_lang] = translated["translated"]
    
    # Update cache
    message.translations = json.dumps(translations)
    db.commit()
    
    return {"translated_text": translated["translated"]}


@router.post("/", response_model=schemas.MessageResponse)
async def create_message(
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Get translations if needed
    translations = {}
    if current_user.auto_translate and current_user.preferred_language != message.original_language:
        translated = translate_text(message.content, current_user.preferred_language)
        translations[current_user.preferred_language] = translated

    # Create message
    db_message = models.Message(
        content=message.content,
        original_language=message.original_language,
        sender_id=current_user.id,
        translations=json.dumps(translations)
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    response_dict = {
        "id": db_message.id,
        "content": db_message.content,
        "original_language": db_message.original_language,
        "sender_id": db_message.sender_id,
        "sender": db_message.sender,
        "created_at": db_message.created_at,
        "translations": json.loads(db_message.translations)
    }
    
    return response_dict