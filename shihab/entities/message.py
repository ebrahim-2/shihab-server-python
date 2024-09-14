from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from shihab.config import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text)
    messages_poll_id = Column(Integer, ForeignKey("messages_polls.id"))
    assistant = Column(Boolean, default=False)
