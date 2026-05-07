# ==================== ADMIN ENDPOINTS ====================
# Этот код нужно добавить в конец main.py

"""
@app.get("/api/admin/users", response_model=List[UserDetailedResponse], tags=["Admin"])
async def admin_get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    Получить список всех пользователей с детальной информацией (только для администраторов)
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/api/admin/users/{user_id}", response_model=UserDetailedResponse, tags=["Admin"])
async def admin_get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    Получить информацию о конкретном пользователе (только для администраторов)
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.patch("/api/admin/users/{user_id}/role", response_model=UserDetailedResponse, tags=["Admin"])
async def admin_update_user_role(
    user_id: int,
    role_update: UpdateUserRoleRequest,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    Изменить роль пользователя (только для администраторов)
    
    Доступные роли:
    - user: Обычный пользователь (врач)
    - admin: Администратор
    # Проверка, что пользователь существует
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверка, что админ не изменяет свою роль
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    # Обновление роли
    updated_user = crud.update_user_role(db, user_id, role_update.role)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role or update failed"
        )
    
    logger.info(f"Admin {current_user.username} changed role of user {user_id} to {role_update.role}")
    return updated_user


@app.patch("/api/admin/users/{user_id}/status", response_model=UserDetailedResponse, tags=["Admin"])
async def admin_update_user_status(
    user_id: int,
    status_update: UpdateUserStatusRequest,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    Заблокировать/разблокировать пользователя (только для администраторов)
    # Проверка, что пользователь существует
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверка, что админ не блокирует сам себя
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own status"
        )
    
    # Обновление статуса
    updated_user = crud.update_user_status(db, user_id, status_update.is_active)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status update failed"
        )
    
    action = "activated" if status_update.is_active else "blocked"
    logger.info(f"Admin {current_user.username} {action} user {user_id}")
    return updated_user


@app.put("/api/admin/users/{user_id}", response_model=UserDetailedResponse, tags=["Admin"])
async def admin_update_user_profile(
    user_id: int,
    profile_update: UpdateUserProfileRequest,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    Обновить профиль пользователя (только для администраторов)
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        updated_user = crud.update_user_profile(
            db, 
            user_id,
            email=profile_update.email,
            username=profile_update.username
        )
        logger.info(f"Admin {current_user.username} updated profile of user {user_id}")
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.delete("/api/admin/users/{user_id}", tags=["Admin"])
async def admin_delete_user(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    Удалить пользователя (только для администраторов)
    try:
        success = crud.delete_user_by_admin(db, user_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"Admin {current_user.username} deleted user {user_id}")
        return {"message": f"User {user_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@app.get("/api/admin/stats", response_model=UsersStatsResponse, tags=["Admin"])
async def admin_get_system_stats(
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    Получить статистику по пользователям системы (только для администраторов)
    from models import UserRole
    
    total_users = crud.count_users_by_role(db)
    admin_count = crud.count_users_by_role(db, UserRole.ADMIN.value)
    user_count = crud.count_users_by_role(db, UserRole.USER.value)
    
    # Подсчет активных и заблокированных
    active_users = db.query(User).filter(User.is_active == True).count()
    blocked_users = db.query(User).filter(User.is_active == False).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "blocked_users": blocked_users,
        "admin_count": admin_count,
        "user_count": user_count
    }


@app.get("/api/admin/images", tags=["Admin"])
async def admin_get_all_images(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    Получить все изображения в системе (только для администраторов)
    images = db.query(ProcessedImage).offset(skip).limit(limit).all()
    
    return [
        {
            "id": img.id,
            "user_id": img.user_id,
            "original_url": s3_service.get_public_url(img.original_url),
            "processed_url": s3_service.get_public_url(img.processed_url),
            "result": img.result,
            "confidence": calculate_confidence(img.result, img.glaucoma_probability),
            "filename": img.filename,
            "file_size": img.file_size,
            "status": img.status,
            "created_at": img.created_at,
            "processed_at": img.processed_at
        }
        for img in images
    ]


@app.delete("/api/admin/images/{image_id}", tags=["Admin"])
async def admin_delete_image(
    image_id: int,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    Удалить любое изображение (только для администраторов)
    image = db.query(ProcessedImage).filter(ProcessedImage.id == image_id).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        # Удаляем из S3
        s3_service.delete_image(image.original_url)
        if image.processed_url != image.original_url:
            s3_service.delete_image(image.processed_url)
        
        # Удаляем из БД
        db.delete(image)
        db.commit()
        
        logger.info(f"Admin {current_user.username} deleted image {image_id}")
        return {"message": f"Image {image_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting image {image_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image"
        )
"""
