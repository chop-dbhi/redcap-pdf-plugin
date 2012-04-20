<?php
    $HtmlPage = new HtmlPage();
    $HtmlPage->PrintHeaderExt();
?>
    <html>
    <head>
    <link rel="stylesheet" type="text/css" href="src/static/css/messages.css">
    </head>
    <body>
    <div class="error">Was not able to get the Project ID. Please contact your REDCap Administrator.</div>
    </body>
    </html>
<?php
    $HtmlPage->PrintFooterExt();
    ob_end_flush();
    exit();
?>
