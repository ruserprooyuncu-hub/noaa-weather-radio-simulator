import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog
import threading
import os
import time
import random
import re
import webbrowser
from datetime import datetime
from noaa_radio import NOAAWeatherRadio
from noaa_stations import NOAA_STATIONS

# ============================================================
# 1. ÇOKLU DİL DESTEĞİ
# ============================================================
LANGUAGES = {
    "en": {
        "app_title": "NOAA Weather Radio Simulator v1.0 - All Stations",
        "start": "▶ START BROADCAST",
        "stop": "⏹ STOP",
        "fetch": "📡 FETCH DATA",
        "select": "🌍 SELECT STATION",
        "settings": "⚙ SETTINGS",
        "save": "💾 SAVE",
        "exit": "❌ EXIT",
        "standby": "STAND-BY",
        "active": "BROADCASTING ACTIVE",
        "ready": "READY",
        "opening": "Opening",
        "time": "Time",
        "hourly": "Hourly Roundup",
        "alerts": "Active Alerts",
        "nowcast": "Nowcast",
        "zone": "Zone Forecast",
        "hazardous": "Hazardous Outlook",
        "marine": "Marine Forecast",
        "coastal": "Coastal Water Observations",
        "climate": "Climate Summary",
        "complete": "Broadcast complete",
        "silence": "seconds silence",
        "no_data": "No data received, retrying in 10 seconds...",
        "error": "Error",
        "settings_title": "⚙ SETTINGS",
        "latitude": "Latitude:",
        "longitude": "Longitude:",
        "enable_tests": "Enable Weekly/Monthly Tests",
        "enable_push": "Enable Push Notifications",
        "language": "Language:",
        "switched": "Switched to",
        "updated": "Settings updated:",
        "test_on": "Test Mode: ON",
        "test_off": "Test Mode: OFF",
        "save_error": "Please enter valid numbers.",
        "saved": "Saved:",
        "save_failed": "Save failed:",
        "shutdown": "System shutting down...",
        "alert_title": "🚨 EMERGENCY ALERT!",
        "warning": "Warning",
        "area": "Area",
        "severity": "Severity",
        "urgent": "Urgent"
    },
    "tr": {
        "app_title": "NOAA Hava Durumu Radyo Simülatörü v1.0 - Tüm İstasyonlar",
        "start": "▶ YAYINI BAŞLAT",
        "stop": "⏹ DURDUR",
        "fetch": "📡 VERİ ÇEK",
        "select": "🌍 İSTASYON SEÇ",
        "settings": "⚙ AYARLAR",
        "save": "💾 KAYDET",
        "exit": "❌ ÇIKIŞ",
        "standby": "BEKLEMEDE",
        "active": "YAYIN AKTİF",
        "ready": "HAZIR",
        "opening": "Açılış",
        "time": "Saat",
        "hourly": "Saatlik Özet",
        "alerts": "Aktif Uyarılar",
        "nowcast": "Kısa Vadeli Tahmin",
        "zone": "Bölge Tahmini",
        "hazardous": "Tehlikeli Hava Durumu",
        "marine": "Denizcilik Tahmini",
        "coastal": "Kıyı Suları Gözlemleri",
        "climate": "İklim Özeti",
        "complete": "Yayın tamamlandı",
        "silence": "saniye sessizlik",
        "no_data": "Veri alınamadı, 10 saniye sonra tekrar deneniyor...",
        "error": "Hata",
        "settings_title": "⚙ AYARLAR",
        "latitude": "Enlem:",
        "longitude": "Boylam:",
        "enable_tests": "Haftalık/Aylık Testleri Aktif Et",
        "enable_push": "Bildirimleri Aktif Et",
        "language": "Dil:",
        "switched": "geçildi",
        "updated": "Ayarlar güncellendi:",
        "test_on": "Test Modu: AÇIK",
        "test_off": "Test Modu: KAPALI",
        "save_error": "Geçerli bir sayı giriniz.",
        "saved": "Kaydedildi:",
        "save_failed": "Kayıt başarısız:",
        "shutdown": "Sistem kapatılıyor...",
        "alert_title": "🚨 ACİL DURUM UYARISI!",
        "warning": "Uyarı",
        "area": "Bölge",
        "severity": "Şiddet",
        "urgent": "Acil"
    },
    "de": {
        "app_title": "NOAA Wetterradio Simulator v1.0 - Alle Stationen",
        "start": "▶ SENDUNG STARTEN",
        "stop": "⏹ STOPP",
        "fetch": "📡 DATEN ABRUFEN",
        "select": "🌍 STATION WÄHLEN",
        "settings": "⚙ EINSTELLUNGEN",
        "save": "💾 SPEICHERN",
        "exit": "❌ BEENDEN",
        "standby": "BEREITSCHAFT",
        "active": "SENDUNG AKTIV",
        "ready": "BEREIT",
        "opening": "Eröffnung",
        "time": "Uhrzeit",
        "hourly": "Stündliche Übersicht",
        "alerts": "Aktive Warnungen",
        "nowcast": "Kurzfristvorhersage",
        "zone": "Zonenprognose",
        "hazardous": "Gefahrenausblick",
        "marine": "Seewettervorhersage",
        "coastal": "Küstengewässer Beobachtungen",
        "climate": "Klimaübersicht",
        "complete": "Sendung abgeschlossen",
        "silence": "Sekunden Stille",
        "no_data": "Keine Daten erhalten, Wiederholung in 10 Sekunden...",
        "error": "Fehler",
        "settings_title": "⚙ EINSTELLUNGEN",
        "latitude": "Breitengrad:",
        "longitude": "Längengrad:",
        "enable_tests": "Wöchentliche/Monatliche Tests aktivieren",
        "enable_push": "Benachrichtigungen aktivieren",
        "language": "Sprache:",
        "switched": "gewechselt zu",
        "updated": "Einstellungen aktualisiert:",
        "test_on": "Testmodus: EIN",
        "test_off": "Testmodus: AUS",
        "save_error": "Bitte gültige Zahlen eingeben.",
        "saved": "Gespeichert:",
        "save_failed": "Speichern fehlgeschlagen:",
        "shutdown": "System wird heruntergefahren...",
        "alert_title": "🚨 NOTFALLWARNUNG!",
        "warning": "Warnung",
        "area": "Gebiet",
        "severity": "Schwere",
        "urgent": "Dringend"
    },
    "es": {
        "app_title": "Simulador de Radio NOAA v1.0 - Todas las Estaciones",
        "start": "▶ INICIAR TRANSMISIÓN",
        "stop": "⏹ DETENER",
        "fetch": "📡 OBTENER DATOS",
        "select": "🌍 SELECCIONAR ESTACIÓN",
        "settings": "⚙ AJUSTES",
        "save": "💾 GUARDAR",
        "exit": "❌ SALIR",
        "standby": "EN ESPERA",
        "active": "TRANSMISIÓN ACTIVA",
        "ready": "LISTO",
        "opening": "Apertura",
        "time": "Hora",
        "hourly": "Resumen Horario",
        "alerts": "Alertas Activas",
        "nowcast": "Pronóstico a Corto Plazo",
        "zone": "Pronóstico por Zona",
        "hazardous": "Perspectiva de Peligros",
        "marine": "Pronóstico Marino",
        "coastal": "Observaciones Costeras",
        "climate": "Resumen Climático",
        "complete": "Transmisión completada",
        "silence": "segundos de silencio",
        "no_data": "No se recibieron datos, reintentando en 10 segundos...",
        "error": "Error",
        "settings_title": "⚙ AJUSTES",
        "latitude": "Latitud:",
        "longitude": "Longitud:",
        "enable_tests": "Activar Pruebas Semanales/Mensuales",
        "enable_push": "Activar Notificaciones",
        "language": "Idioma:",
        "switched": "cambiado a",
        "updated": "Ajustes actualizados:",
        "test_on": "Modo de Prueba: ACTIVADO",
        "test_off": "Modo de Prueba: DESACTIVADO",
        "save_error": "Por favor, ingrese números válidos.",
        "saved": "Guardado:",
        "save_failed": "Error al guardar:",
        "shutdown": "Apagando sistema...",
        "alert_title": "🚨 ¡ALERTA DE EMERGENCIA!",
        "warning": "Advertencia",
        "area": "Área",
        "severity": "Gravedad",
        "urgent": "Urgente"
    },
    "fr": {
        "app_title": "Simulateur de Radio NOAA v1.0 - Toutes les Stations",
        "start": "▶ DÉMARRER LA DIFFUSION",
        "stop": "⏹ ARRÊTER",
        "fetch": "📡 RÉCUPÉRER LES DONNÉES",
        "select": "🌍 SÉLECTIONNER LA STATION",
        "settings": "⚙ PARAMÈTRES",
        "save": "💾 ENREGISTRER",
        "exit": "❌ QUITTER",
        "standby": "EN VEILLE",
        "active": "DIFFUSION ACTIVE",
        "ready": "PRÊT",
        "opening": "Ouverture",
        "time": "Heure",
        "hourly": "Résumé Horaire",
        "alerts": "Alertes Actives",
        "nowcast": "Prévision à Court Terme",
        "zone": "Prévision par Zone",
        "hazardous": "Aperçu des Dangers",
        "marine": "Prévision Maritime",
        "coastal": "Observations Côtières",
        "climate": "Résumé Climatique",
        "complete": "Diffusion terminée",
        "silence": "secondes de silence",
        "no_data": "Aucune donnée reçue, nouvelle tentative dans 10 secondes...",
        "error": "Erreur",
        "settings_title": "⚙ PARAMÈTRES",
        "latitude": "Latitude:",
        "longitude": "Longitude:",
        "enable_tests": "Activer les Tests Hebdomadaires/Mensuels",
        "enable_push": "Activer les Notifications",
        "language": "Langue:",
        "switched": "passé à",
        "updated": "Paramètres mis à jour:",
        "test_on": "Mode Test: ACTIF",
        "test_off": "Mode Test: INACTIF",
        "save_error": "Veuillez entrer des nombres valides.",
        "saved": "Enregistré:",
        "save_failed": "Échec de l'enregistrement:",
        "shutdown": "Arrêt du système...",
        "alert_title": "🚨 ALERTE D'URGENCE!",
        "warning": "Avertissement",
        "area": "Zone",
        "severity": "Gravité",
        "urgent": "Urgent"
    }
}

# ============================================================
# 2. PUSH NOTIFICATION
# ============================================================
try:
    from win10toast import ToastNotifier
    PUSH_AVAILABLE = True
except ImportError:
    PUSH_AVAILABLE = False
    print("⚠️ win10toast not installed. Push notifications disabled.")
    print("📦 Install: pip install win10toast")

def send_push_notification(title, message, duration=10):
    if not PUSH_AVAILABLE:
        return False
    try:
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=duration, threaded=True)
        return True
    except Exception as e:
        print(f"❌ Push notification error: {e}")
        return False

# ============================================================
# 3. HARİTA
# ============================================================
def create_map_html():
    try:
        import folium
    except ImportError:
        print("⚠️ folium not installed. Map feature disabled.")
        print("📦 Install: pip install folium")
        return None
    
    map_center = [39.8283, -98.5795]
    map_obj = folium.Map(location=map_center, zoom_start=4)
    
    for name, data in NOAA_STATIONS.items():
        lat = data.get("lat")
        lon = data.get("lon")
        city = data.get("city", "")
        state = data.get("state", "")
        callsign = data.get("callsign", "")
        freq = data.get("frequency", "")
        
        if lat and lon:
            popup_text = f"""
            <b>{city}, {state}</b><br>
            Callsign: {callsign}<br>
            Frequency: {freq} MHz<br>
            <i>{data.get('description', '')}</i>
            """
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{city}, {state}",
                icon=folium.Icon(color="red", icon="cloud", prefix="fa")
            ).add_to(map_obj)
    
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "station_map.html")
    map_obj.save(html_path)
    return html_path

class NOAAWeatherRadioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NOAA Weather Radio Simulator v1.0 - All Stations")
        self.root.geometry("1000x750")
        self.root.configure(bg='#000000')
        self.root.minsize(800, 600)
        
        self.radio = None
        self.is_broadcasting = False
        self.broadcast_thread = None
        self.alert_played = False
        self.broadcast_count = 0
        self.previous_alerts = []
        self.current_station = "Gunnison"
        self.push_enabled = True
        
        self.current_lang = "en"
        self.lang = LANGUAGES[self.current_lang]
        
        self.create_ui()
        self.load_station("Gunnison")
    
    def _(self, key):
        return self.lang.get(key, key)
    
    def create_ui(self):
        main_frame = tk.Frame(self.root, bg='#000000')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.display = scrolledtext.ScrolledText(
            main_frame,
            bg='#000000',
            fg='#00ff00',
            font=('Courier New', 11),
            insertbackground='#00ff00',
            relief='flat',
            bd=0,
            wrap=tk.WORD
        )
        self.display.pack(fill=tk.BOTH, expand=True)
        
        status_frame = tk.Frame(self.root, bg='#111111', height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(
            status_frame,
            text=f" {self._('standby')} | GUNNISON COUNTY, CO | ZONE: COZ012",
            bg='#111111',
            fg='#00ff00',
            font=('Courier New', 9),
            anchor='w'
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.clock_label = tk.Label(
            status_frame,
            text=datetime.now().strftime('%H:%M:%S MST'),
            bg='#111111',
            fg='#00ff00',
            font=('Courier New', 9)
        )
        self.clock_label.pack(side=tk.RIGHT, padx=10)
        self.update_clock()
        
        btn_frame = tk.Frame(self.root, bg='#1a1a1a', height=45)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_style = {
            'font': ('Segoe UI', 10, 'bold'),
            'padx': 15,
            'pady': 6,
            'relief': 'raised',
            'bd': 2
        }
        
        self.btn_start = tk.Button(
            btn_frame, text=self._('start'), bg='#00aa00', fg='white',
            command=self.start_broadcast, **btn_style
        )
        self.btn_start.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.btn_stop = tk.Button(
            btn_frame, text=self._('stop'), bg='#cc0000', fg='white',
            command=self.stop_broadcast, **btn_style
        )
        self.btn_stop.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_stop.config(state=tk.DISABLED)
        
        tk.Button(
            btn_frame, text=self._('fetch'), bg='#0055aa', fg='white',
            command=self.fetch_data, **btn_style
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            btn_frame, text=self._('select'), bg='#00aaff', fg='white',
            command=self.open_station_selector, **btn_style
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            btn_frame, text="🗺️ MAP", bg='#ff8800', fg='white',
            command=self.open_map, **btn_style
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            btn_frame, text=self._('settings'), bg='#555555', fg='white',
            command=self.open_settings, **btn_style
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            btn_frame, text=self._('save'), bg='#aa8800', fg='white',
            command=self.save_broadcast, **btn_style
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            btn_frame, text=self._('exit'), bg='#444444', fg='white',
            command=self.quit_app, **btn_style
        ).pack(side=tk.RIGHT, padx=5, pady=5)
    
    def open_map(self):
        html_path = create_map_html()
        if html_path:
            webbrowser.open(html_path)
            self.log_message("🗺️ Map opened in browser.")
        else:
            self.log_message("❌ Map feature not available. Install folium: pip install folium")
    
    def update_clock(self):
        now = datetime.now().strftime('%H:%M:%S MST')
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)
    
    def log_message(self, text):
        self.display.insert(tk.END, text + "\n")
        self.display.see(tk.END)
        self.root.update_idletasks()
    
    def update_ui_language(self):
        self.lang = LANGUAGES[self.current_lang]
        self.root.title(self._('app_title'))
        self.btn_start.config(text=self._('start'))
        self.btn_stop.config(text=self._('stop'))
    
    def load_station(self, station_name):
        if station_name not in NOAA_STATIONS:
            station_name = "Gunnison"
        
        station_data = NOAA_STATIONS[station_name]
        self.current_station = station_name
        
        if self.radio:
            if self.is_broadcasting:
                self.stop_broadcast()
        
        self.radio = NOAAWeatherRadio(station_data)
        
        self.status_label.config(
            text=f" {self._('standby')} | {station_data['city']}, {station_data['state']} | {station_data['callsign']} | {station_data['frequency']} MHz"
        )
        
        self.log_message("=" * 70)
        self.log_message(f"  📻 {station_data['callsign']} - {station_data['city']}, {station_data['state']}")
        self.log_message(f"  📡 Frequency: {station_data['frequency']} MHz")
        self.log_message(f"  📍 {station_data['description']}")
        self.log_message("=" * 70)
    
    def open_station_selector(self):
        selector = tk.Toplevel(self.root)
        selector.title(f"{self._('select')} - " + str(len(NOAA_STATIONS)) + " Stations")
        selector.geometry("750x550")
        selector.configure(bg='#1a1a1a')
        selector.transient(self.root)
        selector.grab_set()
        
        tk.Label(selector, text="🌍 NOAA WEATHER RADIO STATIONS (" + str(len(NOAA_STATIONS)) + ")", 
                 bg='#1a1a1a', fg='#00ff00',
                 font=('Courier New', 14, 'bold')).pack(pady=10)
        
        tk.Label(selector, text="ℹ️ Click 'CHECK EVENTS' to see active alerts for selected station",
                 bg='#1a1a1a', fg='#ffaa00',
                 font=('Courier New', 9)).pack(pady=2)
        
        filter_frame = tk.Frame(selector, bg='#1a1a1a')
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(filter_frame, text="State Filter:", bg='#1a1a1a', fg='#00ff00',
                 font=('Courier New', 10)).pack(side=tk.LEFT, padx=5)
        
        states = sorted(set([data['state'] for data in NOAA_STATIONS.values()]))
        state_filter = ttk.Combobox(filter_frame, values=["All"] + states, state="readonly", width=20)
        state_filter.set("All")
        state_filter.pack(side=tk.LEFT, padx=5)
        
        list_frame = tk.Frame(selector, bg='#1a1a1a')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        station_list = tk.Listbox(
            list_frame,
            bg='#000000',
            fg='#00ff00',
            font=('Courier New', 10),
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set,
            height=20
        )
        station_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=station_list.yview)
        
        def update_list():
            station_list.delete(0, tk.END)
            filter_state = state_filter.get()
            for name, data in NOAA_STATIONS.items():
                if filter_state == "All" or data['state'] == filter_state:
                    display = f"{data['callsign']} - {data['city']}, {data['state']} ({data['frequency']} MHz)"
                    station_list.insert(tk.END, display)
        
        state_filter.bind('<<ComboboxSelected>>', lambda e: update_list())
        
        def check_events():
            selection = station_list.curselection()
            if not selection:
                self.log_message("⚠️ Please select a station first.")
                return
            
            idx = selection[0]
            selected_text = station_list.get(idx)
            
            for name, data in NOAA_STATIONS.items():
                display = f"{data['callsign']} - {data['city']}, {data['state']} ({data['frequency']} MHz)"
                if display in selected_text:
                    self.log_message(f"🔍 Checking events for {name}...")
                    try:
                        temp_radio = NOAAWeatherRadio(data)
                        weather_data = temp_radio.get_weather_data()
                        if weather_data:
                            emergency = temp_radio.check_for_emergency(weather_data.get('alerts', {}))
                            if emergency:
                                event_name = emergency.get('event', '')
                                severity = emergency.get('severity', '')
                                if severity in ['Extreme', 'Severe']:
                                    event_display = f" 🔴 {event_name} ({severity})"
                                else:
                                    event_display = f" 🟡 {event_name}"
                                station_list.delete(idx)
                                station_list.insert(idx, f"{display}{event_display}")
                                station_list.selection_set(idx)
                                self.log_message(f"📢 {event_name} ({severity}) active for {name}")
                            else:
                                station_list.delete(idx)
                                station_list.insert(idx, f"{display} ✅")
                                station_list.selection_set(idx)
                                self.log_message(f"✅ No active alerts for {name}")
                        else:
                            self.log_message(f"❌ No data for {name}")
                    except Exception as e:
                        self.log_message(f"❌ Error checking {name}: {e}")
                    break
        
        def select_station():
            selection = station_list.curselection()
            if selection:
                idx = selection[0]
                selected_text = station_list.get(idx)
                for name, data in NOAA_STATIONS.items():
                    display = f"{data['callsign']} - {data['city']}, {data['state']} ({data['frequency']} MHz)"
                    if display in selected_text:
                        selector.destroy()
                        self.load_station(name)
                        self.log_message(f"\n✅ {self._('switched')} {NOAA_STATIONS[name]['callsign']}!")
                        return
        
        btn_frame = tk.Frame(selector, bg='#1a1a1a')
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame, text="🔄 CHECK EVENTS", bg='#aa8800', fg='white',
            command=check_events, font=('Segoe UI', 10, 'bold'),
            padx=20, pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, text="SELECT", bg='#00aa00', fg='white',
            command=select_station, font=('Segoe UI', 10, 'bold'),
            padx=20, pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        update_list()
    
    def wait(self, seconds=3):
        for _ in range(seconds):
            if not self.is_broadcasting:
                return False
            time.sleep(1)
        return True
    
    def start_broadcast(self):
        if self.is_broadcasting or not self.radio:
            return
        
        self.is_broadcasting = True
        self.broadcast_count = 0
        self.previous_alerts = []
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.status_label.config(text=f" {self._('active')}")
        self.log_message("\n" + "=" * 70)
        self.log_message(f"  ▶ {self._('start')} | {datetime.now().strftime('%H:%M:%S')}")
        self.log_message(f"  📻 {self.radio.callsign} - {self.radio.city}")
        self.log_message("=" * 70)
        
        self.broadcast_thread = threading.Thread(target=self.broadcast_loop)
        self.broadcast_thread.daemon = True
        self.broadcast_thread.start()
    
    def broadcast_loop(self):
        first_run = True
        
        while self.is_broadcasting:
            try:
                if self.radio.test_mode:
                    if self.radio.check_and_run_test():
                        if not self.wait(5): break
                
                self.log_message("📡 Fetching NOAA data...")
                data = self.radio.get_weather_data()
                
                if data:
                    # =========================================================
                    # 1. OPENING (İstasyona göre ses)
                    # =========================================================
                    if first_run:
                        opening = self.radio.get_opening_message()
                        voice = self.radio.station.get("voice", "harry")
                        
                        if voice == "tom":
                            voice_name = "tom"
                            speed = -1
                        elif voice == "paul":
                            voice_name = "paul"
                            speed = 0
                        else:
                            voice_name = "harry"
                            speed = 0
                        
                        self.log_message(f"🎙️ {voice_name.upper()} ({self._('opening')}) speaking...")
                        self.log_message("-" * 40)
                        self.log_message(opening)
                        self.log_message("-" * 40)
                        self.radio.speak_with_voice(opening, voice_name, speed)
                        if not self.wait(3): break
                        first_run = False
                    
                    # =========================================================
                    # 2. PAUL - TIME ANNOUNCEMENT
                    # =========================================================
                    time_msg = self.radio.time_announcement()
                    self.log_message(f"🕐 PAUL ({self._('time')}) speaking...")
                    self.log_message("-" * 40)
                    self.log_message(time_msg)
                    self.log_message("-" * 40)
                    self.radio.speak_with_voice(time_msg, "paul", 0)
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 3. TOM - HOURLY ROUNDUP
                    # =========================================================
                    hourly_msg = self.radio.get_hourly_roundup(data)
                    self.log_message(f"📊 TOM ({self._('hourly')}) speaking...")
                    self.log_message("-" * 40)
                    self.log_message(hourly_msg)
                    self.log_message("-" * 40)
                    self.radio.speak_with_voice(hourly_msg, "tom", 0)
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 4. TOM - ACTIVE ALERTS
                    # =========================================================
                    alerts = data.get('alerts', {})
                    active_alerts = []
                    
                    if alerts and 'features' in alerts:
                        for alert in alerts['features']:
                            props = alert.get('properties', {})
                            severity = props.get('severity', '')
                            event = props.get('event', '').lower()
                            if severity in ['Extreme', 'Severe'] or "warning" in event:
                                active_alerts.append(props)
                    
                    current_alert_ids = []
                    for alert in active_alerts:
                        event = alert.get('event', '')
                        area = alert.get('areaDesc', '')
                        area_clean = self.radio.clean_area(area)
                        current_alert_ids.append(f"{event}_{area_clean}")
                    
                    previous_alert_ids = []
                    for alert in self.previous_alerts:
                        event = alert.get('event', '')
                        area = alert.get('area', '')
                        previous_alert_ids.append(f"{event}_{area}")
                    
                    if active_alerts and (current_alert_ids != previous_alert_ids or first_run):
                        self.log_message(f"🚨 TOM ({self._('alerts')}) speaking...")
                        self.log_message("-" * 40)
                        
                        for alert in active_alerts[:5]:
                            event = alert.get('event', 'Alert')
                            area = alert.get('areaDesc', 'this area')
                            area_clean = self.radio.clean_area(area)
                            description = alert.get('description', '')
                            instruction = alert.get('instruction', '')
                            severity = alert.get('severity', '')
                            effective = alert.get('effective', '')
                            expires = alert.get('expires', '')
                            
                            end_time = ""
                            if expires:
                                try:
                                    dt = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                                    end_time = dt.strftime("%I:%M %p %A")
                                    end_time = end_time.replace("AM", "A.M.").replace("PM", "P.M.").replace("  ", " ")
                                except:
                                    end_time = ""
                            
                            if end_time:
                                alert_msg = f"{event} in effect until {end_time}. "
                            else:
                                alert_msg = f"{event} remains in effect until further notice. "
                            
                            if description:
                                alert_msg += description + ". "
                            if instruction:
                                alert_msg += instruction + ". "
                            
                            self.log_message(f"📢 {event} - {area_clean}")
                            self.radio.speak_with_voice(alert_msg, "tom", 0)
                            
                            if self.push_enabled:
                                send_push_notification(
                                    f"{self._('alert_title')}",
                                    f"{event}\n{self._('area')}: {area_clean}\n{self._('severity')}: {severity}",
                                    duration=10
                                )
                            
                            if not self.wait(3): break
                        
                        self.log_message("-" * 40)
                        self.log_message(f"✅ {self._('alerts')} complete.\n")
                        self.previous_alerts = active_alerts
                    else:
                        self.log_message(f"ℹ️ No new alerts.\n")
                    
                    # =========================================================
                    # 5. TOM - NOWCAST
                    # =========================================================
                    nowcast_msg = self.radio.get_nowcast(data)
                    self.log_message(f"🌤️ TOM ({self._('nowcast')}) speaking...")
                    self.log_message("-" * 40)
                    self.log_message(nowcast_msg)
                    self.log_message("-" * 40)
                    self.radio.speak_with_voice(nowcast_msg, "tom", 0)
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 6. TOM - ZONE FORECAST
                    # =========================================================
                    self.log_message(f"📅 TOM ({self._('zone')}) speaking...")
                    self.log_message("-" * 40)
                    
                    forecast_text = self.radio.get_zone_forecast()
                    if not forecast_text:
                        forecast_text = "Zone forecast not available."
                    
                    city = self.radio.city
                    state = self.radio.state
                    now = datetime.now()
                    time_str = now.strftime("%I:%M %p")
                    day_str = now.strftime("%A")
                    
                    tom_opening = f"Zone forecast for {city}, {state}, issued at {time_str} {day_str}."
                    self.log_message(tom_opening)
                    self.radio.speak_with_voice(tom_opening, "tom", 0)
                    if not self.wait(2): break
                    
                    self.log_message(forecast_text)
                    self.radio.speak_with_voice(forecast_text, "tom", 0)
                    
                    self.log_message("-" * 40)
                    self.log_message(f"✅ {self._('zone')} complete.\n")
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 7. TOM - HAZARDOUS WEATHER OUTLOOK
                    # =========================================================
                    hazardous_msg = self.radio.get_hazardous_outlook(data)
                    self.log_message(f"⚠️ TOM ({self._('hazardous')}) speaking...")
                    self.log_message("-" * 40)
                    self.log_message(hazardous_msg)
                    self.log_message("-" * 40)
                    self.radio.speak_with_voice(hazardous_msg, "tom", 0)
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 8. DONNA - MARINE FORECAST
                    # =========================================================
                    self.log_message(f"🌊 DONNA ({self._('marine')}) speaking...")
                    self.log_message("-" * 40)
                    
                    marine_data = self.radio.get_coastal_marine_forecast()
                    self.log_message(marine_data)
                    self.radio.speak_with_voice(marine_data, "donna", 1)
                    
                    self.log_message("-" * 40)
                    self.log_message(f"✅ {self._('marine')} complete.\n")
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 8.5 TOM/DONNA - COASTAL WATER OBSERVATIONS (YENİ!)
                    # =========================================================
                    coastal_msg, coastal_voice = self.radio.get_coastal_water_observations()
                    self.log_message(f"🌊 {coastal_voice.upper()} ({self._('coastal')}) speaking...")
                    self.log_message("-" * 40)
                    self.log_message(coastal_msg)
                    self.log_message("-" * 40)
                    self.radio.speak_with_voice(coastal_msg, coastal_voice, 0)
                    if not self.wait(3): break
                    
                    # =========================================================
                    # 9. TOM - CLIMATE SUMMARY
                    # =========================================================
                    climate_msg = self.radio.get_climate_summary(data)
                    self.log_message(f"🌡️ TOM ({self._('climate')}) speaking...")
                    self.log_message("-" * 40)
                    self.log_message(climate_msg)
                    self.log_message("-" * 40)
                    self.radio.speak_with_voice(climate_msg, "tom", 0)
                    if not self.wait(2): break
                    
                    self.log_message(f"✅ {self._('complete')} | {datetime.now().strftime('%H:%M:%S')}")
                    
                    self.log_message(f"🔇 5 {self._('silence')}...")
                    self.log_message("=" * 70 + "\n")
                    if not self.wait(5): break
                    
                else:
                    self.log_message(self._('no_data'))
                    if not self.wait(10): break
                    
            except Exception as e:
                self.log_message(f"❌ {self._('error')}: {e}")
                import traceback
                self.log_message(traceback.format_exc())
                if not self.wait(10): break
    
    def stop_broadcast(self):
        self.is_broadcasting = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.status_label.config(text=f" {self._('standby')}")
        self.log_message("\n⏹ BROADCAST STOPPED")
        self.log_message("=" * 70 + "\n")
    
    def fetch_data(self):
        if not self.radio:
            return
        self.log_message("\n📡 Manual data fetch...")
        try:
            data = self.radio.get_weather_data()
            if data:
                tom_message = self.radio.get_weather_summary(data)
                self.log_message("✅ Data received:")
                self.log_message("-" * 40)
                self.log_message(tom_message)
                self.log_message("-" * 40)
            else:
                self.log_message("❌ No data received.")
        except Exception as e:
            self.log_message(f"❌ Error: {e}")
    
    def save_broadcast(self):
        try:
            content = self.display.get(1.0, tk.END)
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text File", "*.txt"), ("All Files", "*.*")],
                initialfile=f"NOAA_Broadcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log_message(f"💾 {self._('saved')}: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror(self._('error'), f"{self._('save_failed')} {e}")
    
    def open_settings(self):
        if not self.radio:
            return
        settings_win = tk.Toplevel(self.root)
        settings_win.title(self._('settings_title'))
        settings_win.geometry("500x480")
        settings_win.configure(bg='#1a1a1a')
        settings_win.resizable(False, False)
        settings_win.transient(self.root)
        settings_win.grab_set()
        
        tk.Label(settings_win, text=self._('settings_title'), bg='#1a1a1a', fg='#00ff00',
                 font=('Courier New', 14, 'bold')).pack(pady=10)
        
        tk.Label(settings_win, text=self._('latitude'), bg='#1a1a1a', fg='#00ff00',
                 font=('Courier New', 10)).pack(pady=(10,0))
        lat_entry = tk.Entry(settings_win, font=('Courier New', 10))
        lat_entry.insert(0, str(self.radio.lat))
        lat_entry.pack()
        
        tk.Label(settings_win, text=self._('longitude'), bg='#1a1a1a', fg='#00ff00',
                 font=('Courier New', 10)).pack(pady=(10,0))
        lon_entry = tk.Entry(settings_win, font=('Courier New', 10))
        lon_entry.insert(0, str(self.radio.lon))
        lon_entry.pack()
        
        tk.Label(settings_win, text=self._('language'), bg='#1a1a1a', fg='#00ff00',
                 font=('Courier New', 10)).pack(pady=(10,0))
        
        lang_var = tk.StringVar(value=self.current_lang)
        lang_options = ["English (en)", "Türkçe (tr)", "Deutsch (de)", "Español (es)", "Français (fr)"]
        lang_codes = ["en", "tr", "de", "es", "fr"]
        lang_menu = ttk.Combobox(settings_win, values=lang_options, state="readonly", width=30)
        current_index = lang_codes.index(self.current_lang) if self.current_lang in lang_codes else 0
        lang_menu.current(current_index)
        lang_menu.pack(pady=5)
        
        test_var = tk.BooleanVar(value=self.radio.test_mode)
        tk.Checkbutton(
            settings_win, 
            text=self._('enable_tests'),
            variable=test_var,
            bg='#1a1a1a',
            fg='#00ff00',
            selectcolor='#1a1a1a',
            font=('Courier New', 10)
        ).pack(pady=(10,5))
        
        push_var = tk.BooleanVar(value=self.push_enabled)
        tk.Checkbutton(
            settings_win,
            text=self._('enable_push'),
            variable=push_var,
            bg='#1a1a1a',
            fg='#00ff00',
            selectcolor='#1a1a1a',
            font=('Courier New', 10)
        ).pack(pady=(5,10))
        
        if not PUSH_AVAILABLE:
            tk.Label(settings_win, text="⚠️ win10toast not installed", 
                     bg='#1a1a1a', fg='#ff4444', font=('Courier New', 8)).pack()
        
        def save_settings():
            try:
                self.radio.lat = float(lat_entry.get())
                self.radio.lon = float(lon_entry.get())
                self.radio.city = f"Location {self.radio.lat}, {self.radio.lon}"
                self.radio.test_mode = test_var.get()
                self.push_enabled = push_var.get()
                
                selected_lang = lang_menu.get()
                for i, lang in enumerate(lang_options):
                    if lang == selected_lang:
                        self.current_lang = lang_codes[i]
                        break
                
                self.update_ui_language()
                self.status_label.config(text=f" {self._('standby')} | {self.radio.city[:20]}")
                self.log_message(f"✅ {self._('updated')} {self.radio.lat}, {self.radio.lon}")
                self.log_message(f"✅ {self._('test_on') if self.radio.test_mode else self._('test_off')}")
                self.log_message(f"✅ Language: {selected_lang}")
                settings_win.destroy()
            except ValueError:
                messagebox.showerror(self._('error'), self._('save_error'))
        
        tk.Button(settings_win, text=self._('save'), bg='#00aa00', fg='white',
                  command=save_settings, font=('Segoe UI', 10, 'bold'),
                  padx=20, pady=5).pack(pady=20)
    
    def quit_app(self):
        if self.is_broadcasting:
            self.stop_broadcast()
        self.log_message(f"\n👋 {self._('shutdown')}")
        self.root.after(500, self.root.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    app = NOAAWeatherRadioApp(root)
    root.mainloop()
