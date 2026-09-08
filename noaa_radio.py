import requests
import json
import time
from datetime import datetime
import win32com.client
import winsound
import random
import threading
import re
import os
import pythoncom

class NOAAWeatherRadio:
    def __init__(self, station_data=None):
        # Default station is Gunnison
        if station_data is None:
            station_data = {
                "callsign": "KXI90",
                "frequency": "162.450",
                "lat": 38.5458,
                "lon": -107.0439,
                "city": "Gunnison County",
                "state": "Colorado",
                "region": "mountain",
                "station_id": "WNG549",
                "description": "Gunnison Valley, Elk Mountains",
                "opening": "You are listening to NOAA All-Hazards Radio, the voice of the National Weather Service, station WNG549 in Gunnison County, Colorado, broadcasting on a frequency of 162.450 Megahertz."
            }
        
        self.station = station_data
        self.lat = station_data["lat"]
        self.lon = station_data["lon"]
        self.city = station_data["city"]
        self.state = station_data["state"]
        self.callsign = station_data["callsign"]
        self.frequency = station_data["frequency"]
        self.station_id = station_data["station_id"]
        self.region = station_data.get("region", "default")
        self.custom_opening = station_data.get("opening", None)
        
        self.headers = {"User-Agent": "NOAARadio/1.0 (radio@example.com)"}
        self.speaker = None
        self.emergency_active = False
        
        self.last_emergency_time = 0
        self.last_emergency_event = ""
        self.pending_emergency = None
        self.emergency_lock = threading.Lock()
        self.has_advisory = False
        self.pending_advisory = None
        
        self.paul_voice = None
        self.tom_voice = None
        self.donna_voice = None
        self.harry_voice = None
        
        self.station_ids = [self.station_id, "KXI60", "WNG555", "KXI58", "WNG640", "KEC61", "WNG638"]
        
        # ============ TEST SİSTEMİ ============
        self.test_mode = True
        self.last_test_time = 0
        self.last_test_type = ""
        
        self.init_speaker()
        self.emergency_checked = False
    
    def init_speaker(self):
        try:
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            voices = self.speaker.GetVoices()
            
            print("=" * 60)
            print(f"📻 NOAA Weather Radio - {self.callsign}")
            print(f"📍 {self.city}, {self.state}")
            print(f"📡 Frequency: {self.frequency} MHz")
            print("=" * 60)
            
            for voice in voices:
                desc = voice.GetDescription().lower()
                
                if "nws harry" in desc or "harry" in desc:
                    self.harry_voice = voice
                    print("✅ NWS Harry found!")
                
                if "nws paul" in desc or "paul" in desc:
                    self.paul_voice = voice
                    print("✅ NWS Paul found!")
                
                if "att crystal16" in desc or "crystal16" in desc or "donna" in desc:
                    self.donna_voice = voice
                    print("✅ Donna (ATT Crystal16) found!")
            
            try:
                self.tom_voice = voices.Item(20)
                print(f"✅ Speechify Tom found with INDEX 20!")
            except:
                print("⚠️ Tom INDEX 20 not found, searching by name...")
                for voice in voices:
                    desc = voice.GetDescription().lower()
                    if "speechify tom" in desc or "scansoft tom" in desc or "tom" in desc:
                        self.tom_voice = voice
                        print(f"✅ Speechify Tom found by name!")
                        break
            
            if self.paul_voice:
                self.speaker.Voice = self.paul_voice
                print("🎯 Default voice: NWS Paul")
            elif self.tom_voice:
                self.speaker.Voice = self.tom_voice
                print("🎯 Default voice: Tom")
            elif self.donna_voice:
                self.speaker.Voice = self.donna_voice
                print("🎯 Default voice: Donna")
            else:
                print("⚠️ No NWS voices found!")
            
            print("=" * 60)
                    
        except Exception as e:
            print(f"❌ Voice error: {e}")
            self.speaker = None
    
    def speak_with_voice(self, text, voice_name="paul", rate=0):
        if self.speaker is None:
            return False
        
        if not text:
            return False
        
        clean_text = self.clean_tts_text(text)
        
        if not clean_text:
            return False
        
        try:
            def speak_thread():
                try:
                    pythoncom.CoInitialize()
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    voices = speaker.GetVoices()
                    selected_voice = None
                    
                    if voice_name == "harry":
                        for voice in voices:
                            if "nws harry" in voice.GetDescription().lower() or "harry" in voice.GetDescription().lower():
                                selected_voice = voice
                                break
                    
                    elif voice_name == "paul":
                        for voice in voices:
                            if "nws paul" in voice.GetDescription().lower() or "paul" in voice.GetDescription().lower():
                                selected_voice = voice
                                break
                    
                    elif voice_name == "donna":
                        for voice in voices:
                            desc = voice.GetDescription().lower()
                            if "att crystal16" in desc or "crystal16" in desc or "donna" in desc:
                                selected_voice = voice
                                break
                    
                    elif voice_name == "tom":
                        try:
                            selected_voice = voices.Item(20)
                        except:
                            for voice in voices:
                                desc = voice.GetDescription().lower()
                                if "speechify tom" in desc or "scansoft tom" in desc or "tom" in desc:
                                    selected_voice = voice
                                    break
                    
                    if not selected_voice:
                        selected_voice = voices.Item(0)
                    
                    speaker.Voice = selected_voice
                    speaker.Rate = rate
                    speaker.Speak(clean_text)
                    pythoncom.CoUninitialize()
                    
                except Exception as e:
                    print(f"❌ Speech thread error: {e}")
            
            thread = threading.Thread(target=speak_thread, daemon=True)
            thread.start()
            thread.join()
            return True
            
        except Exception as e:
            print(f"❌ Speech error: {e}")
            return False
    
    def get_weather_data(self):
        try:
            points_url = f"https://api.weather.gov/points/{self.lat},{self.lon}"
            points_response = requests.get(points_url, headers=self.headers)
            points_data = points_response.json()
            
            forecast_url = points_data['properties']['forecast']
            forecast_response = requests.get(forecast_url, headers=self.headers)
            forecast_data = forecast_response.json()
            
            alert_url = points_data['properties'].get('alert', f"https://api.weather.gov/alerts/active?point={self.lat},{self.lon}")
            alert_response = requests.get(alert_url, headers=self.headers)
            alert_data = alert_response.json()
            
            return {
                'forecast': forecast_data,
                'alerts': alert_data,
                'city': self.city,
                'state': self.state
            }
            
        except Exception as e:
            print(f"❌ Data error: {e}")
            return None
    
    def clean_area(self, area):
        """State kısaltmalarını temizle (örn: Lancaster, PA -> Lancaster)"""
        if not area:
            return "this area"
        
        area_clean = re.sub(r',\s*[A-Z]{2}\s*$', '', area)
        area_clean = re.sub(r',\s*[A-Z]{2}\s*,', ',', area_clean)
        area_clean = area_clean.strip()
        
        return area_clean
    
    # ============================================================
    # 1. HARRY - OPENING
    # ============================================================
    def get_opening_message(self):
        """İstasyona özel açılış metni - Sesine göre format değişir"""
        
        # Eğer özel açılış metni varsa onu kullan
        if self.custom_opening:
            return self.custom_opening
        
        # İstasyonun sesini al
        voice = self.station.get("voice", "tom")
        callsign = self.callsign
        station_id = self.station_id
        frequency = self.frequency
        city = self.city
        state = self.state
        
        # ============ TOM AÇILIŞ FORMATI ============
        if voice == "tom":
            openings = [
                f"This is NOAA Weather Radio {station_id} originating from the National Weather Service forecast office in {city}, {state}. We supply the latest available information for the {city} area over station {station_id} on a frequency of {frequency} Megahertz.",
                
                f"You are listening to NOAA Weather Radio station {station_id}, broadcasting on a frequency of {frequency} Megahertz. This station is operated by the National Weather Service in {city}, {state}.",
                
                f"This is NOAA Weather Radio Station {station_id} in {city}, {state}. Broadcast Programming originates from the National Weather Service in {city}.",
                
                f"NOAA Weather Radio station {station_id} in {city}, {state}, broadcasting on a frequency of {frequency} Megahertz. This station is operated by the National Weather Service.",
                
                f"This is NOAA Weather Radio station {station_id} from the National Weather Service in {city}. We provide weather information for the {city} area on {frequency} Megahertz."
            ]
            return random.choice(openings)
        
        # ============ PAUL AÇILIŞ FORMATI ============
        elif voice == "paul":
            openings = [
                f"This is NOAA Weather Radio station {station_id} in {city}, {state}, broadcasting on a frequency of {frequency} Megahertz.",
                
                f"This is NOAA Weather Radio Hazards, station {station_id} in {city}. The station broadcast from the National Weather Service, at the frequency of {frequency} Megahertz.",
                
                f"This is NOAA Weather Radio station {station_id}. We broadcast from the National Weather Service in {city}, {state} on {frequency} Megahertz.",
                
                f"You are listening to NOAA Weather Radio station {station_id} in {city}, {state}, transmitting on {frequency} Megahertz."
            ]
            return random.choice(openings)
        
        # ============ HARRY AÇILIŞ FORMATI ============
        else:
            openings = [
                f"This is NOAA Weather Radio station {station_id} in {city}, broadcasting on a frequency of {frequency} Megahertz.",
                
                f"This is the NOAA Weather Radio {station_id} in {city}. {station_id} operates on a frequency of {frequency} Megahertz.",
                
                f"This is NOAA Weather Radio Hazards, station {station_id} in {city}, at the frequency of {frequency} Megahertz.",
                
                f"NOAA Weather Radio station {station_id} in {city}, {state}. Frequency {frequency} Megahertz."
            ]
            return random.choice(openings)
    
    # ============================================================
    # 2. PAUL - TIME ANNOUNCEMENT
    # ============================================================
    def time_announcement(self):
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        
        import time
        is_dst = time.daylight and time.localtime().tm_isdst
        
        tz_map = {
            "mountain": "MDT" if is_dst else "MST",
            "coastal": "PDT" if is_dst else "PST",
            "urban": "CDT" if is_dst else "CST",
            "plains": "CDT" if is_dst else "CST",
            "southeast": "EDT" if is_dst else "EST",
            "arctic": "AKDT" if is_dst else "AKST"
        }
        
        tz = tz_map.get(self.region, "MST")
        
        return f"The current time is {time_str} {tz}."
    
    # ============================================================
    # 3. TOM - HOURLY ROUNDUP (UZUN VE DETAYLI)
    # ============================================================
    def get_hourly_roundup(self, data):
        """Saatlik hava durumu özeti - UZUN ve detaylı - TOM okur"""
        if not data:
            return "Hourly weather roundup not available."
        
        forecast = data.get('forecast', {})
        city = self.city
        state = self.state
        
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        
        import time
        is_dst = time.daylight and time.localtime().tm_isdst
        tz = "MDT" if is_dst else "MST"
        
        message_parts = []
        message_parts.append(f"Hourly weather roundup for {city}, {state}.")
        message_parts.append(f"At {time_str} {tz},")
        
        if forecast and 'properties' in forecast:
            periods = forecast['properties']['periods']
            if periods:
                current = periods[0]
                temp = current.get('temperature', '')
                short = current.get('shortForecast', '')
                wind = current.get('windSpeed', '')
                wind_dir = current.get('windDirection', '')
                precip = current.get('probabilityOfPrecipitation', {}).get('value', 0)
                
                if temp:
                    message_parts.append(f"the temperature is {temp} degrees Fahrenheit.")
                if wind and wind != " " and wind.strip():
                    if wind_dir and wind_dir != " " and wind_dir.strip():
                        message_parts.append(f"Winds are from the {wind_dir} at {wind}.")
                    else:
                        message_parts.append(f"Wind speeds are {wind}.")
                if short and short != " " and short.strip():
                    message_parts.append(f"Skies are {short.lower()}.")
                if precip and precip > 0:
                    message_parts.append(f"There is a {int(precip)} percent chance of precipitation.")
        
        # ============ UZUN DETAYLAR ============
        # Nem
        humidity = random.randint(25, 75)
        message_parts.append(f"Humidity is {humidity} percent.")
        
        # Çiy Noktası (Dew Point)
        dew_point = random.randint(35, 65)
        message_parts.append(f"The dew point is {dew_point} degrees Fahrenheit.")
        
        # Rüzgar Rüzgarları (Wind Gusts)
        wind_gust = random.randint(15, 35)
        message_parts.append(f"Wind gusts of up to {wind_gust} miles per hour are possible.")
        
        # Barometrik Basınç
        pressure = random.uniform(29.85, 30.25)
        pressure_trend = random.choice(['rising', 'falling', 'steady'])
        message_parts.append(f"Barometric pressure is {pressure:.2f} inches and {pressure_trend}.")
        
        # Görüş Mesafesi (Visibility)
        visibility = random.randint(5, 15)
        message_parts.append(f"Visibility is {visibility} miles.")
        
        # Bulut Örtüsü (Cloud Cover)
        cloud_cover = random.choice([
            "clear skies",
            "mostly clear",
            "partly cloudy",
            "mostly cloudy",
            "overcast"
        ])
        message_parts.append(f"Cloud cover is {cloud_cover}.")
        
        # Yağış Durumu
        precip_status = random.choice([
            "No precipitation expected in the past hour.",
            "Light rain showers have been reported.",
            "Scattered showers in the area.",
            "Snow flurries observed.",
            "Drizzle reported at nearby stations."
        ])
        message_parts.append(precip_status)
        
        # UV İndeksi (Gündüz ise)
        hour = now.hour
        if 8 <= hour <= 17:
            uv_index = random.randint(0, 10)
            uv_category = "low"
            if uv_index >= 8:
                uv_category = "very high"
            elif uv_index >= 6:
                uv_category = "high"
            elif uv_index >= 3:
                uv_category = "moderate"
            message_parts.append(f"UV index is {uv_index}, which is {uv_category}.")
        
        # Ek Bilgiler (opsiyonel)
        message_parts.append(f"Additional observations from nearby stations:")
        
        # 2-3 rastgele ek istasyon
        extra_stations = [
            {"name": "Crested Butte", "temp": random.randint(20, 40), "wind": random.randint(5, 15)},
            {"name": "Monarch Pass", "temp": random.randint(15, 35), "wind": random.randint(10, 25)},
            {"name": "Lake City", "temp": random.randint(25, 45), "wind": random.randint(5, 10)},
        ]
        
        for station in extra_stations:
            message_parts.append(
                f"At {station['name']}, temperature is {station['temp']} degrees, "
                f"winds at {station['wind']} miles per hour."
            )
        
        # Kapanış
        message_parts.append(f"This concludes the hourly weather roundup for {city} at {time_str} {tz}.")
        
        return ' '.join(message_parts)
    
    # ============================================================
    # 4. TOM - NOWCAST
    # ============================================================
    def get_nowcast(self, data):
        if not data:
            return "Short-term forecast not available."
        
        forecast = data.get('forecast', {})
        city = self.city
        
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        
        message_parts = []
        message_parts.append(f"Short-term forecast for {city}.")
        message_parts.append(f"Issued at {time_str}.")
        
        if forecast and 'properties' in forecast:
            periods = forecast['properties']['periods']
            if len(periods) >= 2:
                current = periods[0]
                tonight = periods[1]
                
                temp = current.get('temperature', '')
                short = current.get('shortForecast', '')
                
                if temp and short:
                    message_parts.append(f"Currently, temperature is {temp} degrees with {short.lower()}.")
                
                tonight_short = tonight.get('shortForecast', '')
                tonight_temp = tonight.get('temperature', '')
                
                if tonight_short and tonight_short != " " and tonight_short.strip():
                    message_parts.append(f"Tonight: {tonight_short}.")
                    if tonight_temp:
                        message_parts.append(f"Lows around {tonight_temp} degrees.")
        
        return ' '.join(message_parts)
    
    # ============================================================
    # 5. TOM - ZONE FORECAST
    # ============================================================
    def get_zone_forecast(self):
        try:
            points_url = f"https://api.weather.gov/points/{self.lat},{self.lon}"
            points_response = requests.get(points_url, headers=self.headers)
            points_data = points_response.json()
            
            zone_id = points_data['properties']['forecastZone'].split('/')[-1]
            
            zfp_url = f"https://api.weather.gov/zones/forecast/{zone_id}/forecast"
            zfp_response = requests.get(zfp_url, headers=self.headers)
            zfp_data = zfp_response.json()
            
            periods = zfp_data.get('properties', {}).get('periods', [])
            if periods:
                forecast_parts = []
                for period in periods[:6]:
                    name = period.get('name', '')
                    temp = period.get('temperature', '')
                    temp_unit = period.get('temperatureUnit', 'F')
                    detailed = period.get('detailedForecast', '')
                    wind = period.get('windSpeed', '')
                    wind_dir = period.get('windDirection', '')
                    
                    part = f"{name}: "
                    if temp:
                        part += f"Temperature {temp} degrees {temp_unit}. "
                    if detailed and detailed != " " and detailed.strip():
                        part += f"{detailed} "
                    if wind and wind != " " and wind.strip():
                        if wind_dir and wind_dir != " " and wind_dir.strip():
                            part += f"Winds from the {wind_dir} at {wind}. "
                        else:
                            part += f"Wind speeds {wind}. "
                    
                    if part.strip() and part != f"{name}: ":
                        forecast_parts.append(part.strip())
                
                if forecast_parts:
                    return ' '.join(forecast_parts)
            return "Zone forecast not available."
            
        except Exception as e:
            print(f"❌ ZFP error: {e}")
            return "Zone forecast not available."
    
    # ============================================================
    # 6. TOM - HAZARDOUS WEATHER OUTLOOK
    # ============================================================
    def get_hazardous_outlook(self, data):
        if not data:
            return "Hazardous weather outlook not available."
        
        city = self.city
        state = self.state
        
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        day_str = now.strftime("%A")
        
        hazards = [
            "A winter storm is expected to impact the region mid-week.",
            "Strong winds and heavy rain possible on Thursday.",
            "Isolated thunderstorms with gusty winds possible this afternoon.",
            "Snow showers expected in higher elevations tonight.",
            "Extreme heat warning in effect for the valley areas.",
            "Frost advisory for early morning hours.",
            "Flash flooding possible in low-lying areas.",
            "Wildfire risk remains elevated due to dry conditions.",
            "Coastal flooding possible during high tide.",
            "Heavy lake effect snow expected through the weekend."
        ]
        
        outlook = f"""
        Hazardous Weather Outlook for {city}, {state}.
        Issued at {time_str} {day_str}.
        
        Synopsis: {random.choice(hazards)}
        Additionally, {random.choice(hazards)}
        
        This outlook covers the next 7 days.
        """
        
        return ' '.join(outlook.split())
    
    # ============================================================
    # 7. DONNA - MARINE FORECAST
    # ============================================================
    def get_coastal_marine_forecast(self):
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        day_str = now.strftime("%A")
        
        forecast = f"""
        Coastal marine forecast for the coastal waters,
        issued at {time_str} {day_str}.
        
        Synopsis: A Pacific cold front will move through the coastal waters,
        bringing increasing winds and seas.
        
        TODAY:
        Winds: Northwest 15 to 25 knots.
        Seas: 6 to 10 feet.
        Visibility: 5 to 10 miles.
        Weather: Scattered showers and isolated thunderstorms.
        
        TONIGHT:
        Winds: Northwest 10 to 20 knots.
        Seas: 4 to 8 feet.
        Visibility: 3 to 8 miles.
        
        TOMORROW:
        Winds: Northwest 10 to 15 knots.
        Seas: 3 to 6 feet.
        Visibility: 6 to 12 miles.
        
        Mariners are advised to exercise caution.
        """
        
        return ' '.join(forecast.split())
    
    # ============================================================
    # 8. TOM/DONNA - COASTAL WATER OBSERVATIONS
    # ============================================================
    def get_coastal_water_observations(self):
        """Kıyı suları gözlemleri - UZUN ve detaylı - Tom veya Donna"""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        day_str = now.strftime("%A")
        date_str = now.strftime("%B %d, %Y")
        
        # Rastgele ses seç (Tom veya Donna)
        voice = random.choice(["tom", "donna"])
        
        # Rastgele değerler (gerçek NOAA verilerini taklit eder)
        stations = [
            {"name": "Station 44025 - Long Island Sound", "lat": "41.0N", "lon": "72.0W"},
            {"name": "Station 44065 - New York Harbor", "lat": "40.5N", "lon": "73.8W"},
            {"name": "Station 44017 - Atlantic City", "lat": "39.0N", "lon": "74.0W"},
            {"name": "Station 44020 - Nantucket Sound", "lat": "41.5N", "lon": "70.0W"},
            {"name": "Station 44025 - Block Island", "lat": "41.2N", "lon": "71.5W"},
        ]
        
        # 3 istasyon seç
        selected_stations = random.sample(stations, min(3, len(stations)))
        
        observations = []
        
        for station in selected_stations:
            wind_speed = random.randint(10, 30)
            wind_gust = wind_speed + random.randint(5, 15)
            wind_dir = random.choice(["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"])
            wave_height = random.randint(3, 10)
            wave_period = random.randint(5, 12)
            temp_air = random.randint(50, 75)
            temp_water = random.randint(45, 70)
            pressure = random.uniform(29.85, 30.25)
            pressure_trend = random.choice(["rising", "falling", "steady"])
            visibility = random.randint(5, 15)
            humidity = random.randint(40, 80)
            
            sea_state = random.choice([
                "smooth to slight",
                "slight to moderate",
                "moderate",
                "moderate to rough",
                "rough",
                "very rough"
            ])
            
            observation = f"""
            {station['name']} at {time_str} {day_str}:
            Location: {station['lat']} {station['lon']}.
            Winds: {wind_dir} at {wind_speed} knots, gusting to {wind_gust} knots.
            Seas: {wave_height} feet with a dominant wave period of {wave_period} seconds.
            Sea state: {sea_state}.
            Air temperature: {temp_air} degrees Fahrenheit.
            Sea surface temperature: {temp_water} degrees Fahrenheit.
            Barometric pressure: {pressure:.2f} inches and {pressure_trend}.
            Visibility: {visibility} miles.
            Humidity: {humidity} percent.
            """
            observations.append(observation)
        
        summary = f"""
        Coastal water observations for the coastal waters,
        issued at {time_str} {day_str}, {date_str}.
        
        The following observations are from the National Data Buoy Center
        and the Coastal Marine Automated Network.
        
        {' '.join(observations)}
        
        Additional coastal information:
        - Tidal range: {random.choice(['2 to 4 feet', '3 to 5 feet', '1 to 3 feet'])}.
        - Current speed: {random.randint(1, 5)} knots.
        - Current direction: {random.choice(['northward', 'southward', 'eastward', 'westward'])}.
        - Water visibility: {random.randint(5, 15)} miles.
        
        Mariners are advised to exercise caution due to
        {random.choice([
            'reduced visibility in fog',
            'increasing winds and seas',
            'rough seas and strong currents',
            'possible thunderstorms',
            'small craft advisory in effect'
        ])}.
        
        This concludes the coastal water observations report.
        """
        
        return ' '.join(summary.split()), voice
    
    # ============================================================
    # 9. TOM - CLIMATE SUMMARY
    # ============================================================
    def get_climate_summary(self, data):
        """İklim özeti - TOM okur"""
        if not data:
            return "Climate summary not available."
        
        forecast = data.get('forecast', {})
        city = self.city
        state = self.state
        
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%B %d, %Y")
        day_str = now.strftime("%A")
        
        # ============ SICAKLIK VERİLERİ ============
        max_temp = 0
        min_temp = 100
        precip_today = 0
        total_precip = 0
        
        if forecast and 'properties' in forecast:
            periods = forecast['properties']['periods']
            if periods:
                for period in periods[:6]:
                    temp = period.get('temperature', 0)
                    if temp and temp > max_temp:
                        max_temp = temp
                    if temp and temp < min_temp:
                        min_temp = temp
        
        if max_temp == 0:
            max_temp = random.randint(55, 85)
        if min_temp == 100:
            min_temp = random.randint(25, 55)
        
        # ============ MEVSİM VE KONUMA GÖRE AYARLAR ============
        month = now.month
        is_summer = month in [6, 7, 8, 9]
        is_winter = month in [12, 1, 2]
        
        if "Phoenix" in city or "Arizona" in state:
            normal_high = random.randint(95, 105)
            normal_low = random.randint(70, 80)
            record_high = random.randint(110, 120)
            record_low = random.randint(55, 65)
            record_year_high = random.randint(1970, 2000)
            record_year_low = random.randint(1900, 1950)
            precip = round(random.uniform(0.1, 2.5), 2)
            total_precip = round(random.uniform(3.0, 15.0), 2)
        elif "Miami" in city or "Florida" in state:
            normal_high = random.randint(85, 95)
            normal_low = random.randint(70, 80)
            record_high = random.randint(100, 110)
            record_low = random.randint(60, 70)
            record_year_high = random.randint(1980, 2010)
            record_year_low = random.randint(1900, 1940)
            precip = round(random.uniform(0.1, 5.0), 2)
            total_precip = round(random.uniform(5.0, 25.0), 2)
        elif "Denver" in city or "Colorado" in state:
            normal_high = random.randint(65, 85)
            normal_low = random.randint(40, 60)
            record_high = random.randint(95, 105)
            record_low = random.randint(20, 35)
            record_year_high = random.randint(1970, 2000)
            record_year_low = random.randint(1900, 1950)
            precip = round(random.uniform(0.0, 1.5), 2)
            total_precip = round(random.uniform(2.0, 12.0), 2)
        elif "Seattle" in city or "Washington" in state:
            normal_high = random.randint(60, 75)
            normal_low = random.randint(45, 55)
            record_high = random.randint(85, 95)
            record_low = random.randint(25, 40)
            record_year_high = random.randint(1970, 2000)
            record_year_low = random.randint(1900, 1950)
            precip = round(random.uniform(0.1, 3.0), 2)
            total_precip = round(random.uniform(8.0, 30.0), 2)
        elif "Chicago" in city or "Illinois" in state:
            normal_high = random.randint(70, 85)
            normal_low = random.randint(55, 65)
            record_high = random.randint(95, 105)
            record_low = random.randint(30, 45)
            record_year_high = random.randint(1970, 2000)
            record_year_low = random.randint(1900, 1950)
            precip = round(random.uniform(0.0, 2.0), 2)
            total_precip = round(random.uniform(3.0, 18.0), 2)
        else:
            normal_high = random.randint(70, 90)
            normal_low = random.randint(45, 65)
            record_high = random.randint(100, 110)
            record_low = random.randint(30, 45)
            record_year_high = random.randint(1970, 2000)
            record_year_low = random.randint(1900, 1950)
            precip = round(random.uniform(0.0, 1.5), 2)
            total_precip = round(random.uniform(2.0, 15.0), 2)
        
        # ============ GÜN DOĞUMU / BATIMI ============
        hour = now.hour
        if 6 <= hour < 12:
            time_period = "morning"
        elif 12 <= hour < 17:
            time_period = "afternoon"
        elif 17 <= hour < 21:
            time_period = "evening"
        else:
            time_period = "night"
        
        sunrise = random.choice(["6:08 AM", "6:15 AM", "6:30 AM", "6:45 AM", "7:00 AM"])
        sunset = random.choice(["5:45 PM", "6:00 PM", "6:15 PM", "6:30 PM", "6:44 PM", "7:00 PM"])
        
        # ============ ANONS METNİ ============
        summary = f"""
        The {city}, {state} climate summary for
        this {time_period}, as of {time_str}. {date_str}.
        
        Today's high temperature was {max_temp} degrees.
        The normal high is {normal_high} degrees.
        The record high is {record_high} degrees which was set in {record_year_high}.
        
        Today's low temperature was {min_temp} degrees.
        The normal low is {normal_low} degrees.
        The record low is {record_low} degrees which was set in {record_year_low}.
        
        {precip} inches of precipitation fell today,
        which brings the monthly total to {total_precip:.2f} inches.
        
        The total precipitation for the year now stands at {total_precip + random.uniform(2.0, 10.0):.2f} inches.
        
        The normal high temperature for tomorrow is {normal_high + random.randint(-5, 5)} degrees,
        and the normal low is {normal_low + random.randint(-5, 5)}.
        
        Sunset tonight is at {sunset},
        sunrise tomorrow is at {sunrise}.
        """
        
        return ' '.join(summary.split())
    
    # ============================================================
    # 10. EMERGENCY SYSTEM
    # ============================================================
    def check_for_emergency(self, alerts_data):
        if not alerts_data or 'features' not in alerts_data:
            return None
        
        emergency_keywords = [
            'tornado', 'flash flood', 'severe thunderstorm',
            'hurricane', 'extreme wind', 'blizzard', 'ice storm',
            'tsunami', 'wildfire', 'volcano', 'extreme heat',
            'dust storm', 'winter storm', 'flood', 'landslide',
            'evacuation', 'civil emergency', 'shelter in place',
            'avalanche', 'heavy snow', 'freezing rain', 'extreme cold',
            'advisory', 'watch', 'statement', 'special weather',
            'small craft', 'high wind', 'freeze', 'frost',
            'dense fog', 'air quality', 'red flag'
        ]
        
        for alert in alerts_data['features']:
            props = alert.get('properties', {})
            event = props.get('event', '').lower()
            severity = props.get('severity', '')
            urgency = props.get('urgency', '')
            category = props.get('category', '')
            
            is_emergency = (
                severity in ['Extreme', 'Severe'] or
                urgency in ['Immediate'] or
                category in ['Emergency'] or
                any(keyword in event for keyword in emergency_keywords)
            )
            
            if is_emergency:
                area = props.get('areaDesc', 'this area')
                area_clean = self.clean_area(area)
                
                return {
                    'event': props.get('event', 'Emergency'),
                    'severity': severity,
                    'urgency': urgency,
                    'category': category,
                    'area': area_clean,
                    'headline': props.get('headline', ''),
                    'description': props.get('description', ''),
                    'instruction': props.get('instruction', '')
                }
        
        return None
    
    def play_alert_tone(self):
        try:
            for _ in range(3):
                winsound.Beep(600, 300)
                time.sleep(0.2)
            return True
        except:
            return False
    
    # ============================================================
    # 11. TEST SYSTEM
    # ============================================================
    def is_test_time(self):
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        minute = now.minute
        day = now.day
        
        if weekday == 2 and 11 <= hour < 12:
            test_minute = 15 + (day * 3) % 30
            if minute >= test_minute - 2 and minute <= test_minute + 2:
                return True, "Weekly Test"
        
        if weekday == 2 and day <= 7:
            if 11 <= hour < 12:
                test_minute = 30 + (day * 2) % 20
                if minute >= test_minute - 2 and minute <= test_minute + 2:
                    return True, "Monthly Test"
        
        return False, None
    
    def get_test_message(self, test_type):
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")
        
        if test_type == "Weekly Test":
            return f"""
            This is a weekly test of the NOAA Weather Radio system.
            {date_str} at {time_str}.
            This is only a test. If this had been an actual emergency,
            you would have been provided with important information.
            This concludes the weekly test of the NOAA Weather Radio system.
            """
        elif test_type == "Monthly Test":
            return f"""
            This is a monthly test of the NOAA Weather Radio system.
            {date_str} at {time_str}.
            This is only a test. If this had been an actual emergency,
            you would have been provided with important information.
            This concludes the monthly test of the NOAA Weather Radio system.
            """
        else:
            return f"""
            This is a test of the NOAA Weather Radio system.
            {date_str} at {time_str}.
            This is only a test.
            """
    
    def play_test_alert(self):
        try:
            for _ in range(3):
                winsound.Beep(600, 300)
                time.sleep(0.2)
            return True
        except:
            return False
    
    # ============================================================
    # 11. TEST SYSTEM
    # ============================================================
    def is_test_time(self):
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        minute = now.minute
        day = now.day
        
        if weekday == 2 and 11 <= hour < 12:
            test_minute = 15 + (day * 3) % 30
            if minute >= test_minute - 2 and minute <= test_minute + 2:
                return True, "Weekly Test"
        
        if weekday == 2 and day <= 7:
            if 11 <= hour < 12:
                test_minute = 30 + (day * 2) % 20
                if minute >= test_minute - 2 and minute <= test_minute + 2:
                    return True, "Monthly Test"
        
        return False, None
    
    def get_test_message(self, test_type):
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")
        
        if test_type == "Weekly Test":
            return f"""
            This is a weekly test of the NOAA Weather Radio system.
            {date_str} at {time_str}.
            This is only a test. If this had been an actual emergency,
            you would have been provided with important information.
            This concludes the weekly test of the NOAA Weather Radio system.
            """
        elif test_type == "Monthly Test":
            return f"""
            This is a monthly test of the NOAA Weather Radio system.
            {date_str} at {time_str}.
            This is only a test. If this had been an actual emergency,
            you would have been provided with important information.
            This concludes the monthly test of the NOAA Weather Radio system.
            """
        else:
            return f"""
            This is a test of the NOAA Weather Radio system.
            {date_str} at {time_str}.
            This is only a test.
            """
    
    def play_test_alert(self):
        try:
            for _ in range(3):
                winsound.Beep(750, 250)
                time.sleep(0.1)
                winsound.Beep(500, 250)
                time.sleep(0.1)
            return True
        except:
            return False
    
    def run_test(self, test_type):
        print(f"\n🔊 {test_type} BAŞLATILIYOR!")
        
        self.play_test_alert()
        time.sleep(1)
        
        test_msg = self.get_test_message(test_type)
        
        if self.harry_voice:
            self.speak_with_voice(test_msg, "harry", 1)
        else:
            self.speak_with_voice(test_msg, "paul", 0)
        
        time.sleep(1)
        self.play_test_alert()
        
        print(f"✅ {test_type} TAMAMLANDI!")
        
        return True
    
    def check_and_run_test(self):
        if not self.test_mode:
            return False
        
        is_test, test_type = self.is_test_time()
        
        if is_test:
            now = time.time()
            if now - self.last_test_time > 120:
                self.last_test_time = now
                self.last_test_type = test_type
                self.run_test(test_type)
                return True
        
        return False
    
    # ============================================================
    # TEXT CLEANING
    # ============================================================
    def clean_tts_text(self, text):
        if not text:
            return ""
        
        text = text.replace("*", "")
        text = text.replace("#", "")
        text = text.replace("_", "")
        text = text.replace("~", "")
        text = text.replace("`", "")
        text = text.replace('"', "")
        text = text.replace("'", "")
        text = text.replace("(R)", "")
        text = text.replace("(r)", "")
        text = text.replace("®", "")
        
        text = ' '.join(text.split())
        
        replacements = {
            "MDT": "Mountain Daylight Time",
            "MST": "Mountain Standard Time",
            "CDT": "Central Daylight Time",
            "CST": "Central Standard Time",
            "EDT": "Eastern Daylight Time",
            "EST": "Eastern Standard Time",
            "PDT": "Pacific Daylight Time",
            "PST": "Pacific Standard Time",
            "AKDT": "Alaska Daylight Time",
            "AKST": "Alaska Standard Time",
            "kt": "knots",
            "NM": "Nautical Miles",
            "mph": "miles per hour",
            "ft": "feet",
            "NWS": "National Weather Service",
            "PM": "P M",
            "AM": "A M",
            "p.m.": "P M",
            "a.m.": "A M",
            "&": "and",
            "/": " or ",
            "°F": "degrees Fahrenheit",
            "°C": "degrees Celsius",
            "%": "percent",
            "+": "plus",
            "-": "minus",
        }
        
        for old, new in replacements.items():
            text = re.sub(r'\b' + re.escape(old) + r'\b', new, text, flags=re.IGNORECASE)
        
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        text = ' '.join(text.split())
        
        return text
    
    def get_weather_summary(self, data):
        if not data:
            return "Weather data unavailable."
        
        forecast = data.get('forecast', {})
        city = self.city
        
        message_parts = []
        message_parts.append(f"Here is the latest weather forecast for {city}.")
        
        if forecast and 'properties' in forecast:
            periods = forecast['properties']['periods']
            if periods:
                current = periods[0]
                temp = current.get('temperature', '')
                short = current.get('shortForecast', '')
                wind = current.get('windSpeed', '')
                wind_dir = current.get('windDirection', '')
                
                message_parts.append(f"Temperature {temp} degrees.")
                if short:
                    message_parts.append(short)
                if wind:
                    if wind_dir:
                        message_parts.append(f"Winds from {wind_dir} at {wind}.")
                    else:
                        message_parts.append(f"Wind speeds {wind}.")
        
        if forecast and 'properties' in forecast:
            periods = forecast['properties']['periods']
            if len(periods) >= 3:
                tonight = periods[1].get('shortForecast', '')
                if tonight:
                    message_parts.append(f"Tonight: {tonight}")
                if len(periods) >= 4:
                    tomorrow = periods[2].get('shortForecast', '')
                    if tomorrow:
                        message_parts.append(f"Tomorrow: {tomorrow}")
        
        return ' '.join(message_parts)
