extends Node3D

const MODE_MENU := "menu"
const MODE_HUB := "hub"
const MODE_HOUSE := "house"

# Arquivos canônicos já existentes em D:\STAR\SKINS.
# Não são copiados para star_world: o seletor reutiliza a fonte visual atual.
const SKIN_REFERENCE_FILES := {
	"casual": "base.jpeg",
	"cypher_system": "system.jpeg",
	"rock_simple": "legofshopping.jpeg",
	"brazil": "brazil.jpeg",
	"elegant_blue": "dress1.jpeg",
	"rich_red": "redpaty.jpeg",
}

var mode := MODE_MENU
var universe_root: Node3D
var content_root: Node3D
var camera: Camera3D
var world_environment: WorldEnvironment
var environment: Environment
var sky_material: ProceduralSkyMaterial
var sun: DirectionalLight3D
var core_client: StarCoreClient

var ui_root: Control
var menu_ui: Control
var hud_ui: Control
var hub_ui_blockers: Array[Control] = []
var settings_panel: Control
var chat_panel: Control
var wardrobe_panel: Control
var tv_panel: Control
var modal_panel: Control

var core_status_label: Label
var hud_title_label: Label
var time_label: Label
var crosshair_label: Label
var interaction_button: Button
var status_label: Label
var hud_back_button: Button
var hub_chat_button: Button
var chat_messages: VBoxContainer
var chat_scroll: ScrollContainer
var chat_input: LineEdit
var timezone_input: LineEdit
var settings_status: Label
var tv_status: Label
var wardrobe_info: Label
var equip_button: Button
var wardrobe_preview_avatar: Node3D
var wardrobe_preview_viewport: SubViewport
var _skin_reference_cache := {}
var _wardrobe_skin_thumbnails := {}
var _wardrobe_thumbnails_loaded := false

var menu_star: CrystalStar3D
var player: StarWorldPlayer
var star_avatar: Node3D
var hub_islands := {}
var hub_input_armed := false
var hub_angle := 0.18
var hub_distance := 31.0
var hub_height := 15.5

var current_world := {}
var current_skin := "cypher_system"
var preview_skin := "cypher_system"
var pending_response_target := "chat"
var first_house_entry := true

func _ready() -> void:
	_ensure_input_actions()
	_build_universe()
	_build_ui()

	core_client = StarCoreClient.new()
	core_client.connection_changed.connect(_on_connection_changed)
	core_client.response_received.connect(_on_response_received)
	core_client.world_state_received.connect(_on_world_state_received)
	core_client.request_failed.connect(_on_request_failed)
	add_child(core_client)

	_show_menu()
	# Diagnóstico automatizado da engine: usado por testes/CI local, nunca no fluxo normal.
	if OS.get_environment("STAR_WORLD_SMOKE") == "1":
		call_deferred("_run_smoke_sequence")

func _process(delta: float) -> void:
	if mode == MODE_HUB and not _has_modal():
		var rotate_axis := Input.get_axis("move_left", "move_right")
		var zoom_axis := Input.get_axis("move_forward", "move_back")
		hub_angle += rotate_axis * delta * 0.55
		hub_distance = clamp(hub_distance + zoom_axis * delta * 8.0, 21.0, 42.0)
		_update_hub_camera()

	# O preview do roupeiro permanece frontal para combinar com as referências
	# de turnaround. Rotação manual poderá ser adicionada depois sem afetar o rig.

	if mode == MODE_HOUSE and player and is_instance_valid(player):
		_update_interaction_prompt()
		if star_avatar and is_instance_valid(star_avatar):
			var target := player.global_position
			target.y = star_avatar.global_position.y + 1.0
			var local_target := star_avatar.to_local(target)
			if local_target.length() > 1.0:
				var target_angle := atan2(local_target.x, local_target.z)
				star_avatar.rotation.y = lerp_angle(star_avatar.rotation.y, star_avatar.rotation.y + target_angle, min(1.0, delta * 1.6))

func _input(event: InputEvent) -> void:
	if mode != MODE_HUB or _has_modal():
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if not hub_input_armed:
			return
		if _hub_event_over_ui(event.position):
			return
		_pick_hub_island(event.position)

func _hub_event_over_ui(position: Vector2) -> bool:
	for control in hub_ui_blockers:
		if control and is_instance_valid(control) and control.visible and control.get_global_rect().has_point(position):
			return true
	return false

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if _has_modal():
			_close_all_modals()
			return
		if mode == MODE_HOUSE and player:
			if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
				player.set_active(false)
			else:
				player.set_active(true)
			return

	if mode == MODE_HOUSE and event.is_action_pressed("interact") and not _has_modal():
		_interact_house()
		return

func _ensure_input_actions() -> void:
	_add_key_action("move_forward", KEY_W)
	_add_key_action("move_back", KEY_S)
	_add_key_action("move_left", KEY_A)
	_add_key_action("move_right", KEY_D)
	_add_key_action("sprint", KEY_SHIFT)
	_add_key_action("jump", KEY_SPACE)
	_add_key_action("interact", KEY_E)

func _add_key_action(action: StringName, keycode: Key) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)
	if InputMap.action_get_events(action).is_empty():
		var event := InputEventKey.new()
		event.physical_keycode = keycode
		InputMap.action_add_event(action, event)

func _build_universe() -> void:
	universe_root = Node3D.new()
	universe_root.name = "Universe"
	add_child(universe_root)

	content_root = Node3D.new()
	content_root.name = "SceneContent"
	universe_root.add_child(content_root)

	StarWorldBuilder.build_nebula(universe_root, 7)
	StarWorldBuilder.build_starfield(universe_root, 760)

	camera = Camera3D.new()
	camera.name = "WorldCamera"
	camera.current = true
	camera.fov = 62.0
	add_child(camera)

	world_environment = WorldEnvironment.new()
	environment = Environment.new()
	environment.background_mode = Environment.BG_SKY
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	environment.ambient_light_energy = 0.72
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.ssao_enabled = true
	environment.ssao_radius = 1.8
	environment.ssao_intensity = 1.25
	environment.glow_enabled = true
	environment.glow_intensity = 0.72
	environment.glow_bloom = 0.08

	var sky := Sky.new()
	sky_material = ProceduralSkyMaterial.new()
	sky.sky_material = sky_material
	environment.sky = sky
	world_environment.environment = environment
	add_child(world_environment)

	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52, -28, 0)
	sun.light_energy = 1.1
	sun.shadow_enabled = true
	add_child(sun)

	_apply_day_phase("night")

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 10
	add_child(layer)

	ui_root = Control.new()
	ui_root.name = "UIShell"
	_full_rect(ui_root)
	layer.add_child(ui_root)

	_build_menu_ui()
	_build_hud_ui()
	_build_settings_ui()
	_build_chat_ui()
	_build_wardrobe_ui()
	_build_tv_ui()

func _build_menu_ui() -> void:
	menu_ui = Control.new()
	_full_rect(menu_ui)
	ui_root.add_child(menu_ui)

	var center := CenterContainer.new()
	_full_rect(center)
	menu_ui.add_child(center)

	var box := VBoxContainer.new()
	box.custom_minimum_size = Vector2(440, 510)
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_theme_constant_override("separation", 14)
	center.add_child(box)

	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(1, 136)
	box.add_child(spacer)

	var title := Label.new()
	title.text = "STAR"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_color_override("font_color", StarTheme.TEXT)
	title.add_theme_font_size_override("font_size", 52)
	box.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "System for Thought, Analysis and Response"
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.add_theme_color_override("font_color", StarTheme.LILAC)
	subtitle.add_theme_font_size_override("font_size", 15)
	box.add_child(subtitle)

	var core_status := Label.new()
	core_status.text = "Inicializando STAR Core…"
	core_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	core_status.add_theme_color_override("font_color", StarTheme.MUTED)
	core_status.add_theme_font_size_override("font_size", 13)
	box.add_child(core_status)
	core_status_label = core_status

	var menu_gap := Control.new()
	menu_gap.custom_minimum_size = Vector2(1, 28)
	box.add_child(menu_gap)

	var start := _make_button("INICIAR", StarTheme.LILAC)
	start.custom_minimum_size = Vector2(360, 58)
	start.pressed.connect(_start_world_transition)
	box.add_child(start)

	var settings := _make_button("CONFIGURAÇÕES", StarTheme.VIOLET)
	settings.custom_minimum_size = Vector2(360, 54)
	settings.pressed.connect(_open_settings)
	box.add_child(settings)

	var exit := _make_button("SAIR", StarTheme.BLUE)
	exit.custom_minimum_size = Vector2(360, 50)
	exit.pressed.connect(func(): get_tree().quit())
	box.add_child(exit)

	var version := Label.new()
	version.text = "STAR  •  COSMIC CRYSTAL"
	version.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	version.add_theme_color_override("font_color", Color(0.62, 0.58, 0.74, 0.85))
	version.add_theme_font_size_override("font_size", 11)
	box.add_child(version)

func _build_hud_ui() -> void:
	hud_ui = Control.new()
	_full_rect(hud_ui)
	hud_ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_root.add_child(hud_ui)

	hub_ui_blockers.clear()

	# Hora mínima no canto superior esquerdo. Sem painel gigante.
	time_label = Label.new()
	_anchor_rect(time_label, 0.018, 0.018, 0.28, 0.062)
	time_label.text = "--:--"
	time_label.add_theme_color_override("font_color", Color(0.93, 0.95, 1.0, 0.94))
	time_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.75))
	time_label.add_theme_constant_override("shadow_offset_x", 1)
	time_label.add_theme_constant_override("shadow_offset_y", 2)
	time_label.add_theme_font_size_override("font_size", 17)
	hud_ui.add_child(time_label)

	# Mantido apenas como estado interno para não quebrar fluxos legados.
	hud_title_label = Label.new()
	hud_title_label.visible = false
	hud_ui.add_child(hud_title_label)

	# Mira central discreta.
	crosshair_label = Label.new()
	_anchor_rect(crosshair_label, 0.487, 0.474, 0.513, 0.526)
	crosshair_label.text = "+"
	crosshair_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	crosshair_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	crosshair_label.add_theme_color_override("font_color", Color(0.92, 0.96, 1.0, 0.92))
	crosshair_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	crosshair_label.add_theme_constant_override("shadow_offset_x", 1)
	crosshair_label.add_theme_constant_override("shadow_offset_y", 1)
	crosshair_label.add_theme_font_size_override("font_size", 23)
	crosshair_label.visible = false
	crosshair_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud_ui.add_child(crosshair_label)

	# Mensagens de estado transitórias sem tarja.
	status_label = Label.new()
	_anchor_rect(status_label, 0.30, 0.035, 0.70, 0.075)
	status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	status_label.add_theme_color_override("font_color", Color(0.90, 0.92, 1.0, 0.92))
	status_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	status_label.add_theme_constant_override("shadow_offset_x", 1)
	status_label.add_theme_constant_override("shadow_offset_y", 2)
	status_label.add_theme_font_size_override("font_size", 13)
	status_label.visible = false
	status_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud_ui.add_child(status_label)

	# Botão de interação aparece somente quando há alvo real.
	interaction_button = _make_button("E  ·  INTERAGIR", StarTheme.CYAN)
	_anchor_rect(interaction_button, 0.395, 0.865, 0.605, 0.925)
	interaction_button.add_theme_font_size_override("font_size", 14)
	interaction_button.visible = false
	interaction_button.pressed.connect(_interact_house)
	hud_ui.add_child(interaction_button)
	hub_ui_blockers.append(interaction_button)

	# Navegação mínima: apenas seta discreta.
	hud_back_button = _make_button("←", StarTheme.VIOLET)
	_anchor_rect(hud_back_button, 0.018, 0.915, 0.055, 0.965)
	hud_back_button.add_theme_font_size_override("font_size", 18)
	hud_back_button.pressed.connect(_navigate_back)
	hud_ui.add_child(hud_back_button)
	hub_ui_blockers.append(hud_back_button)

	# Chat direto no Hub preservado como ícone mínimo. Na Casa, fale com a STAR Bot.
	hub_chat_button = _make_button("✦", StarTheme.CYAN)
	_anchor_rect(hub_chat_button, 0.945, 0.915, 0.982, 0.965)
	hub_chat_button.add_theme_font_size_override("font_size", 17)
	hub_chat_button.pressed.connect(_open_chat)
	hud_ui.add_child(hub_chat_button)
	hub_ui_blockers.append(hub_chat_button)

	hud_ui.visible = false
func _build_settings_ui() -> void:
	settings_panel = Control.new()
	_full_rect(settings_panel)
	settings_panel.visible = false
	ui_root.add_child(settings_panel)

	var dim := ColorRect.new()
	_full_rect(dim)
	dim.color = Color(0.01, 0.005, 0.03, 0.52)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	settings_panel.add_child(dim)

	var panel := PanelContainer.new()
	_anchor_rect(panel, 0.18, 0.11, 0.82, 0.89)
	panel.add_theme_stylebox_override("panel", StarTheme.glass_style(Color(0.035,0.022,0.075,0.94), StarTheme.VIOLET, 18, 1))
	settings_panel.add_child(panel)

	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 13)
	panel.add_child(layout)

	var header := HBoxContainer.new()
	layout.add_child(header)
	var title := Label.new()
	title.text = "CONFIGURAÇÕES"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_color_override("font_color", StarTheme.TEXT)
	title.add_theme_font_size_override("font_size", 26)
	header.add_child(title)
	var close := _make_button("FECHAR", StarTheme.VIOLET)
	close.pressed.connect(_close_all_modals)
	header.add_child(close)

	var divider := HSeparator.new()
	layout.add_child(divider)

	var world_title := Label.new()
	world_title.text = "MUNDO"
	world_title.add_theme_color_override("font_color", StarTheme.LILAC)
	world_title.add_theme_font_size_override("font_size", 18)
	layout.add_child(world_title)

	var world_desc := Label.new()
	world_desc.text = "O mesmo relógio e o mesmo céu são compartilhados por Hub, Casa e futuras ilhas."
	world_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	world_desc.add_theme_color_override("font_color", StarTheme.MUTED)
	layout.add_child(world_desc)

	var tz_row := HBoxContainer.new()
	tz_row.add_theme_constant_override("separation", 10)
	layout.add_child(tz_row)
	var tz_label := Label.new()
	tz_label.text = "Fuso horário IANA"
	tz_label.custom_minimum_size = Vector2(170, 42)
	tz_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	tz_label.add_theme_color_override("font_color", StarTheme.TEXT)
	tz_row.add_child(tz_label)
	timezone_input = LineEdit.new()
	timezone_input.placeholder_text = "local ou America/Sao_Paulo"
	timezone_input.text = "local"
	timezone_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	timezone_input.add_theme_color_override("font_color", StarTheme.TEXT)
	tz_row.add_child(timezone_input)
	var apply_tz := _make_button("APLICAR", StarTheme.CYAN)
	apply_tz.pressed.connect(func(): core_client.set_timezone(timezone_input.text))
	tz_row.add_child(apply_tz)

	var scenario_row := HBoxContainer.new()
	layout.add_child(scenario_row)
	var scenario_label := Label.new()
	scenario_label.text = "Cenário cósmico"
	scenario_label.custom_minimum_size = Vector2(170, 42)
	scenario_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	scenario_label.add_theme_color_override("font_color", StarTheme.TEXT)
	scenario_row.add_child(scenario_label)
	var scenario := OptionButton.new()
	scenario.add_item("Cosmic Crystal")
	scenario.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scenario_row.add_child(scenario)

	var voice_title := Label.new()
	voice_title.text = "VOZ / CORE"
	voice_title.add_theme_color_override("font_color", StarTheme.LILAC)
	voice_title.add_theme_font_size_override("font_size", 18)
	layout.add_child(voice_title)
	var voice_desc := Label.new()
	voice_desc.text = "A STAR WORLD usa o mesmo Core, memória, MIND e voz local. Chatterbox, Piper e SAPI continuam no backend Python; nenhum segundo cérebro é criado no 3D."
	voice_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	voice_desc.add_theme_color_override("font_color", StarTheme.MUTED)
	layout.add_child(voice_desc)

	settings_status = Label.new()
	settings_status.text = "Aguardando STAR Core…"
	settings_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	settings_status.add_theme_color_override("font_color", StarTheme.WARN)
	layout.add_child(settings_status)

func _build_chat_ui() -> void:
	chat_panel = Control.new()
	_full_rect(chat_panel)
	chat_panel.visible = false
	chat_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_root.add_child(chat_panel)

	# Blur somente no painel lateral. A cena 3D continua renderizando ao fundo.
	var blur := ColorRect.new()
	blur.name = "ChatBlur"
	_anchor_rect(blur, 0.605, 0.018, 0.988, 0.982)
	blur.color = Color.WHITE
	blur.mouse_filter = Control.MOUSE_FILTER_STOP
	var blur_shader := Shader.new()
	blur_shader.code = """
shader_type canvas_item;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear_mipmap;
void fragment() {
	vec4 scene = textureLod(screen_texture, SCREEN_UV, 3.6);
	vec3 tint = vec3(0.025, 0.030, 0.060);
	vec3 mixed = mix(scene.rgb, tint, 0.46);
	COLOR = vec4(mixed, 0.96);
}
"""
	var blur_material := ShaderMaterial.new()
	blur_material.shader = blur_shader
	blur.material = blur_material
	chat_panel.add_child(blur)

	var panel := PanelContainer.new()
	panel.name = "ChatSidePanel"
	_anchor_rect(panel, 0.615, 0.028, 0.978, 0.972)
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.add_theme_stylebox_override("panel", StarTheme.glass_style(Color(0.02,0.025,0.055,0.54), Color(0.38,0.50,0.82,0.62), 16, 1))
	chat_panel.add_child(panel)

	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 10)
	panel.add_child(layout)

	var header := HBoxContainer.new()
	layout.add_child(header)
	var icon := Label.new()
	icon.text = "✦  STAR"
	icon.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	icon.add_theme_color_override("font_color", StarTheme.CRYSTAL)
	icon.add_theme_font_size_override("font_size", 20)
	header.add_child(icon)

	var close := _make_button("×", StarTheme.VIOLET)
	close.custom_minimum_size = Vector2(42, 38)
	close.pressed.connect(_close_all_modals)
	header.add_child(close)

	chat_scroll = ScrollContainer.new()
	chat_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	chat_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	layout.add_child(chat_scroll)

	chat_messages = VBoxContainer.new()
	chat_messages.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	chat_messages.add_theme_constant_override("separation", 8)
	chat_scroll.add_child(chat_messages)

	_add_chat_message("STAR", "Estou aqui. A cena continua ao fundo enquanto conversamos.", false)

	var input_row := HBoxContainer.new()
	input_row.add_theme_constant_override("separation", 8)
	layout.add_child(input_row)

	chat_input = LineEdit.new()
	chat_input.placeholder_text = "Converse com a STAR…"
	chat_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	chat_input.add_theme_color_override("font_color", StarTheme.TEXT)
	chat_input.text_submitted.connect(func(_value): _send_chat())
	input_row.add_child(chat_input)

	var send := _make_button("ENVIAR", StarTheme.CYAN)
	send.pressed.connect(_send_chat)
	input_row.add_child(send)
func _build_wardrobe_ui() -> void:
	wardrobe_panel = Control.new()
	_full_rect(wardrobe_panel)
	wardrobe_panel.visible = false
	ui_root.add_child(wardrobe_panel)

	var dim := ColorRect.new()
	_full_rect(dim)
	dim.color = Color(0.01, 0.005, 0.03, 0.42)
	wardrobe_panel.add_child(dim)

	var panel := PanelContainer.new()
	_anchor_rect(panel, 0.10, 0.08, 0.90, 0.92)
	panel.add_theme_stylebox_override("panel", StarTheme.glass_style(Color(0.035,0.022,0.080,0.91), StarTheme.BLUE, 20, 1))
	wardrobe_panel.add_child(panel)

	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 12)
	panel.add_child(layout)

	var header := HBoxContainer.new()
	layout.add_child(header)
	var title := Label.new()
	title.text = "APARÊNCIA DA STAR"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_color_override("font_color", StarTheme.TEXT)
	title.add_theme_font_size_override("font_size", 25)
	header.add_child(title)
	var close := _make_button("VOLTAR", StarTheme.VIOLET)
	close.pressed.connect(_close_all_modals)
	header.add_child(close)

	var main_row := HBoxContainer.new()
	main_row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	main_row.add_theme_constant_override("separation", 20)
	layout.add_child(main_row)

	var info_panel := PanelContainer.new()
	info_panel.custom_minimum_size = Vector2(430, 0)
	info_panel.add_theme_stylebox_override("panel", StarTheme.glass_style(StarTheme.PANEL_SOFT, Color(0.35,0.28,0.58,0.65), 16, 1))
	main_row.add_child(info_panel)

	var preview_column := VBoxContainer.new()
	preview_column.add_theme_constant_override("separation", 8)
	info_panel.add_child(preview_column)

	var preview_frame := PanelContainer.new()
	preview_frame.custom_minimum_size = Vector2(400, 405)
	preview_frame.size_flags_vertical = Control.SIZE_EXPAND_FILL
	preview_frame.add_theme_stylebox_override("panel", StarTheme.glass_style(Color(0.018,0.012,0.045,0.96), Color(0.36,0.42,0.70,0.72), 12, 1))
	preview_column.add_child(preview_frame)

	var preview_container := SubViewportContainer.new()
	preview_container.stretch = true
	preview_container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	preview_frame.add_child(preview_container)

	wardrobe_preview_viewport = SubViewport.new()
	wardrobe_preview_viewport.size = Vector2i(512, 640)
	wardrobe_preview_viewport.transparent_bg = false
	wardrobe_preview_viewport.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
	wardrobe_preview_viewport.own_world_3d = true
	preview_container.add_child(wardrobe_preview_viewport)

	var preview_environment := WorldEnvironment.new()
	var preview_env := Environment.new()
	preview_env.background_mode = Environment.BG_COLOR
	preview_env.background_color = Color("#080515")
	preview_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	preview_env.ambient_light_color = Color("#D7D0EE")
	preview_env.ambient_light_energy = 1.18
	preview_environment.environment = preview_env
	wardrobe_preview_viewport.add_child(preview_environment)

	var preview_root := Node3D.new()
	preview_root.name = "WardrobePreviewWorld"
	wardrobe_preview_viewport.add_child(preview_root)

	var preview_camera := Camera3D.new()
	preview_camera.position = Vector3(0.0, 1.15, 4.6)
	preview_camera.fov = 38.0
	preview_camera.current = true
	preview_root.add_child(preview_camera)
	preview_camera.look_at(Vector3(0, 0.95, 0), Vector3.UP)

	var preview_key := DirectionalLight3D.new()
	preview_key.rotation_degrees = Vector3(-35, -28, 0)
	preview_key.light_color = Color("#E8E1FF")
	preview_key.light_energy = 1.75
	preview_root.add_child(preview_key)

	var preview_rim := OmniLight3D.new()
	preview_rim.position = Vector3(-1.3, 1.3, 1.2)
	preview_rim.light_color = Color("#7255E8")
	preview_rim.light_energy = 1.45
	preview_rim.omni_range = 5.0
	preview_root.add_child(preview_rim)

	wardrobe_preview_avatar = StarWorldBuilder.build_star_avatar(preview_root, current_skin)
	wardrobe_preview_avatar.position = Vector3(0, -0.15, 0)

	var preview_pedestal := MeshInstance3D.new()
	var pedestal_mesh := CylinderMesh.new()
	pedestal_mesh.top_radius = 0.72
	pedestal_mesh.bottom_radius = 0.88
	pedestal_mesh.height = 0.18
	pedestal_mesh.radial_segments = 40
	preview_pedestal.mesh = pedestal_mesh
	preview_pedestal.position = Vector3(0, -0.08, 0)
	preview_pedestal.material_override = StarWorldBuilder.material(Color("#1F1838"), Color("#7657C9"), 1.1, 0.12, 0.26)
	preview_root.add_child(preview_pedestal)

	wardrobe_info = Label.new()
	wardrobe_info.text = "Selecione um acabamento. A mesma STAR Bot permanece; paleta, luzes e materiais visuais mudam."
	wardrobe_info.custom_minimum_size = Vector2(0, 108)
	wardrobe_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	wardrobe_info.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	wardrobe_info.add_theme_color_override("font_color", StarTheme.TEXT)
	wardrobe_info.add_theme_font_size_override("font_size", 15)
	preview_column.add_child(wardrobe_info)

	var grid := GridContainer.new()
	grid.columns = 2
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 10)
	main_row.add_child(grid)

	var skins := [
		["casual", "CASUAL"],
		["cypher_system", "CYPHER SYSTEM"],
		["rock_simple", "ROCK SIMPLE"],
		["brazil", "BRASIL"],
		["elegant_blue", "ELEGANT BLUE"],
		["rich_red", "RICH RED"],
	]
	for item in skins:
		var skin_id: String = item[0]
		var display_name: String = item[1]
		var card := PanelContainer.new()
		card.custom_minimum_size = Vector2(230, 170)
		card.add_theme_stylebox_override("panel", StarTheme.glass_style(Color(0.055,0.035,0.115,0.82), Color(0.26,0.34,0.58,0.70), 12, 1))
		grid.add_child(card)

		var card_box := VBoxContainer.new()
		card_box.add_theme_constant_override("separation", 6)
		card.add_child(card_box)

		var thumbnail := TextureRect.new()
		thumbnail.custom_minimum_size = Vector2(210, 104)
		thumbnail.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		thumbnail.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		thumbnail.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card_box.add_child(thumbnail)
		_wardrobe_skin_thumbnails[skin_id] = thumbnail

		var button := _make_button(display_name, StarTheme.BLUE)
		button.custom_minimum_size = Vector2(210, 45)
		button.pressed.connect(_preview_wardrobe_skin.bind(skin_id, display_name))
		card_box.add_child(button)

	var bottom := HBoxContainer.new()
	layout.add_child(bottom)
	var note := Label.new()
	note.text = "PREVIEW não salva. EQUIPAR persiste no mesmo user_settings.json local."
	note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	note.add_theme_color_override("font_color", StarTheme.MUTED)
	bottom.add_child(note)
	equip_button = _make_button("EQUIPAR", StarTheme.CYAN)
	equip_button.pressed.connect(_equip_preview_skin)
	bottom.add_child(equip_button)

func _build_tv_ui() -> void:
	tv_panel = Control.new()
	_full_rect(tv_panel)
	tv_panel.visible = false
	ui_root.add_child(tv_panel)

	var dim := ColorRect.new()
	_full_rect(dim)
	dim.color = Color(0.005, 0.008, 0.02, 0.52)
	tv_panel.add_child(dim)

	var panel := PanelContainer.new()
	_anchor_rect(panel, 0.15, 0.15, 0.85, 0.85)
	panel.add_theme_stylebox_override("panel", StarTheme.glass_style(Color(0.018,0.028,0.060,0.94), StarTheme.BLUE, 18, 1))
	tv_panel.add_child(panel)

	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 16)
	panel.add_child(layout)
	var header := HBoxContainer.new()
	layout.add_child(header)
	var title := Label.new()
	title.text = "STAR TV"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_color_override("font_color", StarTheme.TEXT)
	title.add_theme_font_size_override("font_size", 26)
	header.add_child(title)
	var close := _make_button("FECHAR", StarTheme.BLUE)
	close.pressed.connect(_close_all_modals)
	header.add_child(close)

	var categories := HBoxContainer.new()
	categories.add_theme_constant_override("separation", 10)
	layout.add_child(categories)
	for name in ["HOME", "MEDIA", "FAVORITOS", "PESQUISA"]:
		var category := _make_button(name, StarTheme.BLUE)
		category.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		category.pressed.connect(_tv_category.bind(name))
		categories.add_child(category)

	tv_status = Label.new()
	tv_status.text = "A TV usa o mesmo sistema nas duas telas da Casa. Controles de mídia são enviados ao Core local da STAR."
	tv_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tv_status.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	tv_status.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tv_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tv_status.add_theme_color_override("font_color", StarTheme.TEXT)
	tv_status.add_theme_font_size_override("font_size", 18)
	layout.add_child(tv_status)

	var controls := HBoxContainer.new()
	controls.alignment = BoxContainer.ALIGNMENT_CENTER
	controls.add_theme_constant_override("separation", 12)
	layout.add_child(controls)
	for item in [["◀", "mídia anterior"], ["⏯", "play pause"], ["▶", "próxima mídia"], ["− VOL", "diminuir volume"], ["+ VOL", "aumentar volume"]]:
		var button := _make_button(item[0], StarTheme.CYAN)
		button.pressed.connect(_send_tv_command.bind(item[1]))
		controls.add_child(button)

func _show_menu() -> void:
	_close_all_modals(false)
	mode = MODE_MENU
	hub_input_armed = false
	_apply_day_phase(str(current_world.get("day_phase", "night")))
	hud_ui.visible = false
	menu_ui.visible = true
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	_clear_content()

	camera.current = true
	camera.position = Vector3(0, 0.2, 9.5)
	camera.look_at(Vector3(0, 0.6, 0), Vector3.UP)

	menu_star = CrystalStar3D.new()
	menu_star.star_size = 0.60
	menu_star.position = Vector3(0, 2.95, 0)
	menu_star.rotation_speed = 0.075
	menu_star.energy = 2.75
	content_root.add_child(menu_star)

func _start_world_transition() -> void:
	if mode != MODE_MENU:
		return
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(menu_ui, "modulate:a", 0.0, 0.65)
	if menu_star:
		tween.tween_property(menu_star, "scale", Vector3.ONE * 4.0, 0.80).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	tween.tween_property(camera, "position", Vector3(0, 0.2, 3.2), 0.78).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	tween.finished.connect(func():
		menu_ui.modulate.a = 1.0
		_show_hub()
	)

func _show_hub() -> void:
	_close_all_modals(false)
	mode = MODE_HUB
	_apply_day_phase(str(current_world.get("day_phase", "night")))
	menu_ui.visible = false
	hud_ui.visible = true
	hud_title_label.text = "STAR WORLD"
	if crosshair_label:
		crosshair_label.visible = false
	if interaction_button:
		interaction_button.visible = false
	if hub_chat_button:
		hub_chat_button.visible = true
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	_clear_content()

	camera.current = true
	hub_islands = StarWorldBuilder.build_hub(content_root)
	_update_hub_camera()
	hub_input_armed = false
	call_deferred("_arm_hub_input")

func _arm_hub_input() -> void:
	# Impede que o clique que acionou INICIAR atravesse a transição e
	# selecione a ilha que estiver sob o cursor quando o Hub aparecer.
	await get_tree().create_timer(0.25).timeout
	while mode == MODE_HUB and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	if mode == MODE_HUB:
		hub_input_armed = true

func _update_hub_camera() -> void:
	if mode != MODE_HUB:
		return
	camera.position = Vector3(sin(hub_angle) * hub_distance, hub_height, cos(hub_angle) * hub_distance)
	camera.look_at(Vector3(0, 0.8, 0), Vector3.UP)

func _pick_hub_island(mouse_position: Vector2) -> void:
	var collider := _raycast_hub_island(mouse_position)
	if collider == null:
		collider = _screen_pick_hub_island(mouse_position)
	if collider == null:
		return
	_activate_hub_island(collider)

func _raycast_hub_island(mouse_position: Vector2) -> Node3D:
	var origin := camera.project_ray_origin(mouse_position)
	var direction := camera.project_ray_normal(mouse_position)
	var query := PhysicsRayQueryParameters3D.create(origin, origin + direction * 120.0)
	query.collide_with_areas = true
	query.collide_with_bodies = true
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		return null
	var collider := hit.get("collider") as Node3D
	if collider == null or not collider.has_meta("island_id"):
		return null
	return collider

func _screen_pick_hub_island(mouse_position: Vector2) -> Node3D:
	var best: Node3D = null
	var best_distance := INF
	for island_value in hub_islands.values():
		var collider := island_value as Node3D
		if collider == null or not is_instance_valid(collider):
			continue
		var target_world := collider.global_position + Vector3(0, 1.65, 0)
		if camera.is_position_behind(target_world):
			continue
		var target_screen := camera.unproject_position(target_world)
		var radius_world := float(collider.get_meta("click_radius", 3.0))
		var edge_world := target_world + camera.global_transform.basis.x.normalized() * radius_world
		var edge_screen := camera.unproject_position(edge_world)
		var radius_screen := clampf(target_screen.distance_to(edge_screen) * 1.20, 48.0, 190.0)
		var distance := mouse_position.distance_to(target_screen)
		if distance <= radius_screen and distance < best_distance:
			best = collider
			best_distance = distance
	return best

func _activate_hub_island(collider: Node3D) -> void:
	if collider == null or not collider.has_meta("island_id"):
		return
	var island_id := str(collider.get_meta("island_id"))
	var island_name := str(collider.get_meta("island_name", island_id))
	var status := str(collider.get_meta("status", "planned"))
	if island_id == "casa" and status == "available":
		_enter_house()
	else:
		_show_locked_island(island_name, status)

func _enter_house() -> void:
	_close_all_modals(false)
	mode = MODE_HOUSE
	hub_input_armed = false
	_apply_day_phase(str(current_world.get("day_phase", "night")))
	menu_ui.visible = false
	hud_ui.visible = true
	hud_title_label.text = "STAR HOUSE"
	if crosshair_label:
		crosshair_label.visible = true
	if interaction_button:
		interaction_button.visible = false
	if hub_chat_button:
		hub_chat_button.visible = false
	_clear_content()

	var built := StarWorldBuilder.build_house(content_root)
	star_avatar = built.get("avatar")
	if star_avatar:
		StarWorldBuilder.apply_skin(star_avatar, current_skin)

	player = StarWorldPlayer.new()
	player.name = "Player"
	content_root.add_child(player)
	player.position = built.get("spawn", Vector3(0, 0.35, 5))
	player.rotation.y = float(built.get("spawn_yaw", 0.0))
	camera.current = false
	player.set_active(true)

	if first_house_entry:
		first_house_entry = false
		_show_status_message("STAR HOUSE disponível. Sala, TV, quarto e roupeiro já estão conectados ao novo mundo.")

func _navigate_back() -> void:
	if mode == MODE_HOUSE:
		_show_hub()
	elif mode == MODE_HUB:
		_show_menu()

func _interact_house() -> void:
	if player == null:
		return
	var target := _current_house_interaction_target()
	if target == null or not target.has_meta("action"):
		return
	var action := str(target.get_meta("action"))
	match action:
		"wardrobe":
			_open_wardrobe()
		"tv":
			_open_tv(str(target.get_meta("room", "living")))
		"star":
			_open_chat()
		"future_pc":
			_show_locked_feature("PC DA STAR", "O computador já existe fisicamente no quarto, mas sua interação completa está planejada para uma próxima etapa.")

func _star_interaction_target_nearby() -> Object:
	if player == null or star_avatar == null or not is_instance_valid(star_avatar):
		return null
	if player.global_position.distance_to(star_avatar.global_position) > 2.65:
		return null
	var star_area := star_avatar.get_node_or_null("STARInteraction")
	if star_area != null and star_area.has_meta("action"):
		return star_area
	return null

func _current_house_interaction_target() -> Object:
	var star_target := _star_interaction_target_nearby()
	if star_target != null:
		return star_target
	return player.interaction_target() if player != null else null

func _update_interaction_prompt() -> void:
	if interaction_button == null:
		return
	if player == null or _has_modal():
		interaction_button.visible = false
		return
	var target := _current_house_interaction_target()
	if target != null and target.has_meta("action"):
		interaction_button.text = "E  ·  " + str(target.get_meta("label", "INTERAGIR"))
		interaction_button.visible = true
	else:
		interaction_button.visible = false

func _open_chat() -> void:
	if player and mode == MODE_HOUSE:
		player.set_active(false)
	if crosshair_label:
		crosshair_label.visible = false
	if interaction_button:
		interaction_button.visible = false
	chat_panel.visible = true
	chat_input.grab_focus()

func _send_chat() -> void:
	var value := chat_input.text.strip_edges()
	if value.is_empty():
		return
	chat_input.clear()
	_add_chat_message("VOCÊ", value, true)
	pending_response_target = "chat"
	_show_status_message("STAR está pensando…")
	core_client.send_text(value, true)

func _add_chat_message(author: String, text: String, from_user: bool) -> void:
	var row := HBoxContainer.new()
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	chat_messages.add_child(row)

	if from_user:
		var spacer := Control.new()
		spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(spacer)

	var bubble := PanelContainer.new()
	bubble.custom_minimum_size = Vector2(330, 0)
	var fill := Color(0.15,0.12,0.27,0.92) if from_user else Color(0.08,0.07,0.13,0.92)
	var edge := StarTheme.BLUE if from_user else StarTheme.VIOLET
	bubble.add_theme_stylebox_override("panel", StarTheme.glass_style(fill, Color(edge,0.60), 14, 1))
	row.add_child(bubble)

	var label := Label.new()
	label.text = author + "\n" + text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.custom_minimum_size = Vector2(300, 0)
	label.add_theme_color_override("font_color", StarTheme.TEXT)
	label.add_theme_font_size_override("font_size", 14)
	bubble.add_child(label)

	if not from_user:
		var spacer := Control.new()
		spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(spacer)

	await get_tree().process_frame
	chat_scroll.scroll_vertical = int(chat_scroll.get_v_scroll_bar().max_value)

func _open_settings() -> void:
	if player and mode == MODE_HOUSE:
		player.set_active(false)
	settings_panel.visible = true
	if current_world.has("timezone"):
		timezone_input.text = str(current_world.timezone)

func _open_wardrobe() -> void:
	if player:
		player.set_active(false)
	preview_skin = current_skin
	if wardrobe_preview_avatar:
		StarWorldBuilder.apply_skin(wardrobe_preview_avatar, current_skin)
	_update_wardrobe_info("Skin atual", current_skin)
	wardrobe_panel.visible = true
	_refresh_wardrobe_thumbnails()

func _preview_wardrobe_skin(skin_id: String, display_name: String) -> void:
	preview_skin = skin_id
	if star_avatar:
		StarWorldBuilder.apply_skin(star_avatar, skin_id)
	if wardrobe_preview_avatar:
		StarWorldBuilder.apply_skin(wardrobe_preview_avatar, skin_id)
	_update_wardrobe_info(display_name, skin_id)

func _update_wardrobe_info(display_name: String, skin_id: String) -> void:
	var descriptions := {
		"casual": "Acabamento claro e neutro para a STAR Bot, com metais suaves e luz discreta.",
		"cypher_system": "Acabamento principal branco/azulado com detalhes escuros e iluminação ciano.",
		"rock_simple": "Acabamento grafite e metálico, mais escuro e sóbrio.",
		"brazil": "Paleta amarela, verde e escura aplicada à carcaça e aos pontos luminosos.",
		"elegant_blue": "Acabamento azul profundo com reflexos frios e iluminação cristalina.",
		"rich_red": "Acabamento vinho/bordô com detalhes metálicos e iluminação rosada."
	}
	wardrobe_info.text = display_name + "\n\n" + str(descriptions.get(skin_id, "")) + "\n\nA mesma STAR Bot permanece: Core, memória, identidade, geometria e presença não mudam."
	equip_button.text = "EQUIPAR" if skin_id != current_skin else "EQUIPADA"

func _equip_preview_skin() -> void:
	current_skin = preview_skin
	if star_avatar:
		StarWorldBuilder.apply_skin(star_avatar, current_skin)
	if wardrobe_preview_avatar:
		StarWorldBuilder.apply_skin(wardrobe_preview_avatar, current_skin)
	core_client.set_skin(current_skin)
	equip_button.text = "EQUIPADA"
	_show_status_message("Skin equipada: " + current_skin)

func _star_root_path() -> String:
	var configured_root := OS.get_environment("STAR_ROOT").strip_edges()
	if not configured_root.is_empty():
		return configured_root
	return ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()

func _skin_reference_texture(skin_id: String) -> Texture2D:
	if _skin_reference_cache.has(skin_id):
		return _skin_reference_cache[skin_id]
	if not SKIN_REFERENCE_FILES.has(skin_id):
		return null

	var file_name := str(SKIN_REFERENCE_FILES[skin_id])
	var path := _star_root_path().path_join("SKINS").path_join(file_name)
	if not FileAccess.file_exists(path):
		return null

	var image := Image.new()
	var load_error := image.load(path)
	if load_error != OK or image.is_empty():
		return null

	var width := image.get_width()
	var height := image.get_height()
	if width > 360:
		var target_height := maxi(1, int(round(float(height) * 360.0 / float(width))))
		image.resize(360, target_height, Image.INTERPOLATE_LANCZOS)

	var texture := ImageTexture.create_from_image(image)
	_skin_reference_cache[skin_id] = texture
	return texture

func _refresh_wardrobe_thumbnails() -> void:
	if _wardrobe_thumbnails_loaded:
		return
	_wardrobe_thumbnails_loaded = true
	call_deferred("_load_wardrobe_thumbnails_async")

func _load_wardrobe_thumbnails_async() -> void:
	for skin_key in _wardrobe_skin_thumbnails:
		var skin_id := str(skin_key)
		var thumbnail := _wardrobe_skin_thumbnails[skin_key] as TextureRect
		var texture := _skin_reference_texture(skin_id)
		if thumbnail and texture:
			thumbnail.texture = texture
		await get_tree().process_frame

func _open_tv(room: String) -> void:
	if player:
		player.set_active(false)
	tv_panel.visible = true
	tv_status.text = "TV DA " + ("SALA" if room == "living" else "QUARTO") + "\n\nMesmo sistema, mesmo Core. Use os controles abaixo para enviar comandos locais de mídia."

func _tv_category(category: String) -> void:
	tv_status.text = category + "\n\nInterface modular da STAR TV. Serviços externos só aparecem quando houver provider real configurado."

func _send_tv_command(command: String) -> void:
	pending_response_target = "tv"
	tv_status.text = "Enviando ao Core local: " + command + "…"
	core_client.send_text(command, false)

func _show_locked_island(name: String, status: String) -> void:
	_show_locked_feature(name.to_upper(), "Esta ilha faz parte do STAR WORLD, mas ainda não está disponível. Estado atual: " + status.to_upper() + ".")

func _show_locked_feature(title_text: String, body_text: String) -> void:
	if modal_panel and is_instance_valid(modal_panel):
		modal_panel.queue_free()
	modal_panel = Control.new()
	_full_rect(modal_panel)
	ui_root.add_child(modal_panel)
	if player and mode == MODE_HOUSE:
		player.set_active(false)

	var dim := ColorRect.new()
	_full_rect(dim)
	dim.color = Color(0.01,0.005,0.03,0.48)
	modal_panel.add_child(dim)

	var panel := PanelContainer.new()
	_anchor_rect(panel, 0.31, 0.31, 0.69, 0.68)
	panel.add_theme_stylebox_override("panel", StarTheme.glass_style(Color(0.04,0.025,0.09,0.96), StarTheme.VIOLET, 18, 1))
	modal_panel.add_child(panel)

	var box := VBoxContainer.new()
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_theme_constant_override("separation", 16)
	panel.add_child(box)
	var icon := Label.new()
	icon.text = "◇  🔒"
	icon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	icon.add_theme_color_override("font_color", StarTheme.LILAC)
	icon.add_theme_font_size_override("font_size", 32)
	box.add_child(icon)
	var title := Label.new()
	title.text = title_text
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_color_override("font_color", StarTheme.TEXT)
	title.add_theme_font_size_override("font_size", 23)
	box.add_child(title)
	var body := Label.new()
	body.text = body_text
	body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_theme_color_override("font_color", StarTheme.MUTED)
	box.add_child(body)
	var close := _make_button("ENTENDI", StarTheme.VIOLET)
	close.pressed.connect(_close_all_modals)
	box.add_child(close)

func _close_all_modals(reactivate: bool = true) -> void:
	settings_panel.visible = false
	chat_panel.visible = false
	wardrobe_panel.visible = false
	tv_panel.visible = false
	if modal_panel and is_instance_valid(modal_panel):
		modal_panel.queue_free()
		modal_panel = null
	if mode == MODE_HOUSE and player and reactivate:
		if wardrobe_panel and preview_skin != current_skin and star_avatar:
			StarWorldBuilder.apply_skin(star_avatar, current_skin)
		player.set_active(true)
		if crosshair_label:
			crosshair_label.visible = true
		_update_interaction_prompt()
	else:
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		if interaction_button:
			interaction_button.visible = false

func _has_modal() -> bool:
	return (
		(settings_panel and settings_panel.visible)
		or (chat_panel and chat_panel.visible)
		or (wardrobe_panel and wardrobe_panel.visible)
		or (tv_panel and tv_panel.visible)
		or (modal_panel and is_instance_valid(modal_panel))
	)

func _on_connection_changed(is_connected: bool, detail: String) -> void:
	if core_status_label:
		core_status_label.text = detail
		core_status_label.add_theme_color_override("font_color", StarTheme.OK if is_connected else StarTheme.WARN)
	if settings_status:
		settings_status.text = detail
		settings_status.add_theme_color_override("font_color", StarTheme.OK if is_connected else StarTheme.WARN)

func _on_response_received(text: String, voice_started: bool) -> void:
	if pending_response_target == "tv":
		tv_status.text = text
		pending_response_target = "chat"
	else:
		_add_chat_message("STAR", text, false)
	_show_status_message("STAR está falando…" if voice_started else "STAR respondeu.")

func _on_world_state_received(state: Dictionary) -> void:
	current_world = state.duplicate(true)
	var local_time := str(state.get("local_time", "--:--"))
	var timezone := str(state.get("timezone", "local"))
	var phase := str(state.get("day_phase", "night"))
	var scenario := str(state.get("scenario", "cosmic_crystal"))
	time_label.text = local_time.substr(0, 5)
	time_label.tooltip_text = "%s • %s" % [timezone, scenario]
	if timezone_input and not timezone_input.has_focus():
		timezone_input.text = timezone
	_apply_day_phase(phase)

	var skin := str(state.get("skin", current_skin))
	if not skin.is_empty():
		current_skin = skin
		if star_avatar and is_instance_valid(star_avatar) and not wardrobe_panel.visible:
			StarWorldBuilder.apply_skin(star_avatar, current_skin)

func _on_request_failed(kind: String, detail: String) -> void:
	if kind == "pair":
		return
	if kind == "text":
		_add_chat_message("SISTEMA", detail, false)
	elif kind in ["timezone", "scenario", "skin"]:
		settings_status.text = detail
		settings_status.add_theme_color_override("font_color", StarTheme.ERROR)
	_show_status_message(detail)

func _apply_day_phase(phase: String) -> void:
	var top: Color
	var horizon: Color
	var ground: Color
	var energy: float
	match phase:
		"dawn":
			top = Color("#2C1F58")
			horizon = Color("#B46E9B")
			ground = Color("#27183D")
			energy = 0.88
		"day":
			top = Color("#172B67")
			horizon = Color("#777FC1")
			ground = Color("#29355F")
			energy = 1.12
		"sunset":
			top = Color("#251449")
			horizon = Color("#B45C88")
			ground = Color("#321D4A")
			energy = 0.82
		_:
			top = Color("#05030D")
			horizon = Color("#211342")
			ground = Color("#0E0923")
			energy = 0.55

	sky_material.sky_top_color = top
	sky_material.sky_horizon_color = horizon
	sky_material.ground_bottom_color = ground
	sky_material.ground_horizon_color = horizon
	if mode == MODE_HOUSE:
		# O céu continua seguindo a hora real, mas o interior tem iluminação
		# elétrica própria e precisa permanecer legível à noite.
		environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		environment.ambient_light_color = Color("#B8B2CC")
		environment.ambient_light_energy = 0.56
		sun.light_energy = energy * 0.18
	else:
		environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
		environment.ambient_light_color = Color.WHITE
		environment.ambient_light_energy = 0.62 + energy * 0.18
		sun.light_energy = energy

func _show_status_message(text: String) -> void:
	if status_label == null:
		return
	status_label.text = text
	status_label.visible = true
	var expected := text
	var timer := get_tree().create_timer(3.5)
	timer.timeout.connect(func():
		if status_label and status_label.text == expected:
			status_label.visible = false
	)

func _clear_content() -> void:
	if player and is_instance_valid(player):
		player.set_active(false)
	player = null
	star_avatar = null
	menu_star = null
	hub_islands.clear()
	for child in content_root.get_children():
		child.free()

func _run_smoke_sequence() -> void:
	await get_tree().process_frame
	_show_hub()
	await get_tree().process_frame
	await get_tree().physics_frame
	if hub_islands.size() < 5:
		push_error("STAR WORLD smoke: Hub incompleto")
		get_tree().quit(2)
		return
	var house_collider: Node3D = hub_islands.get("casa")
	if house_collider == null:
		push_error("STAR WORLD smoke: collider da Casa ausente")
		get_tree().quit(3)
		return
	var click_position := camera.unproject_position(house_collider.global_position + Vector3(0, 1.65, 0))
	var click_event := InputEventMouseButton.new()
	click_event.button_index = MOUSE_BUTTON_LEFT
	click_event.pressed = true
	click_event.position = click_position

	# O clique que abriu INICIAR não pode atravessar para a Casa.
	_input(click_event)
	if mode != MODE_HUB:
		push_error("STAR WORLD smoke: clique residual atravessou a transição para o Hub")
		get_tree().quit(4)
		return

	while mode == MODE_HUB and not hub_input_armed:
		await get_tree().process_frame

	# Depois de armado, um novo clique na Casa precisa abrir a STAR House.
	_input(click_event)
	await get_tree().process_frame
	if mode != MODE_HOUSE or player == null or star_avatar == null:
		push_error("STAR WORLD smoke: clique na Casa não abriu a STAR House")
		get_tree().quit(5)
		return

	var house_root := content_root.get_node_or_null("STARHouse")
	if house_root == null:
		push_error("STAR WORLD smoke: raiz da STAR House ausente")
		get_tree().quit(6)
		return

	var required_rooms := {
		"LivingRoom": 12,
		"Kitchen": 18,
		"Bathroom": 12,
		"Bedroom": 24,
	}
	for room_name in required_rooms:
		var room_node := house_root.get_node_or_null(str(room_name))
		if room_node == null:
			push_error("STAR WORLD smoke: cômodo ausente: " + str(room_name))
			get_tree().quit(7)
			return
		if room_node.get_child_count() < int(required_rooms[room_name]):
			push_error("STAR WORLD smoke: cômodo incompleto: " + str(room_name))
			get_tree().quit(8)
			return

	var fp_state := player.first_person_state()
	if not bool(fp_state.get("active", false)) or not bool(fp_state.get("camera_current", false)) or not bool(fp_state.get("ray_parent_is_camera", false)):
		push_error("STAR WORLD smoke: câmera em primeira pessoa não está operacional")
		get_tree().quit(9)
		return
	if not InputMap.has_action("jump") or float(fp_state.get("jump_velocity", 0.0)) < 3.0 or float(fp_state.get("floor_snap_length", 0.0)) < 0.2:
		push_error("STAR WORLD smoke: pulo curto ou assistência de degraus indisponível")
		get_tree().quit(10)
		return
	if crosshair_label == null or not crosshair_label.visible or crosshair_label.text != "+":
		push_error("STAR WORLD smoke: mira central ausente")
		get_tree().quit(11)
		return

	var yaw_before := player.rotation.y
	var pitch_before := player.look_pitch
	player.apply_look_delta(Vector2(32.0, -24.0))
	if is_equal_approx(player.rotation.y, yaw_before) or is_equal_approx(player.look_pitch, pitch_before):
		push_error("STAR WORLD smoke: mouse-look não altera yaw/pitch")
		get_tree().quit(12)
		return

	var environment_triangles := int(house_root.get_meta("environment_triangle_count", 0))
	if environment_triangles < 50000:
		push_error("STAR WORLD smoke: cenário 3D abaixo da densidade mínima (%d triângulos)" % environment_triangles)
		get_tree().quit(13)
		return

	var body_triangles := int(star_avatar.get_meta("body_triangle_count", 0))
	var total_triangles := int(star_avatar.get_meta("triangle_count", 0))
	if str(star_avatar.get_meta("physical_form", "")) != "star_bot":
		push_error("STAR WORLD smoke: forma física não é STAR Bot")
		get_tree().quit(14)
		return
	if body_triangles < 50000 or total_triangles < 50000:
		push_error("STAR WORLD smoke: STAR Bot simplificada demais (%d triângulos)" % total_triangles)
		get_tree().quit(15)
		return

	if interaction_button == null or interaction_button.visible:
		push_error("STAR WORLD smoke: botão de interação deveria iniciar oculto")
		get_tree().quit(16)
		return

	player.global_position = star_avatar.global_position + Vector3(1.45, 0.0, 0.15)
	_update_interaction_prompt()
	if not interaction_button.visible or "STAR" not in interaction_button.text:
		push_error("STAR WORLD smoke: proximidade da STAR Bot não oferece conversa")
		get_tree().quit(17)
		return

	_interact_house()
	await get_tree().process_frame
	if not chat_panel.visible or chat_panel.get_node_or_null("ChatBlur") == null or chat_panel.get_node_or_null("ChatSidePanel") == null:
		push_error("STAR WORLD smoke: chat lateral com blur não abriu sobre a cena")
		get_tree().quit(18)
		return
	if crosshair_label.visible:
		push_error("STAR WORLD smoke: mira permaneceu sobre o chat")
		get_tree().quit(19)
		return
	_close_all_modals()
	await get_tree().process_frame

	print("STAR_WORLD_SMOKE_METRICS rooms=4 environment_triangles=", environment_triangles, " starbot_triangles=", total_triangles)

	_open_wardrobe()
	await get_tree().process_frame
	_preview_wardrobe_skin("rich_red", "RICH RED")
	_close_all_modals()
	_open_tv("bedroom")
	await get_tree().process_frame
	_close_all_modals()
	print("STAR_WORLD_SMOKE_OK")
	get_tree().quit(0)

func _make_button(text_value: String, accent: Color) -> Button:
	var button := Button.new()
	button.text = text_value
	button.focus_mode = Control.FOCUS_ALL
	StarTheme.apply_button(button, accent)
	return button

func _full_rect(control: Control) -> void:
	control.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

func _anchor_rect(control: Control, left: float, top: float, right: float, bottom: float) -> void:
	control.set_anchor(SIDE_LEFT, left)
	control.set_anchor(SIDE_TOP, top)
	control.set_anchor(SIDE_RIGHT, right)
	control.set_anchor(SIDE_BOTTOM, bottom)
	control.offset_left = 0
	control.offset_top = 0
	control.offset_right = 0
	control.offset_bottom = 0
