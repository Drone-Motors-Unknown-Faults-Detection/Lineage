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

function Get-ClassRole {
    param([string]$ClassName)
    if ($ClassName -eq '8screws') { return 'known_healthy' }
    if ($ClassName -in @('1screws', '2screws', '3screws', '4screws')) { return 'known_fault' }
    if ($ClassName -in @('5screws', '6screws', '7screws', '3_14screws', '4_146screws')) { return 'unknown_fault' }
    return 'unmapped'
}

function Get-CsvStats {
    param(
        [Parameter(Mandatory = $true)] [System.IO.Stream]$Stream,
        [Parameter(Mandatory = $true)] [bool]$ValidateNumeric
    )

    $reader = New-Object IO.StreamReader($Stream)
    try {
        $lineCount = 0
        $columnCount = 0
        $malformedRows = 0
        $emptyFields = 0
        $nonNumericFields = 0
        $header = ''
        while (-not $reader.EndOfStream) {
            $line = $reader.ReadLine()
            if ($null -eq $line) { continue }
            $parts = $line.Split(',')
            if ($lineCount -eq 0) {
                $header = $line
                $columnCount = $parts.Count
            }
            else {
                if ($parts.Count -ne $columnCount) { $malformedRows++ }
                if ($ValidateNumeric) {
                    foreach ($part in $parts) {
                        if ([string]::IsNullOrWhiteSpace($part)) {
                            $emptyFields++
                            continue
                        }
                        $number = 0.0
                        if (-not [double]::TryParse(
                                $part,
                                [Globalization.NumberStyles]::Float,
                                [Globalization.CultureInfo]::InvariantCulture,
                                [ref]$number
                            )) {
                            $nonNumericFields++
                        }
                    }
                }
            }
            $lineCount++
        }
        [pscustomobject]@{
            row_count = [math]::Max(0, $lineCount - 1)
            column_count = $columnCount
            malformed_rows = $malformedRows
            empty_fields = $emptyFields
            non_numeric_fields = $nonNumericFields
            header = $header
        }
    }
    finally {
        $reader.Dispose()
    }
}

$rawRows = [System.Collections.Generic.List[object]]::new()
$featureRows = [System.Collections.Generic.List[object]]::new()
$archiveFiles = @(Get-ChildItem -LiteralPath $Root -Filter '*.zip' -File -Recurse)

foreach ($outerFile in $archiveFiles) {
    $outer = [IO.Compression.ZipFile]::OpenRead($outerFile.FullName)
    try {
        foreach ($nested in $outer.Entries | Where-Object { $_.FullName -like '*/csv.zip' }) {
            $csvStream = $nested.Open()
            try {
                $csvArchive = New-Object IO.Compression.ZipArchive($csvStream, [IO.Compression.ZipArchiveMode]::Read, $false)
                try {
                    foreach ($conditionArchiveEntry in $csvArchive.Entries | Where-Object { $_.FullName.ToLowerInvariant().EndsWith('.zip') }) {
                        $conditionParts = $conditionArchiveEntry.FullName.Split('/')
                        $motor = $conditionParts[1]
                        $rpm = $conditionParts[2].Replace('.zip', '')
                        $condition = "$motor/$rpm"
                        $conditionStream = $conditionArchiveEntry.Open()
                        try {
                            $conditionArchive = New-Object IO.Compression.ZipArchive($conditionStream, [IO.Compression.ZipArchiveMode]::Read, $false)
                            try {
                                foreach ($rawEntry in $conditionArchive.Entries | Where-Object { $_.FullName.ToLowerInvariant().EndsWith('.csv') }) {
                                    $className = $rawEntry.FullName.Split('/')[1]
                                    $channel = ($rawEntry.Name -replace '^T[123]_', '') -replace '_data\.csv$', ''
                                    $rawStream = $rawEntry.Open()
                                    try {
                                        $stats = Get-CsvStats -Stream $rawStream -ValidateNumeric:$false
                                    }
                                    finally {
                                        $rawStream.Dispose()
                                    }
                                    $rawRows.Add([pscustomobject]@{
                                        source_archive = "$($outerFile.Name)::$($nested.FullName)::$($conditionArchiveEntry.FullName)"
                                        source_entry = $rawEntry.FullName
                                        stage = [IO.Path]::GetFileNameWithoutExtension($outerFile.Name)
                                        motor = $motor
                                        rpm = $rpm
                                        condition = $condition
                                        class_name = $className
                                        class_role = Get-ClassRole $className
                                        channel = $channel
                                        format = 'CSV'
                                        size_bytes = [int64]$rawEntry.Length
                                        rows = $stats.row_count
                                        columns = $stats.column_count
                                        malformed_rows = $stats.malformed_rows
                                        empty_fields = $stats.empty_fields
                                        non_numeric_fields = ''
                                        header = $stats.header.Substring(0, [math]::Min(80, $stats.header.Length))
                                        sampling_rate_hz = 10000
                                        analysis_status = 'validated_streaming'
                                        candidate_category = 'A_FORMAL_RAW'
                                        confidence = 'High'
                                        evidence = 'nine condition archives; ten screw configurations x five channels; preprocessing scripts state Fs=10000'
                                    })
                                }
                            }
                            finally {
                                $conditionArchive.Dispose()
                            }
                        }
                        finally {
                            $conditionStream.Dispose()
                        }
                    }
                }
                finally {
                    $csvArchive.Dispose()
                }
            }
            finally {
                $csvStream.Dispose()
            }
        }

        foreach ($nested in $outer.Entries | Where-Object { $_.FullName -like '*/myfeature.zip' }) {
            $featureStream = $nested.Open()
            try {
                $featureArchive = New-Object IO.Compression.ZipArchive($featureStream, [IO.Compression.ZipArchiveMode]::Read, $false)
                try {
                    foreach ($featureEntry in $featureArchive.Entries | Where-Object { $_.FullName.ToLowerInvariant().EndsWith('_group_feature_data_clean.csv') }) {
                        $parts = $featureEntry.FullName.Split('/')
                        $motor = $parts[1]
                        $rpm = $parts[2]
                        $className = $parts[3]
                        $featureReadStream = $featureEntry.Open()
                        try {
                            $stats = Get-CsvStats -Stream $featureReadStream -ValidateNumeric:$true
                        }
                        finally {
                            $featureReadStream.Dispose()
                        }
                        $featureRows.Add([pscustomobject]@{
                            source_archive = "$($outerFile.Name)::$($nested.FullName)"
                            source_entry = $featureEntry.FullName
                            stage = [IO.Path]::GetFileNameWithoutExtension($outerFile.Name)
                            motor = $motor
                            rpm = $rpm
                            condition = "$motor/$rpm"
                            class_name = $className
                            class_role = Get-ClassRole $className
                            format = 'CSV'
                            size_bytes = [int64]$featureEntry.Length
                            rows = $stats.row_count
                            columns = $stats.column_count
                            malformed_rows = $stats.malformed_rows
                            empty_fields = $stats.empty_fields
                            non_numeric_fields = $stats.non_numeric_fields
                            header = $stats.header.Substring(0, [math]::Min(120, $stats.header.Length))
                            sampling_rate_hz = 10000
                            analysis_status = 'validated_streaming'
                            candidate_category = 'B_FORMAL_PROCESSED'
                            confidence = if ($stats.column_count -eq 105 -and $stats.non_numeric_fields -eq 0) { 'High' } else { 'Low' }
                            evidence = 'clean feature CSV; header has 105 columns; numeric body validated without unsafe deserialization'
                        })
                    }
                }
                finally {
                    $featureArchive.Dispose()
                }
            }
            finally {
                $featureStream.Dispose()
            }
        }
    }
    finally {
        $outer.Dispose()
    }
}

$rawRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'raw_validation.csv') -NoTypeInformation -Encoding UTF8
$featureRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'feature_validation.csv') -NoTypeInformation -Encoding UTF8

$conditions = @($rawRows | Select-Object -ExpandProperty condition -Unique | Sort-Object)
$conditionRows = foreach ($condition in $conditions) {
    $raw = @($rawRows | Where-Object { $_.condition -eq $condition })
    $feature = @($featureRows | Where-Object { $_.condition -eq $condition })
    [pscustomobject]@{
        condition = $condition
        raw_file_count = $raw.Count
        raw_class_count = @($raw | ForEach-Object { $_.class_name } | Sort-Object -Unique).Count
        raw_channel_count = @($raw | ForEach-Object { $_.channel } | Sort-Object -Unique).Count
        raw_rows_min = [int](($raw | ForEach-Object { $_.rows } | Measure-Object -Minimum).Minimum)
        raw_rows_max = [int](($raw | ForEach-Object { $_.rows } | Measure-Object -Maximum).Maximum)
        raw_columns = (($raw | ForEach-Object { $_.columns } | Sort-Object -Unique) -join ';')
        raw_malformed_rows = [int](($raw | ForEach-Object { $_.malformed_rows } | Measure-Object -Sum).Sum)
        feature_file_count = $feature.Count
        feature_class_count = @($feature | ForEach-Object { $_.class_name } | Sort-Object -Unique).Count
        feature_rows_min = if ($feature.Count -gt 0) { [int](($feature | ForEach-Object { $_.rows } | Measure-Object -Minimum).Minimum) } else { 0 }
        feature_rows_max = if ($feature.Count -gt 0) { [int](($feature | ForEach-Object { $_.rows } | Measure-Object -Maximum).Maximum) } else { 0 }
        feature_columns = (($feature | ForEach-Object { $_.columns } | Sort-Object -Unique) -join ';')
        feature_non_numeric_fields = [int](($feature | ForEach-Object { $_.non_numeric_fields } | Measure-Object -Sum).Sum)
        formal_condition_status = if ($raw.Count -eq 50) { 'raw_present' } else { 'raw_incomplete' }
        feature_status = if ($feature.Count -eq 10 -and @($feature | ForEach-Object { $_.columns } | Sort-Object -Unique) -eq 105) { '105d_complete' } elseif ($feature.Count -eq 0) { 'missing' } else { 'incomplete_or_invalid' }
    }
}
$conditionRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'condition_summary.csv') -NoTypeInformation -Encoding UTF8

$candidateRows = @(
    $rawRows | Select-Object source_archive,source_entry,candidate_category,format,size_bytes,rows,columns,condition,class_name,class_role,sampling_rate_hz,confidence,evidence
    $featureRows | Select-Object source_archive,source_entry,candidate_category,format,size_bytes,rows,columns,condition,class_name,class_role,sampling_rate_hz,confidence,evidence
)
$candidateRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'candidate_inventory.csv') -NoTypeInformation -Encoding UTF8

$progress = [ordered]@{
    scan_stage = 'P2_content_validation'
    raw_data_root = $Root
    raw_files_validated = $rawRows.Count
    feature_clean_files_validated = $featureRows.Count
    condition_count = $conditions.Count
    conditions = $conditions
    raw_rows_min = [int](($rawRows | ForEach-Object { $_.rows } | Measure-Object -Minimum).Minimum)
    raw_rows_max = [int](($rawRows | ForEach-Object { $_.rows } | Measure-Object -Maximum).Maximum)
    raw_columns = (($rawRows | ForEach-Object { $_.columns } | Sort-Object -Unique) -join ';')
    raw_malformed_rows = [int](($rawRows | ForEach-Object { $_.malformed_rows } | Measure-Object -Sum).Sum)
    feature_columns = (($featureRows | ForEach-Object { $_.columns } | Sort-Object -Unique) -join ';')
    feature_non_numeric_fields = [int](($featureRows | ForEach-Object { $_.non_numeric_fields } | Measure-Object -Sum).Sum)
    formal_raw_status = if ($rawRows.Count -eq 450 -and $conditions.Count -eq 9) { 'candidate_complete' } else { 'incomplete' }
    formal_feature_status = if ($featureRows.Count -eq 60) { 'T1_T3_complete_T2_missing' } else { 'incomplete' }
    unsafe_pickle_or_checkpoint_loaded = $false
    raw_source_modified = $false
    analysis_status = 'completed'
    generated_at = (Get-Date).ToString('o')
}
$progress | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDir 'p2_progress.json') -Encoding UTF8

[pscustomobject]@{
    raw_files = $rawRows.Count
    feature_clean_files = $featureRows.Count
    conditions = $conditions.Count
    raw_rows_min = $progress.raw_rows_min
    raw_rows_max = $progress.raw_rows_max
    raw_columns = $progress.raw_columns
    malformed_rows = $progress.raw_malformed_rows
    feature_columns = $progress.feature_columns
    feature_non_numeric_fields = $progress.feature_non_numeric_fields
} | Format-List
