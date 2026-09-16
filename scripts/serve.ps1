# Minimal static file server for local preview (no Python/Node required).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts\serve.ps1 [-Port 8734]

param(
    [int]$Port = 8734
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()
Write-Host ("Serving {0} at http://localhost:{1}/  (PID {2})" -f $root, $Port, $PID)

$mimes = @{
    '.html' = 'text/html; charset=utf-8'
    '.htm'  = 'text/html; charset=utf-8'
    '.css'  = 'text/css; charset=utf-8'
    '.js'   = 'application/javascript; charset=utf-8'
    '.json' = 'application/json; charset=utf-8'
    '.png'  = 'image/png'
    '.jpg'  = 'image/jpeg'
    '.jpeg' = 'image/jpeg'
    '.gif'  = 'image/gif'
    '.svg'  = 'image/svg+xml'
    '.ico'  = 'image/x-icon'
    '.txt'  = 'text/plain; charset=utf-8'
    '.md'   = 'text/plain; charset=utf-8'
    '.xml'  = 'application/xml; charset=utf-8'
    '.webp' = 'image/webp'
    '.woff' = 'font/woff'
    '.woff2'= 'font/woff2'
}

while ($listener.IsListening) {
    $context = $listener.GetContext()
    try {
        $path = $context.Request.Url.AbsolutePath
        if ($path -eq '/') { $path = '/index.html' }
        $rel = [Uri]::UnescapeDataString($path).TrimStart('/')
        $full = Join-Path $root ($rel -replace '/', '\')

        # path traversal guard
        if (-not (([IO.Path]::GetFullPath($full)).StartsWith($root, [StringComparison]::OrdinalIgnoreCase))) {
            $context.Response.StatusCode = 403
            $context.Response.Close()
            continue
        }

        if (Test-Path $full -PathType Leaf) {
            $ext = [IO.Path]::GetExtension($full).ToLower()
            $mime = if ($mimes.ContainsKey($ext)) { $mimes[$ext] } else { 'application/octet-stream' }
            $bytes = [IO.File]::ReadAllBytes($full)
            $context.Response.ContentType = $mime
            $context.Response.ContentLength64 = $bytes.Length
            $context.Response.StatusCode = 200
            $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
        } else {
            $context.Response.StatusCode = 404
            $msg = [Text.Encoding]::UTF8.GetBytes('404 not found')
            $context.Response.OutputStream.Write($msg, 0, $msg.Length)
        }
    } catch {
        try { $context.Response.StatusCode = 500 } catch {}
    } finally {
        try { $context.Response.Close() } catch {}
    }
}
