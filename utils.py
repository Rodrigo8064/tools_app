import time
import threading
from plyer import notification

def lembrete_agua():
    """Exibe notificação para tomar água"""
    try:
        notification.notify(
            title='Hora de tomar água! 💧',
            message='Saia da frente do PC e hidrate-se!',
            timeout=10,
            app_icon='favicon.ico'  # Opcional: usar seu ícone
        )
    except Exception as e:
        print(f"Erro na notificação: {e}")

def iniciar_lembretes_agua(intervalo_minutos=60):
    """Inicia os lembretes periódicos de água"""
    def loop_lembretes():
        while True:
            lembrete_agua()
            time.sleep(intervalo_minutos * 60)  # Converte para segundos
    
    # Iniciar em uma thread separada para não travar o app
    thread = threading.Thread(target=loop_lembretes, daemon=True)
    thread.start()
    return thread
