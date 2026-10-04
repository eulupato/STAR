extends RefCounted
class_name StarWorldBuilder

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
	mesh.radial_segments = 32
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

static func build_house(parent: Node3D) -> Dictionary:
	var result := {}
	add_cylinder(parent, "HouseIsland", Vector3(0, -1.45, 0), 17.0, 2.8, Color("#3F4D39"), true)
	add_cylinder(parent, "HouseGarden", Vector3(0, -0.22, 0), 16.5, 0.20, Color("#557052"), false)

	var floor_color := Color("#D8D1C6")
	var wall_color := Color("#E8E5E1")
	var wood := Color("#8B5D3F")
	var graphite := Color("#242630")
	var stone := Color("#B9B0A5")

	add_box(parent, "GroundFloor", Vector3(0, -0.12, 0), Vector3(17, 0.24, 13), floor_color, true)

	# Tetos por zona: sala gamer escura; banheiro/cozinha claros.
	add_box(parent, "LivingCeiling", Vector3(-4.75, 2.76, -2.65), Vector3(7.1, 0.18, 7.0), Color("#242630"), true)
	add_box(parent, "BathroomCeiling", Vector3(-4.75, 2.76, 4.25), Vector3(7.1, 0.18, 4.0), Color("#D9D5D2"), true)
	add_box(parent, "GroundCeilingKitchen", Vector3(4.85, 2.76, 4.15), Vector3(6.4, 0.18, 4.2), Color("#D9D5D2"), true)

	# Outer walls with openings.
	add_box(parent, "WallNorthL", Vector3(-5.5, 1.45, -6.4), Vector3(6.0, 2.9, 0.25), wall_color, true)
	add_box(parent, "WallNorthR", Vector3(5.5, 1.45, -6.4), Vector3(6.0, 2.9, 0.25), wall_color, true)
	add_box(parent, "WallWest", Vector3(-8.4, 1.45, 0), Vector3(0.25, 2.9, 12.8), stone, true)
	add_box(parent, "WallEast", Vector3(8.4, 1.45, 0), Vector3(0.25, 2.9, 12.8), wall_color, true)
	add_box(parent, "WallSouthL", Vector3(-5.7, 1.45, 6.4), Vector3(5.6, 2.9, 0.25), wall_color, true)
	add_box(parent, "WallSouthR", Vector3(5.7, 1.45, 6.4), Vector3(5.6, 2.9, 0.25), wall_color, true)

	# Living room — referência escura, tecnológica e geek.
	add_box(parent, "LivingFeatureWall", Vector3(-4.5, 1.45, -6.20), Vector3(7.25, 2.75, 0.10), Color("#181A22"), false)
	add_box(parent, "LivingWestPanel", Vector3(-8.20, 1.45, -2.55), Vector3(0.08, 2.75, 7.0), Color("#20232B"), false)
	add_box(parent, "LivingRug", Vector3(-4.5, 0.03, -2.55), Vector3(5.6, 0.05, 3.6), Color("#222633"), false)
	add_box(parent, "SofaSeat", Vector3(-4.5, 0.34, -1.25), Vector3(4.35, 0.42, 1.55), graphite, true)
	add_box(parent, "SofaBack", Vector3(-4.5, 0.83, -0.58), Vector3(4.35, 1.05, 0.28), Color("#1E2028"), true)
	add_box(parent, "SofaArmL", Vector3(-6.55, 0.60, -1.25), Vector3(0.28, 0.85, 1.55), Color("#1E2028"), true)
	add_box(parent, "SofaArmR", Vector3(-2.45, 0.60, -1.25), Vector3(0.28, 0.85, 1.55), Color("#1E2028"), true)
	add_box(parent, "CoffeeTable", Vector3(-4.5, 0.30, -3.45), Vector3(2.4, 0.42, 1.2), Color("#323640"), true)

	var living_tv := add_box(parent, "LivingTV", Vector3(-4.5, 1.58, -6.07), Vector3(4.55, 2.22, 0.18), Color("#101124"), true, {"action":"tv", "room":"living"})
	living_tv.set_meta("label", "USAR TV")
	var living_tv_mesh := _mesh_child(living_tv)
	living_tv_mesh.material_override = emissive_material(Color("#30205B"), Color("#7B5CFF"), 2.15)

	add_box(parent, "LivingRack", Vector3(-4.5, 0.46, -5.72), Vector3(5.2, 0.68, 0.72), Color("#191B22"), true)
	add_box(parent, "LivingShelf", Vector3(-4.5, 2.52, -6.0), Vector3(5.4, 0.10, 0.62), Color("#272A31"), false)
	add_box(parent, "LivingConsole", Vector3(-4.35, 0.88, -5.58), Vector3(1.05, 0.18, 0.34), Color("#101217"), false)
	add_box(parent, "LivingControllerL", Vector3(-5.35, 0.88, -5.48), Vector3(0.42, 0.10, 0.26), Color("#303540"), false)
	add_box(parent, "LivingControllerR", Vector3(-3.35, 0.88, -5.48), Vector3(0.42, 0.10, 0.26), Color("#303540"), false)

	var tv_title := Label3D.new()
	tv_title.text = "STAR TV"
	tv_title.position = Vector3(-4.5, 1.62, -5.94)
	tv_title.font_size = 42
	tv_title.pixel_size = 0.006
	tv_title.modulate = Color("#E9E5FF")
	tv_title.outline_size = 8
	tv_title.outline_modulate = Color(0.12, 0.06, 0.26, 0.9)
	parent.add_child(tv_title)

	for frame_i in range(5):
		var frame := add_box(parent, "GeekFrame_%d" % frame_i, Vector3(-6.25 + frame_i * 0.88, 2.82, -5.94), Vector3(0.62, 0.54 + (frame_i % 2) * 0.14, 0.06), Color("#34364A"), false)
		var frame_mesh := _mesh_child(frame)
		var frame_color: Color = [Color("#77538E"), Color("#355A84"), Color("#755D46"), Color("#4C3E73"), Color("#3F6570")][frame_i]
		frame_mesh.material_override = material(frame_color, frame_color.lightened(0.22), 0.32, 0.0, 0.55)

	# Luzes de recorte atrás da TV, sem depender de textura externa.
	for edge in [
		[Vector3(-4.5, 2.73, -5.94), Vector3(4.85, 0.055, 0.055)],
		[Vector3(-4.5, 0.43, -5.94), Vector3(4.85, 0.055, 0.055)],
		[Vector3(-6.92, 1.58, -5.94), Vector3(0.055, 2.25, 0.055)],
		[Vector3(-2.08, 1.58, -5.94), Vector3(0.055, 2.25, 0.055)],
	]:
		var edge_position: Vector3 = edge[0]
		var edge_size: Vector3 = edge[1]
		var strip := add_box(parent, "LivingLED", edge_position, edge_size, Color("#6D75D8"), false)
		var strip_mesh := _mesh_child(strip)
		strip_mesh.material_override = emissive_material(Color("#707AE0"), Color("#8D94FF"), 3.0)

	_add_room_light(parent, "LivingLight", Vector3(-4.5, 2.20, -2.5), Color("#AFC7FF"), 1.05, 6.2)
	_add_room_light(parent, "LivingVioletAccent", Vector3(-4.5, 1.65, -5.15), Color("#7658E8"), 0.62, 3.8)

	# Kitchen and dining — madeira quente, pedra clara e luz pendente.
	add_box(parent, "KitchenBack", Vector3(5.25, 1.10, 4.05), Vector3(5.4, 2.2, 0.70), wood, true)
	add_box(parent, "KitchenUpperA", Vector3(3.55, 2.05, 3.62), Vector3(1.55, 1.05, 0.55), Color("#9A6747"), false)
	add_box(parent, "KitchenUpperB", Vector3(5.25, 2.05, 3.62), Vector3(1.55, 1.05, 0.55), Color("#9A6747"), false)
	add_box(parent, "KitchenCounter", Vector3(4.0, 0.65, 1.9), Vector3(5.0, 1.25, 1.2), Color("#E7DFD3"), true)
	add_box(parent, "KitchenIsland", Vector3(3.9, 0.55, -0.15), Vector3(3.8, 1.05, 1.45), Color("#D7C9B8"), true)
	add_box(parent, "Fridge", Vector3(7.1, 1.25, 3.72), Vector3(1.4, 2.5, 0.9), Color("#9FA6AE"), true)
	add_box(parent, "Oven", Vector3(2.55, 0.64, 3.70), Vector3(1.20, 1.25, 0.75), Color("#353942"), true)

	var cooktop := add_box(parent, "Cooktop", Vector3(3.15, 1.29, 1.90), Vector3(1.45, 0.045, 0.82), Color("#17191F"), false)
	var cooktop_mesh := _mesh_child(cooktop)
	cooktop_mesh.material_override = material(Color("#17191F"), Color("#E35A87"), 0.20, 0.12, 0.18)
	for burner_x in [2.78, 3.50]:
		for burner_z in [1.66, 2.14]:
			add_cylinder(parent, "Burner", Vector3(burner_x, 1.34, burner_z), 0.15, 0.025, Color("#252833"), false)

	add_box(parent, "Sink", Vector3(5.25, 1.29, 1.90), Vector3(1.20, 0.05, 0.78), Color("#7A828B"), false)
	add_cylinder(parent, "FaucetStem", Vector3(5.25, 1.62, 2.15), 0.045, 0.62, Color("#9EA7AF"), false)

	for jar_i in range(4):
		var jar_color: Color = [Color("#A87855"), Color("#6E874B"), Color("#B28A45"), Color("#8A5A66")][jar_i]
		add_cylinder(parent, "SpiceJar_%d" % jar_i, Vector3(4.45 + jar_i * 0.38, 1.46, 3.52), 0.11, 0.34, jar_color, false)

	for pendant_x in [2.9, 4.2, 5.5]:
		add_cylinder(parent, "PendantStem", Vector3(pendant_x, 2.32, -0.15), 0.035, 0.62, Color("#4A4140"), false)
		var bulb := MeshInstance3D.new()
		var bulb_mesh := SphereMesh.new()
		bulb_mesh.radius = 0.12
		bulb_mesh.height = 0.24
		bulb.mesh = bulb_mesh
		bulb.position = Vector3(pendant_x, 1.98, -0.15)
		bulb.material_override = emissive_material(Color("#FFD9A3"), Color("#FFD2A0"), 3.6)
		parent.add_child(bulb)

	_add_room_light(parent, "KitchenLight", Vector3(4.2, 2.18, 1.0), Color("#FFD1A0"), 0.92, 5.8)

	# Bathroom.
	add_box(parent, "BathroomWallA", Vector3(-1.5, 1.45, 3.6), Vector3(0.22, 2.9, 5.0), wall_color, true)
	add_box(parent, "BathroomWallB", Vector3(-4.0, 1.45, 1.2), Vector3(5.0, 2.9, 0.22), wall_color, true)
	add_box(parent, "BathroomVanity", Vector3(-3.8, 0.6, 4.8), Vector3(2.2, 1.0, 0.65), wood, true)
	add_box(parent, "BathroomMirror", Vector3(-3.8, 1.65, 5.14), Vector3(2.0, 1.0, 0.05), Color(0.62,0.72,0.82,0.32), false)
	add_box(parent, "ShowerGlass", Vector3(-6.2, 1.15, 3.2), Vector3(0.06, 2.25, 2.1), Color(0.65,0.80,0.88,0.28), true)
	_add_room_light(parent, "BathroomLight", Vector3(-4.5, 2.20, 4.0), Color("#E8F3FF"), 0.72, 4.4)

	# Staircase to bedroom floor. Os degraus são visuais; uma rampa invisível
	# fornece colisão contínua para o CharacterBody3D subir sem step-up artificial.
	for i in range(11):
		var y := 0.14 + float(i) * 0.255
		var z := 5.25 - float(i) * 0.47
		add_box(parent, "Step_%02d" % i, Vector3(0.4, y, z), Vector3(2.1, 0.28, 0.58), wood, false)

	var stair_ramp := StaticBody3D.new()
	stair_ramp.name = "StairRampCollision"
	stair_ramp.position = Vector3(0.4, 1.42, 2.90)
	stair_ramp.rotation.x = 0.497
	var stair_shape_node := CollisionShape3D.new()
	var stair_shape := BoxShape3D.new()
	stair_shape.size = Vector3(2.02, 0.18, 5.30)
	stair_shape_node.shape = stair_shape
	stair_ramp.add_child(stair_shape_node)
	parent.add_child(stair_ramp)

	# Upper floor / bedroom.
	add_box(parent, "UpperFloor", Vector3(3.6, 2.78, -2.1), Vector3(9.2, 0.26, 8.3), floor_color, true)
	add_box(parent, "UpperCeiling", Vector3(3.6, 5.72, -2.1), Vector3(9.2, 0.18, 8.3), Color("#D7D4D8"), true)
	add_box(parent, "UpperEastWall", Vector3(8.15, 4.25, -2.1), Vector3(0.22, 2.9, 8.3), wall_color, true)
	add_box(parent, "UpperNorthWall", Vector3(3.6, 4.25, -6.15), Vector3(9.2, 2.9, 0.22), Color("#3B3B44"), true)
	add_box(parent, "UpperSouthWall", Vector3(5.7, 4.25, 1.9), Vector3(4.8, 2.9, 0.22), wall_color, true)

	# Bedroom from supplied reference: bed + TV + L desk + PC + wardrobe.
	add_box(parent, "BedBase", Vector3(2.7, 3.18, -3.4), Vector3(3.3, 0.65, 4.0), Color("#4E4A59"), true)
	add_box(parent, "BedMattress", Vector3(2.7, 3.60, -3.4), Vector3(3.15, 0.35, 3.85), Color("#D8D4DA"), false)
	add_box(parent, "BedHeadboard", Vector3(2.7, 4.12, -5.28), Vector3(3.35, 1.10, 0.18), Color("#2A2932"), false)
	add_box(parent, "PillowL", Vector3(2.08, 3.86, -4.70), Vector3(0.88, 0.18, 0.68), Color("#EEEAF0"), false)
	add_box(parent, "PillowR", Vector3(3.32, 3.86, -4.70), Vector3(0.88, 0.18, 0.68), Color("#EEEAF0"), false)
	add_box(parent, "BedRunner", Vector3(2.7, 3.80, -2.18), Vector3(3.05, 0.05, 0.72), Color("#4E3B63"), false)
	var bedroom_tv := add_box(parent, "BedroomTV", Vector3(0.10, 4.35, -3.6), Vector3(0.18, 2.1, 3.4), Color("#090A0F"), true, {"action":"tv", "room":"bedroom"})
	bedroom_tv.set_meta("label", "USAR TV")
	var bedroom_tv_mesh := _mesh_child(bedroom_tv)
	bedroom_tv_mesh.material_override = emissive_material(Color("#2D1D55"), Color("#9A66F0"), 2.15)

	add_box(parent, "DeskLong", Vector3(5.7, 3.55, 0.9), Vector3(4.4, 0.20, 1.0), graphite, true)
	add_box(parent, "DeskSide", Vector3(7.25, 3.55, -0.7), Vector3(1.0, 0.20, 3.0), graphite, true)
	var monitor_a := add_box(parent, "MonitorA", Vector3(4.8, 4.25, 0.55), Vector3(1.8, 1.05, 0.10), Color("#15142A"), false)
	var monitor_b := add_box(parent, "MonitorB", Vector3(6.8, 4.25, 0.55), Vector3(1.8, 1.05, 0.10), Color("#15142A"), false)
	for monitor in [monitor_a, monitor_b]:
		var monitor_mesh := _mesh_child(monitor)
		monitor_mesh.material_override = emissive_material(Color("#241B48"), Color("#9466F6"), 2.35)

	var pc := add_box(parent, "BedroomPC", Vector3(7.25, 4.1, -0.9), Vector3(0.75, 1.4, 1.1), Color("#181820"), true, {"action":"future_pc"})
	pc.set_meta("label", "PC — FUTURO")
	var pc_mesh := _mesh_child(pc)
	pc_mesh.material_override = material(Color("#24242E"), Color("#8558D5"), 1.10, 0.12, 0.30)

	add_box(parent, "DeskChairSeat", Vector3(5.75, 3.34, -0.15), Vector3(0.82, 0.16, 0.78), Color("#181A22"), true)
	add_box(parent, "DeskChairBack", Vector3(5.75, 4.02, -0.53), Vector3(0.88, 1.20, 0.18), Color("#1C1E27"), true)
	add_cylinder(parent, "DeskChairStem", Vector3(5.75, 3.05, -0.15), 0.09, 0.55, Color("#242630"), false)

	add_box(parent, "BedroomRug", Vector3(4.95, 2.94, -1.35), Vector3(5.1, 0.05, 4.7), Color("#23232B"), false)
	_add_room_light(parent, "BedroomLight", Vector3(4.6, 5.05, -2.0), Color("#CEC4FF"), 0.95, 5.8)
	_add_room_light(parent, "DeskAccent", Vector3(5.8, 4.45, 0.20), Color("#7756E8"), 0.52, 3.4)

	var wardrobe := add_box(parent, "Wardrobe", Vector3(7.55, 4.25, -4.7), Vector3(0.75, 2.9, 2.6), Color("#D9D6DB"), true, {"action":"wardrobe"})
	wardrobe.set_meta("label", "ROUPAS")
	add_box(parent, "WardrobeDoorA", Vector3(7.15, 4.25, -5.32), Vector3(0.06, 2.66, 1.14), Color("#ECE9EF"), false)
	add_box(parent, "WardrobeDoorB", Vector3(7.15, 4.25, -4.08), Vector3(0.06, 2.66, 1.14), Color("#E3E0E7"), false)
	add_box(parent, "WardrobeHandleA", Vector3(7.10, 4.25, -4.80), Vector3(0.05, 0.42, 0.05), Color("#575A65"), false)
	add_box(parent, "WardrobeHandleB", Vector3(7.10, 4.25, -4.56), Vector3(0.05, 0.42, 0.05), Color("#575A65"), false)
	add_box(parent, "WardrobeMirror", Vector3(7.08, 4.25, -3.45), Vector3(0.05, 2.45, 0.82), Color(0.65,0.76,0.86,0.35), false)

	# Geek shelves: scenery only.
	for shelf_i in range(3):
		add_box(parent, "GeekShelf_%d" % shelf_i, Vector3(1.0, 4.2 + shelf_i * 0.55, -5.85), Vector3(2.6, 0.10, 0.38), Color("#E8E5E4"), false)
	for item_i in range(8):
		var item_x := 0.0 + float(item_i % 4) * 0.62
		var item_y := 4.48 + float(item_i / 4) * 0.55
		add_box(parent, "GeekItem_%d" % item_i, Vector3(item_x, item_y, -5.72), Vector3(0.24, 0.35 + (item_i % 3)*0.08, 0.22), [Color("#6E3C55"),Color("#31567A"),Color("#806F3C"),Color("#473A6E")][item_i % 4], false)

	# Balcony.
	add_box(parent, "BalconyFloor", Vector3(3.0, 2.78, -7.4), Vector3(7.0, 0.22, 2.2), Color("#C9BCA9"), true)
	add_box(parent, "BalconyRail", Vector3(3.0, 3.55, -8.45), Vector3(7.0, 1.35, 0.08), Color(0.60,0.72,0.82,0.24), true)

	var avatar := build_star_avatar(parent, "cypher_system")
	avatar.position = Vector3(-1.8, 0.0, -2.8)
	result["avatar"] = avatar
	result["spawn"] = Vector3(2.15, 0.35, 5.25)
	result["spawn_yaw"] = 0.42
	result["living_tv"] = living_tv
	result["bedroom_tv"] = bedroom_tv
	result["wardrobe"] = wardrobe
	return result

static func build_star_avatar(parent: Node3D, skin_id: String = "cypher_system") -> Node3D:
	var avatar := Node3D.new()
	avatar.name = "STARAvatar"
	avatar.set_meta("skin_id", skin_id)
	parent.add_child(avatar)

	var skin_mat := material(Color("#F3C9B8"), Color("#F7CDBE"), 0.04, 0.0, 0.52)
	var hair_mat := material(Color("#E8BC63"), Color("#C88732"), 0.16, 0.0, 0.38)
	var eye_white := material(Color("#F8F7F4"))
	var iris_mat := material(Color("#5B9BCF"), Color("#70B8E8"), 0.18, 0.0, 0.30)
	var pupil_mat := material(Color("#19243A"))
	var lip_mat := material(Color("#B96872"))

	# Cabeça e rosto — frente do avatar aponta para +Z.
	var head := MeshInstance3D.new()
	head.name = "Head"
	var head_mesh := SphereMesh.new()
	head_mesh.radius = 0.31
	head_mesh.height = 0.62
	head_mesh.radial_segments = 32
	head_mesh.rings = 16
	head.mesh = head_mesh
	head.position = Vector3(0, 1.68, 0)
	head.scale = Vector3(0.91, 1.02, 0.88)
	head.material_override = skin_mat
	avatar.add_child(head)

	# Cabelo atrás da cabeça: capuz + mechas laterais e traseiras.
	var hair_cap := MeshInstance3D.new()
	hair_cap.name = "HairCap"
	var hair_shape := SphereMesh.new()
	hair_shape.radius = 0.35
	hair_shape.height = 0.72
	hair_shape.radial_segments = 28
	hair_shape.rings = 14
	hair_cap.mesh = hair_shape
	hair_cap.position = Vector3(0, 1.72, -0.10)
	hair_cap.scale = Vector3(1.03, 1.14, 0.82)
	hair_cap.material_override = hair_mat
	avatar.add_child(hair_cap)

	for strand_data in [
		[Vector3(-0.25, 1.33, -0.11), 0.13, 0.82, -0.08],
		[Vector3(0.25, 1.33, -0.11), 0.13, 0.82, 0.08],
		[Vector3(-0.10, 1.26, -0.18), 0.14, 0.92, -0.03],
		[Vector3(0.10, 1.26, -0.18), 0.14, 0.92, 0.03],
	]:
		var strand_position: Vector3 = strand_data[0]
		var strand_radius: float = float(strand_data[1])
		var strand_height: float = float(strand_data[2])
		var strand_rotation: float = float(strand_data[3])
		var strand := _avatar_capsule("HairStrand", strand_position, strand_radius, strand_height, Color("#E8BC63"))
		strand.rotation.z = strand_rotation
		strand.material_override = hair_mat
		avatar.add_child(strand)

	# Olhos grandes e claros, coerentes com a referência visual.
	for side in [-1.0, 1.0]:
		var eye := MeshInstance3D.new()
		eye.name = "Eye"
		var eye_mesh := SphereMesh.new()
		eye_mesh.radius = 0.066
		eye_mesh.height = 0.085
		eye.mesh = eye_mesh
		eye.position = Vector3(0.105 * side, 1.725, 0.266)
		eye.scale = Vector3(1.0, 0.72, 0.42)
		eye.material_override = eye_white
		avatar.add_child(eye)

		var iris := MeshInstance3D.new()
		iris.name = "Iris"
		var iris_mesh := SphereMesh.new()
		iris_mesh.radius = 0.035
		iris_mesh.height = 0.050
		iris.mesh = iris_mesh
		iris.position = Vector3(0.105 * side, 1.724, 0.302)
		iris.scale = Vector3(1.0, 0.78, 0.30)
		iris.material_override = iris_mat
		avatar.add_child(iris)

		var pupil := MeshInstance3D.new()
		pupil.name = "Pupil"
		var pupil_mesh := SphereMesh.new()
		pupil_mesh.radius = 0.014
		pupil_mesh.height = 0.026
		pupil.mesh = pupil_mesh
		pupil.position = Vector3(0.105 * side, 1.724, 0.319)
		pupil.scale = Vector3(1.0, 0.86, 0.30)
		pupil.material_override = pupil_mat
		avatar.add_child(pupil)

	var mouth := add_box(avatar, "Mouth", Vector3(0, 1.565, 0.283), Vector3(0.105, 0.018, 0.016), Color("#B96872"), false)
	var mouth_mesh := _mesh_child(mouth)
	mouth_mesh.material_override = lip_mat

	# Corpo-base. As roupas são materiais/peças; rosto, corpo e rig permanecem.
	var torso := _avatar_cylinder("Torso", Vector3(0, 1.18, 0), 0.235, 0.305, 0.54, Color.WHITE)
	_mark_outfit(torso, "top")
	avatar.add_child(torso)

	var hips := _avatar_cylinder("Hips", Vector3(0, 0.855, 0), 0.305, 0.285, 0.22, Color.WHITE)
	_mark_outfit(hips, "bottom")
	avatar.add_child(hips)

	for side in [-1.0, 1.0]:
		var arm := _avatar_capsule("Sleeve", Vector3(0.36 * side, 1.13, 0), 0.082, 0.60, Color.WHITE)
		arm.rotation.z = 0.055 * side
		_mark_outfit(arm, "sleeve")
		avatar.add_child(arm)

		var hand := MeshInstance3D.new()
		hand.name = "Hand"
		var hand_mesh := SphereMesh.new()
		hand_mesh.radius = 0.087
		hand_mesh.height = 0.18
		hand.mesh = hand_mesh
		hand.position = Vector3(0.388 * side, 0.79, 0)
		hand.scale = Vector3(0.88, 1.12, 0.82)
		hand.material_override = skin_mat
		avatar.add_child(hand)

	for side in [-1.0, 1.0]:
		var upper_leg := _avatar_capsule("UpperLeg", Vector3(0.145 * side, 0.58, 0), 0.108, 0.52, Color.WHITE)
		_mark_outfit(upper_leg, "bottom")
		avatar.add_child(upper_leg)

		var lower_leg := _avatar_capsule("LowerLeg", Vector3(0.145 * side, 0.285, 0), 0.088, 0.44, Color.WHITE)
		_mark_outfit(lower_leg, "lower_leg")
		avatar.add_child(lower_leg)

		var shoe := add_box(avatar, "Shoe", Vector3(0.145 * side, 0.075, 0.055), Vector3(0.235, 0.15, 0.38), Color.WHITE, false)
		_mark_outfit(shoe, "shoe")

	# Peças opcionais que permitem leitura distinta das skins sem duplicar o avatar.
	var system_panel := add_box(avatar, "SystemChest", Vector3(0, 1.245, 0.255), Vector3(0.25, 0.17, 0.035), Color("#72E8FF"), false)
	_mark_outfit(system_panel, "accent")
	system_panel.visible = false

	var dress_skirt := _avatar_cylinder("DressSkirt", Vector3(0, 0.68, 0), 0.29, 0.47, 0.72, Color("#111B4A"))
	_mark_outfit(dress_skirt, "dress")
	dress_skirt.visible = false
	avatar.add_child(dress_skirt)

	var rock_jacket := _avatar_cylinder("RockJacket", Vector3(0, 1.20, 0), 0.255, 0.325, 0.58, Color("#17181D"))
	_mark_outfit(rock_jacket, "jacket")
	rock_jacket.visible = false
	avatar.add_child(rock_jacket)

	var chest_star := CrystalStar3D.new()
	chest_star.name = "ChestStar"
	chest_star.star_size = 0.105
	chest_star.rotation_speed = 0.0
	chest_star.energy = 1.45
	chest_star.position = Vector3(0, 1.255, 0.305)
	chest_star.visible = false
	avatar.add_child(chest_star)

	var area := Area3D.new()
	area.name = "STARInteraction"
	area.position = Vector3(0, 0.98, 0)
	area.set_meta("action", "star")
	area.set_meta("label", "CONVERSAR")
	var shape_node := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.45
	shape.height = 1.95
	shape_node.shape = shape
	area.add_child(shape_node)
	avatar.add_child(area)

	apply_skin(avatar, skin_id)
	return avatar

static func _avatar_capsule(name: String, position: Vector3, radius: float, height: float, color: Color) -> MeshInstance3D:
	var part := MeshInstance3D.new()
	part.name = name
	var mesh := CapsuleMesh.new()
	mesh.radius = radius
	mesh.height = height
	mesh.radial_segments = 24
	mesh.rings = 10
	part.mesh = mesh
	part.position = position
	part.material_override = material(color)
	return part

static func _avatar_cylinder(name: String, position: Vector3, top_radius: float, bottom_radius: float, height: float, color: Color) -> MeshInstance3D:
	var part := MeshInstance3D.new()
	part.name = name
	var mesh := CylinderMesh.new()
	mesh.top_radius = top_radius
	mesh.bottom_radius = bottom_radius
	mesh.height = height
	mesh.radial_segments = 28
	part.mesh = mesh
	part.position = position
	part.material_override = material(color)
	return part

static func _mark_outfit(node: Node, role: String) -> void:
	node.set_meta("outfit_part", true)
	node.set_meta("outfit_role", role)

static func apply_skin(avatar: Node3D, skin_id: String) -> void:
	if not SKIN_PALETTES.has(skin_id):
		skin_id = "cypher_system"
	var palette: Dictionary = SKIN_PALETTES[skin_id]
	var primary: Color = palette.primary
	var secondary: Color = palette.secondary
	var accent: Color = palette.accent
	var skin_color := Color("#F3C9B8")
	avatar.set_meta("skin_id", skin_id)

	var system_panel := avatar.get_node_or_null("SystemChest")
	var chest_star := avatar.get_node_or_null("ChestStar")
	var dress_skirt := avatar.get_node_or_null("DressSkirt")
	var rock_jacket := avatar.get_node_or_null("RockJacket")
	if system_panel:
		system_panel.visible = skin_id == "cypher_system"
	if chest_star:
		chest_star.visible = skin_id == "cypher_system"
	if dress_skirt:
		dress_skirt.visible = skin_id == "elegant_blue"
	if rock_jacket:
		rock_jacket.visible = skin_id == "rock_simple"

	for child in avatar.get_children():
		if not (child is MeshInstance3D and child.get_meta("outfit_part", false)):
			continue
		var role := str(child.get_meta("outfit_role", "top"))
		var color := primary
		var glow := 0.0

		match role:
			"top":
				color = primary
			"sleeve":
				if skin_id in ["casual", "elegant_blue"]:
					color = skin_color
				elif skin_id == "brazil":
					color = primary
				else:
					color = primary
			"bottom":
				if skin_id == "casual":
					color = secondary
				elif skin_id == "brazil":
					color = secondary
				elif skin_id == "elegant_blue":
					color = primary
				else:
					color = secondary
			"lower_leg":
				if skin_id in ["casual", "elegant_blue"]:
					color = skin_color
				else:
					color = secondary
			"shoe":
				color = Color("#F2F2F4") if skin_id in ["casual", "brazil", "rock_simple", "rich_red"] else primary.lightened(0.12)
			"accent":
				color = accent
				glow = 1.6
			"dress":
				color = primary
			"jacket":
				color = primary

		if skin_id == "cypher_system" and role in ["top", "sleeve", "bottom", "lower_leg"]:
			glow = 0.20
		child.material_override = material(color, accent, glow, 0.04 if role == "jacket" else 0.0, 0.38)

	# A jaqueta deve cobrir o torso, não competir com ele.
	var torso := avatar.get_node_or_null("Torso")
	if torso:
		torso.visible = skin_id != "rock_simple"
	var hips := avatar.get_node_or_null("Hips")
	if hips:
		hips.visible = skin_id != "elegant_blue"
