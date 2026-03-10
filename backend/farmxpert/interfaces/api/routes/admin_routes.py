from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.requests import Request
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from farmxpert.core.utils.logger import get_logger
from farmxpert.models.database import get_db
from farmxpert.models.admin_models import AdminAuditEvent, SensorOverride
from farmxpert.models.farm_models import AgentInteraction, Farm
from farmxpert.models.blynk_models import BlynkDevice, SensorReading
from farmxpert.models.user_models import User
from farmxpert.interfaces.api.routes.auth_routes import get_current_user

from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = get_logger("admin_api")


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    role = (getattr(current_user, "role", None) or "").lower().strip()
    allowed_roles = {"admin", "superadmin", "super_admin"}
    if role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _parse_iso_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except Exception:
        return None


def _user_snapshot(u: User) -> Dict[str, Any]:
    return {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "full_name": u.full_name,
        "phone": u.phone,
        "role": getattr(u, "role", None),
        "is_active": bool(u.is_active),
        "is_verified": bool(u.is_verified),
        "onboarding_completed": bool(getattr(u, "onboarding_completed", False)),
        "suspended_at": u.suspended_at.isoformat() if getattr(u, "suspended_at", None) else None,
        "suspended_until": u.suspended_until.isoformat() if getattr(u, "suspended_until", None) else None,
        "suspend_reason": getattr(u, "suspend_reason", None),
    }


@router.get("/search")
async def admin_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        needle = q.strip()
        like = f"%{needle}%"

        users: List[User] = (
            db.query(User)
            .filter(
                (User.username.ilike(like))
                | (User.email.ilike(like))
                | (User.full_name.ilike(like))
            )
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )

        farms: List[Farm] = (
            db.query(Farm)
            .filter(
                (Farm.farm_name.ilike(like))
                | (Farm.state.ilike(like))
                | (Farm.district.ilike(like))
            )
            .order_by(Farm.created_at.desc())
            .limit(limit)
            .all()
        )

        devices: List[BlynkDevice] = (
            db.query(BlynkDevice)
            .filter(
                (BlynkDevice.device_name.ilike(like))
                | (BlynkDevice.blynk_device_id.ilike(like))
                | (BlynkDevice.status.ilike(like))
            )
            .order_by(BlynkDevice.created_at.desc())
            .limit(limit)
            .all()
        )

        interactions: List[AgentInteraction] = (
            db.query(AgentInteraction)
            .filter(
                (AgentInteraction.agent_name.ilike(like))
                | (AgentInteraction.query.ilike(like))
            )
            .order_by(AgentInteraction.created_at.desc())
            .limit(limit)
            .all()
        )

        items: List[Dict[str, Any]] = []
        items.extend(
            {
                "kind": "user",
                "id": int(u.id),
                "label": f"{u.username} ({u.email})",
                "meta": {"role": getattr(u, "role", None), "is_active": bool(u.is_active)},
            }
            for u in users
        )
        items.extend(
            {
                "kind": "farm",
                "id": int(f.id),
                "label": f"{f.farm_name} (User {f.user_id})",
                "meta": {"state": f.state, "district": f.district},
            }
            for f in farms
        )
        items.extend(
            {
                "kind": "device",
                "id": int(d.id),
                "label": f"{d.device_name} (Farm {d.farm_id})",
                "meta": {"status": d.status, "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None},
            }
            for d in devices
        )
        items.extend(
            {
                "kind": "interaction",
                "id": int(i.id),
                "label": f"{i.agent_name} (Farm {i.farm_id})",
                "meta": {"tokens_used": int(i.tokens_used or 0), "created_at": i.created_at.isoformat() if i.created_at else None},
            }
            for i in interactions
        )

        return {"query": needle, "items": items[: limit * 4]}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


def _write_audit_event(
    *,
    db: Session,
    request: Request,
    actor_user_id: int,
    action_type: str,
    target_type: str,
    target_id: str,
    reason: Optional[str],
    before_json: Optional[Dict[str, Any]],
    after_json: Optional[Dict[str, Any]],
) -> None:
    ev = AdminAuditEvent(
        actor_user_id=actor_user_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        before_json=before_json,
        after_json=after_json,
        request_id=request.headers.get("x-request-id"),
        ip_address=(request.client.host if request.client else None),
        user_agent=request.headers.get("user-agent"),
    )
    db.add(ev)


@router.get("/me")
async def admin_me(current_user: User = Depends(require_admin)) -> Dict[str, Any]:
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": getattr(current_user, "role", "farmer"),
        "is_active": bool(current_user.is_active),
        "is_verified": bool(current_user.is_verified),
    }


@router.get("/users")
async def admin_list_users(
    q: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    onboarding_completed: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        query = db.query(User)

        if q:
            like = f"%{q.strip()}%"
            query = query.filter(
                (User.username.ilike(like))
                | (User.email.ilike(like))
                | (User.full_name.ilike(like))
            )

        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if onboarding_completed is not None:
            query = query.filter(User.onboarding_completed == onboarding_completed)

        total = query.count()
        rows: List[User] = (
            query.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "full_name": u.full_name,
                    "phone": u.phone,
                    "role": getattr(u, "role", "farmer"),
                    "is_active": bool(u.is_active),
                    "is_verified": bool(u.is_verified),
                    "onboarding_completed": bool(getattr(u, "onboarding_completed", False)),
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                }
                for u in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.get("/users/{user_id}")
async def admin_get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": getattr(user, "role", "farmer"),
        "is_active": bool(user.is_active),
        "is_verified": bool(user.is_verified),
        "onboarding_completed": bool(getattr(user, "onboarding_completed", False)),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "suspended_at": user.suspended_at.isoformat() if getattr(user, "suspended_at", None) else None,
        "suspended_until": user.suspended_until.isoformat() if getattr(user, "suspended_until", None) else None,
        "suspend_reason": getattr(user, "suspend_reason", None),
    }


@router.get("/users/{user_id}/iot/devices")
async def admin_list_user_iot_devices(
    user_id: int,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        farm_ids = [
            int(row[0])
            for row in db.query(Farm.id).filter(Farm.user_id == user_id).all()
        ]

        if not farm_ids:
            return {"items": [], "page": page, "page_size": page_size, "total": 0}

        query = db.query(BlynkDevice).filter(BlynkDevice.farm_id.in_(farm_ids))
        if status:
            query = query.filter(BlynkDevice.status == status)

        total = query.count()
        rows: List[BlynkDevice] = (
            query.order_by(BlynkDevice.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [
                {
                    "id": d.id,
                    "farm_id": d.farm_id,
                    "device_name": d.device_name,
                    "blynk_device_id": d.blynk_device_id,
                    "is_active": bool(d.is_active),
                    "status": d.status,
                    "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
                    "last_error": d.last_error,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    except Exception as e:
        logger.error(f"Failed to list user iot devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to list user devices")


@router.get("/users/{user_id}/usage/tokens")
async def admin_user_token_usage(
    user_id: int,
    start: Optional[str] = None,
    end: Optional[str] = None,
    bucket: str = Query("day", pattern="^(hour|day|week|month)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        start_dt = _parse_iso_dt(start)
        end_dt = _parse_iso_dt(end)
        if start and start_dt is None:
            raise HTTPException(status_code=400, detail="Invalid 'start' timestamp; expected ISO format")
        if end and end_dt is None:
            raise HTTPException(status_code=400, detail="Invalid 'end' timestamp; expected ISO format")

        base = (
            db.query(AgentInteraction)
            .join(Farm, Farm.id == AgentInteraction.farm_id)
            .filter(Farm.user_id == user_id)
        )
        if start_dt is not None:
            base = base.filter(AgentInteraction.created_at >= start_dt)
        if end_dt is not None:
            base = base.filter(AgentInteraction.created_at <= end_dt)

        bucket_expr = func.date_trunc(bucket, AgentInteraction.created_at)
        rows = (
            base.with_entities(
                bucket_expr.label("bucket"),
                func.coalesce(func.sum(AgentInteraction.tokens_used), 0).label("tokens"),
                func.count(AgentInteraction.id).label("count"),
                func.coalesce(
                    func.sum(case((AgentInteraction.success == True, 1), else_=0)),
                    0,
                ).label("success_count"),
            )
            .group_by(bucket_expr)
            .order_by(bucket_expr.asc())
            .all()
        )

        total_tokens = int(sum(int(r.tokens or 0) for r in rows))
        total_interactions = int(sum(int(r.count or 0) for r in rows))

        return {
            "user_id": user_id,
            "bucket": bucket,
            "start": start_dt.isoformat() if start_dt else None,
            "end": end_dt.isoformat() if end_dt else None,
            "total_tokens": total_tokens,
            "total_interactions": total_interactions,
            "series": [
                {
                    "bucket": r.bucket.isoformat() if r.bucket else None,
                    "tokens": int(r.tokens or 0),
                    "interactions": int(r.count or 0),
                    "success_count": int(r.success_count or 0),
                }
                for r in rows
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compute user token usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute token usage")


class SuspendUserRequest(BaseModel):
    reason: str
    until: Optional[str] = None


class SensorOverrideCreateRequest(BaseModel):
    farm_id: int
    device_id: Optional[int] = None
    metric: str
    value: float
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    reason: Optional[str] = None


@router.get("/sensor-overrides")
async def admin_list_sensor_overrides(
    farm_id: Optional[int] = None,
    device_id: Optional[int] = None,
    metric: Optional[str] = None,
    active_only: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        query = db.query(SensorOverride)
        if farm_id is not None:
            query = query.filter(SensorOverride.farm_id == farm_id)
        if device_id is not None:
            query = query.filter(SensorOverride.device_id == device_id)
        if metric:
            query = query.filter(SensorOverride.metric == metric)
        if active_only:
            now = datetime.utcnow()
            query = query.filter(SensorOverride.deleted_at.is_(None))
            query = query.filter(SensorOverride.effective_from <= now)
            query = query.filter(or_(SensorOverride.effective_to.is_(None), SensorOverride.effective_to > now))

        total = query.count()
        rows: List[SensorOverride] = (
            query.order_by(SensorOverride.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [
                {
                    "id": int(o.id),
                    "farm_id": int(o.farm_id),
                    "device_id": int(o.device_id) if o.device_id is not None else None,
                    "metric": o.metric,
                    "value": float(o.value),
                    "effective_from": o.effective_from.isoformat() if o.effective_from else None,
                    "effective_to": o.effective_to.isoformat() if o.effective_to else None,
                    "reason": o.reason,
                    "created_by_admin_id": int(o.created_by_admin_id),
                    "deleted_at": o.deleted_at.isoformat() if o.deleted_at else None,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    except Exception as e:
        logger.error(f"Failed to list sensor overrides: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sensor overrides")


@router.post("/sensor-overrides")
async def admin_create_sensor_override(
    payload: SensorOverrideCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        start_dt = _parse_iso_dt(payload.effective_from) or datetime.utcnow()
        end_dt = _parse_iso_dt(payload.effective_to)
        if payload.effective_from and start_dt is None:
            raise HTTPException(status_code=400, detail="Invalid 'effective_from' timestamp; expected ISO format")
        if payload.effective_to and end_dt is None:
            raise HTTPException(status_code=400, detail="Invalid 'effective_to' timestamp; expected ISO format")

        ov = SensorOverride(
            farm_id=payload.farm_id,
            device_id=payload.device_id,
            metric=payload.metric,
            value=payload.value,
            effective_from=start_dt,
            effective_to=end_dt,
            reason=payload.reason,
            created_by_admin_id=current_user.id,
        )
        db.add(ov)
        _write_audit_event(
            db=db,
            request=request,
            actor_user_id=current_user.id,
            action_type="sensor_override.create",
            target_type="sensor_override",
            target_id="pending",
            reason=payload.reason,
            before_json=None,
            after_json={
                "farm_id": payload.farm_id,
                "device_id": payload.device_id,
                "metric": payload.metric,
                "value": payload.value,
                "effective_from": start_dt.isoformat(),
                "effective_to": end_dt.isoformat() if end_dt else None,
            },
        )
        db.commit()
        db.refresh(ov)

        return {"success": True, "id": int(ov.id)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create sensor override: {e}")
        raise HTTPException(status_code=500, detail="Failed to create sensor override")


@router.post("/sensor-overrides/{override_id}/expire")
async def admin_expire_sensor_override(
    override_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    ov = db.query(SensorOverride).filter(SensorOverride.id == override_id).first()
    if not ov:
        raise HTTPException(status_code=404, detail="Override not found")

    before = {
        "effective_to": ov.effective_to.isoformat() if ov.effective_to else None,
        "deleted_at": ov.deleted_at.isoformat() if ov.deleted_at else None,
    }
    now = datetime.utcnow()
    ov.effective_to = now
    ov.deleted_at = now

    after = {
        "effective_to": ov.effective_to.isoformat() if ov.effective_to else None,
        "deleted_at": ov.deleted_at.isoformat() if ov.deleted_at else None,
    }
    _write_audit_event(
        db=db,
        request=request,
        actor_user_id=current_user.id,
        action_type="sensor_override.expire",
        target_type="sensor_override",
        target_id=str(override_id),
        reason=None,
        before_json=before,
        after_json=after,
    )

    db.commit()
    return {"success": True, "id": int(override_id), "status": "expired"}


@router.post("/users/{user_id}/suspend")
async def admin_suspend_user(
    user_id: int,
    payload: SuspendUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    before = _user_snapshot(user)

    until_dt = _parse_iso_dt(payload.until)
    if payload.until and until_dt is None:
        raise HTTPException(status_code=400, detail="Invalid 'until' timestamp; expected ISO format")

    user.is_active = False
    user.suspended_at = datetime.utcnow()
    user.suspended_until = until_dt
    user.suspend_reason = payload.reason

    after = _user_snapshot(user)
    _write_audit_event(
        db=db,
        request=request,
        actor_user_id=current_user.id,
        action_type="user.suspend",
        target_type="user",
        target_id=str(user.id),
        reason=payload.reason,
        before_json=before,
        after_json=after,
    )

    db.commit()
    return {"success": True, "user_id": user.id, "status": "suspended"}


@router.post("/users/{user_id}/unsuspend")
async def admin_unsuspend_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    before = _user_snapshot(user)

    user.is_active = True
    user.suspended_at = None
    user.suspended_until = None
    user.suspend_reason = None

    after = _user_snapshot(user)
    _write_audit_event(
        db=db,
        request=request,
        actor_user_id=current_user.id,
        action_type="user.unsuspend",
        target_type="user",
        target_id=str(user.id),
        reason=None,
        before_json=before,
        after_json=after,
    )

    db.commit()
    return {"success": True, "user_id": user.id, "status": "active"}


@router.get("/farms")
async def admin_list_farms(
    user_id: Optional[int] = None,
    q: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        query = db.query(Farm)

        if user_id is not None:
            query = query.filter(Farm.user_id == user_id)
        if state:
            query = query.filter(Farm.state == state)
        if district:
            query = query.filter(Farm.district == district)

        if q:
            like = f"%{q.strip()}%"
            query = query.filter(
                (Farm.farm_name.ilike(like))
                | (Farm.village.ilike(like))
                | (Farm.district.ilike(like))
                | (Farm.state.ilike(like))
            )

        total = query.count()
        rows: List[Farm] = (
            query.order_by(Farm.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [
                {
                    "id": f.id,
                    "user_id": int(f.user_id) if f.user_id is not None else None,
                    "farm_name": f.farm_name,
                    "crop_type": f.crop_type,
                    "state": f.state,
                    "district": f.district,
                    "village": f.village,
                    "latitude": float(f.latitude) if f.latitude is not None else None,
                    "longitude": float(f.longitude) if f.longitude is not None else None,
                    "soil_type": f.soil_type,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "updated_at": f.updated_at.isoformat() if f.updated_at else None,
                }
                for f in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    except Exception as e:
        logger.error(f"Failed to list farms: {e}")
        raise HTTPException(status_code=500, detail="Failed to list farms")


@router.get("/farms/{farm_id}")
async def admin_get_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return {
        "id": farm.id,
        "user_id": int(farm.user_id) if farm.user_id is not None else None,
        "farm_name": farm.farm_name,
        "crop_type": farm.crop_type,
        "state": farm.state,
        "district": farm.district,
        "village": farm.village,
        "latitude": float(farm.latitude) if farm.latitude is not None else None,
        "longitude": float(farm.longitude) if farm.longitude is not None else None,
        "soil_type": farm.soil_type,
        "created_at": farm.created_at.isoformat() if farm.created_at else None,
        "updated_at": farm.updated_at.isoformat() if farm.updated_at else None,
    }


@router.get("/iot/devices")
async def admin_list_iot_devices(
    farm_id: Optional[int] = None,
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        query = db.query(BlynkDevice)
        if farm_id is not None:
            query = query.filter(BlynkDevice.farm_id == farm_id)
        if status:
            query = query.filter(BlynkDevice.status == status)
        if is_active is not None:
            query = query.filter(BlynkDevice.is_active == is_active)

        total = query.count()
        rows: List[BlynkDevice] = (
            query.order_by(BlynkDevice.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [
                {
                    "id": int(d.id),
                    "farm_id": int(d.farm_id),
                    "device_name": d.device_name,
                    "blynk_device_id": d.blynk_device_id,
                    "is_active": bool(d.is_active),
                    "status": d.status,
                    "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
                    "last_error": d.last_error,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    except Exception as e:
        logger.error(f"Failed to list IoT devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to list devices")


@router.get("/iot/telemetry/latest")
async def admin_latest_telemetry(
    farm_id: Optional[int] = None,
    device_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    if farm_id is None and device_id is None:
        raise HTTPException(status_code=400, detail="farm_id or device_id is required")

    query = db.query(SensorReading)
    if farm_id is not None:
        query = query.filter(SensorReading.farm_id == farm_id)
    if device_id is not None:
        query = query.filter(SensorReading.device_id == device_id)

    r = query.order_by(SensorReading.recorded_at.desc()).first()
    if not r:
        return {"has_data": False}

    return {
        "has_data": True,
        "reading": {
            "id": int(r.id),
            "farm_id": int(r.farm_id),
            "device_id": int(r.device_id),
            "air_temperature": float(r.air_temperature) if r.air_temperature is not None else None,
            "air_humidity": float(r.air_humidity) if r.air_humidity is not None else None,
            "soil_moisture": float(r.soil_moisture) if r.soil_moisture is not None else None,
            "soil_temperature": float(r.soil_temperature) if r.soil_temperature is not None else None,
            "soil_ec": float(r.soil_ec) if r.soil_ec is not None else None,
            "soil_ph": float(r.soil_ph) if r.soil_ph is not None else None,
            "nitrogen": float(r.nitrogen) if r.nitrogen is not None else None,
            "phosphorus": float(r.phosphorus) if r.phosphorus is not None else None,
            "potassium": float(r.potassium) if r.potassium is not None else None,
            "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
        },
    }


@router.get("/iot/telemetry")
async def admin_get_telemetry(
    farm_id: int,
    device_id: Optional[int] = None,
    from_ts: Optional[str] = Query(None, alias="from"),
    to_ts: Optional[str] = Query(None, alias="to"),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        query = db.query(SensorReading).filter(SensorReading.farm_id == farm_id)
        if device_id is not None:
            query = query.filter(SensorReading.device_id == device_id)

        from_dt = _parse_iso_dt(from_ts)
        to_dt = _parse_iso_dt(to_ts)

        if from_ts and from_dt is None:
            raise HTTPException(status_code=400, detail="Invalid 'from' timestamp; expected ISO format")
        if to_ts and to_dt is None:
            raise HTTPException(status_code=400, detail="Invalid 'to' timestamp; expected ISO format")

        if from_dt is not None:
            query = query.filter(SensorReading.recorded_at >= from_dt)
        if to_dt is not None:
            query = query.filter(SensorReading.recorded_at <= to_dt)

        rows: List[SensorReading] = query.order_by(SensorReading.recorded_at.desc()).limit(limit).all()
        points = [
            {
                "ts": r.recorded_at.isoformat() if r.recorded_at else None,
                "airTemperature": float(r.air_temperature) if r.air_temperature is not None else None,
                "airHumidity": float(r.air_humidity) if r.air_humidity is not None else None,
                "soilMoisture": float(r.soil_moisture) if r.soil_moisture is not None else None,
                "soilTemperature": float(r.soil_temperature) if r.soil_temperature is not None else None,
                "soilEC": float(r.soil_ec) if r.soil_ec is not None else None,
                "soilPH": float(r.soil_ph) if r.soil_ph is not None else None,
                "nitrogen": float(r.nitrogen) if r.nitrogen is not None else None,
                "phosphorus": float(r.phosphorus) if r.phosphorus is not None else None,
                "potassium": float(r.potassium) if r.potassium is not None else None,
            }
            for r in reversed(rows)
        ]

        return {
            "farm_id": farm_id,
            "device_id": device_id,
            "count": len(points),
            "points": points,
        }
    except Exception as e:
        logger.error(f"Failed to fetch telemetry: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch telemetry")


@router.get("/ai/interactions")
async def admin_list_agent_interactions(
    farm_id: Optional[int] = None,
    agent_name: Optional[str] = None,
    success: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        query = db.query(AgentInteraction)
        if farm_id is not None:
            query = query.filter(AgentInteraction.farm_id == farm_id)
        if agent_name:
            query = query.filter(AgentInteraction.agent_name == agent_name)
        if success is not None:
            query = query.filter(AgentInteraction.success == success)

        total = query.count()
        rows: List[AgentInteraction] = (
            query.order_by(AgentInteraction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [
                {
                    "id": i.id,
                    "farm_id": i.farm_id,
                    "agent_name": i.agent_name,
                    "tokens_used": int(i.tokens_used or 0),
                    "response_time_ms": i.response_time_ms,
                    "success": bool(i.success),
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                }
                for i in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    except Exception as e:
        logger.error(f"Failed to list agent interactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list interactions")


@router.get("/audit/events")
async def admin_audit_events(
    actor_user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        query = db.query(AdminAuditEvent)
        if actor_user_id is not None:
            query = query.filter(AdminAuditEvent.actor_user_id == actor_user_id)
        if action_type:
            query = query.filter(AdminAuditEvent.action_type == action_type)
        if target_type:
            query = query.filter(AdminAuditEvent.target_type == target_type)
        if target_id:
            query = query.filter(AdminAuditEvent.target_id == target_id)

        total = query.count()
        rows: List[AdminAuditEvent] = (
            query.order_by(AdminAuditEvent.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [
                {
                    "id": int(e.id),
                    "actor_user_id": int(e.actor_user_id),
                    "action_type": e.action_type,
                    "target_type": e.target_type,
                    "target_id": e.target_id,
                    "reason": e.reason,
                    "request_id": e.request_id,
                    "ip_address": e.ip_address,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    except Exception as e:
        logger.error(f"Failed to list audit events: {e}")
        raise HTTPException(status_code=500, detail="Failed to list audit events")


@router.get("/metrics")
async def get_admin_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        interactions = (
            db.query(AgentInteraction)
            .order_by(AgentInteraction.created_at.desc())
            .limit(10)
            .all()
        )

        return [
            {
                "timestamp": i.created_at.isoformat() if i.created_at else None,
                "agent_name": i.agent_name,
                "tokens_used": int(i.tokens_used or 0),
            }
            for i in interactions
            if i.created_at is not None
        ]
    except Exception as e:
        logger.error(f"Failed to fetch admin metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")
