<?php
error_reporting(0);

require_once dirname(__FILE__) . DIRECTORY_SEPARATOR . 'config.php';
require_once $redcap_connect_dir . 'redcap_connect.php';

$temp_dir=tempnam(APP_PATH_TEMP, '');

if (file_exists($temp_dir)){
    unlink($temp_dir);
}
mkdir($temp_dir);
chdir($temp_dir);

$INDEX_DIR = dirname(__FILE__) . DIRECTORY_SEPARATOR;
$SRC_DIR = $INDEX_DIR . 'src' . DIRECTORY_SEPARATOR;
if (isset($_GET['pid'])){
    $pid = $_GET['pid'];
    $config_file = $INDEX_DIR . "config_files" . DIRECTORY_SEPARATOR . "const_" . $pid . ".cfg";

    if (file_exists($config_file)){
        $forms = parse_ini_file($config_file, 1);
        $form_arr = array();
        $base_arr = array();
        if(isset($_GET['const'])){
            $con = $_GET['const'];
            $zip_name = $con . '_pdf.zip';
            
            if (array_key_exists('base', $forms)){
                if (array_key_exists('__forms', $forms['base'])){
                        $base_arr = explode(',', str_replace(' ', '', $forms['base']['__forms']));
                        foreach ($base_arr as &$val){
                            $val="'" . $val . "'";
                        }
                }
            }
	        if (array_key_exists($con, $forms)){
	            if (array_key_exists('__forms', $forms[$con])){
		            $form_arr = explode(',',str_replace(' ', '',$forms[$con]['__forms']));
		            foreach ($form_arr as &$val){
			            $val = "'" . $val . "'";
		            }   
	            }
                $combined = array_merge($form_arr, $base_arr);
                $form_print = implode(',', $combined);
            }else{
                require_once 'src' . DIRECTORY_SEPARATOR . 'warning.php';
                exit;
            }
        }else{
            $form_print = null;
            $con = null;
            $zip_name = 'redcap_pdf.zip';
        }
    }else{
        $form_print = null;
        $con = null;
        $zip_name = 'redcap_pdf.zip';
    }
}else{   
    rmdir($temp_dir);
    require_once 'src' . DIRECTORY_SEPARATOR . 'errors.php';
    exit;
}
require_once $INDEX_DIR . 'src' . DIRECTORY_SEPARATOR . 'get_metadata.php';
$xml_data = Metadata::getRecords($pid, $form_print);
$xml_vals = Metadata::xml($xml_data);

$file_name = 'meta.xml';
$fh = fopen($file_name, 'a+') or die("Can't open file");
fwrite($fh, $xml_vals);
fclose($fh);
chmod($temp_dir, 0700);
chmod($file_name, 0400);

//generate the forms from the xml files
if ($con == null){
    $handle = popen($python_path  . 'python ' . $SRC_DIR . 'print_form.py ' . $file_name . ' ' . $zip_name . ' 2>&1', 'r');
}else{
    $handle = popen($python_path . 'python ' . $SRC_DIR . 'print_form.py ' . $file_name . ' ' . $zip_name . ' ' . $con . ' ' . $config_file . ' 2>&1', 'r');
}

$content = stream_get_contents($handle);
if ($content!= null){

    require_once 'src' . DIRECTORY_SEPARATOR . 'python_error.php';

    //Write to the error log
    chdir(APP_PATH_TEMP);
    $today = getdate();
    $error_log = 'pdf_error_log.txt';
    $pid_stmt = 'PID : ' . $pid . "\n";
    $date_stmt =$today['mon'] . "/" . $today['mday'] . "/" . $today['year']. "  " . $today['hours'] . ":" .$today['minutes'] . ":" . $today['seconds'] . "\n";
    $separate = "=======================\n";
    $el = fopen($error_log, 'a+') or die("Can't open file");
    fwrite($el, $pid_stmt);
    fwrite($el, $date_stmt);
    fwrite($el, $separate);
    fwrite($el, $content);
    fwrite($el, "\n\n");
    fclose($el);

    //Cleanup and exit
    chdir($temp_dir);
    foreach(scandir(getcwd()) as $file){
        if(is_dir($file) == false){
            unlink($file);
        }
    }
    chdir($INDEX_DIR);
    rmdir($temp_dir);
    exit;
}

pclose($handle);
unlink($file_name);

header('Pragma: public');
header('Expires: 0');
header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
header('Cache-Control: public');
header('Content-Description: File Transfer');
header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="' . $zip_name . '"');
header('Content-Transfer-Encoding: binary');
header('Content-Length: ' . filesize($zip_name));
header('Connection: Close');
ob_end_flush();
readfile($zip_name);

//clean-up - remove all created files and directory.
foreach (scandir(getcwd()) as $file){
   if (is_dir($file) === false){
        unlink($file);
    }
}
chdir($INDEX_DIR);
rmdir($temp_dir);

?>
