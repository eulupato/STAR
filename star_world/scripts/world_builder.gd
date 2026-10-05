extends RefCounted
class_name StarWorldBuilder

const TEXTURE_ROOT := "res://assets/textures/materials/"
static var _texture_cache: Dictionary = {}

const SKIN_PALETTES := {
	"casual": {"primary": Color("#F1F2F7"), "secondary": Color("#454753"), "accent": Color("#D7D9E5")},
	"cypher_system": {"primary": Color("#A9D8F5"), "secondary": Color("#263A63"), "accent": Color("#72E8FF")},
	"rock_simple": {"primary": Color("#17181D"), "secondary": Color("#A9ADB5"), "accent": Color("#E6DCEA")},
	"brazil": {"primary": Color("#F5D83B"), "secondary": Color("#17191E"), "accent": Color("#4AB56B")},
	"elegant_blue": {"primary": Color("#111B4A"), "secondary": Color("#1E2E72"), "accent": Color("#A9C6FF")},
	"rich_red": {"primary": Color("#731B33"), "secondary": Color("#4A1023"), "accent": Color("#C97791")},
}

static func material(color: Color, emission: Color = Color(0, 0, 0, 1), energy: float = 0.0, metallic: float = 0.0, roughness: float = 0.55) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.metallic = metallic
	mat.roughness = roughness
	if color.a < 0.999:
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	if energy > 0.0:
		mat.emission_enabled = true
		mat.emission = emission
		mat.emission_energy_multiplier = energy
	return mat

static func textured_material(texture_name: String, tint: Color = Color.WHITE, metallic: float = 0.0, roughness: float = 0.55, uv_scale: float = 1.0) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = tint
	mat.metallic = metallic
	mat.roughness = roughness
	var texture: Texture2D = _texture_cache.get(texture_name)
	if texture == null:
		texture = load(TEXTURE_ROOT + texture_name) as Texture2D
		if texture != null:
			_texture_cache[texture_name] = texture
	if texture != null:
		mat.albedo_texture = texture
	mat.uv1_scale = Vector3(uv_scale, uv_scale, uv_scale)
	return mat

static func set_holder_material(holder: Node, mat: Material) -> void:
	var mesh := _mesh_child(holder)
	if mesh != null:
		mesh.material_override = mat

static func emissive_material(color: Color, emission: Color, energy: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.emission_enabled = true
	mat.emission = emission
	mat.emission_energy_multiplier = energy
	if color.a < 0.999:
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return mat

static func _mesh_child(holder: Node) -> MeshInstance3D:
	for child in holder.get_children():
		if child is MeshInstance3D:
			return child
	return null

static func add_box(parent: Node, name: String, position: Vector3, size: Vector3, color: Color, collision: bool = false, metadata: Dictionary = {}) -> Node3D:
	var holder: Node3D
	if collision:
		var body := StaticBody3D.new()
		holder = body
		var shape_node := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = size
		shape_node.shape = shape
		body.add_child(shape_node)
	else:
		holder = Node3D.new()

	holder.name = name
	holder.position = position
	for key in metadata:
		holder.set_meta(key, metadata[key])

	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	# Subdivisão moderada em toda a geometria-base. Mesmo objetos simples deixam
	# de ser caixas de 12 triângulos e recebem malha densa o bastante para luz,
	# materiais e evolução posterior sem explodir custo de colisão.
	mesh.subdivide_width = 3
	mesh.subdivide_height = 3
	mesh.subdivide_depth = 3
	mesh_instance.mesh = mesh
	mesh_instance.material_override = material(color)
	holder.add_child(mesh_instance)
	parent.add_child(holder)
	return holder

static func add_cylinder(parent: Node, name: String, position: Vector3, radius: float, height: float, color: Color, collision: bool = false, metadata: Dictionary = {}) -> Node3D:
	var holder: Node3D
	if collision:
		var body := StaticBody3D.new()
		holder = body
		var shape_node := CollisionShape3D.new()
		var shape := CylinderShape3D.new()
		shape.radius = radius
		shape.height = height
		shape_node.shape = shape
		body.add_child(shape_node)
	else:
		holder = Node3D.new()

	holder.name = name
	holder.position = position
	for key in metadata:
		holder.set_meta(key, metadata[key])

	var mesh_instance := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius * 0.82
	mesh.height = height
	mesh.radial_segments = 48
	mesh_instance.mesh = mesh
	mesh_instance.material_override = material(color)
	holder.add_child(mesh_instance)
	parent.add_child(holder)
	return holder

static func build_nebula(parent: Node3D, layer_count: int = 7) -> Array[Sprite3D]:
	var sprites: Array[Sprite3D] = []
	var texture := _create_nebula_texture(256)
	var colors := [
		Color(0.42, 0.22, 0.82, 0.34),
		Color(0.22, 0.43, 0.90, 0.24),
		Color(0.68, 0.34, 0.74, 0.20),
		Color(0.24, 0.58, 0.76, 0.16),
	]
	for i in range(layer_count):
		var angle := TAU * float(i) / float(layer_count) + 0.28
		var sprite := Sprite3D.new()
		sprite.name = "Nebula_%02d" % i
		sprite.texture = texture
		sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		sprite.shaded = false
		sprite.pixel_size = 0.23 + float(i % 3) * 0.035
		sprite.modulate = colors[i % colors.size()]
		sprite.position = Vector3(
			sin(angle) * 72.0,
			8.0 + sin(angle * 2.3) * 19.0,
			cos(angle) * 72.0
		)
		parent.add_child(sprite)
		sprites.append(sprite)
	return sprites

static func _create_nebula_texture(size: int) -> ImageTexture:
	var image := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var noise := FastNoiseLite.new()
	noise.seed = 0x5A7A
	noise.frequency = 0.032

	var center := Vector2(float(size - 1), float(size - 1)) * 0.5
	var radius := float(size) * 0.5
	for y in range(size):
		for x in range(size):
			var uv: Vector2 = (Vector2(float(x), float(y)) - center) / radius
			var radial: float = clampf(1.0 - uv.length(), 0.0, 1.0)
			var cloud: float = (noise.get_noise_2d(float(x), float(y)) + 1.0) * 0.5
			var wisps: float = (noise.get_noise_2d(float(x) * 2.1 + 317.0, float(y) * 2.1 - 149.0) + 1.0) * 0.5
			var density: float = pow(radial, 1.55) * (0.22 + cloud * 0.58 + wisps * 0.20)
			density = clampf(density * 0.88, 0.0, 0.78)
			image.set_pixel(x, y, Color(1.0, 1.0, 1.0, density))
	return ImageTexture.create_from_image(image)

static func build_starfield(parent: Node3D, count: int = 560) -> MultiMeshInstance3D:
	var instance := MultiMeshInstance3D.new()
	instance.name = "CosmicStarfield"

	var star_mesh := SphereMesh.new()
	star_mesh.radius = 0.035
	star_mesh.height = 0.07
	star_mesh.radial_segments = 6
	star_mesh.rings = 3
	var star_material := material(Color("#E9E5FF"), Color("#D9CCFF"), 4.2, 0.0, 0.25)
	star_mesh.material = star_material

	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = star_mesh
	multimesh.instance_count = count

	var rng := RandomNumberGenerator.new()
	rng.seed = 0x5A7A2026
	for i in range(count):
		var direction := Vector3(
			rng.randf_range(-1.0, 1.0),
			rng.randf_range(-0.65, 1.0),
			rng.randf_range(-1.0, 1.0)
		).normalized()
		var distance := rng.randf_range(34.0, 95.0)
		var scale_value := rng.randf_range(0.45, 2.5)
		var basis := Basis().scaled(Vector3.ONE * scale_value)
		multimesh.set_instance_transform(i, Transform3D(basis, direction * distance))

	instance.multimesh = multimesh
	parent.add_child(instance)
	return instance

static func build_hub(parent: Node3D) -> Dictionary:
	var result := {}
	var specs := [
		{"id":"casa", "name":"Casa", "status":"available", "pos":Vector3(0, 0, 0), "r":5.1, "surface":Color("#4F704A"), "rock":Color("#5A463F")},
		{"id":"laboratorio", "name":"Laboratório", "status":"planned", "pos":Vector3(-11, 2.0, -7), "r":3.55, "surface":Color("#47707A"), "rock":Color("#4B4654")},
		{"id":"biblioteca", "name":"Biblioteca", "status":"planned", "pos":Vector3(11, 1.2, -8), "r":3.75, "surface":Color("#58724A"), "rock":Color("#5D4B43")},
		{"id":"estudio_musica", "name":"Estúdio de Música", "status":"planned", "pos":Vector3(14, -1.5, 3), "r":3.25, "surface":Color("#5E4B71"), "rock":Color("#493C50")},
		{"id":"atelie", "name":"Ateliê", "status":"planned", "pos":Vector3(9, -2.2, 10), "r":3.15, "surface":Color("#6A5573"), "rock":Color("#584346")},
		{"id":"jardim", "name":"Jardim", "status":"planned", "pos":Vector3(-3, -2.5, 12), "r":4.35, "surface":Color("#4F7B54"), "rock":Color("#55473E")},
		{"id":"observatorio", "name":"Observatório", "status":"planned", "pos":Vector3(-13, 4.0, 8), "r":3.35, "surface":Color("#4B537E"), "rock":Color("#494254")},
		{"id":"correio", "name":"Correio", "status":"planned", "pos":Vector3(-9, -1.0, 3), "r":2.55, "surface":Color("#62764F"), "rock":Color("#59483D")},
		{"id":"herois", "name":"Heróis", "status":"planned", "pos":Vector3(4, 4.2, -15), "r":3.25, "surface":Color("#594D76"), "rock":Color("#494052")},
	]

	for spec in specs:
		var island := Node3D.new()
		island.name = "Island_" + spec.id
		island.position = spec.pos
		parent.add_child(island)

		var collider := _build_floating_island(
			island,
			float(spec.r),
			spec.surface,
			spec.rock,
			{
				"island_id":spec.id,
				"island_name":spec.name,
				"status":spec.status,
				"click_radius":float(spec.r),
			}
		)
		_build_island_landmark(island, spec.id, float(spec.r), spec.status)
		_add_island_label(island, spec.name, spec.status, float(spec.r))
		if spec.status != "available":
			_add_lock_marker(island, float(spec.r))

		result[spec.id] = collider

	_build_hub_spark_paths(parent, specs)
	return result

static func _build_floating_island(parent: Node3D, radius: float, surface_color: Color, rock_color: Color, metadata: Dictionary) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.name = "IslandCollider"
	body.position = Vector3(0, -0.75, 0)
	for key in metadata:
		body.set_meta(key, metadata[key])

	var shape_node := CollisionShape3D.new()
	var shape := CylinderShape3D.new()
	shape.radius = radius
	shape.height = 2.6
	shape_node.shape = shape
	body.add_child(shape_node)

	var upper := MeshInstance3D.new()
	var upper_mesh := CylinderMesh.new()
	upper_mesh.top_radius = radius
	upper_mesh.bottom_radius = radius * 0.70
	upper_mesh.height = 1.55
	upper_mesh.radial_segments = 14
	upper.mesh = upper_mesh
	upper.position.y = -0.10
	upper.material_override = material(rock_color, Color("#7B5D73"), 0.08, 0.0, 0.92)
	body.add_child(upper)

	var lower := MeshInstance3D.new()
	var lower_mesh := CylinderMesh.new()
	lower_mesh.top_radius = radius * 0.70
	lower_mesh.bottom_radius = radius * 0.16
	lower_mesh.height = 2.85
	lower_mesh.radial_segments = 11
	lower.mesh = lower_mesh
	lower.position.y = -2.15
	lower.material_override = material(rock_color.darkened(0.18), Color("#4A3753"), 0.05, 0.0, 0.96)
	body.add_child(lower)

	var shard := MeshInstance3D.new()
	var shard_mesh := CylinderMesh.new()
	shard_mesh.top_radius = radius * 0.26
	shard_mesh.bottom_radius = radius * 0.035
	shard_mesh.height = 1.75
	shard_mesh.radial_segments = 8
	shard.mesh = shard_mesh
	shard.position.y = -4.18
	shard.material_override = material(rock_color.darkened(0.30))
	body.add_child(shard)

	var top := MeshInstance3D.new()
	var top_mesh := CylinderMesh.new()
	top_mesh.top_radius = radius * 0.97
	top_mesh.bottom_radius = radius * 0.92
	top_mesh.height = 0.26
	top_mesh.radial_segments = 18
	top.mesh = top_mesh
	top.position.y = 0.76
	top.material_override = material(surface_color, surface_color.lightened(0.18), 0.10, 0.0, 0.88)
	body.add_child(top)

	parent.add_child(body)
	return body

static func _add_island_label(parent: Node3D, island_name: String, status: String, radius: float) -> void:
	var label := Label3D.new()
	label.name = "IslandLabel"
	label.text = island_name.to_upper() if status == "available" else island_name.to_upper() + "\nINDISPONÍVEL"
	label.position = Vector3(0, max(4.6, radius + 1.1), 0)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size = 40
	label.outline_size = 7
	label.pixel_size = 0.014
	label.modulate = Color("#F3EEFF") if status == "available" else Color("#C8BCE6")
	label.outline_modulate = Color(0.03, 0.015, 0.07, 0.92)
	label.no_depth_test = true
	parent.add_child(label)

static func _add_lock_marker(parent: Node3D, radius: float) -> void:
	var lock_root := Node3D.new()
	lock_root.name = "LockMarker"
	lock_root.position = Vector3(0, max(3.4, radius * 0.72), 0)
	lock_root.scale = Vector3.ONE * clampf(radius / 4.0, 0.62, 0.90)
	parent.add_child(lock_root)

	var glow := Color("#A98DFF")
	var lock_body := add_box(lock_root, "LockBody", Vector3(0, 0.0, 0), Vector3(0.78, 0.62, 0.22), Color("#6E58A4"), false)
	var body_mesh := _mesh_child(lock_body)
	body_mesh.material_override = material(Color("#6E58A4"), glow, 2.2, 0.10, 0.28)

	for side in [-1.0, 1.0]:
		var bar := add_cylinder(lock_root, "LockBar", Vector3(0.25 * side, 0.48, 0), 0.075, 0.58, Color("#BCA8EA"), false)
		var bar_mesh := _mesh_child(bar)
		bar_mesh.material_override = material(Color("#BCA8EA"), glow, 2.0, 0.12, 0.22)

	var top_bar := add_box(lock_root, "LockTop", Vector3(0, 0.78, 0), Vector3(0.58, 0.13, 0.18), Color("#C9B7F5"), false)
	var top_mesh := _mesh_child(top_bar)
	top_mesh.material_override = material(Color("#C9B7F5"), glow, 2.0, 0.12, 0.22)

static func _build_hub_spark_paths(parent: Node3D, specs: Array) -> void:
	var positions: Array[Vector3] = []
	for spec in specs:
		if spec.id == "casa":
			continue
		var target: Vector3 = spec.pos
		for step in range(1, 15):
			var t := float(step) / 15.0
			var point := Vector3.ZERO.lerp(target, t)
			point.y += sin(t * PI) * 1.65 + 0.55
			positions.append(point)

	var spark_mesh := SphereMesh.new()
	spark_mesh.radius = 0.055
	spark_mesh.height = 0.11
	spark_mesh.radial_segments = 6
	spark_mesh.rings = 3
	spark_mesh.material = material(Color("#F2E9FF"), Color("#BFA9FF"), 4.0, 0.0, 0.18)

	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = spark_mesh
	multimesh.instance_count = positions.size()
	for i in range(positions.size()):
		var scale_value := 0.60 + float(i % 5) * 0.10
		multimesh.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * scale_value), positions[i]))

	var sparks := MultiMeshInstance3D.new()
	sparks.name = "HubSparkPaths"
	sparks.multimesh = multimesh
	parent.add_child(sparks)

static func _build_island_landmark(parent: Node3D, id: String, _radius: float, _status: String) -> void:
	match id:
		"casa":
			add_box(parent, "HouseMain", Vector3(0, 1.2, 0.3), Vector3(4.8, 2.2, 3.6), Color("#E8E4DF"))
			add_box(parent, "HouseUpper", Vector3(-0.7, 3.0, 0.0), Vector3(3.4, 1.5, 2.8), Color("#F5F3F0"))
			add_box(parent, "WoodAccent", Vector3(-2.3, 2.4, 0.2), Vector3(0.35, 4.0, 2.7), Color("#8B5D3F"))
			add_box(parent, "StoneAccent", Vector3(1.8, 2.0, 0.0), Vector3(0.45, 3.4, 3.0), Color("#B8AE9E"))

			var roof_left := add_box(parent, "RoofLeft", Vector3(-0.98, 4.02, 0.15), Vector3(2.45, 0.18, 3.75), Color("#4B415A"))
			roof_left.rotation.z = -0.34
			var roof_right := add_box(parent, "RoofRight", Vector3(0.98, 4.02, 0.15), Vector3(2.45, 0.18, 3.75), Color("#40394E"))
			roof_right.rotation.z = 0.34

			var front_window := add_box(parent, "HouseWindow", Vector3(-0.65, 1.55, -1.54), Vector3(1.05, 0.85, 0.08), Color("#9ED4E4"))
			var front_window_mesh := _mesh_child(front_window)
			front_window_mesh.material_override = material(Color("#8ABFD2"), Color("#7FCDF0"), 1.7, 0.02, 0.20)

			var door := add_box(parent, "HouseDoor", Vector3(1.10, 1.02, -1.56), Vector3(0.78, 1.70, 0.10), Color("#6F4C39"))
			var door_mesh := _mesh_child(door)
			door_mesh.material_override = material(Color("#6F4C39"), Color("#C78E63"), 0.20, 0.0, 0.55)

			_add_tree(parent, Vector3(-3.3, 0.5, 2.0), 0.85)
			_add_tree(parent, Vector3(3.0, 0.5, 1.9), 0.7)
		"laboratorio":
			add_cylinder(parent, "LabTower", Vector3(0, 1.3, 0), 1.25, 2.6, Color("#D7E7F1"))
			add_box(parent, "LabWing", Vector3(1.4, 0.8, 0), Vector3(2.2, 1.2, 2.4), Color("#92B8C9"))
		"biblioteca":
			add_box(parent, "LibraryHall", Vector3(0, 1.0, 0), Vector3(4.2, 1.8, 2.8), Color("#BDA98B"))
			for x in [-1.7, -0.55, 0.55, 1.7]:
				add_cylinder(parent, "Column", Vector3(x, 1.2, -1.55), 0.16, 2.4, Color("#E1D7C7"))
		"estudio_musica":
			add_box(parent, "Studio", Vector3(0, 1.0, 0), Vector3(3.4, 1.7, 2.7), Color("#332B46"))
			add_box(parent, "StudioGlow", Vector3(0, 1.0, -1.42), Vector3(2.5, 0.08, 0.08), Color("#A957A8"))
		"atelie":
			add_box(parent, "Atelier", Vector3(0, 1.0, 0), Vector3(3.2, 1.8, 2.8), Color("#D9C9D8"))
			add_box(parent, "Skylight", Vector3(0, 2.0, 0), Vector3(2.0, 0.15, 1.8), Color(0.55, 0.75, 0.9, 0.45))
		"jardim":
			for p in [Vector3(-1.8,0.5,-1.4), Vector3(1.6,0.5,-1.0), Vector3(0.2,0.5,1.9)]:
				_add_tree(parent, p, 1.0)
			add_cylinder(parent, "Pond", Vector3(0, 0.18, 0), 1.5, 0.08, Color("#3B8290"))
		"observatorio":
			add_cylinder(parent, "ObservatoryBase", Vector3(0, 1.0, 0), 1.5, 2.0, Color("#D4D6E2"))
			var dome := MeshInstance3D.new()
			var sphere := SphereMesh.new()
			sphere.radius = 1.3
			sphere.height = 1.3
			dome.mesh = sphere
			dome.position = Vector3(0, 2.25, 0)
			dome.scale.y = 0.55
			dome.material_override = material(Color("#8793B8"))
			parent.add_child(dome)
		"correio":
			add_box(parent, "PostOffice", Vector3(0, 0.9, 0), Vector3(2.4, 1.6, 2.0), Color("#C49A78"))
			add_box(parent, "MailRoof", Vector3(0, 1.85, 0), Vector3(2.8, 0.18, 2.35), Color("#6F3E54"))
		"herois":
			add_box(parent, "HeroesArchive", Vector3(0, 1.1, 0), Vector3(3.6, 2.0, 2.8), Color("#66527D"))
			add_cylinder(parent, "HeroesBeacon", Vector3(0, 2.8, 0), 0.22, 1.7, Color("#B9A0E8"))

static func _add_tree(parent: Node3D, position: Vector3, scale_value: float) -> void:
	add_cylinder(parent, "Trunk", position + Vector3(0, 0.45 * scale_value, 0), 0.12 * scale_value, 0.9 * scale_value, Color("#74513D"))
	var crown := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.55 * scale_value
	sphere.height = 1.0 * scale_value
	sphere.radial_segments = 36
	sphere.rings = 18
	crown.mesh = sphere
	crown.position = position + Vector3(0, 1.25 * scale_value, 0)
	crown.material_override = material(Color("#3D704B"))
	parent.add_child(crown)

static func _add_room_light(parent: Node3D, name: String, position: Vector3, color: Color, energy: float, light_range: float) -> OmniLight3D:
	var light := OmniLight3D.new()
	light.name = name
	light.position = position
	light.light_color = color
	light.light_energy = energy
	light.omni_range = light_range
	light.shadow_enabled = false
	parent.add_child(light)
	return light

static func _new_room(parent: Node3D, name: String) -> Node3D:
	var room := Node3D.new()
	room.name = name
	parent.add_child(room)
	return room

static func _add_ellipsoid(parent: Node3D, name: String, position: Vector3, radii: Vector3, color: Color, emission: Color = Color.BLACK, energy: float = 0.0) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = name
	var sphere := SphereMesh.new()
	sphere.radius = 0.5
	sphere.height = 1.0
	sphere.radial_segments = 48
	sphere.rings = 24
	node.mesh = sphere
	node.position = position
	node.scale = radii * 2.0
	node.material_override = material(color, emission, energy, 0.0, 0.46)
	parent.add_child(node)
	return node

static func _add_window_z(parent: Node3D, name: String, center: Vector3, width: float, height: float) -> void:
	var frame := Color("#2A2C32")
	var glass := add_box(parent, name + "_Glass", center, Vector3(width - 0.16, height - 0.16, 0.045), Color(0.42, 0.67, 0.82, 0.22), false)
	var glass_mesh := _mesh_child(glass)
	glass_mesh.material_override = material(Color(0.42, 0.67, 0.82, 0.22), Color("#587EB8"), 0.20, 0.05, 0.12)
	add_box(parent, name + "_FrameTop", center + Vector3(0, height * 0.5, 0), Vector3(width + 0.12, 0.09, 0.10), frame, false)
	add_box(parent, name + "_FrameBottom", center - Vector3(0, height * 0.5, 0), Vector3(width + 0.12, 0.09, 0.10), frame, false)
	add_box(parent, name + "_FrameL", center + Vector3(-width * 0.5, 0, 0), Vector3(0.09, height, 0.10), frame, false)
	add_box(parent, name + "_FrameR", center + Vector3(width * 0.5, 0, 0), Vector3(0.09, height, 0.10), frame, false)
	add_box(parent, name + "_FrameMid", center, Vector3(0.07, height - 0.10, 0.09), frame, false)

static func _add_window_x(parent: Node3D, name: String, center: Vector3, width: float, height: float) -> void:
	var frame := Color("#2A2C32")
	var glass := add_box(parent, name + "_Glass", center, Vector3(0.045, height - 0.16, width - 0.16), Color(0.42, 0.67, 0.82, 0.22), false)
	var glass_mesh := _mesh_child(glass)
	glass_mesh.material_override = material(Color(0.42, 0.67, 0.82, 0.22), Color("#587EB8"), 0.20, 0.05, 0.12)
	add_box(parent, name + "_FrameTop", center + Vector3(0, height * 0.5, 0), Vector3(0.10, 0.09, width + 0.12), frame, false)
	add_box(parent, name + "_FrameBottom", center - Vector3(0, height * 0.5, 0), Vector3(0.10, 0.09, width + 0.12), frame, false)
	add_box(parent, name + "_FrameL", center + Vector3(0, 0, -width * 0.5), Vector3(0.10, height, 0.09), frame, false)
	add_box(parent, name + "_FrameR", center + Vector3(0, 0, width * 0.5), Vector3(0.10, height, 0.09), frame, false)
	add_box(parent, name + "_FrameMid", center, Vector3(0.09, height - 0.10, 0.07), frame, false)

static func _add_door_frame_z(parent: Node3D, name: String, center_x: float, z: float, width: float, height: float, color: Color) -> void:
	add_box(parent, name + "_L", Vector3(center_x - width * 0.5, height * 0.5, z), Vector3(0.10, height, 0.14), color, false)
	add_box(parent, name + "_R", Vector3(center_x + width * 0.5, height * 0.5, z), Vector3(0.10, height, 0.14), color, false)
	add_box(parent, name + "_Top", Vector3(center_x, height, z), Vector3(width + 0.10, 0.10, 0.14), color, false)

static func _add_door_frame_x(parent: Node3D, name: String, x: float, center_z: float, width: float, height: float, color: Color) -> void:
	add_box(parent, name + "_L", Vector3(x, height * 0.5, center_z - width * 0.5), Vector3(0.14, height, 0.10), color, false)
	add_box(parent, name + "_R", Vector3(x, height * 0.5, center_z + width * 0.5), Vector3(0.14, height, 0.10), color, false)
	add_box(parent, name + "_Top", Vector3(x, height, center_z), Vector3(0.14, 0.10, width + 0.10), color, false)

static func _build_house_shell(house: Node3D) -> void:
	var floor_color := Color("#D6D0C7")
	var wall := Color("#E9E6E2")
	var stone := Color("#B6AEA3")
	var frame := Color("#2A2C32")

	add_box(house, "GroundFloor", Vector3(0, -0.12, 0), Vector3(16.4, 0.24, 12.4), floor_color, true)

	# Fachada frontal (+Z): grande janela da sala e porta de entrada real.
	add_box(house, "FrontWall_A", Vector3(-7.45, 1.50, 6.10), Vector3(1.30, 3.0, 0.24), stone, true)
	add_box(house, "FrontWall_B", Vector3(-0.55, 1.50, 6.10), Vector3(5.10, 3.0, 0.24), wall, true)
	add_box(house, "FrontWall_C", Vector3(5.75, 1.50, 6.10), Vector3(4.50, 3.0, 0.24), wall, true)
	add_box(house, "FrontWindowLow", Vector3(-4.90, 0.34, 6.10), Vector3(3.80, 0.68, 0.24), wall, true)
	add_box(house, "FrontWindowHigh", Vector3(-4.90, 2.66, 6.10), Vector3(3.80, 0.68, 0.24), wall, true)
	add_box(house, "FrontDoorHeader", Vector3(2.70, 2.66, 6.10), Vector3(1.40, 0.68, 0.24), wall, true)
	_add_window_z(house, "LivingFrontWindow", Vector3(-4.90, 1.50, 6.07), 3.78, 1.62)
	_add_door_frame_z(house, "EntryFrame", 2.70, 6.04, 1.40, 2.34, frame)

	# Parede traseira.
	add_box(house, "BackWall", Vector3(0, 1.50, -6.10), Vector3(16.4, 3.0, 0.24), wall, true)

	# Oeste sólida; leste recebe janela horizontal da cozinha.
	add_box(house, "WestWall", Vector3(-8.10, 1.50, 0), Vector3(0.24, 3.0, 12.0), stone, true)
	add_box(house, "EastWallFront", Vector3(8.10, 1.50, 3.70), Vector3(0.24, 3.0, 4.60), wall, true)
	add_box(house, "EastWallRear", Vector3(8.10, 1.50, -5.10), Vector3(0.24, 3.0, 2.00), wall, true)
	add_box(house, "EastWindowLow", Vector3(8.10, 0.38, -1.45), Vector3(0.24, 0.76, 5.30), wall, true)
	add_box(house, "EastWindowHigh", Vector3(8.10, 2.65, -1.45), Vector3(0.24, 0.70, 5.30), wall, true)
	_add_window_x(house, "KitchenEastWindow", Vector3(8.04, 1.52, -1.45), 5.25, 1.55)

	# Piso do andar superior ao redor do vão real da escada.
	add_box(house, "UpperFloorLeft", Vector3(-5.15, 2.98, 0), Vector3(5.70, 0.24, 12.0), floor_color, true)
	add_box(house, "UpperFloorRight", Vector3(4.10, 2.98, 0), Vector3(7.80, 0.24, 12.0), floor_color, true)
	add_box(house, "UpperFloorRearBridge", Vector3(-1.05, 2.98, -4.05), Vector3(2.50, 0.24, 3.90), floor_color, true)
	add_box(house, "UpperFloorFrontBridge", Vector3(-1.05, 2.98, 5.30), Vector3(2.50, 0.24, 1.60), floor_color, true)

	# Andar superior fechado, deixando porta de vidro para a varanda.
	add_box(house, "UpperBackWall", Vector3(0, 4.50, -6.10), Vector3(16.4, 3.0, 0.24), Color("#3A3940"), true)
	add_box(house, "UpperWestWall", Vector3(-8.10, 4.50, 0), Vector3(0.24, 3.0, 12.0), wall, true)
	add_box(house, "UpperEastWall", Vector3(8.10, 4.50, 0), Vector3(0.24, 3.0, 12.0), wall, true)
	add_box(house, "UpperFrontLeft", Vector3(-4.90, 4.50, 6.10), Vector3(6.40, 3.0, 0.24), wall, true)
	add_box(house, "UpperFrontRight", Vector3(6.20, 4.50, 6.10), Vector3(3.80, 3.0, 0.24), wall, true)
	add_box(house, "UpperBalconyHeader", Vector3(2.30, 5.75, 6.10), Vector3(3.80, 0.50, 0.24), wall, true)
	_add_window_z(house, "BedroomBalconyGlass", Vector3(2.30, 4.45, 6.06), 3.70, 2.40)

	add_box(house, "UpperCeiling", Vector3(0, 6.04, 0), Vector3(16.4, 0.20, 12.4), Color("#D9D6D8"), true)

	# Varanda frontal, coerente com o mesmo céu global.
	add_box(house, "BalconyFloor", Vector3(2.30, 2.98, 7.20), Vector3(5.0, 0.22, 2.0), Color("#C7B9A8"), true)
	var rail_glass := add_box(house, "BalconyGlass", Vector3(2.30, 3.70, 8.10), Vector3(5.0, 1.25, 0.07), Color(0.52, 0.70, 0.82, 0.20), true)
	var rail_mesh := _mesh_child(rail_glass)
	rail_mesh.material_override = material(Color(0.52, 0.70, 0.82, 0.20), Color("#6F91B6"), 0.12, 0.05, 0.12)
	for x in [-0.15, 2.30, 4.75]:
		add_box(house, "BalconyPost", Vector3(x, 3.70, 8.08), Vector3(0.08, 1.35, 0.10), frame, false)

	# Pequena varanda/entrada.
	add_box(house, "EntryPorch", Vector3(2.70, -0.02, 6.85), Vector3(3.1, 0.18, 1.45), Color("#BDB4A9"), true)
	for step_i in range(3):
		add_box(house, "EntryStep_%d" % step_i, Vector3(2.70, -0.18 - step_i * 0.10, 7.42 + step_i * 0.34), Vector3(2.8 + step_i * 0.35, 0.16, 0.62), Color("#C8BFB5"), true)

static func _build_living_room(house: Node3D) -> Dictionary:
	var room := _new_room(house, "LivingRoom")
	var graphite := Color("#20222A")
	var dark := Color("#17191F")

	# Painel gamer no oeste, como a referência enviada.
	add_box(room, "FeatureWall", Vector3(-7.92, 1.48, 1.65), Vector3(0.08, 2.82, 5.7), Color("#181A22"), false)
	var tv := add_box(room, "LivingTV", Vector3(-7.82, 1.62, 1.45), Vector3(0.14, 2.15, 3.85), Color("#17122B"), true, {"action":"tv", "room":"living"})
	tv.set_meta("label", "USAR TV")
	var tv_mesh := _mesh_child(tv)
	tv_mesh.material_override = emissive_material(Color("#25194A"), Color("#765DDE"), 1.75)

	add_box(room, "TVRack", Vector3(-7.42, 0.47, 1.45), Vector3(0.72, 0.62, 4.55), Color("#181A20"), true)
	add_box(room, "Console", Vector3(-7.00, 0.88, 1.45), Vector3(0.34, 0.18, 1.05), Color("#0F1115"), false)

	# Sofá em L com almofadas volumétricas.
	add_box(room, "SofaBase", Vector3(-4.25, 0.28, 3.65), Vector3(4.55, 0.38, 1.60), graphite, true)
	add_box(room, "SofaBack", Vector3(-4.25, 0.82, 4.34), Vector3(4.55, 1.10, 0.28), dark, true)
	add_box(room, "SofaChaise", Vector3(-2.35, 0.28, 2.55), Vector3(1.30, 0.38, 2.50), graphite, true)
	for i in range(4):
		_add_ellipsoid(room, "SofaCushion_%d" % i, Vector3(-5.65 + i * 0.95, 0.77, 4.12), Vector3(0.42, 0.38, 0.13), Color("#2A2D37"))
	_add_ellipsoid(room, "AccentCushion", Vector3(-2.95, 0.80, 4.05), Vector3(0.36, 0.36, 0.12), Color("#4A3A63"))

	add_box(room, "LivingRug", Vector3(-4.55, 0.025, 1.70), Vector3(4.7, 0.05, 3.25), Color("#242732"), false)
	add_box(room, "CoffeeTop", Vector3(-4.55, 0.38, 1.65), Vector3(2.25, 0.12, 1.05), Color("#343841"), true)
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			add_box(room, "CoffeeLeg", Vector3(-4.55 + sx * 0.88, 0.19, 1.65 + sz * 0.38), Vector3(0.08, 0.38, 0.08), Color("#1A1C22"), false)

	# Prateleiras, quadros e itens geek decorativos.
	for shelf_i in range(2):
		add_box(room, "MediaShelf_%d" % shelf_i, Vector3(-7.62, 2.45 + shelf_i * 0.34, 1.45), Vector3(0.36, 0.08, 4.60), Color("#292C34"), false)
	for item_i in range(7):
		var color: Color = [Color("#5A396F"), Color("#315A7A"), Color("#765844"), Color("#385E55")][item_i % 4]
		add_box(room, "GeekFrame_%d" % item_i, Vector3(-7.54, 2.45, -0.10 + item_i * 0.52), Vector3(0.07, 0.48 + float(item_i % 2) * 0.15, 0.32), color, false)

	_add_room_light(room, "LivingMainLight", Vector3(-4.7, 2.45, 2.4), Color("#B9C8FF"), 0.78, 5.6)
	_add_room_light(room, "LivingTVGlow", Vector3(-6.9, 1.6, 1.45), Color("#7156D7"), 0.45, 3.4)
	return {"root":room, "tv":tv}

static func _build_kitchen(house: Node3D) -> Dictionary:
	var room := _new_room(house, "Kitchen")
	var wood := Color("#9A6543")
	var wood_dark := Color("#70452F")
	var stone := Color("#E6D8C6")
	var metal := Color("#9CA4AD")

	# Cozinha em L, coerente com a referência quente enviada.
	add_box(room, "BackCabinetRun", Vector3(4.60, 0.60, -5.55), Vector3(6.20, 1.15, 0.85), wood, true)
	add_box(room, "EastCabinetRun", Vector3(7.45, 0.60, -2.95), Vector3(0.85, 1.15, 4.35), wood, true)
	add_box(room, "BackCounter", Vector3(4.60, 1.22, -5.28), Vector3(6.30, 0.10, 1.05), stone, true)
	add_box(room, "EastCounter", Vector3(7.18, 1.22, -2.95), Vector3(1.05, 0.10, 4.40), stone, true)

	# Armários superiores com módulos independentes.
	for i in range(4):
		add_box(room, "UpperCabinet_%d" % i, Vector3(2.45 + i * 1.45, 2.10, -5.68), Vector3(1.28, 1.15, 0.58), wood, false)
		add_box(room, "UpperHandle_%d" % i, Vector3(2.45 + i * 1.45, 2.00, -5.36), Vector3(0.52, 0.04, 0.05), Color("#45464A"), false)

	# Geladeira, forno e exaustor.
	add_box(room, "Fridge", Vector3(7.32, 1.28, -5.05), Vector3(1.25, 2.55, 1.35), metal, true)
	add_box(room, "FridgeSplit", Vector3(7.00, 1.55, -4.35), Vector3(0.05, 1.95, 1.05), Color("#7D858E"), false)
	add_box(room, "Oven", Vector3(2.05, 0.65, -5.42), Vector3(1.10, 1.20, 0.68), Color("#353941"), true)
	var oven_glass := add_box(room, "OvenGlass", Vector3(2.05, 0.62, -5.05), Vector3(0.82, 0.62, 0.04), Color("#10141A"), false)
	_mesh_child(oven_glass).material_override = emissive_material(Color("#12151C"), Color("#D36B42"), 0.22)
	add_box(room, "Hood", Vector3(3.80, 2.15, -5.38), Vector3(1.55, 0.34, 0.72), metal, false)

	# Cooktop e queimadores.
	var cooktop := add_box(room, "Cooktop", Vector3(3.80, 1.31, -5.28), Vector3(1.55, 0.05, 0.78), Color("#17191F"), false)
	_mesh_child(cooktop).material_override = material(Color("#17191F"), Color("#E35A87"), 0.12, 0.10, 0.16)
	for bx in [3.45, 4.15]:
		for bz in [-5.48, -5.08]:
			add_cylinder(room, "Burner", Vector3(bx, 1.35, bz), 0.14, 0.025, Color("#3B3D44"), false)

	# Pia e torneira.
	add_box(room, "SinkBasin", Vector3(6.00, 1.29, -5.28), Vector3(1.25, 0.08, 0.72), Color("#737C84"), false)
	add_cylinder(room, "FaucetStem", Vector3(6.00, 1.55, -5.52), 0.045, 0.52, metal, false)
	var faucet_spout := add_cylinder(room, "FaucetSpout", Vector3(6.00, 1.78, -5.30), 0.035, 0.42, metal, false)
	faucet_spout.rotation.x = PI * 0.5

	# Ilha central com três bancos.
	add_box(room, "IslandBase", Vector3(4.35, 0.62, -2.55), Vector3(3.75, 1.15, 1.45), wood_dark, true)
	add_box(room, "IslandTop", Vector3(4.35, 1.24, -2.55), Vector3(4.05, 0.12, 1.72), stone, true)
	for stool_x in [3.25, 4.35, 5.45]:
		add_cylinder(room, "StoolStem", Vector3(stool_x, 0.46, -1.30), 0.07, 0.86, Color("#3A3B40"), false)
		add_cylinder(room, "StoolSeat", Vector3(stool_x, 0.92, -1.30), 0.32, 0.10, Color("#5B4437"), false)

	# Temperos/utensílios como cenário.
	for jar_i in range(5):
		var jar_color: Color = [Color("#AD8059"), Color("#748D55"), Color("#B3954C"), Color("#945F68"), Color("#718296")][jar_i]
		add_cylinder(room, "SpiceJar_%d" % jar_i, Vector3(4.95 + jar_i * 0.36, 1.48, -5.25), 0.10, 0.32, jar_color, false)

	for pendant_x in [3.35, 4.35, 5.35]:
		add_cylinder(room, "PendantStem", Vector3(pendant_x, 2.52, -2.55), 0.025, 0.65, Color("#4B4140"), false)
		_add_ellipsoid(room, "PendantBulb", Vector3(pendant_x, 2.16, -2.55), Vector3(0.11, 0.15, 0.11), Color("#FFD7A0"), Color("#FFD0A0"), 2.8)

	_add_room_light(room, "KitchenWarmLight", Vector3(4.55, 2.48, -2.90), Color("#FFD0A0"), 0.82, 5.5)
	return {"root":room}

static func _build_bathroom(house: Node3D) -> Dictionary:
	var room := _new_room(house, "Bathroom")
	var wall := Color("#E9E6E2")
	var stone := Color("#D7D5D4")
	var wood := Color("#80604D")
	var metal := Color("#9BA3AA")

	# Paredes internas com vão de porta verdadeiro.
	add_box(room, "BathSouthWallL", Vector3(-6.85, 1.50, -1.95), Vector3(2.30, 3.0, 0.20), wall, true)
	add_box(room, "BathSouthWallR", Vector3(-3.90, 1.50, -1.95), Vector3(1.10, 3.0, 0.20), wall, true)
	add_box(room, "BathDoorHeader", Vector3(-5.25, 2.66, -1.95), Vector3(1.55, 0.68, 0.20), wall, true)
	add_box(room, "BathEastWall", Vector3(-2.95, 1.50, -4.05), Vector3(0.20, 3.0, 4.10), wall, true)
	_add_door_frame_z(room, "BathroomDoor", -5.25, -1.90, 1.55, 2.34, Color("#A89D93"))

	add_box(room, "BathFloor", Vector3(-5.55, 0.015, -4.00), Vector3(4.85, 0.03, 3.75), Color("#C8C9C8"), false)
	add_box(room, "Vanity", Vector3(-5.70, 0.56, -5.35), Vector3(2.25, 1.0, 0.72), wood, true)
	add_box(room, "VanityTop", Vector3(-5.70, 1.10, -5.35), Vector3(2.40, 0.09, 0.82), stone, false)
	_add_ellipsoid(room, "Sink", Vector3(-5.70, 1.16, -5.30), Vector3(0.52, 0.10, 0.30), Color("#F2F1EF"))
	add_box(room, "Mirror", Vector3(-5.70, 1.88, -5.70), Vector3(2.15, 1.10, 0.05), Color(0.55, 0.68, 0.78, 0.25), false)

	# Vaso com base, caixa e assento.
	add_cylinder(room, "ToiletBase", Vector3(-3.85, 0.38, -4.85), 0.34, 0.62, Color("#ECEBE8"), true)
	_add_ellipsoid(room, "ToiletSeat", Vector3(-3.85, 0.69, -4.72), Vector3(0.36, 0.09, 0.44), Color("#F5F4F1"))
	add_box(room, "ToiletTank", Vector3(-3.85, 0.88, -5.25), Vector3(0.68, 0.78, 0.30), Color("#ECEBE8"), true)

	# Box de vidro real.
	add_box(room, "ShowerTray", Vector3(-6.75, 0.08, -3.05), Vector3(2.10, 0.12, 1.75), Color("#C2C4C5"), true)
	var shower_a := add_box(room, "ShowerGlassA", Vector3(-5.70, 1.15, -3.05), Vector3(0.05, 2.20, 1.75), Color(0.60, 0.77, 0.86, 0.16), true)
	var shower_b := add_box(room, "ShowerGlassB", Vector3(-6.75, 1.15, -2.18), Vector3(2.10, 2.20, 0.05), Color(0.60, 0.77, 0.86, 0.16), true)
	_mesh_child(shower_a).material_override = material(Color(0.60, 0.77, 0.86, 0.16), Color("#7FB5D0"), 0.10, 0.0, 0.08)
	_mesh_child(shower_b).material_override = material(Color(0.60, 0.77, 0.86, 0.16), Color("#7FB5D0"), 0.10, 0.0, 0.08)
	add_cylinder(room, "ShowerPipe", Vector3(-7.45, 1.65, -3.38), 0.035, 1.25, metal, false)

	add_box(room, "TowelBar", Vector3(-3.08, 1.30, -3.30), Vector3(0.08, 0.08, 1.10), metal, false)
	add_box(room, "Towel", Vector3(-3.02, 1.05, -3.30), Vector3(0.05, 0.52, 0.82), Color("#D7D9DF"), false)
	_add_room_light(room, "BathroomLight", Vector3(-5.55, 2.50, -4.0), Color("#E8F2FF"), 0.66, 4.1)
	return {"root":room}

static func _build_staircase(house: Node3D) -> Node3D:
	var stairs := _new_room(house, "StairHall")
	var wood := Color("#8C6448")
	var rail := Color("#37383E")
	var step_count := 14
	var start_z := 4.15
	var step_depth := 0.42
	var rise := 2.88 / float(step_count)
	for i in range(step_count):
		var y := 0.11 + float(i) * rise
		var z := start_z - float(i) * step_depth
		add_box(stairs, "Step_%02d" % i, Vector3(-1.00, y, z), Vector3(1.95, 0.22, 0.50), wood, false)
		add_box(stairs, "Riser_%02d" % i, Vector3(-1.00, y - rise * 0.45, z + 0.20), Vector3(1.95, rise, 0.08), wood.darkened(0.12), false)

	var ramp := StaticBody3D.new()
	ramp.name = "StairRampCollision"
	ramp.position = Vector3(-1.00, 1.50, 1.42)
	ramp.rotation.x = atan2(2.88, float(step_count) * step_depth)
	var shape_node := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(1.86, 0.16, float(step_count) * step_depth)
	shape_node.shape = shape
	ramp.add_child(shape_node)
	stairs.add_child(ramp)

	# Corrimão visual.
	for post_i in range(8):
		var t := float(post_i) / 7.0
		var z := lerpf(start_z, start_z - float(step_count - 1) * step_depth, t)
		var y := lerpf(0.75, 3.48, t)
		add_cylinder(stairs, "RailPost", Vector3(-2.02, y, z), 0.035, 0.80, rail, false)
	var top_rail := add_box(stairs, "TopRail", Vector3(-2.02, 2.10, 1.42), Vector3(0.07, 0.07, 5.80), rail, false)
	top_rail.rotation.x = -atan2(2.73, 5.80)
	return stairs

static func _build_bedroom(house: Node3D) -> Dictionary:
	var room := _new_room(house, "Bedroom")
	var graphite := Color("#20222A")
	var wall_dark := Color("#32323A")
	var lilac := Color("#7255C9")

	# Painel escuro da TV no lado oeste.
	add_box(room, "BedroomTVPanel", Vector3(-7.92, 4.48, -0.10), Vector3(0.08, 2.65, 4.40), wall_dark, false)
	var tv := add_box(room, "BedroomTV", Vector3(-7.80, 4.45, -0.10), Vector3(0.14, 1.72, 3.10), Color("#17122B"), true, {"action":"tv", "room":"bedroom"})
	tv.set_meta("label", "USAR TV")
	_mesh_child(tv).material_override = emissive_material(Color("#2B1D50"), Color("#9365EB"), 1.80)
	add_box(room, "BedroomTVConsole", Vector3(-7.42, 3.55, -0.10), Vector3(0.72, 0.58, 3.45), graphite, true)

	# Cama baseada na referência isométrica.
	add_box(room, "BedBase", Vector3(-4.15, 3.32, -2.65), Vector3(3.25, 0.52, 4.20), Color("#3A3742"), true)
	add_box(room, "Mattress", Vector3(-4.15, 3.69, -2.65), Vector3(3.08, 0.30, 4.05), Color("#E1DDE2"), false)
	add_box(room, "Headboard", Vector3(-4.15, 4.25, -4.62), Vector3(3.30, 1.30, 0.18), Color("#272831"), false)
	for side in [-1.0, 1.0]:
		_add_ellipsoid(room, "Pillow", Vector3(-4.15 + side * 0.68, 3.94, -4.00), Vector3(0.62, 0.15, 0.42), Color("#F1EEF2"))
	add_box(room, "BedRunner", Vector3(-4.15, 3.86, -1.35), Vector3(3.02, 0.05, 0.72), Color("#493A61"), false)

	# Criados e luminárias.
	for side in [-1.0, 1.0]:
		var side_value: float = float(side)
		var nx: float = -4.15 + side_value * 2.05
		add_box(room, "Nightstand", Vector3(nx, 3.40, -4.10), Vector3(0.72, 0.62, 0.72), Color("#44434A"), true)
		add_cylinder(room, "LampStem", Vector3(nx, 4.02, -4.10), 0.035, 0.58, Color("#797984"), false)
		_add_ellipsoid(room, "LampGlow", Vector3(nx, 4.30, -4.10), Vector3(0.18, 0.15, 0.18), Color("#D8C7FF"), Color("#C6ABFF"), 1.8)

	# Mesa em L + dual monitors + torre.
	add_box(room, "DeskBack", Vector3(3.95, 3.58, -5.35), Vector3(5.55, 0.18, 1.05), graphite, true)
	add_box(room, "DeskSide", Vector3(7.18, 3.58, -3.35), Vector3(0.95, 0.18, 4.90), graphite, true)
	for monitor_value in [3.25, 5.30]:
		var monitor_x: float = float(monitor_value)
		var monitor := add_box(room, "Monitor", Vector3(monitor_x, 4.30, -4.80), Vector3(1.72, 0.98, 0.10), Color("#171429"), false)
		_mesh_child(monitor).material_override = emissive_material(Color("#241C47"), Color("#8157E4"), 1.85)
		add_cylinder(room, "MonitorStem", Vector3(monitor_x, 3.82, -4.78), 0.035, 0.42, Color("#34353C"), false)

	var pc := add_box(room, "BedroomPC", Vector3(6.95, 4.08, -4.82), Vector3(0.78, 1.35, 0.96), Color("#1A1B22"), true, {"action":"future_pc"})
	pc.set_meta("label", "PC — FUTURO")
	_mesh_child(pc).material_override = material(Color("#23242D"), Color("#8557D5"), 0.65, 0.12, 0.28)

	# Cadeira gamer.
	add_box(room, "ChairSeat", Vector3(4.55, 3.33, -3.78), Vector3(0.82, 0.16, 0.82), Color("#17191F"), true)
	add_box(room, "ChairBack", Vector3(4.55, 4.12, -4.10), Vector3(0.88, 1.42, 0.20), Color("#1C1E27"), true)
	add_cylinder(room, "ChairStem", Vector3(4.55, 3.05, -3.78), 0.08, 0.52, Color("#2C2E35"), false)

	# Roupeiro à direita; a porta continua sendo o ponto de interação.
	var wardrobe := add_box(room, "Wardrobe", Vector3(7.50, 4.48, 1.10), Vector3(0.82, 2.85, 3.10), Color("#D8D6DA"), true, {"action":"wardrobe"})
	wardrobe.set_meta("label", "ROUPAS")
	for door_i in range(2):
		var z := 0.38 + door_i * 1.42
		add_box(room, "WardrobeDoor_%d" % door_i, Vector3(7.06, 4.48, z), Vector3(0.06, 2.62, 1.32), Color("#ECE9EE"), false)
		add_box(room, "WardrobeHandle_%d" % door_i, Vector3(7.00, 4.48, z + (-0.18 if door_i == 0 else 0.18)), Vector3(0.04, 0.46, 0.04), Color("#575A63"), false)

	# Espelho, prateleiras geek, livros e figuras.
	add_box(room, "WardrobeMirror", Vector3(7.02, 4.48, 2.93), Vector3(0.05, 2.48, 0.56), Color(0.56, 0.70, 0.80, 0.24), false)
	for shelf_i in range(3):
		add_box(room, "GeekShelf_%d" % shelf_i, Vector3(-0.20, 4.10 + shelf_i * 0.56, -5.82), Vector3(3.10, 0.10, 0.40), Color("#E7E4E4"), false)
	for item_i in range(12):
		var col: Color = [Color("#7B394F"), Color("#315B7C"), Color("#856F3F"), Color("#4D3E72"), Color("#4D6B55")][item_i % 5]
		var row: int = int(item_i / 6)
		var x: float = -1.45 + float(item_i % 6) * 0.50
		add_box(room, "GeekItem_%02d" % item_i, Vector3(x, 4.36 + row * 0.56, -5.62), Vector3(0.20, 0.30 + float(item_i % 3) * 0.07, 0.18), col, false)

	add_box(room, "BedroomRug", Vector3(1.60, 3.05, -1.15), Vector3(5.7, 0.05, 3.8), Color("#24252D"), false)
	_add_room_light(room, "BedroomMainLight", Vector3(0.5, 5.48, -0.2), Color("#D2C7FF"), 0.72, 6.0)
	_add_room_light(room, "DeskVioletGlow", Vector3(4.5, 4.25, -4.0), lilac, 0.38, 3.8)
	return {"root":room, "tv":tv, "wardrobe":wardrobe, "pc":pc}

static func _build_house_exterior(house: Node3D) -> void:
	# Jardim tropical simples, coerente com a fachada de referência.
	for data in [
		[Vector3(-10.0, 0.0, 5.8), 0.95],
		[Vector3(10.0, 0.0, 4.8), 0.80],
		[Vector3(-10.5, 0.0, -4.5), 0.75],
		[Vector3(10.2, 0.0, -4.2), 0.85],
	]:
		_add_tree(house, data[0], float(data[1]))

	# Caminho de entrada.
	for i in range(7):
		add_box(house, "PathStone_%d" % i, Vector3(2.70, -0.12, 8.45 + i * 0.72), Vector3(1.55, 0.10, 0.52), Color("#C6C1BA"), false)

static func _set_node_material(node: Node, mat: Material) -> void:
	if node is MeshInstance3D:
		node.material_override = mat
	else:
		set_holder_material(node, mat)

static func _apply_house_materials(node: Node) -> void:
	for child in node.get_children():
		var n := child.name.to_lower()
		var preserve := (
			"tv" in n
			or "monitor" in n
			or "glass" in n
			or "mirror" in n
			or "glow" in n
			or "bulb" in n
			or "eye" in n
			or "star" in n
		)
		if not preserve:
			if "wall" in n or "ceiling" in n or "header" in n:
				_set_node_material(child, textured_material("plaster.png", Color("#F0EEEB"), 0.0, 0.78, 2.4))
			elif "bathfloor" in n or "showertray" in n:
				_set_node_material(child, textured_material("tile_light.png", Color("#E8E8E5"), 0.0, 0.42, 2.2))
			elif "groundfloor" in n or "upperfloor" in n or "balconyfloor" in n or "entryporch" in n or "pathstone" in n:
				_set_node_material(child, textured_material("floor_warm.png", Color("#D8D0C4"), 0.0, 0.55, 3.0))
			elif "counter" in n or "islandtop" in n or "vanitytop" in n or "coffeetop" in n:
				_set_node_material(child, textured_material("stone_marble.png", Color("#F2EADF"), 0.0, 0.28, 2.2))
			elif (
				"cabinet" in n
				or "desk" in n
				or "nightstand" in n
				or "vanity" in n
				or "shelf" in n
				or "wardrobe" in n
				or "step_" in n
				or "riser_" in n
				or "rack" in n
			):
				_set_node_material(child, textured_material("wood_warm.png", Color("#A87350"), 0.0, 0.48, 2.8))
			elif (
				"sofa" in n
				or "cushion" in n
				or "bedbase" in n
				or "mattress" in n
				or "pillow" in n
				or "headboard" in n
				or "rug" in n
				or "chair" in n
				or "towel" in n
			):
				_set_node_material(child, textured_material("fabric_dark.png", Color("#757783") if ("mattress" in n or "pillow" in n or "towel" in n) else Color("#353843"), 0.0, 0.88, 4.0))
			elif (
				"fridge" in n
				or "sink" in n
				or "faucet" in n
				or "hood" in n
				or "handle" in n
				or "rail" in n
				or "oven" in n
				or "stem" in n
			):
				_set_node_material(child, textured_material("brushed_metal.png", Color("#BFC6CD"), 0.72, 0.22, 3.0))
			elif "panel" in n or "console" in n or "pc" in n or "cooktop" in n:
				_set_node_material(child, textured_material("tech_panel.png", Color("#5C6170"), 0.24, 0.30, 3.5))
		_apply_house_materials(child)

static func _add_recessed_light(parent: Node3D, name: String, position: Vector3, color: Color = Color("#D9E5FF")) -> void:
	var ring := add_cylinder(parent, name + "_Ring", position, 0.115, 0.035, Color("#6E737E"), false)
	set_holder_material(ring, textured_material("brushed_metal.png", Color("#A8AFB8"), 0.74, 0.18, 2.0))
	var core := add_cylinder(parent, name + "_Core", position - Vector3(0, 0.025, 0), 0.078, 0.025, color, false)
	set_holder_material(core, emissive_material(color, color, 2.8))

static func _add_potted_plant(parent: Node3D, name: String, position: Vector3, scale_value: float = 1.0) -> void:
	var pot := add_cylinder(parent, name + "_Pot", position + Vector3(0, 0.22 * scale_value, 0), 0.22 * scale_value, 0.42 * scale_value, Color("#C6B9A7"), false)
	set_holder_material(pot, textured_material("stone_marble.png", Color("#D8D0C3"), 0.0, 0.62, 2.0))
	for i in range(10):
		var angle := TAU * float(i) / 10.0
		var leaf := _add_ellipsoid(
			parent,
			name + "_Leaf_%02d" % i,
			position + Vector3(cos(angle) * 0.16, 0.62 + float(i % 3) * 0.10, sin(angle) * 0.16) * scale_value,
			Vector3(0.075, 0.28, 0.035) * scale_value,
			Color("#4A7D57")
		)
		leaf.rotation.y = -angle
		leaf.rotation.z = sin(angle) * 0.28

static func _add_house_microdetail(house: Node3D) -> void:
	# Rodapés e guarnições internas.
	var trim_mat := textured_material("wood_warm.png", Color("#70513F"), 0.0, 0.45, 3.0)
	for data in [
		[Vector3(-4.9, 0.11, 5.82), Vector3(5.9, 0.12, 0.08)],
		[Vector3(4.8, 0.11, 5.82), Vector3(5.7, 0.12, 0.08)],
		[Vector3(-7.82, 0.11, 1.1), Vector3(0.08, 0.12, 8.8)],
		[Vector3(7.82, 0.11, -1.2), Vector3(0.08, 0.12, 8.2)],
	]:
		var trim := add_box(house, "Baseboard", data[0], data[1], Color("#70513F"), false)
		set_holder_material(trim, trim_mat)

	# Ripado tecnológico da sala.
	for i in range(18):
		var slat := add_box(house, "LivingSlat_%02d" % i, Vector3(-7.73, 1.45, -0.85 + float(i) * 0.17), Vector3(0.07, 2.55, 0.055), Color("#38333B"), false)
		set_holder_material(slat, textured_material("wood_warm.png", Color("#604638"), 0.0, 0.42, 5.0))

	# Painel ripado e detalhes geek do quarto.
	for i in range(20):
		var x := -1.75 + float(i) * 0.18
		var slat := add_box(house, "BedroomSlat_%02d" % i, Vector3(x, 4.55, -5.93), Vector3(0.055, 2.45, 0.07), Color("#3D3544"), false)
		set_holder_material(slat, textured_material("wood_warm.png", Color("#57403A"), 0.0, 0.46, 5.0))

	# Portas e frentes dos armários da cozinha para quebrar os blocos longos.
	for i in range(5):
		var door := add_box(house, "KitchenCabinetDoor_%02d" % i, Vector3(2.10 + float(i) * 1.15, 0.63, -5.10), Vector3(1.02, 0.92, 0.055), Color("#9A6543"), false)
		set_holder_material(door, textured_material("wood_warm.png", Color("#A87350"), 0.0, 0.44, 2.8))
		var handle := add_box(house, "KitchenDoorHandle_%02d" % i, Vector3(2.10 + float(i) * 1.15, 0.76, -5.06), Vector3(0.34, 0.035, 0.035), Color("#AEB5BE"), false)
		set_holder_material(handle, textured_material("brushed_metal.png", Color("#C9CFD6"), 0.78, 0.18, 2.0))

	# Spots distribuídos pelos ambientes.
	for data in [
		["LivingSpotA", Vector3(-5.8, 2.82, 1.0)],
		["LivingSpotB", Vector3(-3.0, 2.82, 3.4)],
		["KitchenSpotA", Vector3(3.0, 2.82, -4.0)],
		["KitchenSpotB", Vector3(6.0, 2.82, -2.3)],
		["HallSpot", Vector3(-0.8, 2.82, 3.5)],
		["BedroomSpotA", Vector3(-4.5, 5.87, -1.8)],
		["BedroomSpotB", Vector3(1.0, 5.87, -3.4)],
		["BedroomSpotC", Vector3(5.5, 5.87, 0.8)],
	]:
		_add_recessed_light(house, str(data[0]), data[1])

	# Iluminação indireta em linhas.
	for data in [
		[Vector3(-7.60, 2.50, 1.45), Vector3(0.025, 0.035, 4.20), Color("#765DDE")],
		[Vector3(4.25, 2.68, -5.65), Vector3(4.80, 0.025, 0.035), Color("#FFC88E")],
		[Vector3(3.80, 5.55, -5.70), Vector3(5.80, 0.025, 0.035), Color("#8C6BE9")],
	]:
		var strip := add_box(house, "IndirectLight", data[0], data[1], data[2], false)
		set_holder_material(strip, emissive_material(data[2], data[2], 2.4))

	# Plantas internas e de varanda.
	_add_potted_plant(house, "LivingPlant", Vector3(-2.15, 0.0, 5.10), 0.85)
	_add_potted_plant(house, "KitchenPlant", Vector3(7.25, 0.0, 4.65), 0.75)
	_add_potted_plant(house, "BedroomPlant", Vector3(6.65, 3.00, 5.05), 0.78)
	_add_potted_plant(house, "BalconyPlantA", Vector3(0.55, 3.00, 7.30), 0.80)
	_add_potted_plant(house, "BalconyPlantB", Vector3(4.05, 3.00, 7.30), 0.80)

	# Fachada com ripado vertical, arandelas e paisagismo denso.
	for i in range(15):
		var fx := -7.72 + float(i) * 0.16
		var facade_slat := add_box(house, "FacadeSlat_%02d" % i, Vector3(fx, 1.50, 6.20), Vector3(0.055, 2.72, 0.11), Color("#76533D"), false)
		set_holder_material(facade_slat, textured_material("wood_warm.png", Color("#76533D"), 0.0, 0.42, 5.0))

	for x in [1.55, 3.85]:
		var sconce := add_box(house, "FacadeSconce", Vector3(x, 1.55, 6.23), Vector3(0.16, 0.38, 0.10), Color("#23252C"), false)
		set_holder_material(sconce, textured_material("tech_panel.png", Color("#3B3D46"), 0.28, 0.28, 3.0))
		var glow := add_box(house, "FacadeSconceGlow", Vector3(x, 1.55, 6.30), Vector3(0.09, 0.24, 0.03), Color("#FFD7A7"), false)
		set_holder_material(glow, emissive_material(Color("#FFD7A7"), Color("#FFD0A0"), 2.3))

	for i in range(18):
		var angle := TAU * float(i) / 18.0
		var radius := 10.8 + float(i % 3) * 0.55
		var shrub_pos := Vector3(cos(angle) * radius, -0.02, sin(angle) * radius + 1.4)
		for leaf_i in range(3):
			var leaf := _add_ellipsoid(
				house,
				"GardenShrub_%02d_%d" % [i, leaf_i],
				shrub_pos + Vector3((float(leaf_i) - 1.0) * 0.18, 0.30 + float(leaf_i % 2) * 0.12, 0),
				Vector3(0.30, 0.34, 0.30),
				Color("#3F6C49").lightened(float(leaf_i) * 0.04)
			)
			leaf.rotation.y = angle

static func scene_triangle_count(node: Node) -> int:
	var total := 0
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh != null:
			total += int(mesh_instance.mesh.get_faces().size() / 3)
	for child in node.get_children():
		total += scene_triangle_count(child)
	return total

static func build_house(parent: Node3D) -> Dictionary:
	var result := {}
	var house := Node3D.new()
	house.name = "STARHouse"
	parent.add_child(house)

	add_cylinder(house, "HouseIsland", Vector3(0, -1.55, 1.4), 18.5, 2.9, Color("#3F4D39"), true)
	add_cylinder(house, "HouseGarden", Vector3(0, -0.25, 1.4), 18.0, 0.18, Color("#557052"), false)

	_build_house_shell(house)
	var living := _build_living_room(house)
	var kitchen := _build_kitchen(house)
	var bathroom := _build_bathroom(house)
	_build_staircase(house)
	var bedroom := _build_bedroom(house)
	_build_house_exterior(house)

	# Direção de arte do cenário: materiais texturizados e microgeometria.
	_apply_house_materials(house)
	_add_house_microdetail(house)
	var environment_triangles := scene_triangle_count(house)
	house.set_meta("environment_triangle_count", environment_triangles)

	# A STAR Bot recebe quem entra no ambiente principal.
	var avatar := build_star_avatar(house, "cypher_system")
	avatar.position = Vector3(-0.15, 0.0, 1.25)
	avatar.rotation.y = 0.0
	avatar.scale = Vector3.ONE * 0.74

	result["root"] = house
	result["avatar"] = avatar
	result["spawn"] = Vector3(2.70, 0.32, 5.25)
	result["spawn_yaw"] = 0.0
	result["living_tv"] = living.tv
	result["bedroom_tv"] = bedroom.tv
	result["wardrobe"] = bedroom.wardrobe
	result["room_count"] = 4
	result["environment_triangle_count"] = environment_triangles
	result["room_nodes"] = {
		"living": living.root,
		"kitchen": kitchen.root,
		"bathroom": bathroom.root,
		"bedroom": bedroom.root,
	}
	return result

static func _bot_sphere(name: String, position: Vector3, radii: Vector3, mat: Material, radial_segments: int = 48, rings: int = 24) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = name
	var mesh := SphereMesh.new()
	mesh.radius = 0.5
	mesh.height = 1.0
	mesh.radial_segments = radial_segments
	mesh.rings = rings
	node.mesh = mesh
	node.position = position
	node.scale = radii * 2.0
	node.material_override = mat
	return node

static func _bot_capsule(name: String, position: Vector3, radius: float, height: float, mat: Material, radial_segments: int = 40, rings: int = 14) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = name
	var mesh := CapsuleMesh.new()
	mesh.radius = radius
	mesh.height = maxf(height, radius * 2.05)
	mesh.radial_segments = radial_segments
	mesh.rings = rings
	node.mesh = mesh
	node.position = position
	node.material_override = mat
	return node

static func _bot_cylinder(name: String, position: Vector3, top_radius: float, bottom_radius: float, height: float, mat: Material, radial_segments: int = 64) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = name
	var mesh := CylinderMesh.new()
	mesh.top_radius = top_radius
	mesh.bottom_radius = bottom_radius
	mesh.height = height
	mesh.radial_segments = radial_segments
	node.mesh = mesh
	node.position = position
	node.material_override = mat
	return node

static func _bot_profile_mesh(name: String, position: Vector3, profile: Array, mat: Material, segments: int = 64) -> MeshInstance3D:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for ring_i in range(profile.size() - 1):
		var lower: Array = profile[ring_i]
		var upper: Array = profile[ring_i + 1]
		var y0 := float(lower[0])
		var r0 := float(lower[1])
		var d0 := float(lower[2])
		var y1 := float(upper[0])
		var r1 := float(upper[1])
		var d1 := float(upper[2])
		for segment in range(segments):
			var a0 := TAU * float(segment) / float(segments)
			var a1 := TAU * float(segment + 1) / float(segments)
			var p00 := Vector3(cos(a0) * r0, y0, sin(a0) * d0)
			var p01 := Vector3(cos(a1) * r0, y0, sin(a1) * d0)
			var p10 := Vector3(cos(a0) * r1, y1, sin(a0) * d1)
			var p11 := Vector3(cos(a1) * r1, y1, sin(a1) * d1)
			surface.add_vertex(p00)
			surface.add_vertex(p10)
			surface.add_vertex(p11)
			surface.add_vertex(p00)
			surface.add_vertex(p11)
			surface.add_vertex(p01)
	surface.generate_normals()
	var node := MeshInstance3D.new()
	node.name = name
	node.mesh = surface.commit()
	node.position = position
	node.material_override = mat
	return node

static func _mark_bot_role(node: Node, role: String) -> void:
	if node is MeshInstance3D:
		node.set_meta("bot_role", role)
	for child in node.get_children():
		_mark_bot_role(child, role)

static func _bot_add_eye(body: Node3D, x: float, y: float, z: float, glow_mat: Material) -> MeshInstance3D:
	var eye := _bot_sphere("Eye", Vector3(x, y, z), Vector3(0.058, 0.095, 0.020), glow_mat, 36, 16)
	body.add_child(eye)
	_mark_bot_role(eye, "screen_glow")
	return eye

static func _bot_add_hand(body: Node3D, side: float, joint_mat: Material, shell_mat: Material) -> void:
	var x := 0.355 * side
	var palm := _bot_sphere("Palm", Vector3(x, 0.455, 0.015), Vector3(0.080, 0.082, 0.070), joint_mat, 36, 16)
	body.add_child(palm)
	_mark_bot_role(palm, "joint")
	for finger_i in range(3):
		var finger_x := x + (float(finger_i) - 1.0) * 0.030 * side
		var finger := _bot_capsule("Finger_%d" % finger_i, Vector3(finger_x, 0.405, 0.035), 0.016, 0.105, joint_mat, 18, 7)
		finger.rotation.z = 0.12 * side * (float(finger_i) - 1.0)
		body.add_child(finger)
		_mark_bot_role(finger, "joint")
	var cuff := _bot_cylinder("WristCuff", Vector3(x, 0.510, 0.0), 0.085, 0.085, 0.08, shell_mat, 40)
	body.add_child(cuff)
	_mark_bot_role(cuff, "shell")

static func _bot_add_hair(body: Node3D, hair_mat: Material, hair_light_mat: Material) -> void:
	var cap := _bot_sphere("HairCrown", Vector3(0, 1.205, -0.090), Vector3(0.390, 0.360, 0.330), hair_mat, 56, 28)
	body.add_child(cap)
	_mark_bot_role(cap, "hair")

	var strand_specs := [
		[Vector3(-0.290, 0.920, -0.160), 0.095, 0.63, -0.09],
		[Vector3(-0.205, 0.835, -0.235), 0.105, 0.76, -0.05],
		[Vector3(-0.105, 0.800, -0.290), 0.108, 0.82, -0.02],
		[Vector3(0.000, 0.785, -0.315), 0.110, 0.85, 0.00],
		[Vector3(0.105, 0.800, -0.290), 0.108, 0.82, 0.02],
		[Vector3(0.205, 0.835, -0.235), 0.105, 0.76, 0.05],
		[Vector3(0.290, 0.920, -0.160), 0.095, 0.63, 0.09],
		[Vector3(-0.345, 1.000, -0.030), 0.070, 0.52, -0.14],
		[Vector3(0.345, 1.000, -0.030), 0.070, 0.52, 0.14],
	]
	for i in range(strand_specs.size()):
		var data: Array = strand_specs[i]
		var strand := _bot_capsule(
			"HairStrand_%02d" % i,
			data[0],
			float(data[1]),
			float(data[2]),
			hair_light_mat if i % 3 == 0 else hair_mat,
			36,
			12
		)
		strand.rotation.z = float(data[3])
		body.add_child(strand)
		_mark_bot_role(strand, "hair")

	for side in [-1.0, 1.0]:
		var side_value := float(side)
		var lock := _bot_capsule("FaceLock", Vector3(0.315 * side_value, 1.115, 0.160), 0.055, 0.46, hair_light_mat, 32, 10)
		lock.rotation.z = 0.12 * side_value
		body.add_child(lock)
		_mark_bot_role(lock, "hair")

static func _bot_triangle_count(node: Node) -> int:
	var total := 0
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh != null:
			total += int(mesh_instance.mesh.get_faces().size() / 3)
	for child in node.get_children():
		total += _bot_triangle_count(child)
	return total

static func build_star_avatar(parent: Node3D, skin_id: String = "cypher_system") -> Node3D:
	var avatar := Node3D.new()
	avatar.name = "STARAvatar"
	avatar.set_meta("physical_form", "star_bot")
	avatar.set_meta("reference_style", "STAR Bot concept 2026-10-04")
	avatar.set_meta("skin_id", skin_id)
	parent.add_child(avatar)

	var body := Node3D.new()
	body.name = "STARBotBody"
	avatar.add_child(body)

	var shell_mat := material(Color("#E8EDF3"), Color("#CFE8FF"), 0.08, 0.12, 0.28)
	var shell_blue := material(Color("#B8D7EC"), Color("#83CFFF"), 0.12, 0.12, 0.25)
	var dark_mat := material(Color("#1B2230"), Color("#33466A"), 0.05, 0.38, 0.22)
	var joint_mat := material(Color("#151922"), Color("#24324A"), 0.03, 0.48, 0.18)
	var visor_mat := material(Color("#050811"), Color("#07111E"), 0.10, 0.72, 0.06)
	var glow_mat := emissive_material(Color("#9EEAFF"), Color("#72D9FF"), 4.2)
	var hair_mat := material(Color("#E9BE72"), Color("#C89443"), 0.06, 0.04, 0.35)
	var hair_light := material(Color("#F4D28F"), Color("#E5AE5A"), 0.08, 0.03, 0.30)
	var metal_mat := textured_material("brushed_metal.png", Color("#D7DDE5"), 0.75, 0.20, 2.0)

	# Base compacta e estável da referência.
	var base_lower := _bot_cylinder("BaseLower", Vector3(0, 0.095, 0), 0.330, 0.365, 0.17, dark_mat, 72)
	body.add_child(base_lower)
	_mark_bot_role(base_lower, "joint")
	var base_shell := _bot_cylinder("BaseShell", Vector3(0, 0.205, 0), 0.315, 0.340, 0.17, shell_mat, 72)
	body.add_child(base_shell)
	_mark_bot_role(base_shell, "shell")
	var base_glow := _bot_cylinder("BaseGlow", Vector3(0, 0.108, 0), 0.347, 0.347, 0.025, glow_mat, 80)
	body.add_child(base_glow)
	_mark_bot_role(base_glow, "screen_glow")

	# Tronco blindado suavemente afunilado.
	var torso_profile := [
		[0.00, 0.310, 0.270],
		[0.12, 0.305, 0.265],
		[0.30, 0.275, 0.245],
		[0.46, 0.245, 0.225],
		[0.60, 0.300, 0.255],
	]
	var torso := _bot_profile_mesh("TorsoShell", Vector3(0, 0.250, 0), torso_profile, shell_mat, 72)
	body.add_child(torso)
	_mark_bot_role(torso, "shell")
	var chest_plate := _bot_sphere("ChestPlate", Vector3(0, 0.690, 0.245), Vector3(0.225, 0.205, 0.060), shell_blue, 48, 22)
	body.add_child(chest_plate)
	_mark_bot_role(chest_plate, "shell")

	var chest_star := CrystalStar3D.new()
	chest_star.name = "ChestStar"
	chest_star.star_size = 0.105
	chest_star.rotation_speed = 0.0
	chest_star.energy = 2.4
	chest_star.position = Vector3(0, 0.715, 0.310)
	body.add_child(chest_star)

	# Pescoço mecânico.
	var neck_dark := _bot_cylinder("NeckJoint", Vector3(0, 0.850, 0), 0.105, 0.115, 0.14, joint_mat, 48)
	body.add_child(neck_dark)
	_mark_bot_role(neck_dark, "joint")
	var neck_ring := _bot_cylinder("NeckRing", Vector3(0, 0.900, 0), 0.135, 0.135, 0.035, metal_mat, 56)
	body.add_child(neck_ring)
	_mark_bot_role(neck_ring, "metal")

	# Cabeça grande chibi, visor frontal e moldura clara.
	var head_shell := _bot_sphere("HeadShell", Vector3(0, 1.185, 0), Vector3(0.430, 0.355, 0.385), shell_mat, 64, 30)
	body.add_child(head_shell)
	_mark_bot_role(head_shell, "shell")
	var face_frame := _bot_sphere("FaceFrame", Vector3(0, 1.170, 0.230), Vector3(0.372, 0.285, 0.145), dark_mat, 60, 28)
	body.add_child(face_frame)
	_mark_bot_role(face_frame, "joint")
	var visor := _bot_sphere("Visor", Vector3(0, 1.170, 0.305), Vector3(0.330, 0.240, 0.092), visor_mat, 64, 30)
	body.add_child(visor)
	_mark_bot_role(visor, "visor")
	_bot_add_eye(body, -0.115, 1.185, 0.390, glow_mat)
	_bot_add_eye(body, 0.115, 1.185, 0.390, glow_mat)

	# Pods laterais inspirados nos detalhes circulares da referência.
	for side in [-1.0, 1.0]:
		var s := float(side)
		var pod_outer := _bot_cylinder("SidePodOuter", Vector3(0.430 * s, 1.185, 0.015), 0.125, 0.125, 0.105, dark_mat, 64)
		pod_outer.rotation.z = PI * 0.5
		body.add_child(pod_outer)
		_mark_bot_role(pod_outer, "joint")
		var pod_glow := _bot_cylinder("SidePodGlow", Vector3(0.486 * s, 1.185, 0.015), 0.103, 0.103, 0.015, glow_mat, 72)
		pod_glow.rotation.z = PI * 0.5
		body.add_child(pod_glow)
		_mark_bot_role(pod_glow, "screen_glow")
		var pod_center := _bot_cylinder("SidePodCenter", Vector3(0.496 * s, 1.185, 0.015), 0.072, 0.072, 0.020, visor_mat, 64)
		pod_center.rotation.z = PI * 0.5
		body.add_child(pod_center)
		_mark_bot_role(pod_center, "visor")

		var pod_star := CrystalStar3D.new()
		pod_star.name = "SideStar"
		pod_star.star_size = 0.050
		pod_star.rotation_speed = 0.0
		pod_star.energy = 2.0
		pod_star.position = Vector3(0.510 * s, 1.185, 0.015)
		pod_star.rotation.y = PI * 0.5 * s
		body.add_child(pod_star)

	# Cabelo longo e estilizado envolvendo a cabeça.
	_bot_add_hair(body, hair_mat, hair_light)

	# Clip superior com símbolo da STAR.
	var top_clip := _bot_sphere("TopClip", Vector3(0, 1.505, 0.080), Vector3(0.130, 0.055, 0.100), shell_mat, 36, 16)
	body.add_child(top_clip)
	_mark_bot_role(top_clip, "shell")
	var top_star := CrystalStar3D.new()
	top_star.name = "TopStar"
	top_star.star_size = 0.045
	top_star.rotation_speed = 0.0
	top_star.energy = 1.8
	top_star.position = Vector3(0, 1.520, 0.150)
	body.add_child(top_star)

	# Braços articulados com juntas escuras, carenagem clara e mãos de três dedos.
	for side in [-1.0, 1.0]:
		var s := float(side)
		var shoulder := _bot_sphere("ShoulderJoint", Vector3(0.315 * s, 0.760, 0), Vector3(0.105, 0.105, 0.105), joint_mat, 44, 20)
		body.add_child(shoulder)
		_mark_bot_role(shoulder, "joint")
		var upper := _bot_capsule("UpperArmShell", Vector3(0.360 * s, 0.650, 0), 0.090, 0.300, shell_mat, 40, 14)
		upper.rotation.z = 0.16 * s
		body.add_child(upper)
		_mark_bot_role(upper, "shell")
		var elbow := _bot_sphere("ElbowJoint", Vector3(0.380 * s, 0.545, 0), Vector3(0.072, 0.072, 0.072), joint_mat, 36, 16)
		body.add_child(elbow)
		_mark_bot_role(elbow, "joint")
		var forearm := _bot_capsule("ForearmShell", Vector3(0.365 * s, 0.515, 0), 0.078, 0.240, shell_blue, 40, 14)
		forearm.rotation.z = -0.10 * s
		body.add_child(forearm)
		_mark_bot_role(forearm, "shell")
		_bot_add_hand(body, s, joint_mat, shell_mat)

	# Linhas emissivas do traje tecnológico.
	for side in [-1.0, 1.0]:
		var s := float(side)
		var line := add_box(body, "TorsoGlowLine", Vector3(0.205 * s, 0.565, 0.250), Vector3(0.018, 0.330, 0.018), Color("#72D9FF"), false)
		set_holder_material(line, glow_mat)
		_mark_bot_role(line, "screen_glow")

	# Área de conversa generosa: basta estar perto da STAR Bot.
	var area := Area3D.new()
	area.name = "STARInteraction"
	area.position = Vector3(0, 0.760, 0)
	area.set_meta("action", "star")
	area.set_meta("label", "CONVERSAR COM STAR")
	var shape_node := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.85
	shape.height = 1.70
	shape_node.shape = shape
	area.add_child(shape_node)
	avatar.add_child(area)

	apply_skin(avatar, skin_id)
	var triangle_count := _bot_triangle_count(avatar)
	avatar.set_meta("body_triangle_count", triangle_count)
	avatar.set_meta("triangle_count", triangle_count)
	return avatar

static func _apply_bot_role(node: Node, palette: Dictionary) -> void:
	if node is MeshInstance3D and node.has_meta("bot_role"):
		var role := str(node.get_meta("bot_role"))
		var primary: Color = palette.primary
		var secondary: Color = palette.secondary
		var accent: Color = palette.accent
		match role:
			"shell":
				node.material_override = material(Color("#E9EDF2").lerp(primary, 0.18), accent, 0.06, 0.10, 0.26)
			"joint":
				node.material_override = material(Color("#171B24").lerp(secondary, 0.25), secondary, 0.04, 0.42, 0.20)
			"metal":
				node.material_override = textured_material("brushed_metal.png", Color("#D7DDE5"), 0.78, 0.18, 2.0)
			"visor":
				node.material_override = material(Color("#050811"), secondary, 0.08, 0.76, 0.05)
			"screen_glow":
				node.material_override = emissive_material(accent.lightened(0.16), accent, 4.0)
			"hair":
				node.material_override = material(Color("#E9BE72"), Color("#D4A253"), 0.06, 0.03, 0.34)
	for child in node.get_children():
		_apply_bot_role(child, palette)

static func apply_skin(avatar: Node3D, skin_id: String) -> void:
	if not SKIN_PALETTES.has(skin_id):
		skin_id = "cypher_system"
	avatar.set_meta("skin_id", skin_id)
	var palette: Dictionary = SKIN_PALETTES[skin_id]
	_apply_bot_role(avatar, palette)
