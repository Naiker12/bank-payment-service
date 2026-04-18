param (
    [string]$ServiceDir = "d:\bank-payment-service",
    [string]$OutputDir = "d:\bank-payment-service\terraform\payment_service.zip"
)

Write-Host ">>> Construyendo paquete de despliegue para: $ServiceDir" -ForegroundColor Cyan

$TempDir = Join-Path $ServiceDir "deployment_package"
if (Test-Path $TempDir) { Remove-Item -Recurse -Force $TempDir }
New-Item -ItemType Directory -Path $TempDir

Write-Host "Instando dependencias compatibles con Linux..."
pip install -r "$ServiceDir\requirements.txt" `
    --target $TempDir `
    --platform manylinux2014_x86_64 `
    --only-binary=:all: `
    --implementation cp `
    --python-version 3.13 `
    --upgrade

Write-Host "Copiando cdigo fuente y archivos __init__.py..."
Copy-Item -Recurse "$ServiceDir\app" $TempDir
Copy-Item -Recurse "$ServiceDir\lambdas" $TempDir
Write-Host "Creando archivo ZIP..."
if (Test-Path $OutputDir) { Remove-Item -Force $OutputDir }
Compress-Archive -Path "$TempDir\*" -DestinationPath $OutputDir -Force

Write-Host ">>> Paquete creado exitosamente: $OutputDir" -ForegroundColor Green
