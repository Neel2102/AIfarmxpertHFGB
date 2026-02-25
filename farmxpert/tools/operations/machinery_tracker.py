from sqlalchemy.orm import Session
from farmxpert.models.database import SessionLocal
from farmxpert.models.farm_models import FarmEquipment
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MachineryTrackerTool:
    """
    Tool to track machinery maintenance and usage.
    Interacts with the FarmEquipment database model.
    """
    
    def get_maintenance_alerts(self, farm_id: int) -> List[Dict[str, Any]]:
        """
        Get list of equipment due for maintenance.
        """
        db = SessionLocal()
        try:
            today = datetime.now()
            # Find equipment where next_maintenance is in the past or within 7 days
            alert_date = today + timedelta(days=7)
            
            equipment = db.query(FarmEquipment).filter(
                FarmEquipment.farm_id == farm_id,
                FarmEquipment.status == "active",
                FarmEquipment.next_maintenance <= alert_date
            ).all()
            
            alerts = []
            for eq in equipment:
                days_overdue = (today - eq.next_maintenance.replace(tzinfo=None)).days
                status = "overdue" if days_overdue > 0 else "due_soon"
                
                alerts.append({
                    "equipment_id": eq.id,
                    "name": eq.name,
                    "type": eq.equipment_type,
                    "status": status,
                    "due_date": eq.next_maintenance.strftime("%Y-%m-%d"),
                    "days_remaining": -days_overdue
                })
            
            return alerts
        except Exception as e:
            logger.error(f"Error checking maintenance alerts: {e}")
            return []
        finally:
            db.close()

    def update_maintenance_log(self, equipment_id: int, notes: str, next_service_days: int = 90) -> Dict[str, Any]:
        """
        Log completed maintenance and schedule next service.
        """
        db = SessionLocal()
        try:
            eq = db.query(FarmEquipment).filter(FarmEquipment.id == equipment_id).first()
            if not eq:
                return {"success": False, "error": "Equipment not found"}
            
            now = datetime.now()
            eq.last_maintenance = now
            eq.next_maintenance = now + timedelta(days=next_service_days)
            
            # Append to maintenance history (assuming JSON field exists or we just append to notes for now)
            history_entry = f"[{now.strftime('%Y-%m-%d')}] Service completed: {notes}\n"
            eq.notes = (eq.notes or "") + "\n" + history_entry
            
            db.commit()
            return {
                "success": True, 
                "equipment": eq.name,
                "next_service": eq.next_maintenance.strftime("%Y-%m-%d")
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating maintenance log: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()
