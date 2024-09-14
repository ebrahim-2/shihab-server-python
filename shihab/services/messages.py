from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from shihab.config import ALGORITHM, SECRET_KEY, SessionLocal
from shihab.entities.message import Message
from shihab.entities.messages_poll import MessagesPoll
from jose import JWTError, jwt

from shihab.entities.user import User
from shihab.graph_db import queryGraph

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CreateMessageData(BaseModel):
    message: str
    messages_poll_id: Optional[int] = None

def init_message_routes(app):
    router = APIRouter()

    @router.post("/create-message")
    async def create_message(message_data: CreateMessageData, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        messages_poll = await create_or_find_message_poll(user.id, message_data, db)
        user_message = Message(
            message=message_data.message,
            messages_poll_id=messages_poll.id
        )
        assistant_message_data = queryGraph(message_data.message)
        assistant_message = Message(
            message=assistant_message_data['result'],
            messages_poll_id=messages_poll.id,
            assistant=True
        )
        db.add(user_message)
        db.add(assistant_message)
        db.commit()  # Remove await
        db.refresh(user_message)  # Remove await

        return [user_message, assistant_message]

    def get_four_words(input_string: str) -> str:
        words = input_string.split(' ')
        if len(words) >= 4:
            words = words[:4]
        return ' '.join(words)

    async def create_or_find_message_poll(user_id: int, body: CreateMessageData, session: Session):
        message_poll_name = get_four_words(body.message)
        messages_poll = None

        if body.messages_poll_id is None:
            messages_poll = MessagesPoll(user_id=user_id, name=message_poll_name)
            session.add(messages_poll)
            session.commit()  # Remove await
            session.refresh(messages_poll)  # Remove await
        else:
            result =  session.execute(
                select(MessagesPoll).where(MessagesPoll.id == body.messages_poll_id)
            )
            messages_poll = result.scalars().first()

        return messages_poll

    @router.get("/get-messages/{poll_id}")
    async def get_messages_poll(poll_id: int, db: Session = Depends(get_db)):
        messages = db.query(Message).filter(Message.messages_poll_id == poll_id).all()
        return messages

    app.include_router(router)