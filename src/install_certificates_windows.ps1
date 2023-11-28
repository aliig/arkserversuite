param (
    [string]$certUrl,
    [string]$certName
)

$cert_path = Join-Path $env:TEMP (Split-Path -Leaf $certUrl)
Invoke-WebRequest -Uri $certUrl -OutFile $cert_path -UseBasicParsing -ErrorAction Stop

$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
$cert.Import($cert_path)

# Function to add certificate to a specified store
function Add-CertificateToStore {
    param (
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$certificate,
        [string]$storeName,
        [string]$storeLocation
    )

    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store($storeName, $storeLocation)
    $store.Open('ReadWrite')

    $existing = $store.Certificates.Find([System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint, $certificate.Thumbprint, $false)
    if ($existing.Count -eq 0) {
        $store.Add($certificate)
        Write-Output "Installed in $storeLocation"
    }
    else {
        Write-Output "Exists in $storeLocation"
    }

    $store.Close()
}

# Add certificate to CurrentUser store
Add-CertificateToStore -certificate $cert -storeName "CA" -storeLocation "CurrentUser"

# Add certificate to LocalMachine store
Add-CertificateToStore -certificate $cert -storeName "CA" -storeLocation "LocalMachine"
