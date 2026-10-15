# iniciar.ps1
# Arranca FastBite v2: los 3 microservicios HTTP y el servicio de notificaciones
# (que escucha eventos en RabbitMQ), cada uno en su propia ventana.
# Uso: desde la carpeta fastbite-v2 ejecuta   .\iniciar.ps1

$raiz = $PSScriptRoot

# RabbitMQ debe estar corriendo antes (puerto 5672)
$rabbit = Test-NetConnection -ComputerName localhost -Port 5672 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $rabbit) {
    Write-Host "AVISO: RabbitMQ no responde en localhost:5672." -ForegroundColor Yellow
    Write-Host "       Levantalo con:  docker start rabbitmq" -ForegroundColor Yellow
    Write-Host "       (la primera vez: docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management)" -ForegroundColor Yellow
}

$servicios = @(
    @{ nombre = "users-service";  titulo = "users-service :8001";  comando = "uvicorn main:app --reload --port 8001" },
    @{ nombre = "menu-service";   titulo = "menu-service :8002";   comando = "uvicorn main:app --reload --port 8002" },
    @{ nombre = "orders-service"; titulo = "orders-service :8003"; comando = "uvicorn main:app --reload --port 8003" },
    @{ nombre = "notifications-service"; titulo = "notifications-service (RabbitMQ)"; comando = "python main.py" },
    @{ nombre = "gateway-service"; titulo = "gateway-service :8000"; comando = "uvicorn main:app --reload --port 8000" }
)

foreach ($s in $servicios) {
    $comando = "`$host.UI.RawUI.WindowTitle = '$($s.titulo)'; " +
               "Set-Location '$raiz'; " +
               ".\venv\Scripts\Activate.ps1; " +
               "Set-Location '$($s.nombre)'; " +
               $s.comando
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $comando
    Start-Sleep -Seconds 1
}

Write-Host "Servicios iniciados:"
Write-Host "  API Gateway (entrada)  http://localhost:8000/docs"
Write-Host "  users-service          http://localhost:8001/docs"
Write-Host "  menu-service           http://localhost:8002/docs"
Write-Host "  orders-service         http://localhost:8003/docs"
Write-Host "  notifications-service  (sin HTTP, escucha eventos de RabbitMQ)"
Write-Host "  panel de RabbitMQ      http://localhost:15672  (guest / guest)"
