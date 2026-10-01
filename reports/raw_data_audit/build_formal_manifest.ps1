param(
    [Parameter(Mandatory = $true)]
    [string]$Root,
    [Parameter(Mandatory = $true)]
    [string]$OutputDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$archives = foreach ($file in Get-ChildItem -LiteralPath $Root -Filter '*.zip' -File -Recurse) {
    $hash = Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256
    [pscustomobject]@{
        relative_path = $file.FullName.Substring($Root.TrimEnd('\').Length + 1)
        size_bytes = [int64]$file.Length
        last_write_time = $file.LastWriteTime.ToString('o')
        sha256 = $hash.Hash
    }
}

$conditionArchives = Import-Csv (Join-Path $OutputDir 'archive_inventory.csv') |
    Where-Object { $_.entry_kind -eq 'nested_archive' -and $_.entry_path -match '^csv/T[123]/(6000|8000|11000)rpm\.zip$' } |
    Select-Object archive_path,entry_path,uncompressed_size_bytes,compressed_size_bytes,last_write_time

$featureEntries = Import-Csv (Join-Path $OutputDir 'feature_validation.csv') |
    Select-Object source_archive,source_entry,size_bytes,rows,columns,confidence

$manifest = [ordered]@{
    schema_version = 1
    raw_data_root = $Root
    source_type = 'user_provided_nested_zip_archives'
    outer_archives = $archives
    condition_archives = $conditionArchives
    validated_feature_entries = $featureEntries
    raw_contract = [ordered]@{
        conditions = @('T1/6000rpm','T1/8000rpm','T1/11000rpm','T2/6000rpm','T2/8000rpm','T2/11000rpm','T3/6000rpm','T3/8000rpm','T3/11000rpm')
        files_per_condition = 50
        classes_per_condition = 10
        channels_per_class = 5
        rows_per_raw_csv = 10000
        sampling_rate_hz = 10000
    }
    feature_contract = [ordered]@{
        feature_columns = 105
        clean_feature_files_present = $featureEntries.Count
        conditions_with_clean_features = @($featureEntries | ForEach-Object { ($_.source_entry -split '/')[1] + '/' + ($_.source_entry -split '/')[2] } | Sort-Object -Unique)
        conditions_missing_clean_features = @('T2/6000rpm','T2/8000rpm','T2/11000rpm')
    }
    fingerprint_policy = 'SHA-256 of the three outer archives; nested entry sizes and timestamps are included in the manifest'
    generated_at = (Get-Date).ToString('o')
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $OutputDir 'formal_source_manifest.json') -Encoding UTF8
$archives | Export-Csv (Join-Path $OutputDir 'outer_archive_fingerprint.csv') -NoTypeInformation -Encoding UTF8
