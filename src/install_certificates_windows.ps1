param (
    [string]$certUrl,
    [string]$certName
)

$cert_path = Join-Path $env:TEMP (Split-Path -Leaf $certUrl)
Invoke-WebRequest -Uri $certUrl -OutFile $cert_path -UseBasicParsing -ErrorAction Stop

$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
$cert.Import($cert_path)
$store = New-Object System.Security.Cryptography.X509Certificates.X509Store('CA', 'LocalMachine')
$store.Open('ReadOnly')

$existing = $store.Certificates.Find([System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint, $cert.Thumbprint, $false)
if ($existing.Count -eq 0) {
    $store.Close()
    $store.Open('ReadWrite')
    $store.Add($cert)
    $store.Close()
    Write-Output 'Installed'
} else {
    $store.Close()
    Write-Output 'Exists'
}
