from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from farmxpert.models.farm_models import Farm, Field, Crop, Task, SoilTest, Yield, WeatherData, MarketPrice
from datetime import datetime, timedelta

class FarmRepository:
    def __init__(self, db: Session):
        self.db = db
    
    # Farm operations
    def create_farm(self, farm_data: Dict[str, Any]) -> Farm:
        farm = Farm(**farm_data)
        self.db.add(farm)
        self.db.commit()
        self.db.refresh(farm)
        return farm
    
    def get_farm(self, farm_id: int) -> Optional[Farm]:
        return self.db.query(Farm).filter(Farm.id == farm_id).first()
    
    def get_farms_by_location(self, location: str) -> List[Farm]:
        return self.db.query(Farm).filter(Farm.location.ilike(f"%{location}%")).all()
    
    def update_farm(self, farm_id: int, farm_data: Dict[str, Any]) -> Optional[Farm]:
        farm = self.get_farm(farm_id)
        if farm:
            for key, value in farm_data.items():
                setattr(farm, key, value)
            self.db.commit()
            self.db.refresh(farm)
        return farm
    
    # Field operations
    def create_field(self, field_data: Dict[str, Any]) -> Field:
        field = Field(**field_data)
        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)
        return field
    
    def get_farm_fields(self, farm_id: int) -> List[Field]:
        return self.db.query(Field).filter(Field.farm_id == farm_id).all()
    
    # Crop operations
    def create_crop(self, crop_data: Dict[str, Any]) -> Crop:
        crop = Crop(**crop_data)
        self.db.add(crop)
        self.db.commit()
        self.db.refresh(crop)
        return crop
    
    def get_farm_crops(self, farm_id: int, status: Optional[str] = None) -> List[Crop]:
        query = self.db.query(Crop).filter(Crop.farm_id == farm_id)
        if status:
            query = query.filter(Crop.status == status)
        return query.all()
    
    def get_active_crops(self, farm_id: int) -> List[Crop]:
        return self.get_farm_crops(farm_id, status="growing")
    
    def update_crop_status(self, crop_id: int, status: str) -> Optional[Crop]:
        crop = self.db.query(Crop).filter(Crop.id == crop_id).first()
        if crop:
            crop.status = status
            self.db.commit()
            self.db.refresh(crop)
        return crop
    
    # Task operations
    def create_task(self, task_data: Dict[str, Any]) -> Task:
        task = Task(**task_data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_farm_tasks(self, farm_id: int, status: Optional[str] = None, 
                      start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None) -> List[Task]:
        query = self.db.query(Task).filter(Task.farm_id == farm_id)
        
        if status:
            query = query.filter(Task.status == status)
        if start_date:
            query = query.filter(Task.scheduled_date >= start_date)
        if end_date:
            query = query.filter(Task.scheduled_date <= end_date)
        
        return query.order_by(Task.scheduled_date).all()
    
    def get_today_tasks(self, farm_id: int) -> List[Task]:
        today = datetime.now().date()
        return self.db.query(Task).filter(
            Task.farm_id == farm_id,
            Task.scheduled_date >= today,
            Task.scheduled_date < today + timedelta(days=1)
        ).all()
    
    def update_task_status(self, task_id: int, status: str, completed_date: Optional[datetime] = None) -> Optional[Task]:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = status
            if completed_date:
                task.completed_date = completed_date
            self.db.commit()
            self.db.refresh(task)
        return task
    
    # Soil test operations
    def create_soil_test(self, soil_test_data: Dict[str, Any]) -> SoilTest:
        soil_test = SoilTest(**soil_test_data)
        self.db.add(soil_test)
        self.db.commit()
        self.db.refresh(soil_test)
        return soil_test
    
    def get_latest_soil_test(self, farm_id: int, field_id: Optional[int] = None) -> Optional[SoilTest]:
        query = self.db.query(SoilTest).filter(SoilTest.farm_id == farm_id)
        if field_id:
            query = query.filter(SoilTest.field_id == field_id)
        return query.order_by(SoilTest.test_date.desc()).first()
    
    def get_soil_test_history(self, farm_id: int, field_id: Optional[int] = None, 
                             limit: int = 10) -> List[SoilTest]:
        query = self.db.query(SoilTest).filter(SoilTest.farm_id == farm_id)
        if field_id:
            query = query.filter(SoilTest.field_id == field_id)
        return query.order_by(SoilTest.test_date.desc()).limit(limit).all()
    
    # Yield operations
    def create_yield(self, yield_data: Dict[str, Any]) -> Yield:
        yield_record = Yield(**yield_data)
        self.db.add(yield_record)
        self.db.commit()
        self.db.refresh(yield_record)
        return yield_record
    
    def get_crop_yields(self, crop_id: int) -> List[Yield]:
        return self.db.query(Yield).filter(Yield.crop_id == crop_id).order_by(Yield.harvest_date.desc()).all()
    
    def get_farm_yields(self, farm_id: int, year: Optional[int] = None) -> List[Yield]:
        query = self.db.query(Yield).join(Crop).filter(Crop.farm_id == farm_id)
        if year:
            query = query.filter(Yield.harvest_date >= datetime(year, 1, 1))
            query = query.filter(Yield.harvest_date < datetime(year + 1, 1, 1))
        return query.order_by(Yield.harvest_date.desc()).all()
    
    # Weather data operations
    def create_weather_data(self, weather_data: Dict[str, Any]) -> WeatherData:
        weather = WeatherData(**weather_data)
        self.db.add(weather)
        self.db.commit()
        self.db.refresh(weather)
        return weather
    
    def get_recent_weather(self, farm_id: int, days: int = 7) -> List[WeatherData]:
        start_date = datetime.now() - timedelta(days=days)
        return self.db.query(WeatherData).filter(
            WeatherData.farm_id == farm_id,
            WeatherData.date >= start_date
        ).order_by(WeatherData.date.desc()).all()
    
    def get_weather_forecast(self, farm_id: int) -> Optional[WeatherData]:
        return self.db.query(WeatherData).filter(
            WeatherData.farm_id == farm_id,
            WeatherData.forecast_data.isnot(None)
        ).order_by(WeatherData.date.desc()).first()
    
    # Market price operations
    def create_market_price(self, price_data: Dict[str, Any]) -> MarketPrice:
        price = MarketPrice(**price_data)
        self.db.add(price)
        self.db.commit()
        self.db.refresh(price)
        return price
    
    def get_latest_prices(self, crop_types: List[str], location: Optional[str] = None) -> List[MarketPrice]:
        query = self.db.query(MarketPrice).filter(MarketPrice.crop_type.in_(crop_types))
        if location:
            query = query.filter(MarketPrice.market_location.ilike(f"%{location}%"))
        
        # Get latest price for each crop type
        latest_prices = []
        for crop_type in crop_types:
            latest = query.filter(MarketPrice.crop_type == crop_type).order_by(
                MarketPrice.date.desc()
            ).first()
            if latest:
                latest_prices.append(latest)
        
        return latest_prices
    
    def get_price_history(self, crop_type: str, location: Optional[str] = None, 
                         days: int = 30) -> List[MarketPrice]:
        start_date = datetime.now() - timedelta(days=days)
        query = self.db.query(MarketPrice).filter(
            MarketPrice.crop_type == crop_type,
            MarketPrice.date >= start_date
        )
        if location:
            query = query.filter(MarketPrice.market_location.ilike(f"%{location}%"))
        
        return query.order_by(MarketPrice.date.desc()).all()
    
    # Analytics and reporting
    def get_farm_summary(self, farm_id: int) -> Dict[str, Any]:
        farm = self.get_farm(farm_id)
        if not farm:
            return {}
        
        active_crops = len(self.get_active_crops(farm_id))
        pending_tasks = len(self.get_farm_tasks(farm_id, status="pending"))
        today_tasks = len(self.get_today_tasks(farm_id))
        
        # Get recent yields
        recent_yields = self.get_farm_yields(farm_id, year=datetime.now().year)
        total_yield = sum(y.quantity_tons for y in recent_yields)
        total_value = sum(y.total_value for y in recent_yields if y.total_value)
        
        return {
            "farm": farm,
            "active_crops": active_crops,
            "pending_tasks": pending_tasks,
            "today_tasks": today_tasks,
            "total_yield_this_year": total_yield,
            "total_value_this_year": total_value,
            "recent_yields": recent_yields[:5]  # Last 5 yields
        }
