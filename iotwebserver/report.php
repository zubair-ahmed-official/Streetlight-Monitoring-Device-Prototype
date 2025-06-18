<?php
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') 
{
    http_response_code(405);
    echo json_encode(["error" => "Only POST method allowed"]);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);

if (!isset($input['timestamp'], $input['light_level'], $input['power_level'])) 
{
    http_response_code(400);
    echo json_encode(["error" => "Missing required fields"]);
    exit;
}

// Correct folder and file
$logsDir = __DIR__ . '/logs';
if (!file_exists($logsDir)) 
{
    mkdir($logsDir, 0777, true);
}

$xml_file = $logsDir . '/data.xml';

if (!file_exists($xml_file)) 
{
    $xml = new SimpleXMLElement("<data></data>");
} 
else 
{
    $xml = simplexml_load_file($xml_file);
}

$entry = $xml->addChild('entry');
$entry->addChild('device_timestamp', $input['timestamp']);
$entry->addChild('server_timestamp', date('c'));
$entry->addChild('light_level', $input['light_level']);
$entry->addChild('power_level', $input['power_level']);
$entry->addChild('collision_state', $input['collision_state'] ?? 'unknown');
$entry->addChild('power_state', $input['power_state'] ?? 'unknown');

if (isset($input['new_threshold'])) 
{
$entry->addChild('light_threshold', $input['new_threshold']);
}

$xml->asXML($xml_file);

echo json_encode(["status" => "received", "server_time" => time()]);
?>
