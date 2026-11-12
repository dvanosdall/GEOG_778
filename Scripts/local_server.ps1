# ==============================================================================
# OMAHA URBAN HEAT DECISION-SUPPORT TOOLKIT LOCAL DEVELOPMENT WEBSERVER
# LIGHTWEIGHT POWERSHELL-BASED WEBSERVER USING NATIVE .NET CLASSES
# ==============================================================================

# Define the root directory of the web files to be served
$rootDirectoryPath = "C:\Work\UrbanHeat\Frontend"

# Set the port number on which the local webserver will listen for incoming HTTP connections
$localWebServerPortNumber = 8000

# Create a native .NET HTTP listener instance
$netHttpListenerInstance = New-Object System.Net.HttpListener

# Add the listening URL prefix using our port number
$netHttpListenerInstance.Prefixes.Add("http://localhost:$localWebServerPortNumber/")

# Start the listener to begin accepting network requests
$netHttpListenerInstance.Start()

# Print confirmation status to the local console
Write-Host "[SUCCESS] Local development server is running on: http://localhost:$localWebServerPortNumber/"
Write-Host "[INFO] Serving files from: $rootDirectoryPath"
Write-Host "[INFO] Press Ctrl+C or stop the process to terminate the server."

# Keep running the listener loop until interrupted
try {
    while ($netHttpListenerInstance.IsListening) {
        # Block and wait for an incoming HTTP request
        $httpContextRecord = $netHttpListenerInstance.GetContext()
        $httpRequestData = $httpContextRecord.Request
        $httpResponseData = $httpContextRecord.Response

        # Print request URI to the console
        Write-Host "Received request for: $($httpRequestData.Url.PathAndQuery)"

        # Parse requested path and map to our index file
        $requestedFileName = $httpRequestData.Url.LocalPath
        if ($requestedFileName -eq "/" -or $requestedFileName -eq "") {
            $requestedFileName = "/index.html"
        }

        # Resolve full physical path on disk
        $targetPhysicalDiskPath = Join-Path $rootDirectoryPath $requestedFileName.Replace("/", "\")

        # Verify if the requested file physically exists on the disk
        if (Test-Path $targetPhysicalDiskPath -PathType Leaf) {
            # Read all file bytes to prepare for transport
            $fileContentBytes = [System.IO.File]::ReadAllBytes($targetPhysicalDiskPath)

            # Determine response content-type based on file extension
            if ($targetPhysicalDiskPath.EndsWith(".html")) {
                $httpResponseData.ContentType = "text/html"
            } elseif ($targetPhysicalDiskPath.EndsWith(".js")) {
                $httpResponseData.ContentType = "application/javascript"
            } elseif ($targetPhysicalDiskPath.EndsWith(".css")) {
                $httpResponseData.ContentType = "text/css"
            } elseif ($targetPhysicalDiskPath.EndsWith(".json")) {
                $httpResponseData.ContentType = "application/json"
            }

            # Set response status code to 200 OK
            $httpResponseData.StatusCode = 200
            $httpResponseData.ContentLength64 = $fileContentBytes.Length
            
            # Write the bytes to the response output stream
            $httpResponseData.OutputStream.Write($fileContentBytes, 0, $fileContentBytes.Length)
        } else {
            # Return 404 Not Found error status
            $errorResponseBytes = [System.Text.Encoding]::UTF8.GetBytes("404 - File Not Found")
            $httpResponseData.StatusCode = 404
            $httpResponseData.ContentType = "text/plain"
            $httpResponseData.ContentLength64 = $errorResponseBytes.Length
            $httpResponseData.OutputStream.Write($errorResponseBytes, 0, $errorResponseBytes.Length)
        }

        # Close and flush response streams to complete request transaction
        $httpResponseData.Close()
    }
} catch {
    # Print error details to the console
    Write-Host "[INFO] Server loop interrupted or stopped: $_"
} finally {
    # Ensure listener resources are cleanly released
    $netHttpListenerInstance.Stop()
    $netHttpListenerInstance.Close()
    Write-Host "[INFO] Local development server stopped."
}
