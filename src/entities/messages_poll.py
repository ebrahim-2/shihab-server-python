from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from config import Base
from .message import Message

class MessagesPoll(Base):
    __tablename__ = 'messages_polls'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)

    messages = relationship(Message)
    user = relationship("User", back_populates="messages_polls")