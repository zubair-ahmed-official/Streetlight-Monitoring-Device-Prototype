<?php
$logFile = __DIR__ . "/logs/data.xml";

if (!file_exists($logFile)) {
    die("Log file not found.");
}

$xml = simplexml_load_file($logFile);

// Initialize stats
$totalEntries = 0;
$abnormalPowerCount = 0;
$highlightedRows = [];

// Parse entries
foreach ($xml->entry as $entry) {
    $totalEntries++;

    $collision = strtolower((string)$entry->collision_state) === "collision";
    $power = floatval($entry->power_level);
    $isAbnormalPower = ($power < 0 || $power > 100);

    if ($isAbnormalPower) {
        $abnormalPowerCount++;
    }

    $highlightedRows[] = [
        "device_timestamp" => (string)$entry->device_timestamp,
        "server_timestamp" => (string)$entry->server_timestamp,
        "light_level" => (string)$entry->light_level,
        "power_level" => (string)$entry->power_level,
        "light_threshold" => isset($entry->light_threshold) ? (string)$entry->light_threshold : "0",
        "collision_state" => (string)$entry->collision_state
    ];
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>IoT Log Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f9f9f9; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; background: white; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr.highlight { background-color: #ffe6e6; }
    </style>
</head>
<body>

<h1>IoT Environmental Log Viewer</h1>

<p><strong>Total Entries:</strong> <?= $totalEntries ?></p>
<p><strong>Abnormal Power Events:</strong> <?= $abnormalPowerCount ?></p>

<h2>Recorded Timestamps</h2>

<table>
    <thead>
        <tr>
            <th>Device Timestamp</th>
            <th>Server Timestamp</th>
            <th>Humidity (Light Level)</th>
            <th>Temperature (Power Level)</th>
            <th>Light Threshold</th>
            <th>Collision State</th>
        </tr>
    </thead>
    <tbody>
        <?php foreach ($highlightedRows as $row): ?>
            <tr class="highlight">
                <td><?= htmlspecialchars($row['device_timestamp']) ?></td>
                <td><?= htmlspecialchars($row['server_timestamp']) ?></td>
                <td><?= htmlspecialchars($row['light_level']) ?>%</td>
                <td><?= htmlspecialchars($row['power_level']) ?>°C</td>
                <td><?= htmlspecialchars($row['light_threshold']) ?>%</td>
                <td><?= htmlspecialchars($row['collision_state']) ?></td>
            </tr>
        <?php endforeach; ?>
    </tbody>
</table>

</body>
</html>
