param(
    [Parameter(Mandatory = $true)]
    [string]$Root,
    [Parameter(Mandatory = $true)]
    [string]$OutputDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
    throw "Raw data root does not exist or is not a directory: $Root"
}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

function Get-RelativePath {
    param([string]$Base, [string]$FullName)
    $baseUri = [Uri]::new(((Resolve-Path -LiteralPath $Base).Path.TrimEnd('\') + '\'))
    $fullUri = [Uri]::new((Resolve-Path -LiteralPath $FullName).Path)
    return [Uri]::UnescapeDataString($baseUri.MakeRelativeUri($fullUri).ToString()).Replace('/', '\')
}

function Get-CandidateCategory {
    param([string]$RelativePath, [string]$Extension)
    $path = $RelativePath.ToLowerInvariant()
    if ($Extension -in @('.zip', '.7z', '.rar', '.tar', '.gz')) { return 'archive' }
    if ($path -match 'backup|copy|duplicate') { return 'backup_or_duplicate' }
    if ($path -match 'myfeature|feature|clean') { return 'processed_feature' }
    if ($path -match 'csv|raw|stage') { return 'raw_or_source' }
    if ($Extension -in @('.ipynb', '.py', '.m', '.mlx')) { return 'preprocessing_code' }
    if ($Extension -in @('.md', '.txt', '.json', '.yaml', '.yml', '.xlsx', '.xls')) { return 'metadata_or_document' }
    if ($Extension -in @('.keras', '.h5', '.hdf5', '.pt', '.pth', '.ckpt', '.pkl')) { return 'model_or_checkpoint' }
    return 'other'
}

$allItems = @(Get-ChildItem -LiteralPath $Root -Force -Recurse -ErrorAction SilentlyContinue)
$files = @($allItems | Where-Object { -not $_.PSIsContainer })
$directories = @($allItems | Where-Object { $_.PSIsContainer })
$fileRows = foreach ($item in $files) {
    $relative = Get-RelativePath -Base $Root -FullName $item.FullName
    $extension = $item.Extension.ToLowerInvariant()
    [pscustomobject]@{
        absolute_path = $item.FullName
        relative_path = $relative
        filename = $item.Name
        extension = $extension
        size_bytes = [int64]$item.Length
        creation_time = $item.CreationTime.ToString('o')
        last_write_time = $item.LastWriteTime.ToString('o')
        file_type = if ($extension -eq '.ipynb') { 'Jupyter notebook' } elseif ($extension -eq '.zip') { 'ZIP archive' } elseif ($extension -eq '.py') { 'Python source' } else { 'file' }
        candidate_category = Get-CandidateCategory -RelativePath $relative -Extension $extension
        is_archive = ($extension -in @('.zip', '.7z', '.rar', '.tar', '.gz'))
        is_hidden = (($item.Attributes -band [IO.FileAttributes]::Hidden) -ne 0)
        is_reparse_point = (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
        is_symlink = ($item.LinkType -eq 'SymbolicLink')
        analysis_status = 'metadata_only'
        error = ''
    }
}
$fileRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'file_inventory.csv') -NoTypeInformation -Encoding UTF8

$directoryRows = foreach ($directory in @([IO.DirectoryInfo]$Root) + $directories) {
    $relative = if ($directory.FullName -eq (Resolve-Path -LiteralPath $Root).Path) { '.' } else { Get-RelativePath -Base $Root -FullName $directory.FullName }
    $descendants = @($files | Where-Object { $_.FullName.StartsWith($directory.FullName.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase) })
    [pscustomobject]@{
        absolute_path = $directory.FullName
        relative_path = $relative
        file_count = $descendants.Count
        total_size_bytes = [int64](($descendants | Measure-Object Length -Sum).Sum)
        is_reparse_point = (($directory.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
        candidate_category = if ($relative -match 'myfeature|feature|clean') { 'processed_feature' } elseif ($relative -match 'csv|raw|stage') { 'raw_or_source' } elseif ($relative -match 'backup|copy|duplicate') { 'backup_or_duplicate' } else { 'other' }
    }
}
$directoryRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'directory_summary.csv') -NoTypeInformation -Encoding UTF8

$extensionRows = $fileRows | Group-Object extension | Sort-Object Name | ForEach-Object {
    [pscustomobject]@{
        extension = $_.Name
        file_count = $_.Count
        total_size_bytes = [int64](($_.Group | Measure-Object size_bytes -Sum).Sum)
    }
}
$extensionRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'extension_summary.csv') -NoTypeInformation -Encoding UTF8

$archiveRows = [System.Collections.Generic.List[object]]::new()
function Add-ZipEntries {
    param(
        [Parameter(Mandatory = $true)] [System.IO.Stream]$Stream,
        [Parameter(Mandatory = $true)] [string]$ArchivePath,
        [Parameter(Mandatory = $true)] [int]$Depth
    )
    $archive = New-Object IO.Compression.ZipArchive($Stream, [IO.Compression.ZipArchiveMode]::Read, $false)
    try {
        foreach ($entry in $archive.Entries) {
            $isDirectory = $entry.FullName.EndsWith('/')
            $archiveRows.Add([pscustomobject]@{
                archive_path = $ArchivePath
                entry_path = $entry.FullName
                depth = $Depth
                entry_kind = if ($isDirectory) { 'directory' } elseif ($entry.FullName.ToLowerInvariant().EndsWith('.zip')) { 'nested_archive' } else { 'file' }
                uncompressed_size_bytes = [int64]$entry.Length
                compressed_size_bytes = [int64]$entry.CompressedLength
                last_write_time = $entry.LastWriteTime.ToString('o')
            })
            if (-not $isDirectory -and $Depth -lt 3 -and $entry.FullName.ToLowerInvariant().EndsWith('.zip')) {
                $nestedStream = $entry.Open()
                try {
                    Add-ZipEntries -Stream $nestedStream -ArchivePath ($ArchivePath + '::' + $entry.FullName) -Depth ($Depth + 1)
                }
                finally {
                    $nestedStream.Dispose()
                }
            }
        }
    }
    finally {
        $archive.Dispose()
    }
}

foreach ($archiveFile in $files | Where-Object { $_.Extension.ToLowerInvariant() -eq '.zip' }) {
    $relative = Get-RelativePath -Base $Root -FullName $archiveFile.FullName
    $stream = [IO.File]::OpenRead($archiveFile.FullName)
    try {
        Add-ZipEntries -Stream $stream -ArchivePath $relative -Depth 0
    }
    finally {
        $stream.Dispose()
    }
}
$archiveRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'archive_inventory.csv') -NoTypeInformation -Encoding UTF8

$unreadable = @($files | Where-Object { $_.Length -lt 0 } | ForEach-Object { $_.FullName })
$totalBytes = [int64](($files | Measure-Object Length -Sum).Sum)
$progress = [ordered]@{
    raw_data_root = $Root
    root_exists = $true
    root_is_read_only_for_this_audit = $true
    contains_git_repository = (Test-Path -LiteralPath (Join-Path $Root '.git'))
    file_count = $files.Count
    directory_count = $directories.Count + 1
    total_size_bytes = $totalBytes
    total_size_gib = [math]::Round($totalBytes / 1GB, 3)
    archive_file_count = @($files | Where-Object { $_.Extension.ToLowerInvariant() -eq '.zip' }).Count
    nested_archive_entry_count = @($archiveRows | Where-Object { $_.entry_kind -eq 'nested_archive' }).Count
    unreadable_file_count = $unreadable.Count
    unreadable_files = $unreadable
    candidate_directories = @($directoryRows | Where-Object { $_.file_count -gt 0 } | Select-Object -ExpandProperty relative_path)
    scan_stage = 'P1_inventory'
    analysis_status = 'completed'
    generated_at = (Get-Date).ToString('o')
}
$progress | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDir 'progress.json') -Encoding UTF8

[pscustomobject]@{
    root = $Root
    files = $files.Count
    directories = $directories.Count + 1
    bytes = $totalBytes
    gib = [math]::Round($totalBytes / 1GB, 3)
    archives = @($files | Where-Object { $_.Extension.ToLowerInvariant() -eq '.zip' }).Count
    archive_entries = $archiveRows.Count
} | Format-List
