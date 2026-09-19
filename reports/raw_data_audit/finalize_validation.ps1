param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDir,
    [Parameter(Mandatory = $true)]
    [string]$Root
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$raw = @(Import-Csv (Join-Path $OutputDir 'raw_validation.csv'))
$feature = @(Import-Csv (Join-Path $OutputDir 'feature_validation.csv'))
$conditions = @($raw | ForEach-Object { $_.condition } | Sort-Object -Unique)

$conditionRows = foreach ($condition in $conditions) {
    $rawGroup = @($raw | Where-Object { $_.condition -eq $condition })
    $featureGroup = @($feature | Where-Object { $_.condition -eq $condition })
    $featureColumns = @($featureGroup | ForEach-Object { [int]$_.columns } | Sort-Object -Unique)
    [pscustomobject]@{
        condition = $condition
        raw_file_count = $rawGroup.Count
        raw_class_count = @($rawGroup | ForEach-Object { $_.class_name } | Sort-Object -Unique).Count
        raw_channel_count = @($rawGroup | ForEach-Object { $_.channel } | Sort-Object -Unique).Count
        raw_rows_min = [int](($rawGroup | ForEach-Object { [int]$_.rows } | Measure-Object -Minimum).Minimum)
        raw_rows_max = [int](($rawGroup | ForEach-Object { [int]$_.rows } | Measure-Object -Maximum).Maximum)
        raw_columns = (($rawGroup | ForEach-Object { [int]$_.columns } | Sort-Object -Unique) -join ';')
        raw_malformed_rows = [int](($rawGroup | ForEach-Object { [int]$_.malformed_rows } | Measure-Object -Sum).Sum)
        feature_file_count = $featureGroup.Count
        feature_class_count = @($featureGroup | ForEach-Object { $_.class_name } | Sort-Object -Unique).Count
        feature_rows_min = if ($featureGroup.Count -gt 0) { [int](($featureGroup | ForEach-Object { [int]$_.rows } | Measure-Object -Minimum).Minimum) } else { 0 }
        feature_rows_max = if ($featureGroup.Count -gt 0) { [int](($featureGroup | ForEach-Object { [int]$_.rows } | Measure-Object -Maximum).Maximum) } else { 0 }
        feature_columns = ($featureColumns -join ';')
        feature_non_numeric_fields = [int](($featureGroup | ForEach-Object { [int]$_.non_numeric_fields } | Measure-Object -Sum).Sum)
        raw_status = if ($rawGroup.Count -eq 50 -and @($rawGroup | ForEach-Object { $_.class_name } | Sort-Object -Unique).Count -eq 10 -and @($rawGroup | ForEach-Object { $_.channel } | Sort-Object -Unique).Count -eq 5) { 'raw_present' } else { 'raw_incomplete' }
        feature_status = if ($featureGroup.Count -eq 10 -and $featureColumns.Count -eq 1 -and $featureColumns[0] -eq 105) { '105d_complete' } elseif ($featureGroup.Count -eq 0) { 'missing' } else { 'incomplete_or_invalid' }
    }
}
$conditionRows | Export-Csv (Join-Path $OutputDir 'condition_summary.csv') -NoTypeInformation -Encoding UTF8

$candidateRows = @(
    ($raw | Select-Object source_archive,source_entry,candidate_category,format,size_bytes,rows,columns,condition,class_name,class_role,sampling_rate_hz,confidence,evidence)
    ($feature | Select-Object source_archive,source_entry,candidate_category,format,size_bytes,rows,columns,condition,class_name,class_role,sampling_rate_hz,confidence,evidence)
)
$candidateRows | Export-Csv (Join-Path $OutputDir 'candidate_inventory.csv') -NoTypeInformation -Encoding UTF8

$progress = [ordered]@{
    scan_stage = 'P2_content_validation'
    raw_data_root = $Root
    raw_files_validated = $raw.Count
    feature_clean_files_validated = $feature.Count
    condition_count = $conditions.Count
    conditions = $conditions
    raw_rows_min = [int](($raw | ForEach-Object { [int]$_.rows } | Measure-Object -Minimum).Minimum)
    raw_rows_max = [int](($raw | ForEach-Object { [int]$_.rows } | Measure-Object -Maximum).Maximum)
    raw_columns = (($raw | ForEach-Object { [int]$_.columns } | Sort-Object -Unique) -join ';')
    raw_malformed_rows = [int](($raw | ForEach-Object { [int]$_.malformed_rows } | Measure-Object -Sum).Sum)
    feature_columns = (($feature | ForEach-Object { [int]$_.columns } | Sort-Object -Unique) -join ';')
    feature_non_numeric_fields = [int](($feature | ForEach-Object { [int]$_.non_numeric_fields } | Measure-Object -Sum).Sum)
    formal_raw_status = if ($raw.Count -eq 450 -and $conditions.Count -eq 9) { 'candidate_complete' } else { 'incomplete' }
    formal_feature_status = if ($feature.Count -eq 60) { 'T1_T3_complete_T2_missing' } else { 'incomplete' }
    unsafe_pickle_or_checkpoint_loaded = $false
    raw_source_modified = $false
    analysis_status = 'completed'
    generated_at = (Get-Date).ToString('o')
}
$progress | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $OutputDir 'p2_progress.json') -Encoding UTF8

[pscustomobject]@{
    raw_files = $raw.Count
    feature_clean_files = $feature.Count
    conditions = $conditions.Count
    raw_rows = (($raw | ForEach-Object { $_.rows } | Sort-Object -Unique) -join ',')
    raw_columns = $progress.raw_columns
    malformed_rows = $progress.raw_malformed_rows
    feature_columns = $progress.feature_columns
    feature_non_numeric_fields = $progress.feature_non_numeric_fields
} | Format-List
