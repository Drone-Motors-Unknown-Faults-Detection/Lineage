param(
    [Parameter(Mandatory = $true)]
    [string]$Root
)

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-ArchiveSummary {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.Stream]$Stream,
        [Parameter(Mandatory = $true)]
        [string]$OuterName,
        [Parameter(Mandatory = $true)]
        [string]$ArchiveName
    )

    $archive = New-Object IO.Compression.ZipArchive(
        $Stream,
        [IO.Compression.ZipArchiveMode]::Read,
        $false
    )
    try {
        $files = @($archive.Entries | Where-Object { $_.Length -gt 0 })
        $extensionCounts = @(
            $files |
                Group-Object { [IO.Path]::GetExtension($_.FullName).ToLowerInvariant() } |
                Sort-Object Count -Descending |
                ForEach-Object { "$($_.Name):$($_.Count)" }
        ) -join ', '
        [pscustomobject]@{
            outer = $OuterName
            archive = $ArchiveName
            entries = $archive.Entries.Count
            files = $files.Count
            uncompressed_bytes = [int64](($files | Measure-Object Length -Sum).Sum)
            extensions = $extensionCounts
            first_files = (($files | Select-Object -First 5 -ExpandProperty FullName) -join ' | ')
            last_files = (($files | Select-Object -Last 5 -ExpandProperty FullName) -join ' | ')
        }
    }
    finally {
        $archive.Dispose()
    }
}

$rows = [System.Collections.Generic.List[object]]::new()
foreach ($outerFile in Get-ChildItem -LiteralPath $Root -Filter '*.zip' -File) {
    $outer = [IO.Compression.ZipFile]::OpenRead($outerFile.FullName)
    try {
        foreach ($nested in $outer.Entries | Where-Object { $_.FullName -like '*/csv.zip' }) {
            $csvStream = $nested.Open()
            try {
                $csvArchive = New-Object IO.Compression.ZipArchive(
                    $csvStream,
                    [IO.Compression.ZipArchiveMode]::Read,
                    $false
                )
                try {
                    foreach ($condition in $csvArchive.Entries | Where-Object { $_.FullName -like '*.zip' }) {
                        $conditionStream = $condition.Open()
                        try {
                            $summary = Get-ArchiveSummary `
                                -Stream $conditionStream `
                                -OuterName $outerFile.Name `
                                -ArchiveName $condition.FullName
                            $rows.Add($summary)
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
    }
    finally {
        $outer.Dispose()
    }
}

$rows | Format-List
