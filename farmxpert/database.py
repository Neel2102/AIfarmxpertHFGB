"""
Centralized Database Operations - All PostgreSQL Save/Load Functions
No magic, no complex inheritance - just straightforward functions.
"""

import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from farmxpert.models.database import get_db
from farmxpert.models.user_models import User, UserSession, ChatSession, ChatMessage
from farmxpert.models.farm_models import Farm, Crop, SoilTest, Task, Yield

# ============================================================================
# USER OPERATIONS
# ============================================================================

def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    full_name: str,
    phone: str = None
) -> Optional[User]:
    """
    Create a new user
    
    Args:
        db: Database session
        username: Unique username
        email: User email
        password: Plain text password (will be hashed)
        full_name: User's full name
        phone: Optional phone number
        
    Returns:
        Created user object or None if failed
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            or_(User.username == username, User.email == email)
        ).first()
        
        if existing_user:
            return None
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            is_active=True,
            is_verified=False
        )
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
        
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        return None

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate user with username and password
    
    Args:
        db: Database session
        username: Username or email
        password: Plain text password
        
    Returns:
        User object if authenticated, None otherwise
    """
    user = db.query(User).filter(
        and_(
            or_(User.username == username, User.email == username),
            User.is_active == True
        )
    ).first()
    
    if user and user.check_password(password):
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        return user
    
    return None

def update_user_profile(
    db: Session,
    user_id: int,
    **kwargs
) -> Optional[User]:
    """
    Update user profile
    
    Args:
        db: Database session
        user_id: User ID
        **kwargs: Fields to update (full_name, email, phone)
        
    Returns:
        Updated user object or None if failed
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            return None
        
        # Update allowed fields
        allowed_fields = ['full_name', 'email', 'phone']
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user
        
    except Exception as e:
        db.rollback()
        print(f"Error updating user profile: {e}")
        return None

# ============================================================================
# SESSION OPERATIONS
# ============================================================================

def create_user_session(
    db: Session,
    user_id: int,
    ip_address: str = None,
    user_agent: str = None
) -> Optional[str]:
    """
    Create a new user session
    
    Args:
        db: Database session
        user_id: User ID
        ip_address: Optional IP address
        user_agent: Optional user agent string
        
    Returns:
        Session token string or None if failed
    """
    try:
        import secrets
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        
        # Create session record
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=datetime.utcnow() + timedelta(days=30),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(session)
        db.commit()
        
        return session_token
        
    except Exception as e:
        db.rollback()
        print(f"Error creating user session: {e}")
        return None

def get_user_by_session(db: Session, session_token: str) -> Optional[User]:
    """
    Get user by session token
    
    Args:
        db: Database session
        session_token: Session token string
        
    Returns:
        User object if session valid, None otherwise
    """
    try:
        session = db.query(UserSession).filter(
            and_(
                UserSession.session_token == session_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()
        
        if session:
            # Update last activity
            session.last_activity = datetime.utcnow()
            db.commit()
            return session.user
        
        return None
        
    except Exception as e:
        print(f"Error getting user by session: {e}")
        return None

def invalidate_session(db: Session, session_token: str) -> bool:
    """Invalidate a user session"""
    try:
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
            return True
        
        return False
        
    except Exception as e:
        db.rollback()
        print(f"Error invalidating session: {e}")
        return False

# ============================================================================
# CHAT OPERATIONS
# ============================================================================

def create_chat_session(
    db: Session,
    user_id: int,
    title: str = None
) -> Optional[str]:
    """
    Create a new chat session
    
    Args:
        db: Database session
        user_id: User ID
        title: Optional chat title
        
    Returns:
        Chat session ID or None if failed
    """
    try:
        import uuid
        
        session_id = str(uuid.uuid4())
        
        chat_session = ChatSession(
            id=session_id,
            title=title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(chat_session)
        db.commit()
        
        return session_id
        
    except Exception as e:
        db.rollback()
        print(f"Error creating chat session: {e}")
        return None

def save_chat_message(
    db: Session,
    session_id: str,
    role: str,
    content: str
) -> Optional[ChatMessage]:
    """
    Save a chat message
    
    Args:
        db: Database session
        session_id: Chat session ID
        role: Message role ('user' or 'assistant')
        content: Message content
        
    Returns:
        Created message object or None if failed
    """
    try:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.utcnow()
        )
        
        db.add(message)
        
        # Update session timestamp
        chat_session = db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        if chat_session:
            chat_session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        
        return message
        
    except Exception as e:
        db.rollback()
        print(f"Error saving chat message: {e}")
        return None

def get_chat_messages(
    db: Session,
    session_id: str,
    limit: int = 50
) -> List[ChatMessage]:
    """
    Get chat messages for a session
    
    Args:
        db: Database session
        session_id: Chat session ID
        limit: Maximum number of messages to return
        
    Returns:
        List of chat messages
    """
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(asc(ChatMessage.created_at)).limit(limit).all()
        
        return messages
        
    except Exception as e:
        print(f"Error getting chat messages: {e}")
        return []

def get_user_chat_sessions(
    db: Session,
    user_id: int,
    limit: int = 20
) -> List[ChatSession]:
    """
    Get user's chat sessions
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of sessions
        
    Returns:
        List of chat sessions
    """
    try:
        sessions = db.query(ChatSession).order_by(
            desc(ChatSession.updated_at)
        ).limit(limit).all()
        
        return sessions
        
    except Exception as e:
        print(f"Error getting user chat sessions: {e}")
        return []

# ============================================================================
# FARM OPERATIONS
# ============================================================================

def create_farm(
    db: Session,
    user_id: int,
    name: str,
    location: str,
    size_acres: float,
    farmer_name: str = None,
    farmer_phone: str = None,
    farmer_email: str = None
) -> Optional[Farm]:
    """
    Create a new farm
    
    Args:
        db: Database session
        user_id: User ID
        name: Farm name
        location: Farm location
        size_acres: Farm size in acres
        farmer_name: Farmer name
        farmer_phone: Farmer phone
        farmer_email: Farmer email
        
    Returns:
        Created farm object or None if failed
    """
    try:
        farm = Farm(
            user_id=user_id,
            name=name,
            location=location,
            size_acres=size_acres,
            farmer_name=farmer_name,
            farmer_phone=farmer_phone,
            farmer_email=farmer_email,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(farm)
        db.commit()
        db.refresh(farm)
        
        return farm
        
    except Exception as e:
        db.rollback()
        print(f"Error creating farm: {e}")
        return None

def get_user_farms(db: Session, user_id: int) -> List[Farm]:
    """Get all farms for a user"""
    try:
        farms = db.query(Farm).filter(Farm.user_id == user_id).all()
        return farms
    except Exception as e:
        print(f"Error getting user farms: {e}")
        return []

def update_farm(
    db: Session,
    farm_id: int,
    user_id: int,
    **kwargs
) -> Optional[Farm]:
    """
    Update farm information
    
    Args:
        db: Database session
        farm_id: Farm ID
        user_id: User ID (for ownership verification)
        **kwargs: Fields to update
        
    Returns:
        Updated farm object or None if failed
    """
    try:
        farm = db.query(Farm).filter(
            and_(Farm.id == farm_id, Farm.user_id == user_id)
        ).first()
        
        if not farm:
            return None
        
        # Update allowed fields
        allowed_fields = ['name', 'location', 'size_acres', 'farmer_name', 'farmer_phone', 'farmer_email']
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(farm, field):
                setattr(farm, field, value)
        
        farm.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(farm)
        
        return farm
        
    except Exception as e:
        db.rollback()
        print(f"Error updating farm: {e}")
        return None

# ============================================================================
# CROP OPERATIONS
# ============================================================================

def create_crop(
    db: Session,
    farm_id: int,
    crop_name: str,
    variety: str = None,
    sowing_date: datetime = None,
    expected_harvest_date: datetime = None,
    area_acres: float = None,
    status: str = "planned"
) -> Optional[Crop]:
    """
    Create a new crop record
    
    Args:
        db: Database session
        farm_id: Farm ID
        crop_name: Crop name
        variety: Crop variety
        sowing_date: Sowing date
        expected_harvest_date: Expected harvest date
        area_acres: Area in acres
        status: Crop status
        
    Returns:
        Created crop object or None if failed
    """
    try:
        crop = Crop(
            farm_id=farm_id,
            crop_name=crop_name,
            variety=variety,
            sowing_date=sowing_date or datetime.utcnow(),
            expected_harvest_date=expected_harvest_date,
            area_acres=area_acres,
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(crop)
        db.commit()
        db.refresh(crop)
        
        return crop
        
    except Exception as e:
        db.rollback()
        print(f"Error creating crop: {e}")
        return None

def get_farm_crops(db: Session, farm_id: int) -> List[Crop]:
    """Get all crops for a farm"""
    try:
        crops = db.query(Crop).filter(Crop.farm_id == farm_id).all()
        return crops
    except Exception as e:
        print(f"Error getting farm crops: {e}")
        return []

def update_crop_status(
    db: Session,
    crop_id: int,
    status: str,
    notes: str = None
) -> Optional[Crop]:
    """Update crop status"""
    try:
        crop = db.query(Crop).filter(Crop.id == crop_id).first()
        if not crop:
            return None
        
        crop.status = status
        crop.notes = notes
        crop.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(crop)
        
        return crop
        
    except Exception as e:
        db.rollback()
        print(f"Error updating crop status: {e}")
        return None

# ============================================================================
# SOIL TEST OPERATIONS
# ============================================================================

def save_soil_test(
    db: Session,
    farm_id: int,
    test_data: Dict[str, Any],
    test_date: datetime = None
) -> Optional[SoilTest]:
    """
    Save soil test results
    
    Args:
        db: Database session
        farm_id: Farm ID
        test_data: Soil test data (pH, NPK, etc.)
        test_date: Test date
        
    Returns:
        Created soil test object or None if failed
    """
    try:
        soil_test = SoilTest(
            farm_id=farm_id,
            test_date=test_date or datetime.utcnow(),
            ph=test_data.get('ph'),
            nitrogen=test_data.get('nitrogen'),
            phosphorus=test_data.get('phosphorus'),
            potassium=test_data.get('potassium'),
            organic_matter=test_data.get('organic_matter'),
            soil_type=test_data.get('soil_type'),
            texture=test_data.get('texture'),
            recommendations=json.dumps(test_data.get('recommendations', [])),
            created_at=datetime.utcnow()
        )
        
        db.add(soil_test)
        db.commit()
        db.refresh(soil_test)
        
        return soil_test
        
    except Exception as e:
        db.rollback()
        print(f"Error saving soil test: {e}")
        return None

def get_farm_soil_tests(db: Session, farm_id: int) -> List[SoilTest]:
    """Get all soil tests for a farm"""
    try:
        tests = db.query(SoilTest).filter(
            SoilTest.farm_id == farm_id
        ).order_by(desc(SoilTest.test_date)).all()
        
        return tests
        
    except Exception as e:
        print(f"Error getting farm soil tests: {e}")
        return []

# ============================================================================
# TASK OPERATIONS
# ============================================================================

def create_task(
    db: Session,
    farm_id: int,
    title: str,
    description: str = None,
    task_type: str = "general",
    priority: str = "medium",
    due_date: datetime = None,
    status: str = "pending"
) -> Optional[Task]:
    """
    Create a new farm task
    
    Args:
        db: Database session
        farm_id: Farm ID
        title: Task title
        description: Task description
        task_type: Type of task
        priority: Task priority
        due_date: Due date
        status: Task status
        
    Returns:
        Created task object or None if failed
    """
    try:
        task = Task(
            farm_id=farm_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            due_date=due_date,
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return task
        
    except Exception as e:
        db.rollback()
        print(f"Error creating task: {e}")
        return None

def get_farm_tasks(
    db: Session,
    farm_id: int,
    status: str = None,
    limit: int = 50
) -> List[Task]:
    """Get tasks for a farm"""
    try:
        query = db.query(Task).filter(Task.farm_id == farm_id)
        
        if status:
            query = query.filter(Task.status == status)
        
        tasks = query.order_by(asc(Task.due_date)).limit(limit).all()
        return tasks
        
    except Exception as e:
        print(f"Error getting farm tasks: {e}")
        return []

def update_task_status(
    db: Session,
    task_id: int,
    status: str,
    notes: str = None
) -> Optional[Task]:
    """Update task status"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        task.status = status
        task.notes = notes
        task.updated_at = datetime.utcnow()
        
        if status == "completed":
            task.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(task)
        
        return task
        
    except Exception as e:
        db.rollback()
        print(f"Error updating task status: {e}")
        return None

# ============================================================================
# YIELD OPERATIONS
# ============================================================================

def save_yield_record(
    db: Session,
    crop_id: int,
    actual_yield: float,
    yield_unit: str = "quintals",
    harvest_date: datetime = None,
    quality_grade: str = None,
    market_price: float = None
) -> Optional[Yield]:
    """
    Save crop yield record
    
    Args:
        db: Database session
        crop_id: Crop ID
        actual_yield: Actual yield amount
        yield_unit: Unit of yield
        harvest_date: Harvest date
        quality_grade: Quality grade
        market_price: Market price per unit
        
    Returns:
        Created yield record or None if failed
    """
    try:
        yield_record = Yield(
            crop_id=crop_id,
            actual_yield=actual_yield,
            yield_unit=yield_unit,
            harvest_date=harvest_date or datetime.utcnow(),
            quality_grade=quality_grade,
            market_price=market_price,
            created_at=datetime.utcnow()
        )
        
        db.add(yield_record)
        db.commit()
        db.refresh(yield_record)
        
        return yield_record
        
    except Exception as e:
        db.rollback()
        print(f"Error saving yield record: {e}")
        return None

def get_crop_yields(db: Session, crop_id: int) -> List[Yield]:
    """Get yield records for a crop"""
    try:
        yields = db.query(Yield).filter(Yield.crop_id == crop_id).all()
        return yields
    except Exception as e:
        print(f"Error getting crop yields: {e}")
        return []

# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================

def get_farm_summary(db: Session, farm_id: int) -> Dict[str, Any]:
    """
    Get farm summary statistics
    
    Args:
        db: Database session
        farm_id: Farm ID
        
    Returns:
        Farm summary data
    """
    try:
        # Get farm info
        farm = db.query(Farm).filter(Farm.id == farm_id).first()
        if not farm:
            return {}
        
        # Get crops count
        crops_count = db.query(Crop).filter(Crop.farm_id == farm_id).count()
        
        # Get active tasks
        active_tasks = db.query(Task).filter(
            and_(Task.farm_id == farm_id, Task.status.in_(['pending', 'in_progress']))
        ).count()
        
        # Get total yield
        total_yield = db.query(func.sum(Yield.actual_yield)).filter(
            Yield.crop_id.in_(
                db.query(Crop.id).filter(Crop.farm_id == farm_id)
            )
        ).scalar() or 0
        
        # Get latest soil test
        latest_soil_test = db.query(SoilTest).filter(
            SoilTest.farm_id == farm_id
        ).order_by(desc(SoilTest.test_date)).first()
        
        return {
            "farm": {
                "id": farm.id,
                "name": farm.name,
                "location": farm.location,
                "size_acres": farm.size_acres
            },
            "crops_count": crops_count,
            "active_tasks": active_tasks,
            "total_yield": float(total_yield),
            "latest_soil_test": {
                "test_date": latest_soil_test.test_date.isoformat() if latest_soil_test else None,
                "ph": latest_soil_test.ph if latest_soil_test else None
            }
        }
        
    except Exception as e:
        print(f"Error getting farm summary: {e}")
        return {}

def get_user_dashboard_data(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Get dashboard data for a user
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Dashboard data
    """
    try:
        # Get user's farms
        farms = get_user_farms(db, user_id)
        
        # Calculate totals
        total_farms = len(farms)
        total_acres = sum(farm.size_acres for farm in farms)
        
        # Get recent activity
        recent_tasks = []
        for farm in farms:
            tasks = get_farm_tasks(db, farm.id, limit=5)
            recent_tasks.extend(tasks)
        
        # Sort by date
        recent_tasks.sort(key=lambda x: x.created_at, reverse=True)
        
        return {
            "total_farms": total_farms,
            "total_acres": total_acres,
            "farms": [
                {
                    "id": farm.id,
                    "name": farm.name,
                    "location": farm.location,
                    "size_acres": farm.size_acres
                }
                for farm in farms
            ],
            "recent_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date.isoformat() if task.due_date else None
                }
                for task in recent_tasks[:10]
            ]
        }
        
    except Exception as e:
        print(f"Error getting user dashboard data: {e}")
        return {}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_database_session():
    """Get a database session"""
    return next(get_db())

def execute_query(db: Session, query: str, params: Dict = None) -> List[Dict]:
    """
    Execute raw SQL query
    
    Args:
        db: Database session
        query: SQL query string
        params: Query parameters
        
    Returns:
        Query results as list of dictionaries
    """
    try:
        result = db.execute(query, params or {})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]
    except Exception as e:
        print(f"Error executing query: {e}")
        return []

def backup_user_data(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Backup all data for a user
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User data backup
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            return {}
        
        # Get all related data
        farms = get_user_farms(db, user_id)
        farms_data = []
        
        for farm in farms:
            farm_data = {
                "farm": {
                    "id": farm.id,
                    "name": farm.name,
                    "location": farm.location,
                    "size_acres": farm.size_acres
                },
                "crops": [
                    {
                        "id": crop.id,
                        "crop_name": crop.crop_name,
                        "variety": crop.variety,
                        "sowing_date": crop.sowing_date.isoformat() if crop.sowing_date else None,
                        "status": crop.status
                    }
                    for crop in get_farm_crops(db, farm.id)
                ],
                "soil_tests": [
                    {
                        "id": test.id,
                        "test_date": test.test_date.isoformat(),
                        "ph": test.ph,
                        "nitrogen": test.nitrogen,
                        "phosphorus": test.phosphorus,
                        "potassium": test.potassium
                    }
                    for test in get_farm_soil_tests(db, farm.id)
                ],
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date.isoformat() if task.due_date else None
                    }
                    for task in get_farm_tasks(db, farm.id)
                ]
            }
            farms_data.append(farm_data)
        
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat()
            },
            "farms": farms_data,
            "backup_date": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error backing up user data: {e}")
        return {}
