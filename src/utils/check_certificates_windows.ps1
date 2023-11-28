param (
    [string]$certUrl
)

$cert_path = Join-Path $env:TEMP (Split-Path -Leaf $certUrl)
Invoke-WebRequest -Uri $certUrl -OutFile $cert_path -UseBasicParsing -ErrorAction Stop

$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
$cert.Import($cert_path)

function Check-CertificateInstalled {
    param (
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$certificate,
        [string]$storeName,
        [string]$storeLocation
    )

    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store($storeName, $storeLocation)
    $store.Open('ReadOnly')

    $existing = $store.Certificates.Find([System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint, $certificate.Thumbprint, $false)
    $store.Close()

    return $existing.Count -gt 0
}

$currentUserExists = Check-CertificateInstalled -certificate $cert -storeName "CA" -storeLocation "CurrentUser"
$localMachineExists = Check-CertificateInstalled -certificate $cert -storeName "CA" -storeLocation "LocalMachine"

if ($currentUserExists -and $localMachineExists) {
    Write-Output "Exists"
}
else {
    Write-Output "NotInstalled"
}
