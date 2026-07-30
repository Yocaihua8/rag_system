# check-placeholders.ps1
#
# 检查模板占位符：
#   - Consumer：拒绝非模板文件中的任何 {{...}} 残留、残缺双花括号，
#     以及 .github/CODEOWNERS 中未替换的 @your-org/。若存在
#     .docs-template/state.tsv，仅精确豁免其中 placeholder_policy=preserve-template
#     的安全 destination；无 state 时使用内置窄 allowlist。
#   - TemplateRepository：允许模板源文件保留占位符，但校验 token 必须使用
#     SCREAMING_SNAKE_CASE；examples 等非模板内容仍不得残留占位符。
#
# 用法：
#   pwsh scripts/check-placeholders.ps1
#   pwsh scripts/check-placeholders.ps1 docs/features
#   pwsh scripts/check-placeholders.ps1 -Mode TemplateRepository
#
# 退出码：0 = 通过；1 = 发现残留或非法 token；2 = 参数或目标路径错误

param(
    [Parameter(Position = 0)]
    [string]$Target = ".",

    [string]$Mode = "Consumer",

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArguments = @()
)

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if ($RemainingArguments.Count -gt 0) {
    Write-Host "ERROR only one target may be provided."
    exit 2
}
if ($Mode -notin @("Consumer", "TemplateRepository")) {
    Write-Host "ERROR unknown mode: $Mode. Use Consumer or TemplateRepository."
    exit 2
}

$consumerTemplatePatterns = @(
    '-template\.md$',
    'ADR-000-template\.md$',
    '^docs[/\\]style-guide\.md$'
)

$templateRepositoryPatterns = @(
    '^AGENTS\.md$',
    '^CHANGELOG\.md$',
    '^CONTRIBUTING\.md$',
    '^README\.md$',
    '^SECURITY\.md$',
    '^TEMPLATE_REPOSITORY_MAINTENANCE\.md$',
    '^template-mapping\.md$',
    '^docs[/\\].*\.md$',
    '^scaffold[/\\].*\.tsv$',
    '^scaffold[/\\]templates[/\\].*$',
    '^\.github[/\\]pull_request_template\.md$',
    '^\.github[/\\]ISSUE_TEMPLATE[/\\].*\.ya?ml$',
    '^\.github[/\\]CODEOWNERS$'
)

# style-guide 需要展示一个明确禁止的反例；只豁免这一处，不放宽通用语法。
$syntaxExampleAllowlist = @{
    'docs/style-guide.md' = @('xxx')
}

function Test-MatchesAnyPattern {
    param(
        [string]$Value,
        [string[]]$Patterns
    )

    foreach ($pattern in $Patterns) {
        if ($Value -match $pattern) { return $true }
    }
    return $false
}

function Test-IsSyntaxExample {
    param(
        [string]$RelativePath,
        [string]$Token
    )

    if (-not $syntaxExampleAllowlist.ContainsKey($RelativePath)) { return $false }
    return $syntaxExampleAllowlist[$RelativePath] -contains $Token
}

function Get-DisplayPath {
    param([System.IO.FileInfo]$File)

    $repoPrefix = $repoRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if ($File.FullName.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $File.FullName.Substring($repoPrefix.Length) -replace '\\', '/'
    }
    return $File.FullName -replace '\\', '/'
}

function Stop-InvalidState {
    param([string]$Message)
    Write-Host "ERROR invalid .docs-template/state.tsv: $Message"
    exit 2
}

function Test-SafeStateDestination {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    if ($Value.Contains('\')) { return $false }
    if ($Value.StartsWith('/') -or $Value.EndsWith('/')) { return $false }
    if ($Value.Contains('//') -or $Value.Contains(':')) { return $false }
    if ([System.IO.Path]::IsPathRooted($Value)) { return $false }
    foreach ($segment in $Value.Split([char]'/')) {
        if ($segment -eq '' -or $segment -eq '.' -or $segment -eq '..') { return $false }
    }
    return $true
}

function Test-ValidStatePacks {
    param([string]$Value)

    if ($Value -cnotmatch '^[a-z0-9]+(?:-[a-z0-9]+)*(?:;[a-z0-9]+(?:-[a-z0-9]+)*)*$') {
        return $false
    }

    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($pack in $Value.Split([char]';')) {
        if (-not $seen.Add($pack)) { return $false }
    }
    return $true
}

function Test-IsAuthorizedPreserveDestination {
    param([string]$Value)

    # Keep this policy portable: reusable *-template.md files may live in any
    # safe project directory, while non-suffixed template targets are exact.
    if ($Value -cmatch '(^|/)[^/]+-template\.md$') { return $true }

    $exactDestinations = @('docs/style-guide.md')
    return $exactDestinations -ccontains $Value
}

function Get-ConsumerStateAllowlist {
    $statePath = Join-Path $repoRoot '.docs-template\state.tsv'
    if (-not (Test-Path -LiteralPath $statePath)) { return $null }

    $stateItem = Get-Item -LiteralPath $statePath -Force
    if ($stateItem.PSIsContainer) { Stop-InvalidState 'state.tsv is not a regular file.' }

    $lines = @(Get-Content -LiteralPath $stateItem.FullName -Encoding UTF8)
    $expectedHeader = "schema_version`ttemplate_version`tdestination`tsource`tpacks`tplaceholder_policy`tsha256"
    if ($lines.Count -eq 0 -or $lines[0] -cne $expectedHeader) {
        Stop-InvalidState 'unexpected header.'
    }

    $destinations = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $allowlist = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    $stateTemplateVersion = $null
    for ($index = 1; $index -lt $lines.Count; $index++) {
        $lineNumber = $index + 1
        if ($lines[$index].Length -eq 0) { Stop-InvalidState "blank row at line $lineNumber." }

        $columns = $lines[$index].Split(@([char]"`t"), [System.StringSplitOptions]::None)
        if ($columns.Count -ne 7) { Stop-InvalidState "expected 7 columns at line $lineNumber." }

        $schemaVersion = $columns[0]
        $templateVersion = $columns[1]
        $destination = $columns[2]
        $source = $columns[3]
        $packs = $columns[4]
        $placeholderPolicy = $columns[5]
        $sha256 = $columns[6]
        if ($schemaVersion -cne '1') { Stop-InvalidState "unsupported schema_version at line $lineNumber." }
        if ($templateVersion -cnotmatch '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$') {
            Stop-InvalidState "invalid template_version '$templateVersion' at line $lineNumber."
        }
        if ($null -eq $stateTemplateVersion) {
            $stateTemplateVersion = $templateVersion
        } elseif ($templateVersion -cne $stateTemplateVersion) {
            Stop-InvalidState "inconsistent template_version '$templateVersion' at line $lineNumber."
        }
        if (-not (Test-SafeStateDestination $destination)) {
            Stop-InvalidState "unsafe destination '$destination' at line $lineNumber."
        }
        if (-not (Test-SafeStateDestination $source)) {
            Stop-InvalidState "unsafe source '$source' at line $lineNumber."
        }
        if (
            $destination.Equals('.docs-template/state.tsv', [System.StringComparison]::OrdinalIgnoreCase) -or
            $source.Equals('.docs-template/state.tsv', [System.StringComparison]::OrdinalIgnoreCase)
        ) {
            Stop-InvalidState "state.tsv cannot reference itself at line $lineNumber."
        }
        if (-not $destinations.Add($destination)) {
            Stop-InvalidState "duplicate destination '$destination' at line $lineNumber."
        }
        if (-not (Test-ValidStatePacks $packs)) {
            Stop-InvalidState "invalid packs '$packs' at line $lineNumber."
        }
        if ($placeholderPolicy -cnotin @('replace', 'preserve-template', 'none')) {
            Stop-InvalidState "unknown placeholder_policy '$placeholderPolicy' at line $lineNumber."
        }
        if ($sha256 -cnotmatch '^[0-9a-f]{64}$') {
            Stop-InvalidState "invalid sha256 at line $lineNumber."
        }
        if ($placeholderPolicy -ceq 'preserve-template') {
            if (-not (Test-IsAuthorizedPreserveDestination $destination)) {
                Stop-InvalidState "unauthorized preserve-template destination '$destination' at line $lineNumber."
            }

            $preservedPath = Join-Path $repoRoot ($destination -replace '/', [System.IO.Path]::DirectorySeparatorChar)
            if (-not (Test-Path -LiteralPath $preservedPath -PathType Leaf)) {
                Stop-InvalidState "preserve-template destination '$destination' does not exist as a file."
            }
            $actualHash = (Get-FileHash -LiteralPath $preservedPath -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($actualHash -cne $sha256) {
                Stop-InvalidState "sha256 mismatch for preserve-template destination '$destination'."
            }
            [void]$allowlist.Add($destination)
        }
    }

    return ,$allowlist
}

if ([System.IO.Path]::IsPathRooted($Target)) {
    $targetPath = $Target
} else {
    $targetPath = Join-Path $repoRoot $Target
}

if (-not (Test-Path -LiteralPath $targetPath)) {
    Write-Host "ERROR target does not exist: $Target"
    exit 2
}

$targetItem = Get-Item -LiteralPath $targetPath -Force
$targetIsSupportedFile = $targetItem.Name -ceq 'CODEOWNERS' -or
    $targetItem.Extension -in @('.md', '.yml', '.yaml', '.tsv')
if (-not $targetItem.PSIsContainer -and -not $targetIsSupportedFile) {
    Write-Host "ERROR target must be a directory or a supported documentation file: $Target"
    exit 2
}

$consumerStateAllowlist = $null
if ($Mode -eq 'Consumer') {
    $consumerStateAllowlist = Get-ConsumerStateAllowlist
}

if ($targetItem.PSIsContainer) {
    $files = Get-ChildItem -LiteralPath $targetItem.FullName -Recurse -Force -File | Where-Object {
        ($_.Extension -in @('.md', '.yml', '.yaml', '.tsv') -or $_.Name -eq 'CODEOWNERS') -and
        $_.FullName -notmatch '[/\\]\.git([/\\]|$)'
    }
} else {
    $files = @($targetItem) | Where-Object {
        $_.Extension -in @('.md', '.yml', '.yaml', '.tsv') -or $_.Name -eq 'CODEOWNERS'
    }
}

Write-Host "==> 扫描 $Target 中的模板占位符"
if ($Mode -eq 'TemplateRepository') {
    Write-Host "    Mode: TemplateRepository，模板源允许合法 token，非模板内容不得残留。"
} else {
    Write-Host "    Mode: Consumer，非模板文件不得残留占位符。"
}
Write-Host ''

$found = 0
$balancedPlaceholderPattern = '\{\{([^{}\r\n]*)\}\}'
$validTokenPattern = '^[A-Z][A-Z0-9_]*$'

foreach ($file in $files) {
    $relForward = Get-DisplayPath $file
    if ($Mode -eq 'Consumer') {
        if ($null -ne $consumerStateAllowlist) {
            $tokenAllowed = $consumerStateAllowlist.Contains($relForward)
        } else {
            $tokenAllowed = Test-MatchesAnyPattern $relForward $consumerTemplatePatterns
        }
    } else {
        $tokenAllowed = (Test-MatchesAnyPattern $relForward $consumerTemplatePatterns) -or
            (Test-MatchesAnyPattern $relForward $templateRepositoryPatterns)
    }

    $lineNumber = 0
    foreach ($line in (Get-Content -LiteralPath $file.FullName -Encoding UTF8)) {
        $lineNumber++

        if ($line -match '\{\{\{|\}\}\}') {
            Write-Host "  ${relForward}:${lineNumber}: malformed triple-brace marker: $($line.Trim())"
            $found++
        }

        $matches = [regex]::Matches($line, $balancedPlaceholderPattern)
        foreach ($match in $matches) {
            $token = $match.Groups[1].Value
            if (-not $tokenAllowed) {
                Write-Host "  ${relForward}:${lineNumber}: unresolved placeholder $($match.Value)"
                $found++
            } elseif ($token -notmatch $validTokenPattern -and -not (Test-IsSyntaxExample $relForward $token)) {
                Write-Host "  ${relForward}:${lineNumber}: invalid placeholder token $($match.Value)"
                $found++
            }
        }

        $withoutBalancedPlaceholders = [regex]::Replace($line, $balancedPlaceholderPattern, '')
        if ($withoutBalancedPlaceholders -match '\{\{|\}\}') {
            Write-Host "  ${relForward}:${lineNumber}: incomplete double-brace marker: $($line.Trim())"
            $found++
        }

        if ($Mode -eq 'Consumer' -and $relForward -match '(^|/)\.github/CODEOWNERS$') {
            $markerMatches = [regex]::Matches($line, '@your-org/')
            foreach ($markerMatch in $markerMatches) {
                Write-Host "  ${relForward}:${lineNumber}: unresolved CODEOWNERS marker $($markerMatch.Value)"
                $found++
            }
        }
    }
}

Write-Host ''
if ($found -eq 0) {
    Write-Host 'OK placeholder checks passed.'
    exit 0
}

Write-Host "FAIL found $found placeholder issue(s)."
if ($Mode -eq 'Consumer') {
    Write-Host '     Replace project placeholders and CODEOWNERS markers before committing.'
} else {
    Write-Host '     Template tokens must use SCREAMING_SNAKE_CASE; examples must remain placeholder-clean.'
}
exit 1
