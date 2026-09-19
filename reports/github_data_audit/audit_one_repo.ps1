param(
    [Parameter(Mandatory = $true)] [string] $Owner,
    [Parameter(Mandatory = $true)] [string] $Repo,
    [Parameter(Mandatory = $true)] [string] $AuditRoot,
    [string] $LocalClone = ''
)

$ErrorActionPreference = "Stop"
$repoFull = "$Owner/$Repo"
$repoSlug = $repoFull.Replace('/', '__')
$repoDir = Join-Path $AuditRoot "repositories/$repoSlug"
New-Item -ItemType Directory -Force -Path $repoDir | Out-Null

function Invoke-GhJson {
    param([string] $Endpoint, [switch] $Paginate)
    $args = @('api', $Endpoint)
    if ($Paginate) { $args += @('--paginate', '--slurp') }
    $raw = & gh @args
    if ($LASTEXITCODE -ne 0) { throw "gh api failed: $Endpoint" }
    if ([string]::IsNullOrWhiteSpace(($raw -join ''))) { return $null }
    return (($raw -join [Environment]::NewLine) | ConvertFrom-Json)
}

function Expand-Pages {
    param($Value)
    if ($null -eq $Value) { return @() }
    if ($Value -is [System.Array]) {
        if ($Value.Count -eq 0) { return @() }
        if ($Value[0] -is [System.Array]) {
            $flat = @()
            foreach ($page in $Value) { $flat += @($page) }
            return $flat
        }
        return @($Value)
    }
    return @($Value)
}

function Get-RecursiveTree {
    param([string] $FullName, [string] $CommitSha)
    $recursive = Invoke-GhJson "repos/$FullName/git/trees/$CommitSha`?recursive=1"
    if ($recursive -and -not $recursive.truncated) {
        return [pscustomobject]@{ entries = @($recursive.tree); truncated = $false; mode = 'recursive' }
    }

    $all = @()
    function Walk-Tree {
        param([string] $TreeSha, [string] $Prefix)
        $node = Invoke-GhJson "repos/$repoFull/git/trees/$TreeSha"
        foreach ($entry in @($node.tree)) {
            $path = if ([string]::IsNullOrEmpty($Prefix)) { $entry.path } else { "$Prefix/$($entry.path)" }
            if ($entry.type -eq 'tree') {
                Walk-Tree $entry.sha $path
            } else {
                $all += [pscustomobject]@{
                    path = $path
                    mode = $entry.mode
                    type = $entry.type
                    sha = $entry.sha
                    size = $entry.size
                }
            }
        }
    }
    Walk-Tree $CommitSha ''
    return [pscustomobject]@{ entries = $all; truncated = $true; mode = 'subtree-walk' }
}

function Is-TextPath {
    param([string] $Path)
    $name = [IO.Path]::GetFileName($Path).ToLowerInvariant()
    $ext = [IO.Path]::GetExtension($Path).ToLowerInvariant()
    return ($name -in @('dockerfile', '.gitignore', '.gitattributes', '.dvc', 'dvc.yaml', 'dvc.lock', 'config') -or
        $ext -in @('.md','.txt','.rst','.py','.ipynb','.json','.yaml','.yml','.toml','.ini','.cfg','.sh','.ps1','.bat','.csv','.tsv','.xml','.tex','.html','.js','.ts','.css'))
}

function Get-BlobInspection {
    param([string] $FullName, [string] $BlobSha, [int64] $Size, [string] $CommitSha, [string] $Path)
    $text = $null; $bytes = $null
    if (-not [string]::IsNullOrWhiteSpace($LocalClone) -and (Test-Path -LiteralPath (Join-Path $LocalClone '.git'))) {
        $gitSpec = "$CommitSha`:$Path"
        $raw = & git -C $LocalClone show $gitSpec 2>$null
        if ($LASTEXITCODE -eq 0) {
            $text = ($raw -join [Environment]::NewLine)
            $bytes = [Text.Encoding]::UTF8.GetBytes($text)
        }
    }
    if ($null -eq $text) {
        $obj = Invoke-GhJson "repos/$FullName/git/blobs/$BlobSha"
        if (-not $obj -or $obj.encoding -ne 'base64') {
            return [pscustomobject]@{ status = 'metadata-only'; text = $null; lfs = $false; bytes = 0 }
        }
        $clean = ([string]$obj.content) -replace '\s', ''
        $bytes = [Convert]::FromBase64String($clean)
        $text = [Text.Encoding]::UTF8.GetString($bytes)
    }
    if ($bytes.Length -gt 8MB) {
        return [pscustomobject]@{ status = 'metadata-only-too-large'; text = $null; lfs = $false; bytes = $bytes.Length }
    }
    $isLfs = $text -match 'version https://git-lfs.github.com/spec/v1' -and $text -match 'oid sha256:'
    return [pscustomobject]@{ status = 'read'; text = $text; lfs = $isLfs; bytes = $bytes.Length }
}

function Initial-Category {
    param([string] $Path)
    $lower = $Path.ToLowerInvariant()
    $ext = [IO.Path]::GetExtension($lower)
    if ($lower -match '(^|/)(sample|samples|demo|toy|debug|synthetic)(/|_|-|\.)') { return 'C_SAMPLE_DEBUG' }
    if ($lower -match '(^|/)(data|dataset|datasets|myfeature|features?)(/|_)' -or $lower -match 'group_feature|\.csv$|\.tsv$|\.parquet$|\.npz$|\.npy$|\.mat$|\.h5$|\.hdf5$') { return 'B_PROCESSED_DERIVED' }
    if ($ext -in @('.keras','.h5','.hdf5','.pt','.pth','.ckpt','.bin','.pkl')) { return 'E_CHECKPOINT_ONLY' }
    if ($ext -in @('.zip','.gz','.tgz','.tar','.7z','.rar')) { return 'D_POINTER_EXTERNAL' }
    return 'F_IRRELEVANT'
}

function Add-Candidate {
    param([string] $Branch, [string] $Commit, [string] $Path, [string] $Category, [string] $Size, [string] $Evidence, [string] $Confidence)
    $script:candidates += [pscustomobject]@{
        repository = $repoFull; branch = $Branch; commit_sha = $Commit; path_or_url = $Path
        type = $Category; size = $Size; lfs_or_dvc = ''; conditions = ''; classes = ''; split = ''
        schema_match = 'pending'; available = 'unknown'; confidence = $Confidence; evidence = $Evidence; missing = ''
    }
}

$meta = Invoke-GhJson "repos/$repoFull"
$branches = @(Expand-Pages (Invoke-GhJson "repos/$repoFull/branches?per_page=100" -Paginate))
$releases = @(Expand-Pages (Invoke-GhJson "repos/$repoFull/releases?per_page=100" -Paginate))
$tags = @(Expand-Pages (Invoke-GhJson "repos/$repoFull/tags?per_page=100" -Paginate))
$branchRows = @(); $fileRows = @(); $candidates = @(); $blobStatus = @{}

foreach ($branch in ($branches | Sort-Object name)) {
    $branchName = [string]$branch.name
    $head = [string]$branch.commit.sha
    $treeStatus = 'completed'; $treeMode = ''; $entries = @(); $treeError = ''
    try {
        $tree = Get-RecursiveTree $repoFull $head
        $entries = @($tree.entries); $treeMode = $tree.mode
    } catch {
        $treeStatus = 'failed'; $treeError = $_.Exception.Message
    }
    $branchRows += [pscustomobject]@{
        repository = $repoFull; branch = $branchName; head_sha = $head
        head_date = ''; protected = ''; default_branch = ($branchName -eq $meta.default_branch)
        tree_mode = $treeMode; file_count = @($entries).Count; audit_status = $treeStatus; error = $treeError
    }
    foreach ($entry in $entries) {
        $path = [string]$entry.path; $sha = [string]$entry.sha
        $kind = Initial-Category $path; $analysis = if ($entry.type -eq 'commit') { 'submodule-metadata' } elseif ($entry.type -eq 'blob') { 'metadata' } else { 'unknown' }
        $lfs = $false; $dvc = ($path -match '(^|/)(\.dvc|dvc\.yaml|dvc\.lock|\.dvc/config)$'); $notes = ''
        $text = $null
        if ($entry.type -eq 'blob' -and (Is-TextPath $path -or $kind -ne 'F_IRRELEVANT' -or $dvc)) {
            if (-not $blobStatus.ContainsKey($sha)) {
                try { $blobStatus[$sha] = Get-BlobInspection $repoFull $sha ([int64]$entry.size) $head $path }
                catch { $blobStatus[$sha] = [pscustomobject]@{ status = 'failed'; text = $null; lfs = $false; bytes = 0 } }
            }
            $inspection = $blobStatus[$sha]; $analysis = $inspection.status; $text = $inspection.text; $lfs = [bool]$inspection.lfs
            if ($lfs) { $kind = 'D_POINTER_EXTERNAL'; $notes = 'Git LFS pointer; blob content is not the data object' }
            if ($dvc) { $kind = 'D_POINTER_EXTERNAL'; $notes = 'DVC metadata; not the data object' }
            if ($text) {
                $urls = [regex]::Matches($text, 'https?://[^\s\)\]<>"'']+') | ForEach-Object Value
                foreach ($url in @($urls | Select-Object -Unique)) {
                    if ($url -match '(?i)drive|dropbox|onedrive|kaggle|huggingface|zenodo|figshare|s3|download|release|lfs|dvc|dataset|data') {
                        Add-Candidate $branchName $head $url 'D_POINTER_EXTERNAL' ([string]$entry.size) "$path external URL" 'Low'
                    }
                }
                if ($path -match '(?i)(Group_feature_data_clean|data/|dataset|myfeature|manifest|checksum|\.dvc|dvc\.yaml|dvc\.lock)') {
                    Add-Candidate $branchName $head $path $kind ([string]$entry.size) "$path static text inspection" 'Medium'
                }
            }
        }
        if ($kind -ne 'F_IRRELEVANT' -and $entry.type -eq 'blob') {
            Add-Candidate $branchName $head $path $kind ([string]$entry.size) 'path/type candidate classification' 'Low'
        }
        $fileRows += [pscustomobject]@{
            repository = $repoFull; branch = $branchName; commit_sha = $head; path = $path
            filename = [IO.Path]::GetFileName($path); extension = [IO.Path]::GetExtension($path).ToLowerInvariant()
            object_type = $entry.type; mode = $entry.mode; blob_or_tree_sha = $sha; size = $entry.size
            analysis_status = $analysis; candidate_category = $kind; lfs_pointer = $lfs; dvc_metadata = $dvc; notes = $notes
        }
    }
}

$repoRow = [pscustomobject]@{
    owner = $meta.owner.login; name = $meta.name; full_name = $meta.full_name; url = $meta.html_url
    visibility = $meta.visibility; archived = $meta.archived; disabled = $meta.disabled; fork = $meta.fork
    parent = if ($meta.parent) { $meta.parent.full_name } else { '' }; default_branch = $meta.default_branch
    created_at = $meta.created_at; updated_at = $meta.updated_at; pushed_at = $meta.pushed_at; size = $meta.size
    language = $meta.language; license = if ($meta.license) { $meta.license.spdx_id } else { '' }
    topics = (@($meta.topics) -join '|'); branch_count = @($branches).Count; release_count = @($releases).Count
    tag_count = @($tags).Count; lfs_detected = (@($fileRows | Where-Object lfs_pointer).Count -gt 0)
    dvc_detected = (@($fileRows | Where-Object dvc_metadata).Count -gt 0)
    submodule_detected = (@($fileRows | Where-Object { $_.object_type -eq 'commit' }).Count -gt 0)
    audit_status = if (@($branchRows | Where-Object audit_status -ne 'completed').Count -eq 0) { 'completed' } else { 'failed' }
}

function Replace-RepoRows {
    param([string] $Path, $Rows)
    $keep = @(); if (Test-Path -LiteralPath $Path) { $keep = @(Import-Csv -LiteralPath $Path | Where-Object { $_.repository -ne $repoFull -and $_.full_name -ne $repoFull }) }
    @($keep + @($Rows)) | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding utf8
}

Replace-RepoRows (Join-Path $AuditRoot 'repository_inventory.csv') @($repoRow)
Replace-RepoRows (Join-Path $AuditRoot 'branch_inventory.csv') $branchRows
Replace-RepoRows (Join-Path $AuditRoot 'file_inventory.csv') $fileRows
$candidatePath = Join-Path $AuditRoot 'data_candidates.csv'
$candidateKeep = @(); if (Test-Path -LiteralPath $candidatePath) { $candidateKeep = @(Import-Csv -LiteralPath $candidatePath | Where-Object { $_.repository -ne $repoFull }) }
@($candidateKeep + @($candidates)) | Export-Csv -LiteralPath $candidatePath -NoTypeInformation -Encoding utf8

$repoRow | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $repoDir 'repository.json') -Encoding utf8
$branchRows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $repoDir 'branches.json') -Encoding utf8
Write-Output ($repoRow | ConvertTo-Json -Depth 8)
