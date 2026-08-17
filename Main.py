import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog
import threading
import os
import time
import random
from datetime import datetime
from noaa_radio import NOAAWeatherRadio
from noaa_stations import NOAA_STATIONS

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
        
        self.create_ui()
        self.load_station("Gunnison")
    
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
            text=" STAND-BY | GUNNISON COUNTY, CO | ZONE: COZ012",
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
            btn_frame, text="▶ START BROADCAST", bg='#00aa00', fg='white',
            command=self.start_broadcast, **btn_style
        )
        self.btn_start.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.btn_stop = tk.Button(
            btn_frame, text="⏹ STOP", bg='#cc0000', fg='white',
            command=self.stop_broadcast, **btn_style
        )
        self.btn_stop.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_stop.config(state=tk.DISABLED)
        
        tk.Button(
            btn_frame, text="📡 FETCH DATA", bg='#0055aa', fg='white',
            command=self.fetch_data, **btn_style
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            btn_frame, text="🌍 SELECT STATION", bg='#00aaff', fg='white',
            command=self.open_station_selector, **btn_style
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            btn_frame, text="⚙ SETTINGS", bg='#555555', fg='white',
            command=self.open_settings, **btn_style
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            btn_frame, text="💾 SAVE", bg='#aa8800', fg='white',
            command=self.save_broadcast, **btn_style
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            btn_frame, text="❌ EXIT", bg='#444444', fg='white',
            command=self.quit_app, **btn_style
        ).pack(side=tk.RIGHT, padx=5, pady=5)
    
    def update_clock(self):
        now = datetime.now().strftime('%H:%M:%S MST')
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)
    
    def log_message(self, text):
        self.display.insert(tk.END, text + "\n")
        self.display.see(tk.END)
        self.root.update_idletasks()
    
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
            text=f" STAND-BY | {station_data['city']}, {station_data['state']} | {station_data['callsign']} | {station_data['frequency']} MHz"
        )
        
        self.log_message("=" * 70)
        self.log_message(f"  📻 {station_data['callsign']} - {station_data['city']}, {station_data['state']}")
        self.log_message(f"  📡 Frequency: {station_data['frequency']} MHz")
        self.log_message(f"  📍 {station_data['description']}")
        self.log_message("=" * 70)
    
    def open_station_selector(self):
        selector = tk.Toplevel(self.root)
        selector.title("Select Station - " + str(len(NOAA_STATIONS)) + " Stations")
        selector.geometry("550x500")
        selector.configure(bg='#1a1a1a')
        selector.transient(self.root)
        selector.grab_set()
        
        tk.Label(selector, text="🌍 NOAA WEATHER RADIO STATIONS (" + str(len(NOAA_STATIONS)) + ")", 
                 bg='#1a1a1a', fg='#00ff00',
                 font=('Courier New', 14, 'bold')).pack(pady=10)
        
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
            yscrollcommand=scrollbar.set
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
        
        update_list()
        
        station_names = list(NOAA_STATIONS.keys())
        
        def select_station():
            selection = station_list.curselection()
            if selection:
                idx = selection[0]
                selected_text = station_list.get(idx)
                for name, data in NOAA_STATIONS.items():
                    display = f"{data['callsign']} - {data['city']}, {data['state']} ({data['frequency']} MHz)"
                    if display == selected_text:
                        selector.destroy()
                        self.load_station(name)
                        self.log_message(f"\n✅ Switched to {NOAA_STATIONS[name]['callsign']}!")
                        return
        
        btn_frame = tk.Frame(selector, bg='#1a1a1a')
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame, text="SELECT", bg='#00aa00', fg='white',
            command=select_station, font=('Segoe UI', 10, 'bold'),
            padx=20, pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, text="REFRESH", bg='#555555', fg='white',
            command=update_list, font=('Segoe UI', 10, 'bold'),
            padx=20, pady=5
        ).pack(side=tk.LEFT, padx=5)
    
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
        self.status_label.config(text=" BROADCASTING ACTIVE")
        self.log_message("\n" + "=" * 70)
        self.log_message(f"  ▶ BROADCAST STARTED | {datetime.now().strftime('%H:%M:%S')}")
        self.log_message(f"  📻 {self.radio.callsign} - {self.radio.city}")
        self.log_message("=" * 70)
        
        self.broadcast_thread = threading.Thread(target=self.broadcast_loop)
        self.broadcast_thread.daemon = True
        self.broadcast_thread.start()
    
    def broadcast_loop(self):
        first_run = True
        
        while self.is_broadcasting:
            try:
                self.log_message("📡 Fetching NOAA data...")
                data = self.radio.get_weather_data()
                
                if data:
                    # =========================================================
                    # 1. HARRY - OPENING
                    # =========================================================
                    if first_run:
                        opening = self.radio.get_opening_message()
                        self.log_message("🎙️ HARRY (Opening) speaking...")
                        self.log_message("-" * 40)
                        self.log_message(opening)
                        self.log_message("-" * 40)
                        self.radio.speak_with_voice(opening, "harry", 1)
                        if not self.wait(3): break
                        first_run = False
                    
                    # =========================================================
                    # 2. PAUL - TIME ANNOUNCEMENT
                    # =========================================================
                    time_msg = self.radio.time_announcement()
                    self.log_message("🕐 PAUL (Time) speaking...")
                    self.log_message("-" * 40)
                    self.log_message(time_msg)
                    self.log_message("-" * 40)
                    self.radio.speak_with_voice(time_msg, "paul", 0)
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 3. TOM - HOURLY ROUNDUP
                    # =========================================================
                    hourly_msg = self.radio.get_hourly_roundup(data)
                    self.log_message("📊 TOM (Hourly Roundup) speaking...")
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
                        current_alert_ids.append(f"{event}_{area}")
                    
                    previous_alert_ids = []
                    for alert in self.previous_alerts:
                        event = alert.get('event', '')
                        area = alert.get('areaDesc', '')
                        previous_alert_ids.append(f"{event}_{area}")
                    
                    if active_alerts and (current_alert_ids != previous_alert_ids or first_run):
                        self.log_message("🚨 TOM - ACTIVE ALERTS speaking...")
                        self.log_message("-" * 40)
                        
                        for alert in active_alerts[:5]:
                            event = alert.get('event', 'Alert')
                            area = alert.get('areaDesc', 'this area')
                            description = alert.get('description', '')
                            instruction = alert.get('instruction', '')
                            
                            alert_msg = f"{event} for {area}. "
                            if description:
                                alert_msg += description + ". "
                            if instruction:
                                alert_msg += instruction
                            
                            self.log_message(f"📢 {event} - {area}")
                            self.radio.speak_with_voice(alert_msg, "tom", 0)
                            if not self.wait(3): break
                        
                        self.log_message("-" * 40)
                        self.log_message("✅ Active alerts complete.\n")
                        self.previous_alerts = active_alerts
                    else:
                        self.log_message("ℹ️ No new alerts.\n")
                    
                    # =========================================================
                    # 5. TOM - NOWCAST
                    # =========================================================
                    nowcast_msg = self.radio.get_nowcast(data)
                    self.log_message("🌤️ TOM (Nowcast) speaking...")
                    self.log_message("-" * 40)
                    self.log_message(nowcast_msg)
                    self.log_message("-" * 40)
                    self.radio.speak_with_voice(nowcast_msg, "tom", 0)
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 6. TOM - ZONE FORECAST
                    # =========================================================
                    self.log_message("📅 TOM - Zone Forecast speaking...")
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
                    self.log_message("✅ Zone Forecast complete.\n")
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 7. TOM - HAZARDOUS WEATHER OUTLOOK
                    # =========================================================
                    hazardous_msg = self.radio.get_hazardous_outlook(data)
                    self.log_message("⚠️ TOM (Hazardous Outlook) speaking...")
                    self.log_message("-" * 40)
                    self.log_message(hazardous_msg)
                    self.log_message("-" * 40)
                    self.radio.speak_with_voice(hazardous_msg, "tom", 0)
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 8. DONNA - MARINE FORECAST
                    # =========================================================
                    self.log_message("🌊 DONNA - Marine Forecast speaking...")
                    self.log_message("-" * 40)
                    
                    marine_data = self.radio.get_coastal_marine_forecast()
                    self.log_message(marine_data)
                    self.radio.speak_with_voice(marine_data, "donna", 1)
                    
                    self.log_message("-" * 40)
                    self.log_message("✅ Marine Forecast complete.\n")
                    if not self.wait(2): break
                    
                    # =========================================================
                    # 9. TOM - CLIMATE SUMMARY (YENİ! Tom okuyor)
                    # =========================================================
                    climate_msg = self.radio.get_climate_summary(data)
                    self.log_message("🌡️ TOM (Climate Summary) speaking...")
                    self.log_message("-" * 40)
                    self.log_message(climate_msg)
                    self.log_message("-" * 40)
                    self.radio.speak_with_voice(climate_msg, "tom", 0)
                    if not self.wait(2): break
                    
                    self.log_message(f"✅ Broadcast complete | {datetime.now().strftime('%H:%M:%S')}")
                    
                    self.log_message("🔇 5 seconds silence...")
                    self.log_message("=" * 70 + "\n")
                    if not self.wait(5): break
                    
                else:
                    self.log_message("❌ No data received, retrying in 10 seconds...")
                    if not self.wait(10): break
                    
            except Exception as e:
                self.log_message(f"❌ Error: {e}")
                import traceback
                self.log_message(traceback.format_exc())
                if not self.wait(10): break
    
    def stop_broadcast(self):
        self.is_broadcasting = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.status_label.config(text=" STAND-BY")
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
                self.log_message(f"💾 Saved: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")
    
    def open_settings(self):
        if not self.radio:
            return
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("400x350")
        settings_win.configure(bg='#1a1a1a')
        settings_win.resizable(False, False)
        settings_win.transient(self.root)
        settings_win.grab_set()
        
        tk.Label(settings_win, text="⚙ SETTINGS", bg='#1a1a1a', fg='#00ff00',
                 font=('Courier New', 14, 'bold')).pack(pady=10)
        
        tk.Label(settings_win, text="Latitude:", bg='#1a1a1a', fg='#00ff00',
                 font=('Courier New', 10)).pack(pady=(10,0))
        lat_entry = tk.Entry(settings_win, font=('Courier New', 10))
        lat_entry.insert(0, str(self.radio.lat))
        lat_entry.pack()
        
        tk.Label(settings_win, text="Longitude:", bg='#1a1a1a', fg='#00ff00',
                 font=('Courier New', 10)).pack(pady=(10,0))
        lon_entry = tk.Entry(settings_win, font=('Courier New', 10))
        lon_entry.insert(0, str(self.radio.lon))
        lon_entry.pack()
        
        def save_settings():
            try:
                self.radio.lat = float(lat_entry.get())
                self.radio.lon = float(lon_entry.get())
                self.radio.city = f"Location {self.radio.lat}, {self.radio.lon}"
                self.status_label.config(text=f" STAND-BY | {self.radio.city[:20]}")
                self.log_message(f"✅ Settings updated: {self.radio.lat}, {self.radio.lon}")
                settings_win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers.")
        
        tk.Button(settings_win, text="SAVE", bg='#00aa00', fg='white',
                  command=save_settings, font=('Segoe UI', 10, 'bold'),
                  padx=20, pady=5).pack(pady=20)
    
    def quit_app(self):
        if self.is_broadcasting:
            self.stop_broadcast()
        self.log_message("\n👋 System shutting down...")
        self.root.after(500, self.root.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    app = NOAAWeatherRadioApp(root)
    root.mainloop()