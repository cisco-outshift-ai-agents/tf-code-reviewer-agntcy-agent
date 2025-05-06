param(
    [string]$ImageName = "tfcodeanalyzer"
)

# Specify path to your .env file
$envFilePath = ".\.env"

# Verify that the .env file exists
if (!(Test-Path $envFilePath)) {
    Write-Error ".env file not found at $envFilePath"
    exit 1
}

Write-Output "Starting Docker container with image '$ImageName' using .env file '$envFilePath'..."

# Run the container in detached mode with port 8123 mapped
docker run --rm -d --env-file $envFilePath -p 8123:8123 $ImageName