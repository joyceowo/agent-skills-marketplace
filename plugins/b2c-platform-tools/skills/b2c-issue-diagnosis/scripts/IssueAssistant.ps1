#requires -Version 7.0
param(
    [string]$WorkspaceRoot,
    [string]$ScopeJson,
    [ValidateSet('Validate','CheckPath','ValidateReport')][string]$Action = 'Validate',
    [string]$Path,
    [ValidateSet('read','write')][string]$Operation = 'read',
    [switch]$Authorized,
    [string]$ReportPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) { throw 'WorkspaceRoot is required.' }
if (-not [IO.Path]::IsPathFullyQualified($WorkspaceRoot)) { throw 'WorkspaceRoot must be absolute.' }
$script:ProjectRoot = [IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd([char[]]'\/')
if (-not (Test-Path -LiteralPath $script:ProjectRoot -PathType Container)) { throw 'WorkspaceRoot must exist.' }
if ((Get-Item -LiteralPath $script:ProjectRoot -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw 'WorkspaceRoot cannot be a symlink or junction.'
}
$script:SchemaRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../references/schemas'))

function Assert-JsonSchema([string]$Json, [string]$SchemaPath) {
    if (-not (Test-Json -Json $Json -SchemaFile $SchemaPath -ErrorAction Stop)) { throw 'JSON Schema validation failed.' }
}

function Get-SafePath([string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or [IO.Path]::IsPathRooted($RelativePath) -or
        $RelativePath -match '(^|[/\\])\.\.([/\\]|$)|[:*?\[\]]') { throw "Unsafe relative path: $RelativePath" }
    $full = [IO.Path]::GetFullPath((Join-Path $script:ProjectRoot $RelativePath))
    $prefix = $script:ProjectRoot + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw "Path leaves workspace: $RelativePath" }
    $cursor = $full
    while ($cursor -ne $script:ProjectRoot) {
        if (Test-Path -LiteralPath $cursor) {
            if ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Reparse point outside permitted scope: $RelativePath"
            }
        }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    return $full
}

function Test-WithinPath([string]$Candidate, [string]$Allowed) {
    $candidateFull = Get-SafePath $Candidate
    $allowedFull = Get-SafePath $Allowed
    if ($candidateFull.Equals($allowedFull,[StringComparison]::OrdinalIgnoreCase)) { return $true }
    return (Test-Path -LiteralPath $allowedFull -PathType Container) -and
        $candidateFull.StartsWith($allowedFull.TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)
}

function Get-AnalyzedScope([string]$Json) {
    if ([string]::IsNullOrWhiteSpace($Json)) { throw 'Supply this request''s analyzed scope for path/report checks.' }
    Assert-JsonSchema $Json (Join-Path $script:SchemaRoot 'scope.schema.json')
    $scope = ConvertFrom-Json -InputObject $Json -AsHashtable
    foreach ($entry in @($scope.read_paths) + @($scope.docs_paths) + @($scope.shared_dependencies)) {
        if (-not (Test-Path -LiteralPath (Get-SafePath $entry))) { throw "Scope read path missing: $entry" }
    }
    foreach ($entry in $scope.shared_dependencies) {
        if (-not @($scope.read_paths | Where-Object { Test-WithinPath $entry $_ }).Count) { throw "Shared path is not readable: $entry" }
    }
    foreach ($entry in $scope.write_paths) {
        $null = Get-SafePath $entry
        if (-not @($scope.read_paths | Where-Object { Test-WithinPath $entry $_ }).Count) { throw "Write path is not readable: $entry" }
        foreach ($shared in $scope.shared_dependencies) {
            if ((Test-WithinPath $entry $shared) -or (Test-WithinPath $shared $entry)) {
                throw "SHARED_COMPONENT: write scope overlaps shared dependency: $entry"
            }
        }
    }
    return $scope
}

function Assert-ScopePath($Scope, [string]$Candidate, [string]$Mode, [bool]$HasAuthorization = $false) {
    $null = Get-SafePath $Candidate
    if ($Mode -notin @('read','write')) { throw 'Unknown path operation.' }
    if ($Mode -eq 'write') {
        if (-not $HasAuthorization) { throw 'Explicit user authorization required for code changes.' }
        foreach ($shared in $Scope.shared_dependencies) {
            if ((Test-WithinPath $Candidate $shared) -or (Test-WithinPath $shared $Candidate)) {
                throw 'SHARED_COMPONENT: analyze impact and obtain applicable authorization separately.'
            }
        }
        $allowed = @($Scope.write_paths)
    } else { $allowed = @($Scope.read_paths) + @($Scope.docs_paths) }
    if (-not @($allowed | Where-Object { Test-WithinPath $Candidate $_ }).Count) { throw "OUT_OF_SCOPE: $Mode $Candidate" }
}

function Assert-Report($Scope, [string]$Json, [bool]$HasAuthorization = $false) {
    Assert-JsonSchema $Json (Join-Path $script:SchemaRoot 'diagnosis.schema.json')
    $report = ConvertFrom-Json -InputObject $Json -AsHashtable
    if ($null -eq $Scope) {
        if ($report.system_id -or $report.system_name -or $report.evidence.Count -or $report.changed_files.Count -or $report.requires_code_change -or
            $report.classification -ne 'UNKNOWN' -or $report.status -ne 'NEEDS_INFO') {
            throw 'An unidentified system requires UNKNOWN/NEEDS_INFO without source evidence or changes.'
        }
        return $report
    }
    if ($report.system_id -cne $Scope.system_id -or $report.system_name -cne $Scope.system_name) { throw 'Report target differs from analyzed scope.' }
    if (($report.classification -eq 'OUT_OF_SCOPE') -ne ($report.status -eq 'OUT_OF_SCOPE')) { throw 'OUT_OF_SCOPE classification and status must match.' }
    foreach ($entry in $report.evidence) { Assert-ScopePath $Scope $entry.path 'read' }
    foreach ($entry in $report.changed_files) { Assert-ScopePath $Scope $entry 'write' $HasAuthorization }
    if ($report.classification -eq 'USAGE_ERROR' -and ($report.requires_code_change -or $report.changed_files.Count)) { throw 'Usage guidance cannot carry code changes.' }
    if ($report.changed_files.Count -and (-not $report.requires_code_change -or $report.impact_scope -ne 'TARGET_SYSTEM')) { throw 'Changes must declare the reviewed target impact.' }
    if ($report.status -eq 'FIXED') {
        if ($report.classification -notin @('CODE_BUG','FEATURE_REQUEST') -or -not $report.changed_files.Count -or -not $report.evidence.Count -or
            -not @($report.test_results | Where-Object { $_.result -eq 'PASS' }).Count -or
            @($report.test_results | Where-Object { $_.result -in @('FAIL','NOT_RUN') }).Count) {
            throw 'FIXED requires changed files, evidence and passing relevant tests without FAIL/NOT_RUN.'
        }
    }
    return $report
}

if ($MyInvocation.InvocationName -ne '.') {
    try {
        $scope = if ([string]::IsNullOrWhiteSpace($ScopeJson)) { $null } else { Get-AnalyzedScope $ScopeJson }
        switch ($Action) {
            'Validate' {
                if ($null -eq $scope) { 'Workspace checked; no file permissions inferred. No registration required.' }
                else { 'Analyzed scope valid; this does not grant authorization.' }
            }
            'CheckPath' {
                if ($null -eq $scope) { throw 'CheckPath requires the analyzed scope.' }
                Assert-ScopePath $scope $Path $Operation $Authorized.IsPresent
                "Allowed: $Operation $Path"
            }
            'ValidateReport' {
                if (-not $ReportPath) { throw 'ReportPath is required.' }
                $null = Assert-Report $scope (Get-Content -LiteralPath (Get-SafePath $ReportPath) -Raw) $Authorized.IsPresent
                'Report valid; test claims still require actual evidence.'
            }
        }
    } catch { Write-Error $_ -ErrorAction Continue; exit 1 }
}
