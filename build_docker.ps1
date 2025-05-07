Write-Output "Building Docker image 'tf-code-reviewer'..."
docker build -t tf-code-reviewer .
if ($LASTEXITCODE -eq 0) {
    Write-Output "Docker image built successfully as 'tf-code-reviewer'."
} else {
    Write-Error "Failed to build Docker image."
}