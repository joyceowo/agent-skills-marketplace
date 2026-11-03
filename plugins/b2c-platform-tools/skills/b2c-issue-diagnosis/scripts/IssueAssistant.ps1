#requires -Version 7.0
param(
    [string]$WorkspaceRoot,
    [string]$ConfigRoot,
    [ValidateSet('Validate','Resolve','CheckPath','ValidateReport','ValidateNotion','ResolveNotion')][string]$Action = 'Validate',
    [string]$SystemId,
    [string]$Path,
    [ValidateSet('read','write')][string]$Operation = 'read',
    [switch]$Authorized,
    [string]$ReportPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# The Skill may be installed outside the target repository. Never infer its workspace.
if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) { throw '-WorkspaceRoot is required; specify the target repository.' }
$script:ProjectRoot = [IO.Path]::GetFullPath($WorkspaceRoot)
if (-not (Test-Path -LiteralPath $script:ProjectRoot -PathType Container)) { throw 'WorkspaceRoot must be an existing directory.' }
# Local configuration is selected independently of both the workspace and the Skill installation.
if ([string]::IsNullOrWhiteSpace($ConfigRoot)) { throw '-ConfigRoot is required; specify the external local configuration directory.' }
if (-not [IO.Path]::IsPathFullyQualified($ConfigRoot)) { throw 'ConfigRoot must be an absolute directory path.' }
$script:ConfigRoot = [IO.Path]::GetFullPath($ConfigRoot)
if (-not (Test-Path -LiteralPath $script:ConfigRoot -PathType Container)) { throw 'ConfigRoot must be an existing directory.' }
$workspacePrefix = $script:ProjectRoot.TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar
if ($script:ConfigRoot.TrimEnd([char[]]'\/').Equals($script:ProjectRoot.TrimEnd([char[]]'\/'),[StringComparison]::OrdinalIgnoreCase) -or
    $script:ConfigRoot.StartsWith($workspacePrefix,[StringComparison]::OrdinalIgnoreCase)) {
    throw 'ConfigRoot must be outside the target workspace.'
}
$script:SchemaRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../references/schemas'))

function Assert-JsonSchema([string]$Json, [string]$SchemaPath) {
    if (-not (Test-Json -Json $Json -SchemaFile $SchemaPath -ErrorAction Stop)) {
        throw 'JSON Schema validation failed.'
    }
}

function Get-SafePath([string]$RelativePath) {
    # Reject absolute paths, traversal, alternate data streams and wildcard paths.
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or
        [IO.Path]::IsPathRooted($RelativePath) -or
        $RelativePath -match '(^|[/\\])\.\.([/\\]|$)|[:*?\[\]]') {
        throw "Unsafe relative path: $RelativePath"
    }
    $full = [IO.Path]::GetFullPath((Join-Path $script:ProjectRoot $RelativePath))
    $prefix = $script:ProjectRoot.TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path leaves repository: $RelativePath"
    }
    # Do not follow symlinks/junctions, including ancestors of new files.
    $cursor = $full
    while ($cursor -ne $script:ProjectRoot) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Reparse point is outside repository scope policy: $RelativePath"
            }
        }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    return $full
}

function Test-WithinPath([string]$Candidate, [string]$Allowed) {
    $candidateFull = Get-SafePath $Candidate
    $allowedFull = Get-SafePath $Allowed
    if ($candidateFull.Equals($allowedFull, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    if (Test-Path -LiteralPath $allowedFull -PathType Container) {
        return $candidateFull.StartsWith(
            $allowedFull.TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase)
    }
    return $false
}

function Get-Registry([string]$Json = '') {
    if (-not $Json) {
        $Json = Get-Content -LiteralPath (Join-Path $script:ConfigRoot 'systems.yaml') -Raw
    }
    # JSON is a YAML 1.2 subset. No YAML packages or new services are required.
    Assert-JsonSchema $Json (Join-Path $script:SchemaRoot 'systems.schema.json')
    $registry = ConvertFrom-Json -InputObject $Json -AsHashtable
    $ids = @($registry.systems | ForEach-Object { $_.system_id })
    if (@($ids | Sort-Object -Unique).Count -ne $ids.Count) { throw 'Duplicate system_id.' }
    $enabled = @($registry.systems | Where-Object { $_.enabled })
    foreach ($system in $enabled) {
        foreach ($entry in @($system.root_path) + @($system.read_paths) + @($system.write_paths) +
            @($system.docs_paths) + @($system.shared_dependencies)) {
            $resolved = Get-SafePath $entry
            if (-not (Test-Path -LiteralPath $resolved)) { throw "Registered path missing: $entry" }
        }
        foreach ($entry in $system.write_paths) {
            if (-not (Test-WithinPath $entry $system.root_path)) { throw "Write leaves system root: $entry" }
            if (-not @($system.read_paths | Where-Object { Test-WithinPath $entry $_ }).Count) {
                throw "Write path is not readable: $entry"
            }
            foreach ($dependency in $system.shared_dependencies) {
                if ((Test-WithinPath $entry $dependency) -or (Test-WithinPath $dependency $entry)) {
                    throw "Shared dependency overlaps write scope: $entry"
                }
            }
        }
        foreach ($dependency in $system.shared_dependencies) {
            if (-not @($system.read_paths | Where-Object { Test-WithinPath $dependency $_ }).Count) {
                throw "Shared dependency is not readable: $dependency"
            }
        }
    }
    # A file writable by one system cannot also be writable or shared by another enabled system.
    for ($leftIndex = 0; $leftIndex -lt $enabled.Count; $leftIndex++) {
        $left = $enabled[$leftIndex]
        for ($rightIndex = $leftIndex + 1; $rightIndex -lt $enabled.Count; $rightIndex++) {
            $right = $enabled[$rightIndex]
            foreach ($leftWrite in $left.write_paths) {
                foreach ($rightPath in @($right.write_paths) + @($right.shared_dependencies)) {
                    if ((Test-WithinPath $leftWrite $rightPath) -or (Test-WithinPath $rightPath $leftWrite)) {
                        throw "Cross-system write/shared overlap: $($left.system_id), $($right.system_id)"
                    }
                }
            }
            foreach ($rightWrite in $right.write_paths) {
                foreach ($leftShared in $left.shared_dependencies) {
                    if ((Test-WithinPath $rightWrite $leftShared) -or (Test-WithinPath $leftShared $rightWrite)) {
                        throw "Cross-system shared/write overlap: $($left.system_id), $($right.system_id)"
                    }
                }
            }
        }
    }
    return $registry
}

function Get-NotionRegistry($Registry, [string]$Json = '') {
    if (-not $Json) {
        $Json = Get-Content -LiteralPath (Join-Path $script:ConfigRoot 'notion.json') -Raw
    }
    Assert-JsonSchema $Json (Join-Path $script:SchemaRoot 'notion.schema.json')
    $notion = ConvertFrom-Json -InputObject $Json -AsHashtable
    $knownIds = @($Registry.systems | ForEach-Object { $_.system_id })
    foreach ($targetId in $notion.systems.Keys) {
        if ($knownIds -cnotcontains $targetId) { throw "Notion destination has unknown system_id: $targetId" }
    }
    return $notion
}

function Resolve-NotionDestination($Registry, $NotionRegistry, [string]$TargetId) {
    if ([string]::IsNullOrWhiteSpace($TargetId)) { throw 'Select a system_id before resolving Notion.' }
    if (-not @($Registry.systems | Where-Object { $_.system_id -ceq $TargetId }).Count) {
        throw "Unknown system_id: $TargetId"
    }
    if (-not $NotionRegistry.systems.ContainsKey($TargetId)) {
        throw "Notion destination is not configured for system: $TargetId"
    }
    # Local validation does not verify remote existence, write access, or user authorization.
    return $NotionRegistry.systems[$TargetId]
}

function Resolve-System($Registry, [string]$TargetId) {
    if ([string]::IsNullOrWhiteSpace($TargetId)) { throw 'OUT_OF_SCOPE: select a system_id first.' }
    $matches = @($Registry.systems | Where-Object { $_.system_id -ceq $TargetId })
    if ($matches.Count -ne 1 -or -not $matches[0].enabled) {
        throw "OUT_OF_SCOPE: unregistered or disabled system: $TargetId"
    }
    return $matches[0]
}

function Assert-SystemPath($System, [string]$Candidate, [string]$Mode, [bool]$HasAuthorization = $false) {
    $null = Get-SafePath $Candidate
    if ($Mode -notin @('read','write')) { throw 'Unknown path operation.' }
    if ($Mode -eq 'write') {
        if (-not $HasAuthorization) { throw 'Explicit user authorization is required for code changes.' }
        foreach ($dependency in $System.shared_dependencies) {
            if (Test-WithinPath $Candidate $dependency) { throw 'SHARED_COMPONENT: separate review required.' }
        }
        $allowed = @($System.write_paths)
    } else {
        $allowed = @($System.read_paths) + @($System.docs_paths)
    }
    if (-not @($allowed | Where-Object { Test-WithinPath $Candidate $_ }).Count) {
        throw "OUT_OF_SCOPE: $Mode path is not registered: $Candidate"
    }
}

function Assert-Report($Registry, [string]$Json, [string]$TargetId, [bool]$HasAuthorization = $false) {
    Assert-JsonSchema $Json (Join-Path $script:SchemaRoot 'diagnosis.schema.json')
    $report = ConvertFrom-Json -InputObject $Json -AsHashtable
    if ($report.system_id -cne $TargetId) { throw 'Report system differs from selected system.' }
    $system = @($Registry.systems | Where-Object { $_.system_id -ceq $TargetId -and $_.enabled })
    if ($system.Count -ne 1) {
        if ($report.classification -ne 'OUT_OF_SCOPE' -or $report.status -ne 'OUT_OF_SCOPE' -or
            $report.evidence.Count -or $report.changed_files.Count -or $report.requires_code_change) {
            throw 'Unselected/disabled/unknown systems must return OUT_OF_SCOPE without source evidence or changes.'
        }
        return $report
    }
    $selected = $system[0]
    if ($report.system_name -cne $selected.name) { throw 'Report system_name mismatch.' }
    if (($report.classification -eq 'OUT_OF_SCOPE') -ne ($report.status -eq 'OUT_OF_SCOPE')) {
        throw 'OUT_OF_SCOPE classification and status must match.'
    }
    foreach ($entry in $report.evidence) { Assert-SystemPath $selected $entry.path 'read' }
    foreach ($entry in $report.changed_files) { Assert-SystemPath $selected $entry 'write' $HasAuthorization }
    if ($report.classification -eq 'USAGE_ERROR' -and ($report.requires_code_change -or $report.changed_files.Count)) {
        throw 'Usage errors cannot change code.'
    }
    if ($report.changed_files.Count -and (-not $report.requires_code_change -or $report.impact_scope -ne 'TARGET_SYSTEM')) {
        throw 'Code changes must be declared and limited to TARGET_SYSTEM.'
    }
    if ($report.status -eq 'FIXED') {
        if ($report.classification -notin @('CODE_BUG','FEATURE_REQUEST') -or
            -not $report.changed_files.Count -or -not $report.evidence.Count -or
            -not @($report.test_results | Where-Object { $_.result -eq 'PASS' }).Count -or
            @($report.test_results | Where-Object { $_.result -in @('FAIL','NOT_RUN') }).Count) {
            throw 'FIXED requires changed files, evidence and passing relevant tests without FAIL/NOT_RUN.'
        }
    }
    return $report
}

if ($MyInvocation.InvocationName -ne '.') {
    try {
        $registry = Get-Registry
        switch ($Action) {
            'Validate' { 'Registry valid: enabled system scopes checked; no default system.' }
            'ValidateNotion' {
                $null = Get-NotionRegistry $registry
                'Notion mappings valid. Remote access and recording authorization still require confirmation.'
            }
            'ResolveNotion' {
                $notion = Get-NotionRegistry $registry
                Resolve-NotionDestination $registry $notion $SystemId | ConvertTo-Json -Depth 10
            }
            'Resolve' { Resolve-System $registry $SystemId | ConvertTo-Json -Depth 20 }
            'CheckPath' {
                $system = Resolve-System $registry $SystemId
                Assert-SystemPath $system $Path $Operation $Authorized.IsPresent
                "Allowed: $Operation $Path"
            }
            'ValidateReport' {
                if (-not $ReportPath) { throw 'ReportPath is required.' }
                $null = Assert-Report $registry (Get-Content -LiteralPath (Get-SafePath $ReportPath) -Raw) $SystemId $Authorized.IsPresent
                'Report valid. Test claims still require human/agent evidence review.'
            }
        }
    } catch { Write-Error $_ -ErrorAction Continue; exit 1 }
}
