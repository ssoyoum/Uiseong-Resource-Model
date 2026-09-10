param([string]$InputDoc = 'docs/submission/sgis-uiseong-excellent-use-case-submission.docx')
$resolvedDocument = (Resolve-Path -LiteralPath $InputDoc).Path
$renderDirectory = Join-Path $env:TEMP 'sgis-submission-render'
[IO.Directory]::CreateDirectory($renderDirectory) | Out-Null
$renderPdf = Join-Path $renderDirectory 'submission.pdf'
$wordApp = New-Object -ComObject Word.Application
$wordApp.Visible = $false
$wordApp.DisplayAlerts = 0
$wordApp.Options.UpdateLinksAtOpen = $false
$wordApp.Options.PrintBackground = $false
try { $wordApp.ActivePrinter = 'Microsoft Print to PDF' } catch { Write-Output 'DEFAULT_PRINTER_RETAINED' }
Write-Output 'WORD_READY'
try {
    $wordDocument = $wordApp.Documents.Open($resolvedDocument, $false, $true)
    Write-Output 'DOCUMENT_OPEN'
    $wordDocument.ExportAsFixedFormat($renderPdf, 17)
    Write-Output 'PDF_EXPORTED'
    $pageCount = $wordDocument.ComputeStatistics(2)
    $wordDocument.Close(0)
    Write-Output "PDF=$renderPdf PAGES=$pageCount"
} finally {
    $wordApp.Quit()
    [Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp) | Out-Null
}
