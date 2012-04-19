<?php
require_once APP_PATH_DOCROOT .'ProjectGeneral/header.php';
$con = $_GET['const'];
unset($_GET['const']);
$path = APP_PATH_WEBROOT_FULL . 'plugins/nbstrn-forms/form/index.php?pid=';
?>
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
    <html>
    <head>
        <link rel="stylesheet" type="text/css" href="src/static/css/messages.css">
        <meta http-equiv="content-type" content="text/html; charset=UTF-8"/>
        <meta http-equiv="refresh" content="0;url=<?php echo $path . $_GET['pid'] . '"/>';?>
      </head>
    <body>
        <div class="warning"><?php echo "The specified constraint \"" . $con .  "\" was not found in the constraint file for your project. Printing form(s) with all fields.";?></div>
    </body>
    </html>
<?php
require_once APP_PATH_DOCROOT .'ProjectGeneral/footer.php';
?>
