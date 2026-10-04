extends RefCounted
class_name StarTheme

const BG_VOID := Color("#05030D")
const BG_DEEP := Color("#0E0923")
const PANEL := Color(0.043, 0.028, 0.102, 0.88)
const PANEL_SOFT := Color(0.09, 0.06, 0.17, 0.80)
const PANEL_EDGE := Color("#57388F")
const VIOLET := Color("#7E58B3")
const LILAC := Color("#C49EE0")
const BLUE := Color("#638CBF")
const CYAN := Color("#72E8FF")
const CRYSTAL := Color("#E6DCEA")
const TEXT := Color("#F3EEFF")
const MUTED := Color("#A9A2BC")
const OK := Color("#6FE0A2")
const WARN := Color("#F0C66D")
const ERROR := Color("#FF7C9A")

static func glass_style(fill: Color = PANEL, border: Color = PANEL_EDGE, radius: int = 14, width: int = 1) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = border
	box.set_border_width_all(width)
	box.set_corner_radius_all(radius)
	box.shadow_color = Color(0, 0, 0, 0.28)
	box.shadow_size = 12
	box.content_margin_left = 18
	box.content_margin_right = 18
	box.content_margin_top = 12
	box.content_margin_bottom = 12
	return box

static func button_styles(accent: Color = VIOLET) -> Dictionary:
	var normal := glass_style(Color(0.07, 0.04, 0.15, 0.78), Color(accent, 0.75), 12, 1)
	var hover := glass_style(Color(0.11, 0.07, 0.22, 0.92), Color(accent.lightened(0.22), 0.95), 12, 2)
	var pressed := glass_style(Color(0.05, 0.03, 0.12, 0.95), Color(CRYSTAL, 0.95), 12, 2)
	return {"normal": normal, "hover": hover, "pressed": pressed}

static func apply_button(button: Button, accent: Color = VIOLET) -> void:
	var styles := button_styles(accent)
	button.add_theme_stylebox_override("normal", styles.normal)
	button.add_theme_stylebox_override("hover", styles.hover)
	button.add_theme_stylebox_override("pressed", styles.pressed)
	button.add_theme_stylebox_override("focus", styles.hover)
	button.add_theme_color_override("font_color", TEXT)
	button.add_theme_color_override("font_hover_color", TEXT)
	button.add_theme_color_override("font_pressed_color", TEXT)
	button.add_theme_font_size_override("font_size", 18)
