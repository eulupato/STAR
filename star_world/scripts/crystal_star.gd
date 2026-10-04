extends Node3D
class_name CrystalStar3D

@export var star_size: float = 1.0
@export var rotation_speed: float = 0.12
@export var energy: float = 2.2

var _mesh_instance: MeshInstance3D
var _halo_instance: MeshInstance3D

func _ready() -> void:
	_build_mesh()

func _process(delta: float) -> void:
	rotation.z += rotation_speed * delta
	rotation.y = sin(Time.get_ticks_msec() * 0.00035) * 0.14
	if _halo_instance:
		var pulse := 1.0 + sin(Time.get_ticks_msec() * 0.0022) * 0.055
		_halo_instance.scale = Vector3.ONE * pulse

func _build_mesh() -> void:
	_mesh_instance = MeshInstance3D.new()
	_mesh_instance.name = "CrystalMesh"
	_mesh_instance.mesh = _create_star_mesh()
	_mesh_instance.material_override = _create_material()
	add_child(_mesh_instance)

	_halo_instance = MeshInstance3D.new()
	_halo_instance.name = "CrystalCoreGlow"
	var halo_mesh := SphereMesh.new()
	halo_mesh.radius = star_size * 0.24
	halo_mesh.height = star_size * 0.48
	halo_mesh.radial_segments = 20
	halo_mesh.rings = 10
	_halo_instance.mesh = halo_mesh
	_halo_instance.material_override = _create_halo_material()
	add_child(_halo_instance)

func _create_star_mesh() -> ArrayMesh:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)

	var core_radius := star_size * 0.235
	var core_depth := star_size * 0.20

	# Oito pontas facetadas: quatro longas e quatro diagonais menores.
	for i in range(8):
		var angle := float(i) * PI / 4.0
		var direction := Vector3(cos(angle), sin(angle), 0.0)
		var tangent := Vector3(-sin(angle), cos(angle), 0.0)
		var length := star_size * (1.28 if i % 2 == 0 else 0.82)
		var width := star_size * (0.145 if i % 2 == 0 else 0.125)
		var base_center := direction * core_radius * 0.82
		var tip := direction * length
		var front_left := base_center + tangent * width + Vector3(0, 0, core_depth * 0.68)
		var front_right := base_center - tangent * width + Vector3(0, 0, core_depth * 0.68)
		var back_right := base_center - tangent * width - Vector3(0, 0, core_depth * 0.68)
		var back_left := base_center + tangent * width - Vector3(0, 0, core_depth * 0.68)

		_add_triangle(surface, tip, front_left, front_right, 1.00)
		_add_triangle(surface, tip, front_right, back_right, 0.86)
		_add_triangle(surface, tip, back_right, back_left, 0.72)
		_add_triangle(surface, tip, back_left, front_left, 0.92)

	# Núcleo octogonal fechado. Elimina o vazio central e cria o aspecto de gema.
	var front_apex := Vector3(0, 0, core_depth)
	var back_apex := Vector3(0, 0, -core_depth)
	for i in range(8):
		var a0 := float(i) * PI / 4.0
		var a1 := float(i + 1) * PI / 4.0
		var p0 := Vector3(cos(a0) * core_radius, sin(a0) * core_radius, 0)
		var p1 := Vector3(cos(a1) * core_radius, sin(a1) * core_radius, 0)
		_add_triangle(surface, front_apex, p0, p1, 1.08 if i % 2 == 0 else 0.92)
		_add_triangle(surface, back_apex, p1, p0, 0.72 if i % 2 == 0 else 0.82)

	surface.generate_normals()
	return surface.commit()

func _add_triangle(surface: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, brightness: float) -> void:
	var bright := Color(0.96, 0.94, 1.0, 1.0) * brightness
	bright.a = 1.0
	var mid := Color(0.72, 0.64, 0.96, 1.0) * brightness
	mid.a = 1.0
	var cool := Color(0.48, 0.68, 0.96, 1.0) * brightness
	cool.a = 1.0
	surface.set_color(bright)
	surface.add_vertex(a)
	surface.set_color(mid)
	surface.add_vertex(b)
	surface.set_color(cool)
	surface.add_vertex(c)

func _create_material() -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.vertex_color_use_as_albedo = true
	material.albedo_color = Color(0.88, 0.84, 1.0, 0.98)
	material.metallic = 0.08
	material.roughness = 0.12
	material.emission_enabled = true
	material.emission = Color("#A98DFF")
	material.emission_energy_multiplier = energy * 0.72
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return material

func _create_halo_material() -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.68, 0.50, 1.0, 0.10)
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.emission_enabled = true
	material.emission = Color("#B99AFF")
	material.emission_energy_multiplier = energy * 0.55
	return material

func set_glow(value: float) -> void:
	energy = max(0.1, value)
	if _mesh_instance and _mesh_instance.material_override:
		_mesh_instance.material_override.emission_energy_multiplier = energy * 0.72
	if _halo_instance and _halo_instance.material_override:
		_halo_instance.material_override.emission_energy_multiplier = energy * 0.55
