#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$skillRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd([char[]]'\/')
$testRoot = Join-Path $tempRoot ('b2c-skill-tests-' + [Guid]::NewGuid().ToString('N'))
$workspace = Join-Path $testRoot 'workspace with spaces'
$script:Passed = 0
$script:Failed = 0
function Check([string]$Name,[scriptblock]$Body) {
    try { & $Body; $script:Passed++; "PASS: $Name" }
    catch { $script:Failed++; "FAIL: $Name -- $($_.Exception.Message)" }
}
function Assert-True([bool]$Value) { if (-not $Value) { throw 'Assertion failed.' } }
function Assert-Rejected([scriptblock]$Body) {
    $rejected = $false
    try { $null = & $Body } catch { $rejected = $true }
    if (-not $rejected) { throw 'Expected rejection.' }
}
function Copy-Value($Value) { return $Value | ConvertTo-Json -Depth 30 | ConvertFrom-Json -AsHashtable }
function Json($Value) { return ConvertTo-Json -InputObject $Value -Depth 30 }

try {
    [IO.Directory]::CreateDirectory($workspace) > $null
    . (Join-Path $skillRoot 'scripts/IssueAssistant.ps1') -WorkspaceRoot $workspace
    $source = 'src/Forecast/Service/SampleForecastService.cs'
    $shared = 'src/Forecast/Profiles/FcstMappings.cs'
    $knowledge = 'docs/sampleforecast/knowledge.md'
    foreach ($relative in @($source,$shared,$knowledge,'tests/existing.txt','src/Orders/OrdersService.cs')) {
        $target = Join-Path $workspace $relative
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) > $null
        [IO.File]::WriteAllText($target,'Synthetic fixture; not business source.')
    }
    $scope = @{
        system_id='sampleforecast'; system_name='SampleForecast'
        read_paths=@($source,$shared,'tests'); write_paths=@($source,'tests/NewTests.cs')
        docs_paths=@('docs/sampleforecast'); shared_dependencies=@($shared)
    }
    $scopeJson = Json $scope
    $validated = Get-AnalyzedScope $scopeJson
    $demoJson = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'fixtures/demo-diagnosis.json') -Raw
    $demo = ConvertFrom-Json -InputObject $demoJson -AsHashtable
    Check 'Current analyzed target works without any registration or settings' { Assert-True ($validated.system_id -ceq 'sampleforecast') }
    Check 'Previously unknown targets can be analyzed without registration' {
        $fresh = Copy-Value $scope
        $fresh.system_id='new-feature'; $fresh.system_name='New feature'
        Assert-True ((Get-AnalyzedScope (Json $fresh)).system_id -ceq 'new-feature')
    }
    Check 'Missing scope grants no implicit system or paths' { Assert-Rejected { Get-AnalyzedScope '' } }
    Check 'Enabled state and legacy registry cannot grant permissions' {
        $bad = Copy-Value $scope; $bad.enabled=$true
        Assert-Rejected { Get-AnalyzedScope (Json $bad) }
        Assert-Rejected { Get-AnalyzedScope '{"version":2,"systems":[]}' }
    }
    Check 'Missing path fields rejected' {
        $bad = Copy-Value $scope; $bad.Remove('write_paths')
        Assert-Rejected { Get-AnalyzedScope (Json $bad) }
    }
    Check 'Duplicate paths rejected' {
        $bad = Copy-Value $scope; $bad.read_paths += @($source)
        Assert-Rejected { Get-AnalyzedScope (Json $bad) }
    }
    Check 'Missing read paths rejected' {
        $bad = Copy-Value $scope; $bad.read_paths += @('missing.txt')
        Assert-Rejected { Get-AnalyzedScope (Json $bad) }
    }
    Check 'Shared dependency must be readable' {
        $bad = Copy-Value $scope; $bad.read_paths=@($source)
        Assert-Rejected { Get-AnalyzedScope (Json $bad) }
    }
    Check 'Shared files cannot enter write scope' {
        $bad = Copy-Value $scope; $bad.write_paths += @($shared)
        Assert-Rejected { Get-AnalyzedScope (Json $bad) }
    }
    Check 'Broad writable parent cannot encompass a shared dependency' {
        $bad = Copy-Value $scope; $bad.read_paths=@('src/Forecast'); $bad.write_paths=@('src/Forecast')
        Assert-Rejected { Get-AnalyzedScope (Json $bad) }
    }
    Check 'Write candidates must be within readable scope' {
        $bad = Copy-Value $scope; $bad.write_paths+=@('src/Orders/OrdersService.cs')
        Assert-Rejected { Get-AnalyzedScope (Json $bad) }
    }
    Check 'Dedicated source, relevant documentation and shared reads permitted' {
        Assert-ScopePath $scope $source 'read'
        Assert-ScopePath $scope $shared 'read'
        Assert-ScopePath $scope $knowledge 'read'
    }
    Check 'Unrelated module read rejected' { Assert-Rejected { Assert-ScopePath $scope 'src/Orders/OrdersService.cs' 'read' } }
    Check 'Source writes require actual authorization' {
        Assert-Rejected { Assert-ScopePath $scope $source 'write' }
        Assert-ScopePath $scope $source 'write' $true
    }
    Check 'New file candidate supported within existing readable directory' { Assert-ScopePath $scope 'tests/NewTests.cs' 'write' $true }
    Check 'New file is a candidate check, not an actual readable file' { Assert-True (-not (Test-Path -LiteralPath (Join-Path $workspace 'tests/NewTests.cs'))) }
    Check 'Authorization cannot expand scope or write shared files' {
        Assert-Rejected { Assert-ScopePath $scope $shared 'write' $true }
        Assert-Rejected { Assert-ScopePath $scope 'src/Orders/OrdersService.cs' 'write' $true }
    }
    Check 'Unknown operation rejected' { Assert-Rejected { Assert-ScopePath $scope $source 'delete' $true } }
    Check 'Traversal, absolute paths, alternate streams and wildcards rejected' {
        foreach ($unsafe in @('../outside','src/../../secret','C:\Windows\win.ini','\\server\share','file:secret','src/*','.','')) {
            Assert-Rejected { Get-SafePath $unsafe }
        }
    }
    Check 'Directory prefix cannot match similarly named sibling' {
        Assert-True (Test-WithinPath $knowledge 'docs/sampleforecast')
        Assert-True (-not (Test-WithinPath 'docs/sampleforecast-other/x.md' 'docs/sampleforecast'))
    }
    Check 'Junction descendants and junction workspace rejected' {
        $junction = Join-Path $workspace 'linked-tests'
        New-Item -ItemType Junction -Path $junction -Target (Join-Path $workspace 'tests') > $null
        Assert-Rejected { Get-SafePath 'linked-tests/existing.txt' }
        $null = & pwsh -NoProfile -NonInteractive -File (Join-Path $skillRoot 'scripts/IssueAssistant.ps1') -WorkspaceRoot $junction 2>&1
        Assert-True ($LASTEXITCODE -ne 0)
        Remove-Item -LiteralPath $junction -Force
    }
    Check 'Known-target report validates against analyzed scope' { $null = Assert-Report $scope $demoJson }
    Check 'Report cannot switch target' {
        $bad = Copy-Value $demo; $bad.system_id='orders'
        Assert-Rejected { Assert-Report $scope (Json $bad) }
    }
    Check 'Report cannot cite unrelated source' {
        $bad = Copy-Value $demo; $bad.evidence[0].path='src/Orders/OrdersService.cs'
        Assert-Rejected { Assert-Report $scope (Json $bad) }
    }
    Check 'Usage guidance cannot include code changes' {
        $bad = Copy-Value $demo; $bad.requires_code_change=$true; $bad.changed_files=@($source)
        Assert-Rejected { Assert-Report $scope (Json $bad) $true }
    }
    Check 'Code bug proposal can be delivered before implementation' {
        $proposal=Copy-Value $demo; $proposal.classification='CODE_BUG'; $proposal.requires_code_change=$true; $proposal.status='PROPOSED_FIX'
        $null=Assert-Report $scope (Json $proposal)
    }
    Check 'FIXED rejected without changes and actual tests' {
        $bad=Copy-Value $demo; $bad.classification='CODE_BUG'; $bad.status='FIXED'
        Assert-Rejected { Assert-Report $scope (Json $bad) $true }
    }
    Check 'FIXED rejected with relevant tests not run' {
        $bad=Copy-Value $demo; $bad.classification='CODE_BUG'; $bad.requires_code_change=$true; $bad.status='FIXED'; $bad.changed_files=@($source)
        Assert-Rejected { Assert-Report $scope (Json $bad) $true }
    }
    Check 'Synthetic tested repair report requires authorization' {
        $fixed=Copy-Value $demo; $fixed.classification='CODE_BUG'; $fixed.requires_code_change=$true; $fixed.status='FIXED'; $fixed.changed_files=@($source)
        $fixed.test_results=@(@{name='Synthetic check';result='PASS';details='Contract test only'})
        $null=Assert-Report $scope (Json $fixed) $true
        Assert-Rejected { Assert-Report $scope (Json $fixed) }
        $fixed.test_results+=@(@{name='Failed check';result='FAIL';details='Synthetic failure'})
        Assert-Rejected { Assert-Report $scope (Json $fixed) $true }
    }
    Check 'Unidentified target requests information instead of registration or OUT_OF_SCOPE' {
        $unknown=Copy-Value $demo; $unknown.system_id=''; $unknown.system_name=''
        $unknown.classification='UNKNOWN'; $unknown.status='NEEDS_INFO'; $unknown.evidence=@()
        $null=Assert-Report $null (Json $unknown)
        $unknown.evidence=$demo.evidence
        Assert-Rejected { Assert-Report $null (Json $unknown) }
    }
    Check 'Out-of-scope status must agree with classification' {
        $bad=Copy-Value $demo; $bad.status='OUT_OF_SCOPE'
        Assert-Rejected { Assert-Report $scope (Json $bad) }
    }
    Check 'Shared impact report cannot smuggle target writes' {
        $bad=Copy-Value $demo; $bad.classification='CODE_BUG'; $bad.requires_code_change=$true
        $bad.impact_scope='SHARED_COMPONENT'; $bad.changed_files=@($source)
        Assert-Rejected { Assert-Report $scope (Json $bad) $true }
    }
    Check 'Schema rejects invented classification' {
        $bad=Copy-Value $demo; $bad.classification='PROBABLY_OK'
        Assert-Rejected { Assert-Report $scope (Json $bad) }
    }
    $tool=Join-Path $skillRoot 'scripts/IssueAssistant.ps1'
    Check 'CLI needs no configuration files or Notion mapping' {
        $null=& pwsh -NoProfile -NonInteractive -File $tool -WorkspaceRoot $workspace -Action Validate
        Assert-True ($LASTEXITCODE -eq 0)
    }
    Check 'CLI without scope cannot check file permissions' {
        $null=& pwsh -NoProfile -NonInteractive -File $tool -WorkspaceRoot $workspace -Action CheckPath -Path $source 2>&1
        Assert-True ($LASTEXITCODE -ne 0)
    }
    Check 'CLI requires an explicit absolute workspace' {
        $null=& pwsh -NoProfile -NonInteractive -File $tool -Action Validate 2>&1
        Assert-True ($LASTEXITCODE -ne 0)
        $null=& pwsh -NoProfile -NonInteractive -File $tool -WorkspaceRoot '.' -Action Validate 2>&1
        Assert-True ($LASTEXITCODE -ne 0)
    }
    Check 'Relocated tool checks explicit workspace without registration' {
        $relocated=Join-Path $testRoot 'installed skill'
        Copy-Item -LiteralPath $skillRoot -Destination $relocated -Recurse
        $relocatedTool=Join-Path $relocated 'scripts/IssueAssistant.ps1'
        Push-Location $testRoot
        try {
            $null=& pwsh -NoProfile -NonInteractive -File $relocatedTool -WorkspaceRoot $workspace -ScopeJson $scopeJson -Action CheckPath -Path $source -Operation write -Authorized
            Assert-True ($LASTEXITCODE -eq 0)
            [IO.File]::WriteAllText((Join-Path $workspace 'report.json'),$demoJson)
            $null=& pwsh -NoProfile -NonInteractive -File $relocatedTool -WorkspaceRoot $workspace -ScopeJson $scopeJson -Action ValidateReport -ReportPath report.json
            Assert-True ($LASTEXITCODE -eq 0)
        } finally { Pop-Location }
    }
    "Results: $script:Passed passed, $script:Failed failed. Synthetic path/report tests; no live Notion or business API calls."
} finally {
    $cleanup=[IO.Path]::GetFullPath($testRoot)
    if (-not $cleanup.StartsWith($tempRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
        (Split-Path -Leaf $cleanup) -notmatch '^b2c-skill-tests-[a-f0-9]{32}$') { throw 'Unverified cleanup path.' }
    if (Test-Path -LiteralPath $cleanup) { Remove-Item -LiteralPath $cleanup -Recurse -Force }
}
if ($script:Failed) { exit 1 }
