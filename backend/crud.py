from sqlalchemy.orm import Session
from models import User, UserSession
from schemas import UserCreate
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta

ph = PasswordHasher()

def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def delete_user(db: Session, user_id: int):
    """Удаление пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

# === ФУНКЦИИ ДЛЯ СЕССИЙ ===

def get_active_session(db: Session, user_id: int, device_info: str, ip_address: str):
    """Получить активную сессию для данного устройства"""
    return db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.device_info == device_info,
        UserSession.ip_address == ip_address,
        UserSession.is_active == True
    ).first()

def create_or_update_session(
    db: Session,
    user_id: int,
    refresh_token: str,
    device_info: str,
    ip_address: str
):
    """Создать новую сессию или обновить существующую для того же устройства"""
    # Ищем существующую активную сессию для этого устройства
    existing_session = get_active_session(db, user_id, device_info, ip_address)
    
    if existing_session:
        # Обновляем существующую сессию
        existing_session.refresh_token = refresh_token
        existing_session.last_used_at = datetime.utcnow()
        existing_session.expires_at = datetime.utcnow() + timedelta(days=30)
        db.commit()
        db.refresh(existing_session)
        return existing_session
    else:
        # Создаём новую сессию
        new_session = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

def create_session(
    db: Session,
    user_id: int,
    refresh_token: str,
    device_info: str,
    ip_address: str
):
    """Создать новую сессию (старая версия для обратной совместимости)"""
    return create_or_update_session(db, user_id, refresh_token, device_info, ip_address)

def get_session_by_refresh_token(db: Session, refresh_token: str):
    """Получить сессию по refresh токену"""
    return db.query(UserSession).filter(
        UserSession.refresh_token == refresh_token,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).first()

def update_session_last_used(db: Session, session_id: int):
    """Обновить время последнего использования сессии"""
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session:
        session.last_used_at = datetime.utcnow()
        db.commit()

def revoke_session(db: Session, session_id: int):
    """Отозвать сессию"""
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session:
        session.is_active = False
        db.commit()
        return True
    return False

def revoke_all_user_sessions(db: Session, user_id: int):
    """Отозвать все сессии пользователя"""
    db.query(UserSession).filter(
        UserSession.user_id == user_id
    ).update({"is_active": False})
    db.commit()

def get_user_active_sessions(db: Session, user_id: int):
    """Получить все активные сессии пользователя"""
    return db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).all()

# === ФУНКЦИИ ДЛЯ ПРОВЕРОК ===

def get_user_checks(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    """Получить проверки пользователя"""
    from models import Check
    return db.query(Check).filter(
        Check.user_id == user_id
    ).order_by(Check.created_at.desc()).offset(skip).limit(limit).all()

def get_user_stats(db: Session, user_id: int):
    """Статистика пользователя"""
    from models import Check
    from sqlalchemy import func
    
    total_checks = db.query(func.count(Check.id)).filter(
        Check.user_id == user_id
    ).scalar()
    
    completed_checks = db.query(func.count(Check.id)).filter(
        Check.user_id == user_id,
        Check.status == "completed"
    ).scalar()
    
    avg_score = db.query(func.avg(Check.glaucoma_score)).filter(
        Check.user_id == user_id,
        Check.glaucoma_score.isnot(None)
    ).scalar()
    
    return {
        "total_checks": total_checks or 0,
        "completed_checks": completed_checks or 0,
        "average_score": round(float(avg_score or 0), 2)
    }

def delete_user(db: Session, user_id: int):
    """Удаление пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def get_user_checks(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    """Получить проверки пользователя"""
    from models import Check
    return db.query(Check).filter(
        Check.user_id == user_id
    ).order_by(Check.created_at.desc()).offset(skip).limit(limit).all()

def get_user_stats(db: Session, user_id: int):
    """Статистика пользователя"""
    from models import Check
    from sqlalchemy import func
    
    total_checks = db.query(func.count(Check.id)).filter(
        Check.user_id == user_id
    ).scalar()
    
    completed_checks = db.query(func.count(Check.id)).filter(
        Check.user_id == user_id,
        Check.status == "completed"
    ).scalar()
    
    avg_score = db.query(func.avg(Check.glaucoma_score)).filter(
        Check.user_id == user_id,
        Check.glaucoma_score.isnot(None)
    ).scalar()
    
    return {
        "total_checks": total_checks or 0,
        "completed_checks": completed_checks or 0,
        "average_score": round(float(avg_score or 0), 2)
    }
