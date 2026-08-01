param(
    [Parameter(Position = 0)]
    [string]$Target = ".",

    [ValidateSet("Consumer", "TemplateRepository")]
    [string]$Mode = "Consumer"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$targetPath = if ([IO.Path]::IsPathRooted($Target)) { $Target } else { Join-Path $repositoryRoot $Target }

if (-not (Test-Path -LiteralPath $targetPath)) {
    Write-Host "ERROR target does not exist: $Target"
    exit 2
}

$targetItem = Get-Item -LiteralPath $targetPath -Force
$excluded = '(^|[\\/])(?:\.git|\.venv|node_modules|__pycache__|\.pytest_cache|runtime|static_dist|dist|build|release-cache|docker-workspace|tmp|\.tmp|temp|test-results)(?:[\\/]|$)'
$supportedExtensions = @('.md', '.yml', '.yaml')
$files = if ($targetItem.PSIsContainer) {
    Get-ChildItem -LiteralPath $targetItem.FullName -Recurse -File -Force | Where-Object {
        ($supportedExtensions -contains $_.Extension -or $_.Name -eq 'CODEOWNERS') -and
        $_.FullName -notmatch $excluded
    }
} else {
    @($targetItem)
}

$balancedPattern = '\{\{([^{}\r\n]*)\}\}'
$validTokenPattern = '^[A-Z][A-Z0-9_]*$'
$tokenLikePattern = '^\s*[A-Za-z][A-Za-z0-9_-]*\s*$'
$githubExpressionPattern = '\$\{\{[^{}\r\n]*\}\}'
$found = 0

foreach ($file in $files) {
    $relative = [IO.Path]::GetRelativePath($repositoryRoot, $file.FullName).Replace('\', '/')
    $templateAllowed = $file.Name -match '(?:-template|ADR-000-template)\.md$' -or
        $relative -eq 'docs/governance/style-guide.md' -or
        $Mode -eq 'TemplateRepository'
    $lineNumber = 0
    foreach ($line in Get-Content -LiteralPath $file.FullName -Encoding UTF8) {
        $lineNumber++
        $scanLine = [regex]::Replace($line, $githubExpressionPattern, '')
        foreach ($match in [regex]::Matches($scanLine, $balancedPattern)) {
            $token = $match.Groups[1].Value
            if ((-not $templateAllowed -and $token -match $tokenLikePattern) -or
                ($templateAllowed -and $token -notmatch $validTokenPattern -and $token -ne 'xxx')) {
                Write-Host "  ${relative}:${lineNumber}: invalid placeholder $($match.Value)"
                $found++
            }
        }
        $withoutBalanced = [regex]::Replace($scanLine, $balancedPattern, '')
        if ($withoutBalanced -match '\{\{\s*[A-Za-z][A-Za-z0-9_-]*\s*$|(?<!\{)\{\s*[A-Za-z][A-Za-z0-9_-]*\s*\}\}') {
            Write-Host "  ${relative}:${lineNumber}: incomplete placeholder"
            $found++
        }
        if ($Mode -eq 'Consumer' -and $relative -eq '.github/CODEOWNERS' -and $line.Contains('@your-org/')) {
            Write-Host "  ${relative}:${lineNumber}: unresolved CODEOWNERS marker"
            $found++
        }
    }
}

if ($found -eq 0) {
    Write-Host "OK placeholder checks passed."
    exit 0
}

Write-Host "FAIL found $found placeholder issue(s)."
exit 1
