<?php
class Metadata {
    public static function xml($dataset)
    {
        $output = '<?xml version="1.0" encoding="UTF-8" ?>';
        $output .= "\n<records>\n";
        
        foreach ($dataset as $row)
        {
            $line = '';
            foreach ($row as $item => $value)
            {
                if ($value != ""){
                    $line .= "<$item><![CDATA[" .
                    utf8_encode(html_entity_decode($value, ENT_QUOTES)) . "]]></$item>";
                }
                else{
                    $line .= "<$item></$item>";
                }
            }
            
            $output .= "<item>$line</item>\n";
        }
        $output .= "</records>\n";
        
        return $output;
    }

    public static function getRecords($pid, $form_list)
    {
	    if ($form_list == null){
	        $form_query = "SELECT DISTINCT form_name FROM redcap_metadata WHERE project_id = ".$pid;
	        $form_res = mysql_query($form_query);
	        $form_list="";
            while($row = mysql_fetch_assoc($form_res)){
	            $form_list.="'" .  $row['form_name'] . "'";
	        }
	    $form_list = str_replace("''", "','", $form_list);
	    }	

        $query = "SELECT field_name, form_name, element_preceding_header as section_header, 
                        if(element_type='textarea','notes',if(element_type='select','dropdown',element_type)) as field_type, 
                        element_label as field_label, element_enum as select_choices_or_calculations, element_note as field_note,
                        if(element_validation_type='int','integer',if(element_validation_type='float','number',element_validation_type)) as text_validation_type_or_show_slider_number, 
                        element_validation_min as text_validation_min, 
                        element_validation_max as text_validation_max, if(field_phi='1','Y','') as identifier, branching_logic, 
                        if(field_req='0','','Y') as required_field, custom_alignment, question_num as question_number
                  FROM redcap_metadata 
                  WHERE project_id = " . $pid . " AND field_name != concat(form_name, '_complete') AND form_name in ($form_list) ORDER BY field_order";
	    $result = mysql_query($query);
        $records = array();
	    while ($row = mysql_fetch_assoc($result)) {
            $records[] = $row;
        }
        return $records;
    }
}
?>
