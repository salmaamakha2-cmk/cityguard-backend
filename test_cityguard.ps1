# CityGuard API Test Script
$BaseUrl = "https://v-production-fd5a.up.railway.app/api"
$Username = "AMAKHA524"
$Password = "salma123"

Write-Host "--- 1. Authentification ---" -ForegroundColor Cyan
$LoginBody = @{
    username = $Username
    password = $Password
} | ConvertTo-Json

try {
    $LoginRes = Invoke-RestMethod -Uri "$BaseUrl/users/login/" -Method Post -Body $LoginBody -ContentType "application/json"
    $Token = $LoginRes.access
    Write-Host "Succès ! Token récupéré." -ForegroundColor Green
} catch {
    Write-Host "Erreur d'authentification : $_" -ForegroundColor Red
    exit
}

Write-Host "`n--- 2. Envoi d'un signalement de test ---" -ForegroundColor Cyan
$ReportBody = @{
    title = "Test de synchronisation AI"
    description = "Ceci est un test envoyé via script pour vérifier que le Dashboard reçoit bien les données de Railway."
    category_type = "pothole"
    latitude = 30.4278
    longitude = -9.5981
} | ConvertTo-Json

try {
    $Headers = @{ Authorization = "Bearer $Token" }
    $ReportRes = Invoke-RestMethod -Uri "$BaseUrl/reports/" -Method Post -Headers $Headers -Body $ReportBody -ContentType "application/json"
    Write-Host "Signalement envoyé avec succès !" -ForegroundColor Green
    Write-Host "ID du rapport : $($ReportRes.id)"
} catch {
    Write-Host "Erreur lors de l'envoi : $_" -ForegroundColor Red
}

Write-Host "`n--- Vérifiez maintenant votre Dashboard Admin sur : http://localhost:5173 ---" -ForegroundColor Yellow
