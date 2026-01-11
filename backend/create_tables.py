from db import engine, Base
from models.users import User
from models.conversations import Conversation
from models.message import Message

Base.metadata.create_all(bind=engine)