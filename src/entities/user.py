from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config import Base
from .messages_poll import MessagesPoll

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    messages_polls = relationship(MessagesPoll, back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
        }


