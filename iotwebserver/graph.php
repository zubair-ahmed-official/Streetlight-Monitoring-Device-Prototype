<?php
header('Content-Type: application/json');

$xml_file = __DIR__ . '/logs/data.xml';

if (!file_exists($xml_file)) 
{
echo json_encode(["status" => "error", "message" => "Log file not found"]);
exit;
}

$xml = simplexml_load_file($xml_file);
$entries = $xml->entry;

$last_entry = $entries[count($entries) - 1];

$response_data = [
"light_intensity" => isset($last_entry->light_level) ? (float)$last_entry->light_level : 0,
"temperature" => isset($last_entry->power_level) ? (float)$last_entry->power_level : 0,
"timestamp" => (string)$last_entry->device_timestamp
];

echo json_encode($response_data);

?>
