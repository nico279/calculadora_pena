<?php
// webhook.php

// Siempre responder 200 a Meta
http_response_code(200);

// Leer el cuerpo del POST
$input = file_get_contents('php://input');

// Guardar el contenido en un archivo de log para ver qué llega
file_put_contents('webhook.log', date('Y-m-d H:i:s') . " " . $input . PHP_EOL, FILE_APPEND);

// También puedes imprimirlo en pantalla (opcional)
echo "Webhook recibido ✅";
