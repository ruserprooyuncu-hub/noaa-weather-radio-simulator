import requests
import json
import time
from datetime import datetime
import win32com.client
import winsound
import random
import threading
import re
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
                "voice": "tom",
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

        self.paul_voice = None
        self.tom_voice = None
        self.donna_voice = None
        self.harry_voice = None

        # ============ TEST SİSTEMİ ============
        self.test_mode = True
        self.last_test_time = 0
        self.last_test_type = ""

        self.init_speaker()

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
            points_response = requests.get(points_url, headers=self.headers, timeout=10)
            points_data = points_response.json()

            forecast_url = points_data['properties']['forecast']
            forecast_response = requests.get(forecast_url, headers=self.headers, timeout=10)
            forecast_data = forecast_response.json()

            alert_url = f"https://api.weather.gov/alerts/active?point={self.lat},{self.lon}"
            alert_response = requests.get(alert_url, headers=self.headers, timeout=10)
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
        """State kısaltmalarını temizle ve county'leri doğal okunacak şekilde birleştir"""
        if not area:
            return "this area"

        parts = [p.strip() for p in area.split(';') if p.strip()]

        cleaned = []
        for part in parts:
            part = re.sub(r',\s*([A-Z]{2})\s*$', r' \1', part)
            part = part.replace(' County', '').replace(' county', '')
            part = ' '.join(part.split())
            if part:
                cleaned.append(part)

        if len(cleaned) == 0:
            return "this area"
        elif len(cleaned) == 1:
            return cleaned[0]
        elif len(cleaned) == 2:
            return f"{cleaned[0]} and {cleaned[1]}"
        else:
            if len(cleaned) > 5:
                return ', '.join(cleaned[:4]) + f", and {len(cleaned) - 4} other counties"
            return ', '.join(cleaned[:-1]) + f", and {cleaned[-1]}"

    # ============================================================
    # TIMEZONE YARDIMCISI
    # ============================================================
    def get_timezone(self):
        """Region ve state'e göre timezone ETİKETİ döndürür (MDT, PDT vs.)"""
        import time as time_module
        is_dst = time_module.daylight and time_module.localtime().tm_isdst

        tz_map = {
            "mountain":  "MDT" if is_dst else "MST",
            "coastal":   "PDT" if is_dst else "PST",
            "urban":     "CDT" if is_dst else "CST",
            "plains":    "CDT" if is_dst else "CST",
            "southeast": "EDT" if is_dst else "EST",
            "arctic":    "AKDT" if is_dst else "AKST",
        }

        state_lower = self.state.lower()
        if state_lower == "arizona":
            return "MST"
        elif state_lower == "hawaii":
            return "HST"

        return tz_map.get(self.region, "CST")

    def format_frequency(self):
        """162.550 → 'one sixty-two point five five zero' formatına çevirir"""
        freq = self.frequency  # "162.550"

        try:
            # Ondalık ayır
            parts = freq.split(".")
            if len(parts) != 2:
                return freq

            integer_part = parts[0]  # "162"
            decimal_part = parts[1]  # "550"

            # Integer kısmı: 162 → "one sixty-two"
            hundreds = int(integer_part[0])  # 1
            tens_ones = int(integer_part[1:])  # 62

            # 1-9 arası
            ones_words = ["zero", "one", "two", "three", "four", "five",
                          "six", "seven", "eight", "nine"]
            # 10-19 arası
            teens_words = ["ten", "eleven", "twelve", "thirteen", "fourteen",
                           "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
            # Onluklar
            tens_words = ["", "", "twenty", "thirty", "forty", "fifty",
                          "sixty", "seventy", "eighty", "ninety"]

            # Yüzler basamağı
            if hundreds > 0:
                result = f"{ones_words[hundreds]} hundred"
            else:
                result = ""

            # Onlar ve birler
            if tens_ones >= 20:
                tens = tens_ones // 10
                ones = tens_ones % 10
                if ones > 0:
                    result += f" {tens_words[tens]}-{ones_words[ones]}"
                else:
                    result += f" {tens_words[tens]}"
            elif tens_ones >= 10:
                result += f" {teens_words[tens_ones - 10]}"
            elif tens_ones > 0:
                result += f" {ones_words[tens_ones]}"

            integer_words = result.strip()

            # Ondalık kısmı: 550 → "five five zero"
            decimal_words = " ".join([ones_words[int(d)] for d in decimal_part])

            return f"{integer_words} point {decimal_words}"

        except Exception as e:
            print(f"⚠️ Frequency format error: {e}")
            return freq

    def get_local_time(self):
        """İstasyonun bulunduğu bölgede ŞU ANKİ saati döndürür (gerçek saat)"""
        from datetime import datetime
        from zoneinfo import ZoneInfo

        # State → IANA timezone eşleşmesi
        state_to_tz = {
            # Eastern
            "connecticut": "America/New_York",
            "delaware": "America/New_York",
            "florida": "America/New_York",  # çoğu Eastern (Panhandle Central)
            "georgia": "America/New_York",
            "indiana": "America/New_York",  # çoğu Eastern
            "kentucky": "America/New_York",  # çoğu Eastern
            "maine": "America/New_York",
            "maryland": "America/New_York",
            "massachusetts": "America/New_York",
            "michigan": "America/New_York",  # çoğu Eastern
            "new hampshire": "America/New_York",
            "new jersey": "America/New_York",
            "new york": "America/New_York",
            "north carolina": "America/New_York",
            "ohio": "America/New_York",
            "pennsylvania": "America/New_York",
            "rhode island": "America/New_York",
            "south carolina": "America/New_York",
            "vermont": "America/New_York",
            "virginia": "America/New_York",
            "west virginia": "America/New_York",

            # Central
            "alabama": "America/Chicago",
            "arkansas": "America/Chicago",
            "illinois": "America/Chicago",
            "iowa": "America/Chicago",
            "kansas": "America/Chicago",  # çoğu Central
            "louisiana": "America/Chicago",
            "minnesota": "America/Chicago",
            "mississippi": "America/Chicago",
            "missouri": "America/Chicago",
            "nebraska": "America/Chicago",  # çoğu Central
            "north dakota": "America/Chicago",
            "oklahoma": "America/Chicago",
            "south dakota": "America/Chicago",  # çoğu Central
            "tennessee": "America/Chicago",  # çoğu Central
            "texas": "America/Chicago",  # çoğu Central
            "wisconsin": "America/Chicago",

            # Mountain
            "arizona": "America/Phoenix",  # DST yok
            "colorado": "America/Denver",
            "idaho": "America/Boise",  # çoğu Mountain
            "montana": "America/Denver",
            "new mexico": "America/Denver",
            "utah": "America/Denver",
            "wyoming": "America/Denver",

            # Pacific
            "california": "America/Los_Angeles",
            "nevada": "America/Los_Angeles",
            "oregon": "America/Los_Angeles",  # çoğu Pacific
            "washington": "America/Los_Angeles",

            # Alaska
            "alaska": "America/Anchorage",

            # Hawaii
            "hawaii": "Pacific/Honolulu",
        }

        state_lower = self.state.lower()
        iana_tz = state_to_tz.get(state_lower, "America/Chicago")

        try:
            local_tz = ZoneInfo(iana_tz)
            local_now = datetime.now(local_tz)
            return local_now
        except Exception as e:
            print(f"⚠️ Timezone error: {e}, falling back to system time")
            return datetime.now()

    # ============================================================
    # 1. OPENING — 2010'lar üslubu
    # ============================================================
    def get_opening_message(self):
        """İstasyona özel açılış metni - Sesine göre format değişir"""

        if self.custom_opening:
            return self.custom_opening

        voice = self.station.get("voice", "tom")
        callsign = self.callsign
        station_id = self.station_id
        frequency = self.frequency
        city = self.city
        state = self.state

        # ============ TOM — 2010'lar üslubu ============
        if voice == "tom":
            openings = [
                f"This is NOAA Weather Radio {station_id}, originating from the National Weather Service forecast office in {city}, {state}. We supply the latest available weather information for the {city} area on a frequency of {frequency} Megahertz.",
                f"You are listening to NOAA Weather Radio station {station_id}, broadcasting on a frequency of {frequency} Megahertz. This station is operated by the National Weather Service in {city}, {state}. The latest weather information is updated continuously.",
                f"This is NOAA Weather Radio station {station_id} in {city}, {state}. Broadcast programming originates from the National Weather Service forecast office in {city}. We broadcast on a frequency of {frequency} Megahertz.",
                f"NOAA Weather Radio station {station_id} in {city}, {state}. Broadcasting on a frequency of {frequency} Megahertz. This station is operated by the National Weather Service and provides continuous weather information for the {city} area.",
                f"This is NOAA Weather Radio station {station_id}, originating from the National Weather Service in {city}. We provide the latest weather information for the {city} area on a frequency of {frequency} Megahertz. Stay tuned for the latest forecast."
            ]
            return random.choice(openings)

        # ============ PAUL ============
        elif voice == "paul":
            openings = [
                f"This is NOAA Weather Radio station {station_id} in {city}, {state}, broadcasting on a frequency of {frequency} Megahertz.",
                f"This is NOAA Weather Radio Hazards, station {station_id} in {city}. The station broadcast from the National Weather Service, at the frequency of {frequency} Megahertz.",
                f"This is NOAA Weather Radio station {station_id}. We broadcast from the National Weather Service in {city}, {state} on {frequency} Megahertz.",
                f"You are listening to NOAA Weather Radio station {station_id} in {city}, {state}, transmitting on {frequency} Megahertz."
            ]
            return random.choice(openings)

        # ============ DONNA ============
        elif voice == "donna":
            openings = [
                f"You are listening to NOAA Weather Radio, the voice of the National Weather Service, station {station_id} in {city}, {state}, broadcasting on a frequency of {frequency} Megahertz.",
                f"This is NOAA Weather Radio station {station_id}, serving {city}, {state}, and surrounding areas, on a frequency of {frequency} Megahertz.",
                f"Welcome to NOAA Weather Radio station {station_id}, operating from the National Weather Service office in {city}, {state}, at {frequency} Megahertz.",
                f"NOAA Weather Radio station {station_id}, the voice of the National Weather Service for {city}, {state}, on {frequency} Megahertz.",
                f"This is NOAA Weather Radio station {station_id} in {city}, {state}. Broadcasting on a frequency of {frequency} Megahertz, providing continuous weather information for the {city} area."
            ]
            return random.choice(openings)

        # ============ HARRY (default) ============
        else:
            openings = [
                f"This is NOAA Weather Radio station {station_id} in {city}, broadcasting on a frequency of {frequency} Megahertz.",
                f"This is the NOAA Weather Radio {station_id} in {city}. {station_id} operates on a frequency of {frequency} Megahertz.",
                f"This is NOAA Weather Radio Hazards, station {station_id} in {city}, at the frequency of {frequency} Megahertz.",
                f"NOAA Weather Radio station {station_id} in {city}, {state}. Frequency {frequency} Megahertz.",
                f"Thanks for listening to NOAA Weather Radio Station {station_id}. Transmitting on a frequency of {frequency} Megahertz.",
            ]
            return random.choice(openings)

    # ============================================================
    # 2. PAUL - TIME ANNOUNCEMENT — varyasyonlu
    # ============================================================
    def time_announcement(self):
        local_now = self.get_local_time()
        time_str = local_now.strftime("%I:%M %p")
        tz = self.get_timezone()

        variants = [
            f"The current time is {time_str} {tz}.",
        ]

        return random.choice(variants)

    # ============================================================
    # 3. TOM - HOURLY ROUNDUP — günlük özet ile
    # ============================================================
    def get_hourly_roundup(self, data):
        if not data:
            return "Hourly weather roundup not available."

        forecast = data.get('forecast', {})
        city = self.city
        state = self.state

        now = self.get_local_time()
        time_str = now.strftime("%I:%M %p")
        tz = self.get_timezone()

        message_parts = []

        # ============ AÇILIŞ VARYASYONLARI ============
        opening_variants = [
            f"Hourly weather roundup for {city}, {state}.",
            f"Here is the hourly weather roundup for {city}, {state}.",
            f"The hourly weather roundup for {city}, {state}.",
            f"Now the hourly weather roundup for {city}, {state}.",
            f"This is the hourly weather roundup for {city}, {state}.",
            f"Hourly observations for {city}, {state}.",
            f"Here are the current conditions for {city}, {state}.",
            f"The latest hourly weather roundup for {city}, {state}.",
            f"Time now for the hourly weather roundup for {city}, {state}.",
            f"Up next, the hourly weather roundup for {city}, {state}.",
        ]
        message_parts.append(random.choice(opening_variants))

        # ============ ZAMAN GEÇİŞ VARYASYONLARI ============
        time_intro_variants = [
            f"At {time_str} {tz},",
            f"As of {time_str} {tz},",
            f"At {time_str} this hour,",
            f"At {time_str} {tz},",
            f"Currently at {time_str} {tz},",
            f"The {time_str} observation shows,",
            f"At {time_str} local time,",
        ]
        message_parts.append(random.choice(time_intro_variants))

        # ============ SICAKLIK VARYASYONLARI ============
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
                    temp_variants = [
                        f"the temperature is {temp} degrees Fahrenheit.",
                        f"the temperature stands at {temp} degrees.",
                        f"we're looking at a temperature of {temp} degrees.",
                        f"the mercury reads {temp} degrees.",
                        f"the reading is {temp} degrees Fahrenheit.",
                        f"it's currently {temp} degrees outside.",
                    ]
                    message_parts.append(random.choice(temp_variants))

                if wind and wind != " " and wind.strip():
                    if wind_dir and wind_dir != " " and wind_dir.strip():
                        wind_variants = [
                            f"Winds are from the {wind_dir} at {wind}.",
                            f"Winds are out of the {wind_dir} at {wind}.",
                            f"Current winds are {wind_dir} at {wind}.",
                            f"Wind direction is {wind_dir} at {wind}.",
                            f"Winds are blowing from the {wind_dir} at {wind}.",
                        ]
                    else:
                        wind_variants = [
                            f"Wind speeds are {wind}.",
                            f"Winds are at {wind}.",
                            f"Current wind speed is {wind}.",
                        ]
                    message_parts.append(random.choice(wind_variants))

                if short and short != " " and short.strip():
                    sky_variants = [
                        f"Skies are {short.lower()}.",
                        f"Sky conditions are {short.lower()}.",
                        f"We have {short.lower()} skies.",
                        f"The sky condition is {short.lower()}.",
                        f"Currently observing {short.lower()}.",
                    ]
                    message_parts.append(random.choice(sky_variants))

                if precip and precip > 0:
                    precip_variants = [
                        f"There is a {int(precip)} percent chance of precipitation.",
                        f"Precipitation chances are {int(precip)} percent.",
                        f"The precipitation probability is {int(precip)} percent.",
                        f"A {int(precip)} percent chance of precipitation is forecast.",
                    ]
                    message_parts.append(random.choice(precip_variants))

        # ============ NEM VARYASYONLARI ============
        humidity = random.randint(25, 75)
        humidity_variants = [
            f"Relative humidity is {humidity} percent.",
            f"Humidity stands at {humidity} percent.",
            f"The relative humidity is {humidity} percent.",
            f"Humidity level is {humidity} percent.",
            f"Current humidity is {humidity} percent.",
        ]
        message_parts.append(random.choice(humidity_variants))

        # ============ ÇİY NOKTASI VARYASYONLARI ============
        dew_point = random.randint(35, 65)
        dew_variants = [
            f"The dew point is {dew_point} degrees Fahrenheit.",
            f"Dew point is {dew_point} degrees.",
            f"The dew point stands at {dew_point} degrees Fahrenheit.",
            f"Dew point temperature is {dew_point} degrees.",
        ]
        message_parts.append(random.choice(dew_variants))

        # ============ RÜZGAR GUST VARYASYONLARI ============
        wind_gust = random.randint(15, 35)
        gust_variants = [
            f"Wind gusts of up to {wind_gust} miles per hour are possible.",
            f"Gusts could reach {wind_gust} miles per hour.",
            f"Wind gusts may reach {wind_gust} miles per hour.",
            f"Gusts up to {wind_gust} miles per hour are expected.",
            f"Wind gusts are forecast to reach {wind_gust} miles per hour.",
        ]
        message_parts.append(random.choice(gust_variants))

        # ============ BASINÇ VARYASYONLARI ============
        pressure = random.uniform(29.85, 30.25)
        pressure_trend = random.choice(['rising', 'falling', 'steady'])
        pressure_variants = [
            f"Barometric pressure is {pressure:.2f} inches and {pressure_trend}.",
            f"The barometer reads {pressure:.2f} inches and is {pressure_trend}.",
            f"Pressure is {pressure:.2f} inches, currently {pressure_trend}.",
            f"Barometric pressure stands at {pressure:.2f} inches, {pressure_trend}.",
            f"The atmospheric pressure is {pressure:.2f} inches and {pressure_trend}.",
        ]
        message_parts.append(random.choice(pressure_variants))

        # ============ GÖRÜŞ VARYASYONLARI ============
        visibility = random.randint(5, 15)
        vis_variants = [
            f"Visibility is {visibility} miles.",
            f"Visibility stands at {visibility} miles.",
            f"We have {visibility} miles of visibility.",
            f"Current visibility is {visibility} miles.",
            f"Visible range is {visibility} miles.",
        ]
        message_parts.append(random.choice(vis_variants))

        # ============ SKY CONDITION ============
        cloud_cover = random.choice([
            "clear", "mostly clear", "partly cloudy",
            "mostly cloudy", "overcast"
        ])
        cloud_variants = [
            f"The sky condition is {cloud_cover}.",
            f"Sky condition: {cloud_cover}.",
            f"Current sky condition is {cloud_cover}.",
            f"We're observing {cloud_cover} skies.",
        ]
        message_parts.append(random.choice(cloud_variants))

        # ============ GÜNLÜK ÖZET VARYASYONLARI ============
        if forecast and 'properties' in forecast:
            periods = forecast['properties']['periods']
            if periods:
                today_high = periods[0].get('temperature', '')
                today_low = periods[1].get('temperature', '') if len(periods) > 1 else ''

                if today_high:
                    high_variants = [
                        f"Today's high so far has been {today_high} degrees.",
                        f"The high today has reached {today_high} degrees.",
                        f"We've topped out at {today_high} degrees so far today.",
                        f"Today's maximum temperature is {today_high} degrees.",
                    ]
                    message_parts.append(random.choice(high_variants))

                if today_low:
                    low_variants = [
                        f"The overnight low was {today_low} degrees.",
                        f"Overnight we dropped to {today_low} degrees.",
                        f"The low since midnight was {today_low} degrees.",
                        f"We bottomed out at {today_low} degrees overnight.",
                    ]
                    message_parts.append(random.choice(low_variants))

        # ============ EK İSTASYONLAR ============
        extra_intro_variants = [
            "Additional observations from nearby stations:",
            "Here are observations from surrounding areas:",
            "Nearby station reports:",
            "Observations from area stations:",
            "Other reporting stations show:",
        ]
        message_parts.append(random.choice(extra_intro_variants))

        EXTRA_STATIONS_BY_REGION = {
            "mountain": ["Crested Butte", "Monarch Pass", "Lake City", "Leadville", "Silverton", "Telluride"],
            "coastal": ["Harbor Station", "Buoy 44025", "Lighthouse Point", "Coastal Buoy 41010", "Beach Station"],
            "plains": ["Prairie View", "Grainfield", "North Field", "Ranch Station", "Wheatland"],
            "southeast": ["Piedmont", "Riverbend", "Oak Grove", "Pine Ridge", "Magnolia"],
            "urban": ["Metro Airport", "Downtown Station", "North Suburb", "South Side", "Industrial Park"],
            "arctic": ["North Slope", "Brooks Range", "Kobuk Valley", "Seward Peninsula", "Yukon Flats"],
        }

        extra_names = EXTRA_STATIONS_BY_REGION.get(self.region, EXTRA_STATIONS_BY_REGION["plains"])
        selected_extras = random.sample(extra_names, min(2, len(extra_names)))

        for name in selected_extras:
            station_temp = random.randint(20, 75)
            station_wind = random.randint(5, 25)

            station_variants = [
                f"At {name}, temperature is {station_temp} degrees, winds at {station_wind} miles per hour.",
                f"{name} reports {station_temp} degrees with winds at {station_wind} miles per hour.",
                f"At {name}, we have {station_temp} degrees and winds at {station_wind} miles per hour.",
                f"{name} is reporting {station_temp} degrees, wind speed {station_wind} miles per hour.",
            ]
            message_parts.append(random.choice(station_variants))

        # ============ KAPANIŞ VARYASYONLARI ============
        closing_variants = [
            f"This concludes the hourly weather roundup for {city} at {time_str} {tz}.",
            f"That's the hourly weather roundup for {city}.",
            f"End of hourly weather roundup for {city} at {time_str}.",
            f"This has been the hourly weather roundup for {city}.",
            f"Concluding the hourly roundup for {city} at {time_str} {tz}.",
        ]
        message_parts.append(random.choice(closing_variants))

        return ' '.join(message_parts)

    # ============================================================
    # 4. TOM - NOWCAST — uzun versiyon
    # ============================================================
    def get_nowcast(self, data):
        if not data:
            return "Short-term forecast not available."

        forecast = data.get('forecast', {})
        city = self.city
        state = self.state

        now = self.get_local_time()
        time_str = now.strftime("%I:%M %p")
        tz = self.get_timezone()

        message_parts = []

        # ============ AÇILIŞ VARYASYONLARI ============
        opening_variants = [
            f"Short-term forecast for {city}, {state}.",
            f"Here is the short-term forecast for {city}, {state}.",
            f"The short-term forecast for {city}, {state}.",
            f"Now the short-term forecast for {city}, {state}.",
            f"Nowcast for {city} and surrounding areas.",
            f"Looking at the short-term forecast for {city}.",
            f"The latest short-term forecast for {city}, {state}.",
            f"Short-term outlook for {city}, {state}.",
        ]
        message_parts.append(random.choice(opening_variants))

        # ============ ZAMAN GİRİŞİ ============
        time_intro_variants = [
            f"At {time_str} {tz},",
            f"As of {time_str} {tz},",
            f"Currently, at {time_str},",
            f"At this hour, {time_str},",
            f"Right now, {time_str},",
        ]
        message_parts.append(random.choice(time_intro_variants))

        # ============ MEVCUT DURUM ============
        if forecast and 'properties' in forecast:
            periods = forecast['properties']['periods']
            if len(periods) >= 2:
                current = periods[0]
                tonight = periods[1]

                temp = current.get('temperature', '')
                short = current.get('shortForecast', '')
                wind = current.get('windSpeed', '')
                wind_dir = current.get('windDirection', '')

                if temp and short:
                    current_variants = [
                        f"the current temperature is {temp} degrees with {short.lower()}.",
                        f"we're seeing {temp} degrees and {short.lower()}.",
                        f"temperature is {temp} degrees, conditions are {short.lower()}.",
                        f"it's {temp} degrees with {short.lower()}.",
                        f"the reading is {temp} degrees and {short.lower()}.",
                    ]
                    message_parts.append(random.choice(current_variants))
                elif temp:
                    message_parts.append(f"the current temperature is {temp} degrees.")

                if wind and wind != " " and wind.strip():
                    if wind_dir and wind_dir != " " and wind_dir.strip():
                        wind_variants = [
                            f"Winds are from the {wind_dir} at {wind}.",
                            f"Winds are {wind_dir} at {wind}.",
                            f"Current winds are {wind_dir} at {wind}.",
                        ]
                    else:
                        wind_variants = [
                            f"Wind speeds are {wind}.",
                            f"Winds are at {wind}.",
                        ]
                    message_parts.append(random.choice(wind_variants))

        # ============ KISA VADELİ GİRİŞ ============
        transition_variants = [
            "Looking at the short-term forecast,",
            "For the short term,",
            "In the near term,",
            "Over the next few hours,",
            "For the upcoming hours,",
            "Short-term, we expect",
        ]
        message_parts.append(random.choice(transition_variants))

        if forecast and 'properties' in forecast:
            periods = forecast['properties']['periods']
            if len(periods) >= 2:
                current = periods[0]
                tonight = periods[1]

                current_short = current.get('shortForecast', '')
                tonight_short = tonight.get('shortForecast', '')
                tonight_temp = tonight.get('temperature', '')

                if current_short and current_short != " " and current_short.strip():
                    expect_variants = [
                        f"expect {current_short.lower()} to continue through the afternoon.",
                        f"{current_short.lower()} should persist through the afternoon.",
                        f"conditions will remain {current_short.lower()}.",
                        f"we can expect {current_short.lower()} through the afternoon.",
                    ]
                    message_parts.append(random.choice(expect_variants))

                if tonight_short and tonight_short != " " and tonight_short.strip():
                    tonight_variants = [
                        f"Tonight, look for {tonight_short.lower()}.",
                        f"Overnight, expect {tonight_short.lower()}.",
                        f"Tonight's outlook calls for {tonight_short.lower()}.",
                        f"Going into tonight, {tonight_short.lower()}.",
                    ]
                    message_parts.append(random.choice(tonight_variants))

                    if tonight_temp:
                        low_variants = [
                            f"Lows will be around {tonight_temp} degrees.",
                            f"Overnight lows near {tonight_temp} degrees.",
                            f"Expect lows around {tonight_temp} degrees.",
                            f"Low temperatures near {tonight_temp}.",
                        ]
                        message_parts.append(random.choice(low_variants))

        # ============ RÜZGAR DEĞİŞİMİ ============
        wind_shift = random.choice([
            "Winds will shift to the northwest later this evening.",
            "Winds will become lighter after sunset.",
            "Winds will increase slightly overnight.",
            "Winds will remain steady through the evening hours.",
            "A wind shift to the northeast is expected overnight.",
            "Wind speeds will diminish after dark.",
            "Winds will gradually decrease overnight.",
        ])
        message_parts.append(wind_shift)

        # ============ SICAKLIK DEĞİŞİMİ ============
        temp_change = random.choice([
            "Temperatures will drop quickly after sunset.",
            "Temperatures will remain steady through the evening.",
            "A gradual cooling trend is expected overnight.",
            "Temperatures will fall into the lower range by midnight.",
            "Overnight temperatures will be cooler than last night.",
            "We'll see temperatures dropping steadily overnight.",
            "Look for temperatures to fall through the evening hours.",
        ])
        message_parts.append(temp_change)

        # ============ YAĞIŞ İHTİMALİ ============
        precip_chance = random.choice([
            "There is a slight chance of precipitation after midnight.",
            "No precipitation is expected in the short term.",
            "Scattered showers could develop later tonight.",
            "A few sprinkles are possible this evening.",
            "Precipitation chances remain low through the overnight hours.",
            "Isolated thunderstorms cannot be ruled out.",
            "Precipitation is not anticipated in the near term.",
        ])
        message_parts.append(precip_chance)

        # ============ GÖRÜŞ ============
        visibility_note = random.choice([
            "Visibility will remain good through the evening.",
            "Patchy fog could develop in low-lying areas overnight.",
            "Visibility may be reduced in areas of fog after midnight.",
            "Clear visibility is expected for the next several hours.",
            "Some patchy fog is possible along river valleys overnight.",
            "Visibility should remain unrestricted through the period.",
        ])
        message_parts.append(visibility_note)

        # ============ GÖKYÜZÜ ============
        sky_detail = random.choice([
            "Skies will remain mostly clear through the evening.",
            "Cloud cover will increase overnight.",
            "Expect clearing skies after midnight.",
            "Partly cloudy conditions will persist through the night.",
            "Overcast conditions will continue with gradual clearing.",
            "Skies will become mostly clear after midnight.",
        ])
        message_parts.append(sky_detail)

        # ============ YARIN ÖZETİ ============
        if forecast and 'properties' in forecast:
            periods = forecast['properties']['periods']
            if len(periods) >= 3:
                extended = periods[2]
                extended_short = extended.get('shortForecast', '')
                extended_temp = extended.get('temperature', '')

                if extended_short and extended_short != " " and extended_short.strip():
                    tomorrow_variants = [
                        f"Looking ahead to tomorrow, expect {extended_short.lower()}.",
                        f"Tomorrow's outlook calls for {extended_short.lower()}.",
                        f"Going into tomorrow, {extended_short.lower()}.",
                        f"For tomorrow, we expect {extended_short.lower()}.",
                    ]
                    message_parts.append(random.choice(tomorrow_variants))

                    if extended_temp:
                        high_variants = [
                            f"Highs tomorrow will be near {extended_temp} degrees.",
                            f"Tomorrow's high will be around {extended_temp} degrees.",
                            f"Expect highs near {extended_temp} degrees tomorrow.",
                        ]
                        message_parts.append(random.choice(high_variants))

        # ============ KAPANIŞ ============
        closing_variants = [
            f"This concludes the short-term forecast for {city}.",
            f"That's the short-term forecast for {city}.",
            f"This has been the short-term forecast for {city} at {time_str}.",
            f"End of short-term forecast for {city}.",
            f"Concluding the short-term forecast for {city}.",
        ]
        message_parts.append(random.choice(closing_variants))

        return ' '.join(message_parts)

    # ============================================================
    # 5. TOM - ZONE FORECAST — 8 gün + varyasyonlu
    # ============================================================
    def get_zone_forecast(self):
        try:
            points_url = f"https://api.weather.gov/points/{self.lat},{self.lon}"
            points_response = requests.get(points_url, headers=self.headers, timeout=10)
            points_data = points_response.json()

            zone_id = points_data['properties']['forecastZone'].split('/')[-1]

            zfp_url = f"https://api.weather.gov/zones/forecast/{zone_id}/forecast"
            zfp_response = requests.get(zfp_url, headers=self.headers, timeout=10)
            zfp_data = zfp_response.json()

            periods = zfp_data.get('properties', {}).get('periods', [])
            if periods:
                forecast_parts = []

                for i, period in enumerate(periods[:8]):  # 8 gün
                    name = period.get('name', '')
                    temp = period.get('temperature', '')
                    temp_unit = period.get('temperatureUnit', 'F')
                    detailed = period.get('detailedForecast', '')
                    wind = period.get('windSpeed', '')
                    wind_dir = period.get('windDirection', '')
                    short = period.get('shortForecast', '')

                    # ============ PERIOD GİRİŞ VARYASYONLARI ============
                    # İlk period için farklı, sonrakiler için farklı varyasyonlar
                    if i == 0:
                        # İlk period (Tonight/Today)
                        period_intro_variants = [
                            f"{name}: ",
                            f"For {name}: ",
                            f"{name}, ",
                            f"Starting with {name}: ",
                        ]
                    else:
                        # Sonraki periodlar (Thursday, Friday vs.)
                        period_intro_variants = [
                            f"{name}: ",
                            f"Then for {name}: ",
                            f"Moving on to {name}: ",
                            f"Looking at {name}: ",
                            f"{name} outlook: ",
                            f"Next, {name}: ",
                        ]

                    part = random.choice(period_intro_variants)

                    # ============ SICAKLIK VARYASYONLARI ============
                    if temp:
                        temp_variants = [
                            f"Temperature around {temp} degrees {temp_unit}. ",
                            f"Temperature near {temp} degrees. ",
                            f"Highs/lows around {temp} degrees. ",
                            f"Temperatures near {temp} degrees {temp_unit}. ",
                            f"Expect temperatures around {temp} degrees. ",
                        ]
                        part += random.choice(temp_variants)

                    # ============ DETAYLI TAHMİN ============
                    if detailed and detailed != " " and detailed.strip():
                        part += f"{detailed}. "

                    # ============ RÜZGAR VARYASYONLARI ============
                    if wind and wind != " " and wind.strip():
                        if wind_dir and wind_dir != " " and wind_dir.strip():
                            wind_variants = [
                                f"Winds from the {wind_dir} at {wind}. ",
                                f"Winds {wind_dir} at {wind}. ",
                                f"Winds will be {wind_dir} at {wind}. ",
                                f"Expect winds from the {wind_dir} at {wind}. ",
                            ]
                        else:
                            wind_variants = [
                                f"Wind speeds {wind}. ",
                                f"Winds at {wind}. ",
                            ]
                        part += random.choice(wind_variants)

                    if part.strip() and part != f"{name}: ":
                        forecast_parts.append(part.strip())

                if forecast_parts:
                    return ' '.join(forecast_parts)

            return "Zone forecast not available."

        except Exception as e:
            print(f"❌ ZFP error: {e}")
            return "Zone forecast not available."

    def get_zone_forecast_opening(self):
        """Zone forecast için varyasyonlu açılış cümlesi"""
        city = self.city
        state = self.state

        variants = [
            f"Now for the official National Weather Service forecast for {city}, {state}.",
            f"Now the official National Weather Service forecast for {city}, {state}.",
            f"Here is the official National Weather Service forecast for {city}, {state}.",
            f"The official National Weather Service forecast for {city}, {state}.",
            f"Now for the official National Weather Service forecast for {city} and surrounding areas.",
            f"And now, the official National Weather Service forecast for {city}, {state}.",
            f"Time for the official National Weather Service forecast for {city}, {state}.",
            f"Now the National Weather Service forecast for {city}, {state}.",
        ]
        return random.choice(variants)

    # ============================================================
    # 6. DONNA - HAZARDOUS WEATHER OUTLOOK
    # ============================================================
    def get_hazardous_outlook(self, data):
        """Bölgeye ve mevsime göre akıllı hazard outlook - DONNA okur"""
        if not data:
            return "Hazardous weather outlook not available."

        city = self.city
        state = self.state

        now = self.get_local_time()
        month = now.month
        is_winter = month in [11, 12, 1, 2, 3]
        is_summer = month in [6, 7, 8, 9]

        HAZARDS_BY_REGION = {
            "mountain": {
                "winter": [
                    "A winter storm is expected to impact the region mid-week.",
                    "Snow showers expected in higher elevations tonight.",
                    "Avalanche risk remains elevated in backcountry areas.",
                    "Blowing snow could reduce visibility on mountain passes.",
                    "Heavy snow accumulation expected above 8,000 feet.",
                ],
                "summer": [
                    "Afternoon thunderstorms possible with lightning and gusty winds.",
                    "Wildfire risk remains elevated due to dry conditions.",
                    "Flash flooding possible in burn scar areas.",
                    "Hail and strong winds possible with afternoon storms.",
                    "Red flag warning in effect for high fire danger.",
                ],
                "default": [
                    "Strong winds possible across mountain passes.",
                    "Frost advisory for early morning hours.",
                    "Mixed precipitation expected in higher elevations.",
                    "Wildfire risk remains elevated due to dry conditions.",
                ]
            },
            "coastal": {
                "default": [
                    "Coastal flooding possible during high tide.",
                    "Small craft advisory in effect for coastal waters.",
                    "Rip current risk is high at area beaches.",
                    "Dense fog possible along the coastline overnight.",
                    "High surf advisory in effect through tomorrow.",
                    "Strong onshore winds could cause minor coastal flooding.",
                ]
            },
            "plains": {
                "winter": [
                    "Blizzard conditions possible with blowing snow.",
                    "Ice storm warning in effect for the region.",
                    "Extreme cold wind chills expected overnight.",
                    "Freezing rain could create hazardous travel conditions.",
                ],
                "summer": [
                    "Extreme heat warning in effect for the valley areas.",
                    "Isolated thunderstorms with gusty winds possible this afternoon.",
                    "Severe thunderstorm watch in effect through evening.",
                    "Large hail and damaging winds possible with storms.",
                    "Tornado watch in effect for portions of the area.",
                    "Dust storm could reduce visibility on area roadways.",
                ],
                "default": [
                    "Strong winds and heavy rain possible on Thursday.",
                    "Frost advisory for early morning hours.",
                    "Wildfire risk remains elevated due to dry conditions.",
                    "Flash flooding possible in low-lying areas.",
                ]
            },
            "southeast": {
                "summer": [
                    "Hurricane watch in effect for coastal sections.",
                    "Flash flooding possible from heavy rainfall.",
                    "Scattered thunderstorms with frequent lightning.",
                    "Tropical storm conditions expected within 48 hours.",
                    "Heat advisory in effect with high humidity.",
                ],
                "winter": [
                    "Freezing rain possible in northern sections.",
                    "Frost advisory for early morning hours.",
                    "Strong cold front will bring gusty winds and rain.",
                ],
                "default": [
                    "Flash flooding possible in low-lying areas.",
                    "Isolated thunderstorms with gusty winds possible.",
                    "Dense fog possible during early morning hours.",
                    "Strong to severe thunderstorms possible this afternoon.",
                ]
            },
            "urban": {
                "winter": [
                    "Winter weather advisory in effect for the metro area.",
                    "Ice accumulation possible on area roadways.",
                    "Extreme cold wind chills expected overnight.",
                ],
                "summer": [
                    "Heat advisory in effect for the metro area.",
                    "Air quality alert in effect due to high ozone levels.",
                    "Severe thunderstorms possible during evening commute.",
                    "Flash flooding possible in urban areas.",
                ],
                "default": [
                    "Strong winds possible across the metro area.",
                    "Frost advisory for early morning hours.",
                    "Dense fog could impact morning commute.",
                    "Isolated thunderstorms possible this afternoon.",
                ]
            },
            "arctic": {
                "winter": [
                    "Extreme cold warning in effect with dangerous wind chills.",
                    "Blizzard conditions expected with whiteout visibility.",
                    "Heavy snow accumulation expected through the weekend.",
                    "Ice fog possible in valley locations overnight.",
                ],
                "summer": [
                    "Wildfire smoke could reduce air quality.",
                    "Strong winds possible across exposed areas.",
                    "Afternoon thunderstorms possible in interior sections.",
                ],
                "default": [
                    "High wind warning in effect for exposed areas.",
                    "Snow showers possible at higher elevations.",
                    "Dense fog possible along coastal sections.",
                ]
            },
        }

        region_hazards = HAZARDS_BY_REGION.get(self.region, HAZARDS_BY_REGION["plains"])

        if is_winter and "winter" in region_hazards:
            hazard_pool = region_hazards["winter"]
        elif is_summer and "summer" in region_hazards:
            hazard_pool = region_hazards["summer"]
        else:
            hazard_pool = region_hazards.get("default", region_hazards.get("winter", []))

        if not hazard_pool:
            hazard_pool = ["No significant hazardous weather is expected at this time."]

        if len(hazard_pool) >= 2:
            selected = random.sample(hazard_pool, 2)
        else:
            selected = [hazard_pool[0], hazard_pool[0]]

        # BÖLGE GÖRÜNÜMÜ
        region_display = {
            "mountain": f"the mountains of {state}",
            "coastal": f"the coastal waters and adjacent areas of {state}",
            "plains": f"the plains region of {state}",
            "southeast": f"the southeastern region of {state}",
            "urban": f"the {city} metropolitan area",
            "arctic": f"the arctic regions of {state}",
        }

        area_display = region_display.get(self.region, f"{city} and surrounding areas")

        opening_variants = [
            f"Now here is the hazardous weather outlook for {area_display}.",
            f"The hazardous weather outlook for {area_display}.",
            f"And now, the hazardous weather outlook for {area_display}.",
            f"Here is the hazardous weather outlook for {area_display}.",
            f"This is the hazardous weather outlook for {area_display}.",
        ]

        opening = random.choice(opening_variants)

        # ============ BUGÜN VE TONIGHT ============
        today_note = random.choice([
            "For today and tonight, there is a slight risk of severe weather across the outlook area.",
            "For today and tonight, no hazardous weather is expected at this time.",
            "For today and tonight, scattered thunderstorms are possible during the afternoon and evening hours.",
            "For today and tonight, conditions will remain generally quiet across the region.",
            "For today and tonight, residents should monitor weather conditions closely.",
        ])

        # ============ YARIN VE HAFTA ============
        tomorrow_note = random.choice([
            "For tomorrow through the weekend, an approaching storm system could bring significant weather changes.",
            "Looking ahead to the next several days, a pattern change is expected to bring cooler temperatures.",
            "For the extended period, a series of disturbances will move across the region bringing chances for precipitation.",
            "The extended forecast calls for generally quiet conditions through mid-week.",
            "Through the rest of the week, expect a gradual warming trend with increasing humidity.",
        ])

        # ============ DAY ONE (BUGÜN) ============
        day_one_variants = [
            f"Day one, today and tonight: {selected[0]}",
            f"Day one outlook: {selected[0]}",
            f"For the day one period: {selected[0]}",
        ]
        day_one = random.choice(day_one_variants)

        # ============ DAY TWO (YARIN) ============
        day_two_variants = [
            f"Day two, tomorrow: {selected[1]}",
            f"Day two outlook: {selected[1]}",
            f"For the day two period: {selected[1]}",
        ]
        day_two = random.choice(day_two_variants)

        # ============ SPOTTER BİLGİSİ ============
        spotter_note = random.choice([
            "Spotter activation will not be needed at this time.",
            "Spotter activation may be needed during the afternoon hours.",
            "Spotters are encouraged to report any significant weather to the National Weather Service.",
            "No spotter activation is expected through the forecast period.",
            "Spotter activation will be possible if severe weather develops.",
        ])

        # ============ KAPANIŞ ============
        closing_variants = [
            f"This hazardous weather outlook is issued by the National Weather Service office in {city}.",
            f"This outlook was issued by the National Weather Service in {city}, {state}.",
            f"The next hazardous weather outlook will be issued by the National Weather Service in {city}.",
            f"This concludes the hazardous weather outlook for {area_display}.",
        ]
        closing = random.choice(closing_variants)

        # ============ TAM OUTLOOK METNİ ============
        outlook = f"""
        {opening}

        {today_note}

        {day_one}

        {day_two}

        {tomorrow_note}

        {spotter_note}

        {closing}
        """

        return ' '.join(outlook.split())

    # ============================================================
    # 7. DONNA - MARINE FORECAST
    # ============================================================
    def get_coastal_marine_forecast(self):
        """Bölgeye göre marine forecast - DONNA okur"""
        now = self.get_local_time()
        time_str = now.strftime("%I:%M %p")
        day_str = now.strftime("%A")

        state = self.state.lower()

        if state in ["california", "oregon", "washington", "alaska", "hawaii"]:
            ocean = "pacific"
        elif state in ["florida", "alabama", "mississippi", "louisiana", "texas"]:
            ocean = "gulf"
        elif state in ["maine", "new hampshire", "massachusetts", "rhode island",
                       "connecticut", "new york", "new jersey", "delaware",
                       "maryland", "virginia", "north carolina", "south carolina", "georgia"]:
            ocean = "atlantic"
        else:
            ocean = "generic"

        synopsis_map = {
            "pacific": "A Pacific cold front will move through the coastal waters, bringing increasing winds and seas.",
            "atlantic": "A low-pressure system off the Atlantic coast will produce gusty winds and building seas.",
            "gulf": "A Gulf disturbance will bring scattered squalls and elevated seas to the coastal waters.",
            "generic": "A frontal system will move through the coastal waters, bringing increasing winds and seas.",
        }

        forecast_map = {
            "pacific": {
                "today_wind": "Northwest 15 to 25 knots",
                "today_seas": "6 to 10 feet",
                "tonight_wind": "Northwest 10 to 20 knots",
                "tonight_seas": "4 to 8 feet",
                "tomorrow_wind": "Northwest 10 to 15 knots",
                "tomorrow_seas": "3 to 6 feet",
            },
            "atlantic": {
                "today_wind": "Southwest 10 to 20 knots",
                "today_seas": "3 to 6 feet",
                "tonight_wind": "West 15 to 25 knots",
                "tonight_seas": "5 to 8 feet",
                "tomorrow_wind": "Northwest 10 to 20 knots",
                "tomorrow_seas": "4 to 7 feet",
            },
            "gulf": {
                "today_wind": "Southeast 10 to 15 knots",
                "today_seas": "2 to 4 feet",
                "tonight_wind": "South 5 to 15 knots",
                "tonight_seas": "2 to 3 feet",
                "tomorrow_wind": "Southwest 10 to 20 knots",
                "tomorrow_seas": "3 to 5 feet",
            },
            "generic": {
                "today_wind": "Northwest 15 to 25 knots",
                "today_seas": "5 to 9 feet",
                "tonight_wind": "Northwest 10 to 20 knots",
                "tonight_seas": "4 to 7 feet",
                "tomorrow_wind": "Northwest 10 to 15 knots",
                "tomorrow_seas": "3 to 6 feet",
            },
        }

        synopsis = synopsis_map.get(ocean, synopsis_map["generic"])
        data = forecast_map.get(ocean, forecast_map["generic"])

        opening_variants = [
            "Coastal marine forecast for the coastal waters.",
            "Here is the coastal marine forecast for the coastal waters.",
            "The coastal marine forecast for the coastal waters.",
            "Now the coastal marine forecast for the coastal waters.",
            "This is the coastal marine forecast for the coastal waters.",
        ]

        opening = random.choice(opening_variants)

        forecast = f"""
        {opening}

        Synopsis: {synopsis}

        TODAY:
        Winds: {data['today_wind']}.
        Seas: {data['today_seas']}.
        Visibility: 5 to 10 miles.
        Weather: Scattered showers and isolated thunderstorms.

        TONIGHT:
        Winds: {data['tonight_wind']}.
        Seas: {data['tonight_seas']}.
        Visibility: 3 to 8 miles.

        TOMORROW:
        Winds: {data['tomorrow_wind']}.
        Seas: {data['tomorrow_seas']}.
        Visibility: 6 to 12 miles.

        Mariners are advised to exercise caution.
        """

        return ' '.join(forecast.split())

    # ============================================================
    # 8. COASTAL WATER OBSERVATIONS
    # ============================================================
    def get_coastal_water_observations(self):
        now = self.get_local_time()
        time_str = now.strftime("%I:%M %p")
        day_str = now.strftime("%A")

        voice = random.choice(["tom", "donna"])

        state = self.state.lower()
        if state in ["california", "oregon", "washington", "alaska", "hawaii"]:
            stations = [
                {"name": "Station 46025 - Santa Monica Basin", "lat": "33.7N", "lon": "119.0W"},
                {"name": "Station 46026 - San Francisco", "lat": "37.7N", "lon": "122.8W"},
                {"name": "Station 46050 - Newport, Oregon", "lat": "44.6N", "lon": "124.5W"},
                {"name": "Station 46011 - Santa Maria", "lat": "34.9N", "lon": "120.9W"},
                {"name": "Station 51001 - Northwest Hawaii", "lat": "23.4N", "lon": "162.2W"},
            ]
        elif state in ["florida", "alabama", "mississippi", "louisiana", "texas"]:
            stations = [
                {"name": "Station 42001 - Gulf of Mexico", "lat": "25.9N", "lon": "89.7W"},
                {"name": "Station 42002 - West Gulf", "lat": "26.1N", "lon": "93.4W"},
                {"name": "Station 42003 - East Gulf", "lat": "26.0N", "lon": "85.9W"},
                {"name": "Station 42036 - Tampa", "lat": "28.5N", "lon": "84.5W"},
                {"name": "Station 42040 - Mobile South", "lat": "29.2N", "lon": "88.2W"},
            ]
        else:
            stations = [
                {"name": "Station 44025 - Long Island Sound", "lat": "41.0N", "lon": "72.0W"},
                {"name": "Station 44065 - New York Harbor", "lat": "40.5N", "lon": "73.8W"},
                {"name": "Station 44017 - Atlantic City", "lat": "39.0N", "lon": "74.0W"},
                {"name": "Station 44020 - Nantucket Sound", "lat": "41.5N", "lon": "70.0W"},
                {"name": "Station 44025 - Block Island", "lat": "41.2N", "lon": "71.5W"},
            ]

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
                "smooth to slight", "slight to moderate", "moderate",
                "moderate to rough", "rough", "very rough"
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

        opening_variants = [
            "Coastal water observations for the coastal waters.",
            "Here are the coastal water observations for the coastal waters.",
            "The coastal water observations for the coastal waters.",
            "Now the coastal water observations for the coastal waters.",
            "This is the coastal water observations report for the coastal waters.",
        ]

        opening = random.choice(opening_variants)

        summary = f"""
        {opening}

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
    # 9. TOM - CLIMATE SUMMARY — 2010'lar formatı
    # ============================================================
    def get_climate_summary(self, data):
        if not data:
            return "Climate summary not available."

        forecast = data.get('forecast', {})
        city = self.city
        state = self.state

        now = self.get_local_time()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%B %d, %Y")

        max_temp = 0
        min_temp = 100
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

        # Şehre/bölgeye göre normal değerler
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

        normal_precip = round(random.uniform(0.5, 4.0), 2)
        year_precip = round(total_precip + random.uniform(5.0, 20.0), 2)

        opening_variants = [
            f"The {city}, {state} climate summary for this {time_period}.",
            f"Here is the {city}, {state} climate summary for this {time_period}.",
            f"The climate summary for {city}, {state} this {time_period}.",
            f"Now the climate summary for {city}, {state} this {time_period}.",
            f"This is the {city}, {state} climate summary for this {time_period}.",
        ]

        opening = random.choice(opening_variants)

        summary = f"""
        {opening}

        The high temperature today was {max_temp} degrees.
        The normal high for this date is {normal_high} degrees.
        The record high for this date is {record_high} degrees, set in {record_year_high}.

        The low temperature today was {min_temp} degrees.
        The normal low for this date is {normal_low} degrees.
        The record low for this date is {record_low} degrees, set in {record_year_low}.

        Precipitation today was {precip} inches.
        The monthly precipitation total is {total_precip:.2f} inches.
        The normal monthly precipitation is {normal_precip} inches.
        The year-to-date precipitation total is {year_precip:.2f} inches.

        The normal high temperature for tomorrow is {normal_high + random.randint(-5, 5)} degrees,
        and the normal low is {normal_low + random.randint(-5, 5)} degrees.

        Sunset tonight is at {sunset}.
        Sunrise tomorrow is at {sunrise}.
        """

        return ' '.join(summary.split())

    # ============================================================
    # 10. EMERGENCY SYSTEM
    # ============================================================
    def check_for_emergency(self, alerts_data):
        """En yüksek öncelikli uyarıyı döndürür"""
        if not alerts_data or 'features' not in alerts_data:
            return None

        emergency_keywords = [
            'tornado', 'flash flood', 'severe thunderstorm',
            'hurricane', 'extreme wind', 'blizzard', 'ice storm',
            'tsunami', 'wildfire', 'volcano', 'extreme heat',
            'dust storm', 'winter storm', 'flood', 'landslide',
            'evacuation', 'civil emergency', 'shelter in place',
            'avalanche', 'heavy snow', 'freezing rain', 'extreme cold'
        ]

        best_alert = None
        best_priority = -1

        for alert in alerts_data['features']:
            props = alert.get('properties', {})
            event = props.get('event', '').lower()
            severity = props.get('severity', '')
            urgency = props.get('urgency', '')
            category = props.get('category', '')
            status = props.get('status', '').lower()

            if status in ['cancelled', 'canceled']:
                continue

            priority = 0

            if 'emergency' in event or category == 'Emergency':
                priority = 100
            elif 'warning' in event:
                priority = 80
            elif 'watch' in event:
                priority = 60
            elif 'advisory' in event:
                priority = 40
            elif 'statement' in event:
                priority = 20
            else:
                priority = 30

            if any(kw in event for kw in emergency_keywords):
                priority += 15

            if severity == 'Extreme':
                priority += 20
            elif severity == 'Severe':
                priority += 10

            if urgency == 'Immediate':
                priority += 15
            elif urgency == 'Expected':
                priority += 5

            if priority > best_priority:
                best_priority = priority
                area = props.get('areaDesc', 'this area')
                area_clean = self.clean_area(area)

                best_alert = {
                    'event': props.get('event', 'Emergency'),
                    'severity': severity,
                    'urgency': urgency,
                    'category': category,
                    'area': area_clean,
                    'headline': props.get('headline', ''),
                    'description': props.get('description', ''),
                    'instruction': props.get('instruction', ''),
                    '_priority': priority
                }

        return best_alert

    # ============================================================
    # 11. TEST SYSTEM
    # ============================================================
    def is_test_time(self):
        now = self.get_local_time()
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
        now = self.get_local_time()
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
            "HST": "Hawaii Standard Time",
            "kt": "knots",
            "NM": "Nautical Miles",
            "mph": "miles per hour",
            "ft": "feet",
            "NWS": "National Weather Service",
            "&": "and",
            "°F": "degrees Fahrenheit",
            "°C": "degrees Celsius",
            "%": "percent",
        }

        for old, new in replacements.items():
            text = re.sub(r'\b' + re.escape(old) + r'\b', new, text, flags=re.IGNORECASE)

        # TARİH FORMATI KORU
        text = re.sub(
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',
            r'\1 slash \2 slash \3',
            text
        )

        # Kalan slash'ler
        text = re.sub(r'(\d+)/(\d+)', r'\1 or \2', text)

        # NEGATİF KOORDİNAT
        text = re.sub(r'-\s*(\d+\.\d+)', r'\1', text)

        # GERÇEK EKSİ
        text = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 minus \2', text)

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

                if len(periods) >= 3:
                    tonight = periods[1].get('shortForecast', '')
                    if tonight:
                        message_parts.append(f"Tonight: {tonight}")
                    if len(periods) >= 4:
                        tomorrow = periods[2].get('shortForecast', '')
                        if tomorrow:
                            message_parts.append(f"Tomorrow: {tomorrow}")

        return ' '.join(message_parts)
