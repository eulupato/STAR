extends CharacterBody3D
class_name StarWorldPlayer

@export var move_speed := 4.3
@export var sprint_speed := 6.6
@export var mouse_sensitivity := 0.0022
@export var gravity := 18.0

var active := false
var camera: Camera3D
var interaction_ray: RayCast3D

func _ready() -> void:
	var collision := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.34
	shape.height = 1.7
	collision.shape = shape
	collision.position.y = 0.85
	add_child(collision)

	camera = Camera3D.new()
	camera.position = Vector3(0, 1.58, 0)
	camera.current = false
	add_child(camera)

	interaction_ray = RayCast3D.new()
	interaction_ray.position = Vector3(0, 1.48, 0)
	interaction_ray.target_position = Vector3(0, 0, -3.2)
	interaction_ray.collide_with_areas = true
	interaction_ray.collide_with_bodies = true
	add_child(interaction_ray)

func set_active(value: bool) -> void:
	active = value
	camera.current = value
	if value:
		Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	else:
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		velocity = Vector3.ZERO

func _unhandled_input(event: InputEvent) -> void:
	if not active:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * mouse_sensitivity)
		camera.rotation.x = clamp(camera.rotation.x - event.relative.y * mouse_sensitivity, -1.32, 1.32)

func _physics_process(delta: float) -> void:
	if not active:
		return
	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		velocity.y = -0.5

	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction := (transform.basis * Vector3(input.x, 0, input.y)).normalized()
	var speed := sprint_speed if Input.is_action_pressed("sprint") else move_speed
	velocity.x = direction.x * speed
	velocity.z = direction.z * speed
	move_and_slide()

func interaction_target() -> Object:
	interaction_ray.force_raycast_update()
	if interaction_ray.is_colliding():
		return interaction_ray.get_collider()
	return null
