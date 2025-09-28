import socket

try:
    ip = socket.gethostbyname("db.xlknciyujekwbhysmamn.supabase.co")
    print("IP encontrada:", ip)
except socket.gaierror as e:
    print("Error de DNS:", e)
