import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import pytz
from ..utils.cache import CacheManager
from ..utils.config import get_config

class PrayerTimeService:
    """Prayer time intelligence service for message scheduling."""
    
    def __init__(self):
        self.config = get_config()
        self.base_url = "https://api.aladhan.com/v1"
        self.cache = CacheManager()
        self.prayer_buffer_minutes = 10  # 10-minute buffer before/after prayers
        
        # Saudi cities mapping
        self.saudi_cities = {
            "riyadh": {"city": "Riyadh", "country": "Saudi Arabia"},
            "jeddah": {"city": "Jeddah", "country": "Saudi Arabia"},
            "mecca": {"city": "Mecca", "country": "Saudi Arabia"},
            "medina": {"city": "Medina", "country": "Saudi Arabia"},
            "dammam": {"city": "Dammam", "country": "Saudi Arabia"},
            "khobar": {"city": "Al Khobar", "country": "Saudi Arabia"},
            "tabuk": {"city": "Tabuk", "country": "Saudi Arabia"},
            "abha": {"city": "Abha", "country": "Saudi Arabia"}
        }
        
        # Prayer names in order
        self.prayer_names = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
        
        self.client = httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": "CRM-RES AI Processor"}
        )
    
    async def is_prayer_time(self, city: str = "Riyadh") -> bool:
        """Check if it's currently prayer time (with buffer)."""
        try:
            current_prayer = await self.get_current_prayer(city)
            return current_prayer is not None
        except Exception as e:
            print(f"Error checking prayer time: {e}")
            return False
    
    async def get_current_prayer(self, city: str = "Riyadh") -> Optional[str]:
        """Get current prayer if within prayer time window."""
        try:
            prayer_times = await self.get_prayer_times(city)
            if not prayer_times:
                return None
            
            now = datetime.now(pytz.timezone('Asia/Riyadh'))
            current_time = now.time()
            
            for prayer_name, prayer_time_str in prayer_times.items():
                if prayer_name in self.prayer_names:
                    prayer_time = datetime.strptime(prayer_time_str, "%H:%M").time()
                    
                    # Create buffer window
                    prayer_dt = datetime.combine(now.date(), prayer_time)
                    buffer_start = prayer_dt - timedelta(minutes=self.prayer_buffer_minutes)
                    buffer_end = prayer_dt + timedelta(minutes=self.prayer_buffer_minutes)
                    
                    now_dt = datetime.combine(now.date(), current_time)
                    
                    if buffer_start.time() <= current_time <= buffer_end.time():
                        return prayer_name
            
            return None
            
        except Exception as e:
            print(f"Error getting current prayer: {e}")
            return None
    
    async def get_next_prayer(self, city: str = "Riyadh") -> Optional[Dict[str, Any]]:
        """Get next prayer time and minutes until it."""
        try:
            prayer_times = await self.get_prayer_times(city)
            if not prayer_times:
                return None
            
            now = datetime.now(pytz.timezone('Asia/Riyadh'))
            current_time = now.time()
            
            # Find next prayer
            for prayer_name in self.prayer_names:
                if prayer_name in prayer_times:
                    prayer_time = datetime.strptime(prayer_times[prayer_name], "%H:%M").time()
                    
                    if current_time < prayer_time:
                        prayer_dt = datetime.combine(now.date(), prayer_time)
                        now_dt = datetime.combine(now.date(), current_time)
                        minutes_until = int((prayer_dt - now_dt).total_seconds() / 60)
                        
                        return {
                            "prayer": prayer_name,
                            "time": prayer_times[prayer_name],
                            "minutes_until": minutes_until
                        }
            
            # If no more prayers today, get Fajr of next day
            tomorrow = now + timedelta(days=1)
            tomorrow_prayers = await self.get_prayer_times(city, tomorrow.date())
            
            if tomorrow_prayers and "Fajr" in tomorrow_prayers:
                fajr_time = datetime.strptime(tomorrow_prayers["Fajr"], "%H:%M").time()
                fajr_dt = datetime.combine(tomorrow.date(), fajr_time)
                now_dt = datetime.combine(now.date(), current_time)
                minutes_until = int((fajr_dt - now_dt).total_seconds() / 60)
                
                return {
                    "prayer": "Fajr",
                    "time": tomorrow_prayers["Fajr"],
                    "minutes_until": minutes_until
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting next prayer: {e}")
            return None
    
    async def get_prayer_times(self, city: str = "Riyadh", date: Optional[datetime] = None) -> Optional[Dict[str, str]]:
        """Get prayer times for a specific city and date."""
        try:
            if date is None:
                date = datetime.now(pytz.timezone('Asia/Riyadh')).date()
            
            # Check cache first
            cache_key = f"prayer_times_{city.lower()}_{date.isoformat()}"
            cached_times = await self.cache.get(cache_key)
            if cached_times:
                return cached_times
            
            # Get city info
            city_info = self.saudi_cities.get(city.lower())
            if not city_info:
                city_info = {"city": city, "country": "Saudi Arabia"}
            
            # Make API request
            params = {
                "city": city_info["city"],
                "country": city_info["country"],
                "method": 4,  # Umm Al-Qura University, Makkah
                "date": date.strftime("%d-%m-%Y")
            }
            
            response = await self.client.get(f"{self.base_url}/timingsByCity", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") == 200 and "data" in data:
                timings = data["data"]["timings"]
                
                # Extract main prayer times
                prayer_times = {
                    "Fajr": timings.get("Fajr", ""),
                    "Dhuhr": timings.get("Dhuhr", ""),
                    "Asr": timings.get("Asr", ""),
                    "Maghrib": timings.get("Maghrib", ""),
                    "Isha": timings.get("Isha", "")
                }
                
                # Remove timezone info and keep only HH:MM
                for prayer in prayer_times:
                    if prayer_times[prayer]:
                        prayer_times[prayer] = prayer_times[prayer].split()[0]  # Remove timezone
                
                # Cache for 24 hours
                await self.cache.set(cache_key, prayer_times, expire=86400)
                
                return prayer_times
            
            return None
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit
                print(f"Prayer times API rate limit reached for {city}")
                await asyncio.sleep(2)
                return None
            raise
        except Exception as e:
            print(f"Error fetching prayer times for {city}: {e}")
            return None
    
    async def is_ramadan_period(self) -> bool:
        """Check if it's currently Ramadan period."""
        try:
            # Use Hijri calendar API
            now = datetime.now(pytz.timezone('Asia/Riyadh'))
            
            response = await self.client.get(
                f"{self.base_url}/hijriCalendarByCity",
                params={
                    "city": "Riyadh",
                    "country": "Saudi Arabia",
                    "date": now.strftime("%d-%m-%Y")
                }
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 200 and "data" in data:
                hijri_month = data["data"]["hijri"]["month"]["number"]
                return hijri_month == 9  # Ramadan is the 9th month
            
            return False
            
        except Exception as e:
            print(f"Error checking Ramadan period: {e}")
            return False
    
    async def get_ramadan_schedule_adjustments(self) -> Dict[str, Any]:
        """Get special adjustments for Ramadan period."""
        try:
            is_ramadan = await self.is_ramadan_period()
            
            if not is_ramadan:
                return {"is_ramadan": False, "adjustments": {}}
            
            return {
                "is_ramadan": True,
                "adjustments": {
                    "extended_maghrib_buffer": 30,  # 30 minutes for Iftar
                    "extended_fajr_buffer": 15,     # 15 minutes for Suhoor
                    "special_greetings": [
                        "رمضان كريم",
                        "كل عام وأنتم بخير",
                        "تقبل الله صيامكم"
                    ],
                    "iftar_awareness": True,
                    "tarawih_awareness": True
                }
            }
            
        except Exception as e:
            print(f"Error getting Ramadan adjustments: {e}")
            return {"is_ramadan": False, "adjustments": {}}
    
    async def should_delay_message(self, city: str = "Riyadh") -> Dict[str, Any]:
        """Check if message should be delayed due to prayer time."""
        try:
            current_prayer = await self.get_current_prayer(city)
            next_prayer = await self.get_next_prayer(city)
            ramadan_adjustments = await self.get_ramadan_schedule_adjustments()
            
            if current_prayer:
                # Calculate delay based on prayer and Ramadan adjustments
                base_delay = self.prayer_buffer_minutes
                
                if ramadan_adjustments["is_ramadan"]:
                    adjustments = ramadan_adjustments["adjustments"]
                    if current_prayer == "Maghrib":
                        base_delay = adjustments.get("extended_maghrib_buffer", 30)
                    elif current_prayer == "Fajr":
                        base_delay = adjustments.get("extended_fajr_buffer", 15)
                
                return {
                    "should_delay": True,
                    "delay_minutes": base_delay,
                    "reason": f"prayer_time_{current_prayer.lower()}",
                    "message": f"تم تأجيل الرسالة بسبب وقت صلاة {current_prayer}"
                }
            
            return {"should_delay": False, "delay_minutes": 0, "reason": None, "message": None}
            
        except Exception as e:
            print(f"Error checking message delay: {e}")
            return {"should_delay": False, "delay_minutes": 0, "reason": None, "message": None}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()