# Local data builder (Windows, no Python required).
# Fetches all 15 feeds/homepages and writes data/headlines.json.
# The canonical updater remains .github/workflows (Python). This script is a fallback
# for machines without Python - it mirrors fetch_headlines.py logic.
# Source list lives in scripts/sources.json (UTF-8), so this file stays ASCII-only.

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root = Split-Path -Parent $PSScriptRoot
$ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

$sources = Get-Content -Raw -Encoding UTF8 (Join-Path $PSScriptRoot 'sources.json') | ConvertFrom-Json

function Fetch-Text([string]$url) {
    $tmp = [IO.Path]::GetTempFileName()
    try {
        & curl.exe -sS -f -L --retry 2 --retry-delay 2 --max-time 40 -A $ua `
            -H "Accept: text/html,application/xhtml+xml,application/xml,application/rss+xml,*/*;q=0.8" `
            -H "Accept-Language: bn,en;q=0.8" `
            -o $tmp $url 2>$null
        if ($LASTEXITCODE -ne 0) { throw ("curl exit " + $LASTEXITCODE) }
        return [IO.File]::ReadAllText($tmp, [Text.Encoding]::UTF8)
    } finally {
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
}

function Clean-Text([string]$s) {
    if (-not $s) { return '' }
    $t = $s -replace '<[^>]+>', ' '
    $t = [System.Net.WebUtility]::HtmlDecode($t)
    return ($t -replace '\s+', ' ').Trim()
}

function Test-ArticleUrl([string]$url, [string]$pattern) {
    if (-not $url) { return $false }
    if ($url -match '/(tag|tags|topic|category|author|writer|video|videos|photo|photos|gallery|epaper|archive|login|register|subscribe|contact|about|privacy|terms|jobs|advertisement|rss|feed)(/|$)') { return $false }
    if ($url -match '#') { return $false }
    if ($pattern -and ($url -notmatch $pattern)) { return $false }
    return $true
}

function Resolve-BingRedirect([string]$url) {
    $url = [System.Net.WebUtility]::HtmlDecode($url)
    if ($url -notmatch 'bing\.com') { return $url }
    $m = [regex]::Match($url, '[?&]url=([^&]+)')
    if ($m.Success) {
        try {
            return [System.Uri]::UnescapeDataString($m.Groups[1].Value)
        } catch { return $url }
    }
    return $url
}

function Get-FeedItems([string]$feedUrl, [string]$site, [string]$pattern) {
    $items = @()
    try {
        $xml = Fetch-Text $feedUrl
        $xml = $xml.Replace('<![CDATA[', '').Replace(']]>', '')
        $blocks = [regex]::Matches($xml, '<item[^>]*>(.*?)</item>', 'Singleline')
        foreach ($b in $blocks) {
            $block = $b.Groups[1].Value
            $t = [regex]::Match($block, '<title>(.*?)</title>', 'Singleline').Groups[1].Value
            $l = [regex]::Match($block, '<link>([^<]+)</link>', 'Singleline').Groups[1].Value
            $d = [regex]::Match($block, '<pubDate>(.*?)</pubDate>', 'Singleline').Groups[1].Value
            if (-not $t -or -not $l) { continue }
            $t = Clean-Text $t
            $l = [System.Net.WebUtility]::HtmlDecode($l.Trim())
            $l = Resolve-BingRedirect $l
            if ($l -notmatch '^https?://') {
                try { $l = (New-Object Uri((New-Object Uri $site), $l)).ToString() } catch { continue }
            }
            if (-not (Test-ArticleUrl $l $pattern)) { continue }
            $items += [pscustomobject]@{ title = $t; url = $l; time = (Clean-Text $d) }
        }
    } catch {
        Write-Host ("  feed fail: {0}" -f $_.Exception.Message)
    }
    $seen = @{}; $out = @()
    foreach ($i in $items) {
        if ($null -ne $i -and $i.url -and -not $seen.ContainsKey($i.url)) { $seen[$i.url] = $true; $out += $i }
    }
    return $out
}

function Get-PageItems([string]$pageUrl, [string]$site, [string]$pattern) {
    $items = @()
    try {
        $html = Fetch-Text $pageUrl
        $anchors = [regex]::Matches($html, '<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', 'Singleline')
        foreach ($a in $anchors) {
            $href = $a.Groups[1].Value
            $text = Clean-Text $a.Groups[2].Value
            if ($text.Length -lt 15 -or $text.Length -gt 220) { continue }
            if ($href -notmatch '^https?://') {
                try { $href = (New-Object Uri((New-Object Uri $site), $href)).ToString() } catch { continue }
            }
            if ($href -notmatch '^https?://') { continue }
            if (-not (Test-ArticleUrl $href $pattern)) { continue }
            $items += [pscustomobject]@{ title = $text; url = $href; time = '' }
        }
    } catch {
        Write-Host ("  page fail {0}: {1}" -f $pageUrl, $_.Exception.Message)
    }
    $seen = @{}; $uniq = @()
    foreach ($i in $items) {
        if ($null -ne $i -and $i.url -and -not $seen.ContainsKey($i.url)) { $seen[$i.url] = $true; $uniq += $i }
    }
    return $uniq
}

function Merge-Items([object[]]$base, [object[]]$extra) {
    $seen = @{}; $out = @()
    foreach ($i in @($base)) {
        if ($null -ne $i -and $i.url -and -not $seen.ContainsKey($i.url)) { $seen[$i.url] = $true; $out += $i }
    }
    foreach ($p in @($extra)) {
        if ($null -ne $p -and $p.url -and -not $seen.ContainsKey($p.url)) { $seen[$p.url] = $true; $out += $p }
    }
    return $out
}

$results = @()
$failed = @()
$total = 0

foreach ($s in $sources) {
    Write-Host ("{0} ..." -f $s.name)
    Start-Sleep -Milliseconds 800
    $pattern = [string]$s.pattern
    $items = @()

    foreach ($f in @($s.feeds)) {
        if (-not $f) { continue }
        $newItems = @(Get-FeedItems $f $s.site $pattern | Where-Object { $null -ne $_ })
        $items = @(Merge-Items $items $newItems | Where-Object { $null -ne $_ })
        if ($items.Count -ge 10) { break }
    }

    if ($items.Count -lt 10) {
        $pages = @($s.pages)
        if ($pages.Count -eq 0) { $pages = @($s.site) }
        $pageItems = @()
        foreach ($p in $pages) {
            if (-not $p) { continue }
            $p = $p.Replace('TODAY', (Get-Date).ToString('yyyy-MM-dd'))
            $pageItems = @(Merge-Items $pageItems @(Get-PageItems $p $s.site $pattern) | Where-Object { $null -ne $_ })
        }
        $items = @(Merge-Items $items $pageItems | Where-Object { $null -ne $_ })
    }

    $items = @($items | Where-Object { $null -ne $_ } | Select-Object -First 10)
    $status = 'ok'
    if ($items.Count -lt 10) { $status = 'warning'; $failed += $s.name }
    $total += $items.Count

    $results += [ordered]@{
        source     = $s.name
        url        = $s.site
        count      = $items.Count
        headlines  = $items
        status     = $status
    }
    Write-Host ("  -> {0} headlines" -f $items.Count)
}

$payload = [ordered]@{
    updated_at                   = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss+00:00')
    refresh_minutes              = 10
    minimum_headlines_per_source = 10
    sources                      = $results
    summary                      = [ordered]@{
        sources              = $results.Count
        sources_with_10_plus = @($results | Where-Object { $_.count -ge 10 }).Count
        total_headlines      = $total
        warnings             = @($failed)
    }
}

$json = ConvertTo-Json -InputObject $payload -Depth 6
$outPath = Join-Path $root 'data\headlines.json'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outPath) | Out-Null
[IO.File]::WriteAllText($outPath, $json, (New-Object Text.UTF8Encoding($false)))
Write-Host ("Wrote {0}" -f $outPath)
Write-Host ("Summary: " + ($payload.summary | ConvertTo-Json -Compress))
