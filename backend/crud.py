from sqlalchemy.orm import Session
from models import User, UserSession
from schemas import UserCreate
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta

ph = PasswordHasher()

def get_password_hash(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
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
    existing_session = get_active_session(db, user_id, device_info, ip_address)
    
    if existing_session:
        existing_session.refresh_token = refresh_token
        existing_session.last_used_at = datetime.utcnow()
        existing_session.expires_at = datetime.utcnow() + timedelta(days=30)
        db.commit()
        db.refresh(existing_session)
        return existing_session
    else:
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

def check_session_security(session: UserSession, ip_address: str) -> tuple[bool, str]:
    """
    Проверить безопасность сессии после использования refresh token.
    Детектировать признаки компрометации (использование из разных IP).
    
    Returns:
        (is_safe, message)
    """
    if not session or not ip_address:
        return False, "Invalid session or IP"
    
    # Если сессия используется из нового IP адреса
    if session.ip_address != ip_address:
        return False, f"Suspicious activity: session accessed from different IP. Previous: {session.ip_address}, Current: {ip_address}"
    
    return True, "Session is secure"

def rotate_refresh_token(
    db: Session,
    session_id: int,
    new_refresh_token: str,
    ip_address: str
) -> UserSession:
    """
    Ротация refresh token - создание нового и обновление сессии.
    Это часть логики при обновлении access token.
    
    Args:
        db: Сессия БД
        session_id: ID текущей сессии
        new_refresh_token: Новый refresh token
        ip_address: IP адрес клиента
    
    Returns:
        Обновленная UserSession
    """
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session:
        raise ValueError("Session not found")
    
    # Проверяем безопасность перед ротацией
    is_safe, message = check_session_security(session, ip_address)
    if not is_safe:
        # Отзываем сессию при подозрении на компрометацию
        session.is_active = False
        db.commit()
        raise PermissionError(message)
    
    # Ротируем токен
    session.refresh_token = new_refresh_token
    session.last_used_at = datetime.utcnow()
    session.expires_at = datetime.utcnow() + timedelta(days=30)
    
    db.commit()
    db.refresh(session)
    
    return session

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

# === ФУНКЦИИ ДЛЯ ПРОВЕРОК И СТАТИСТИКИ ===

def get_user_checks(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    """Получить проверки пользователя"""
    from models import Check
    return db.query(Check).filter(
        Check.user_id == user_id
    ).order_by(Check.created_at.desc()).offset(skip).limit(limit).all()

def get_user_stats(db: Session, user_id: int):
    """Статистика пользователя по изображениям"""
    from models import ProcessedImage
    from sqlalchemy import func, cast, Date
    from datetime import datetime, timezone
    
    # Общее количество изображений
    total_checks = db.query(func.count(ProcessedImage.id)).filter(
        ProcessedImage.user_id == user_id
    ).scalar()
    
    # Количество с глаукомой
    glaucoma_count = db.query(func.count(ProcessedImage.id)).filter(
        ProcessedImage.user_id == user_id,
        ProcessedImage.result.ilike('%glaucoma%'),
        ~ProcessedImage.result.ilike('%non%')
    ).scalar()
    
    # Количество без глаукомы
    non_glaucoma_count = db.query(func.count(ProcessedImage.id)).filter(
        ProcessedImage.user_id == user_id,
        ProcessedImage.result.ilike('%non%')
    ).scalar()
    
    # Загрузки сегодня
    today = datetime.now(timezone.utc).date()
    today_uploads = db.query(func.count(ProcessedImage.id)).filter(
        ProcessedImage.user_id == user_id,
        cast(ProcessedImage.created_at, Date) == today
    ).scalar()
    
    return {
        "total_checks": total_checks or 0,
        "glaucoma_count": glaucoma_count or 0,
        "non_glaucoma_count": non_glaucoma_count or 0,
        "today_uploads": today_uploads or 0
    }


# === ФУНКЦИИ ДЛЯ УПРАВЛЕНИЯ РОЛЯМИ (ADMIN) ===

def update_user_role(db: Session, user_id: int, new_role: str):
    from models import UserRole
    # Проверка валидности роли
    if new_role not in [role.value for role in UserRole]:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.role = new_role
        db.commit()
        db.refresh(user)
        return user
    return None


def update_user_status(db: Session, user_id: int, is_active: bool):
    """
    Блокировка/разблокировка пользователя
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = is_active
        db.commit()
        db.refresh(user)
        return user
    return None


def update_user_profile(db: Session, user_id: int, email: str = None, username: str = None):
    """
    Обновление профиля пользователя (admin может обновлять любого)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Проверка уникальности username
    if username and username != user.username:
        existing_user = get_user_by_username(db, username)
        if existing_user:
            raise ValueError("Username already exists")
        user.username = username
    
    # Проверка уникальности email
    if email and email != user.email:
        existing_user = get_user_by_email(db, email)
        if existing_user:
            raise ValueError("Email already exists")
        user.email = email
    
    db.commit()
    db.refresh(user)
    return user


def get_users_by_role(db: Session, role: str, skip: int = 0, limit: int = 100):
    """
    Получить пользователей по роли
    
    Args:
        db: Сессия БД
        role: Роль ("user" или "admin")
        skip: Пропустить N записей
        limit: Максимальное количество
    
    Returns:
        Список пользователей
    """
    return db.query(User).filter(User.role == role).offset(skip).limit(limit).all()


def count_users_by_role(db: Session, role: str = None):
    """
    Подсчет пользователей по роли
    
    Args:
        db: Сессия БД
        role: Роль (опционально, если None - все пользователи)
    
    Returns:
        Количество пользователей
    """
    from sqlalchemy import func
    
    if role:
        return db.query(func.count(User.id)).filter(User.role == role).scalar()
    return db.query(func.count(User.id)).scalar()


def delete_user_by_admin(db: Session, user_id: int, admin_id: int):
    """
    Удаление пользователя администратором (с проверкой, что не удаляет сам себя)
    
    Args:
        db: Сессия БД
        user_id: ID пользователя для удаления
        admin_id: ID администратора
    
    Returns:
        True если удален, False иначе
    """
    if user_id == admin_id:
        raise ValueError("Cannot delete yourself")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
