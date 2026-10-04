extends Node
class_name StarCoreClient

signal connection_changed(connected: bool, detail: String)
signal response_received(text: String, voice_started: bool)
signal world_state_received(state: Dictionary)
signal request_failed(kind: String, detail: String)

const DEVICE_ID := "star-world-pc"

var base_url := ""
var pairing_code := ""
var token := ""
var connected := false
var _pairing := false
var _star_root := ""
var _retry_timer: Timer
var _world_timer: Timer

func _ready() -> void:
	_star_root = OS.get_environment("STAR_ROOT")
	if _star_root.is_empty():
		_star_root = ProjectSettings.globalize_path("res://..").simplify_path()

	_retry_timer = Timer.new()
	_retry_timer.wait_time = 1.0
	_retry_timer.autostart = true
	_retry_timer.timeout.connect(_poll_session)
	add_child(_retry_timer)

	_world_timer = Timer.new()
	_world_timer.wait_time = 5.0
	_world_timer.autostart = true
	_world_timer.timeout.connect(_poll_world)
	add_child(_world_timer)

	_poll_session()

func _session_path() -> String:
	return _star_root.path_join("runtime").path_join("oni").path_join("local_session.json")

func _poll_session() -> void:
	if connected or _pairing:
		return
	var path := _session_path()
	if not FileAccess.file_exists(path):
		connection_changed.emit(false, "Inicializando STAR Core…")
		return
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return
	var parsed = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return
	base_url = str(parsed.get("local_url", ""))
	pairing_code = str(parsed.get("pairing_code", ""))
	if base_url.is_empty() or pairing_code.is_empty():
		return
	_pair()

func _pair() -> void:
	_pairing = true
	_request(
		"pair",
		HTTPClient.METHOD_POST,
		"/v1/pair",
		{
			"pairing_code": pairing_code,
			"device_id": DEVICE_ID,
			"name": "STAR World PC",
			"capabilities": ["text", "speech", "world_state", "3d_world"],
			"metadata": {
				"platform": "windows",
				"form_factor": "desktop",
				"app_version": "star-world"
			}
		},
		false
	)

func send_text(text: String, speak: bool = true) -> void:
	var cleaned := text.strip_edges()
	if cleaned.is_empty():
		return
	if not connected:
		request_failed.emit("text", "STAR Core ainda está conectando.")
		return
	_request("text", HTTPClient.METHOD_POST, "/v1/text", {"text": cleaned, "speak": speak}, true)

func set_timezone(timezone_id: String) -> void:
	if not connected:
		request_failed.emit("timezone", "STAR Core ainda está conectando.")
		return
	_request("timezone", HTTPClient.METHOD_POST, "/v1/world/timezone", {"timezone": timezone_id}, true)

func set_scenario(scenario_id: String) -> void:
	if not connected:
		request_failed.emit("scenario", "STAR Core ainda está conectando.")
		return
	_request("scenario", HTTPClient.METHOD_POST, "/v1/world/scenario", {"scenario": scenario_id}, true)

func set_skin(skin_id: String) -> void:
	if not connected:
		request_failed.emit("skin", "STAR Core ainda está conectando.")
		return
	_request("skin", HTTPClient.METHOD_POST, "/v1/world/skin", {"skin": skin_id}, true)

func request_world_state() -> void:
	if connected:
		_request("world", HTTPClient.METHOD_GET, "/v1/world", {}, true)

func _poll_world() -> void:
	request_world_state()

func _request(kind: String, method: int, path: String, payload: Dictionary, authenticated: bool) -> void:
	if base_url.is_empty():
		return
	var request := HTTPRequest.new()
	request.timeout = 25.0
	add_child(request)
	request.request_completed.connect(_on_request_completed.bind(kind, request))

	var headers := PackedStringArray(["Content-Type: application/json"])
	if authenticated:
		headers.append("Authorization: Bearer " + token)
		headers.append("X-STAR-Device: " + DEVICE_ID)

	var body := JSON.stringify(payload) if method != HTTPClient.METHOD_GET else ""
	var error := request.request(base_url + path, headers, method, body)
	if error != OK:
		request.queue_free()
		if kind == "pair":
			_pairing = false
		request_failed.emit(kind, "Falha ao iniciar request: %s" % error)

func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray, kind: String, request: HTTPRequest) -> void:
	request.queue_free()
	if kind == "pair":
		_pairing = false
	if result != HTTPRequest.RESULT_SUCCESS or response_code < 200 or response_code >= 300:
		if kind == "pair":
			_set_connected(false, "Aguardando STAR Core…")
		request_failed.emit(kind, "HTTP %s / result %s" % [response_code, result])
		return

	var body_text := body.get_string_from_utf8()
	var data = JSON.parse_string(body_text) if not body_text.is_empty() else {}
	if not data is Dictionary:
		request_failed.emit(kind, "Resposta JSON inválida.")
		return

	match kind:
		"pair":
			token = str(data.get("token", ""))
			if token.is_empty():
				_set_connected(false, "Pareamento local incompleto.")
				return
			_set_connected(true, "STAR Core conectado")
			request_world_state()
		"text":
			response_received.emit(str(data.get("response", "")), bool(data.get("voice_started", false)))
		"world":
			world_state_received.emit(data)
		"timezone", "scenario", "skin":
			var world = data.get("world", {})
			if world is Dictionary:
				world_state_received.emit(world)

func _set_connected(value: bool, detail: String) -> void:
	connected = value
	connection_changed.emit(value, detail)
