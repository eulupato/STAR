extends CharacterBody3D
class_name StarWorldPlayer

@export var move_speed := 4.3
@export var sprint_speed := 6.6
@export var mouse_sensitivity := 0.0022
@export var gravity := 18.0
@export var jump_velocity := 4.05
@export var eye_height := 1.62

var active := false
var head: Node3D
var camera: Camera3D
var interaction_ray: RayCast3D
var look_pitch := 0.0

func _ready() -> void:
	floor_snap_length = 0.38
	floor_max_angle = deg_to_rad(50.0)
	floor_stop_on_slope = true
	safe_margin = 0.035

	var collision := CollisionShape3D.new()
	collision.name = "PlayerCollision"
	var shape := CapsuleShape3D.new()
	shape.radius = 0.34
	shape.height = 1.72
	collision.shape = shape
	collision.position.y = 0.86
	add_child(collision)

	head = Node3D.new()
	head.name = "HeadPivot"
	head.position = Vector3(0, eye_height, 0)
	add_child(head)

	camera = Camera3D.new()
	camera.name = "FirstPersonCamera"
	camera.current = false
	camera.fov = 72.0
	camera.near = 0.035
	camera.far = 180.0
	head.add_child(camera)

	interaction_ray = RayCast3D.new()
	interaction_ray.name = "InteractionRay"
	interaction_ray.target_position = Vector3(0, 0, -3.4)
	interaction_ray.collide_with_areas = true
	interaction_ray.collide_with_bodies = true
	interaction_ray.enabled = true
	camera.add_child(interaction_ray)

func set_active(value: bool) -> void:
	active = value
	camera.current = value
	set_process_input(value)
	if value:
		Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	else:
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		velocity = Vector3.ZERO

func _input(event: InputEvent) -> void:
	if not active:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		apply_look_delta(event.relative)

func apply_look_delta(relative: Vector2) -> void:
	rotate_y(-relative.x * mouse_sensitivity)
	look_pitch = clampf(
		look_pitch - relative.y * mouse_sensitivity,
		deg_to_rad(-78.0),
		deg_to_rad(78.0)
	)
	head.rotation.x = look_pitch

func _physics_process(delta: float) -> void:
	if not active:
		return

	var grounded := is_on_floor()
	if grounded:
		if Input.is_action_just_pressed("jump"):
			velocity.y = jump_velocity
		else:
			# Pressão mínima para manter aderência no piso e na rampa invisível
			# da escada sem impedir o pulo curto.
			velocity.y = -0.45
	else:
		velocity.y -= gravity * delta

	var input_vector := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction := (transform.basis * Vector3(input_vector.x, 0, input_vector.y)).normalized()
	var speed := sprint_speed if Input.is_action_pressed("sprint") else move_speed
	velocity.x = direction.x * speed
	velocity.z = direction.z * speed
	move_and_slide()

func interaction_target() -> Object:
	if interaction_ray == null:
		return null
	interaction_ray.force_raycast_update()
	if interaction_ray.is_colliding():
		return interaction_ray.get_collider()
	return null

func first_person_state() -> Dictionary:
	return {
		"active": active,
		"camera_current": camera != null and camera.current,
		"mouse_captured": Input.mouse_mode == Input.MOUSE_MODE_CAPTURED,
		"yaw": rotation.y,
		"pitch": look_pitch,
		"ray_parent_is_camera": interaction_ray != null and interaction_ray.get_parent() == camera,
		"jump_velocity": jump_velocity,
		"floor_snap_length": floor_snap_length,
	}
