from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime
import uuid
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode
from database import User, Session as ChatSession, Message, get_db_sync


class DBService:
    @staticmethod
    def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
        if salt is None:
            salt = urlsafe_b64encode(uuid.uuid4().bytes).decode('utf-8')
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=urlsafe_b64decode(salt),
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        return f"{salt}:{urlsafe_b64encode(key).decode('utf-8')}"

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        try:
            salt, hashed = password_hash.split(':')
            computed_hash = DBService._hash_password(password, salt)
            return computed_hash == password_hash
        except Exception:
            return False

    @staticmethod
    def create_user(db: Session, username: str, password: str) -> Optional[User]:
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return None
        
        password_hash = DBService._hash_password(password)
        uid = str(uuid.uuid4())
        user = User(
            uid=uid,
            username=username,
            password_hash=password_hash
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def login_user(db: Session, username: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.username == username).first()
        if user and DBService._verify_password(password, user.password_hash):
            return user
        return None

    @staticmethod
    def get_or_create_user(db: Session, uid: str, username: Optional[str] = None) -> User:
        user = db.query(User).filter(User.uid == uid).first()
        if not user:
            password_hash = DBService._hash_password(str(uuid.uuid4()))
            user = User(uid=uid, username=username or uid, password_hash=password_hash)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_uid(db: Session, uid: str) -> Optional[User]:
        return db.query(User).filter(User.uid == uid).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def create_session(db: Session, user_id: int, session_id: Optional[str] = None, title: Optional[str] = None) -> ChatSession:
        if not session_id:
            session_id = str(uuid.uuid4())
        chat_session = ChatSession(
            session_id=session_id,
            u_id=user_id,
            title=title
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        return chat_session
    
    @staticmethod
    def get_session_by_id(db: Session, session_id: str) -> Optional[ChatSession]:
        return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> List[ChatSession]:
        return db.query(ChatSession).filter(ChatSession.u_id == user_id).order_by(desc(ChatSession.updated_at)).all()
    
    @staticmethod
    def update_session_title(db: Session, session_id: str, title: str) -> Optional[ChatSession]:
        chat_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if chat_session:
            chat_session.title = title
            chat_session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(chat_session)
        return chat_session
    
    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        chat_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if chat_session:
            db.delete(chat_session)
            db.commit()
            return True
        return False
    
    @staticmethod
    def create_message(
        db: Session,
        message_id: str,
        session_id: str,
        user_id: int,
        role: str,
        content: Optional[str] = None,
        prompt: Optional[str] = None,
        reasoning_content: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_input: Optional[str] = None,
        tool_output: Optional[str] = None,
        message_type: int = 0,
        sequence: Optional[int] = None,
        finish_status: Optional[str] = None
    ) -> Message:
        message = Message(
            message_id=message_id,
            session_id=session_id,
            u_id=user_id,
            role=role,
            content=content,
            prompt=prompt,
            reasoning_content=reasoning_content,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            message_type=message_type,
            time=datetime.utcnow(),
            sequence=sequence,
            finish_status=finish_status
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def update_message_content(
        db: Session,
        message_id: str,
        content: str,
        finish_status: Optional[str] = None,
        reasoning_content: Optional[str] = None
    ) -> Optional[Message]:
        message = db.query(Message).filter(Message.message_id == message_id).first()
        if message:
            message.content = content
            if finish_status is not None:
                message.finish_status = finish_status
            if reasoning_content is not None:
                message.reasoning_content = reasoning_content
            db.commit()
            db.refresh(message)
        return message
    
    @staticmethod
    def get_session_messages(db: Session, session_id: str, limit: Optional[int] = None) -> List[Message]:
        query = db.query(Message).filter(Message.session_id == session_id).order_by(Message.time)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_message_by_id(db: Session, message_id: str) -> Optional[Message]:
        return db.query(Message).filter(Message.message_id == message_id).first()
    
    @staticmethod
    def delete_message(db: Session, message_id: str) -> bool:
        message = db.query(Message).filter(Message.message_id == message_id).first()
        if message:
            db.delete(message)
            db.commit()
            return True
        return False


db_service = DBService()
