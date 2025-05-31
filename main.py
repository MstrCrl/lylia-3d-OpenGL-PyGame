import pygame
from pygame.locals import *
from OpenGL.GL import *
import glm
import time
import config
from model_loader import load_model_from_txt
from texture_loader import load_texture
from shader import create_shader_program

def lerp(a, b, t):
    return a + (b - a) * t

def main():
    pygame.init()
    pygame.mixer.init()
    
    display = (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption(config.WINDOW_TITLE)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # Handle transparent textures

    shader_program = create_shader_program()
    glUseProgram(shader_program)

    objects = load_model_from_txt("parts", load_texture)

    # Sort objects so 'astaff.txt' renders last (on top)
    objects.sort(key=lambda o: 1 if "astaff.txt" in o.source_path.lower() else 0)

    projection = glm.perspective(glm.radians(config.FOV), display[0] / display[1], config.NEAR_PLANE, config.FAR_PLANE)
    proj_loc = glGetUniformLocation(shader_program, "projection")
    view_loc = glGetUniformLocation(shader_program, "view")
    model_loc = glGetUniformLocation(shader_program, "model")
    emissive_loc = glGetUniformLocation(shader_program, "emissiveColor")

    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, glm.value_ptr(projection))

    glClearColor(0.0, 0.0, 0.0, 1.0)  # Black background

    # Initial camera state
    current_distance = 5.94
    current_rot_x = 42.50
    current_rot_y = 20.50

    target_distance = current_distance
    target_rot_x = current_rot_x
    target_rot_y = current_rot_y

    last_mouse_pos = (0, 0)
    mouse_down = False

    clock = pygame.time.Clock()
    start_time = time.time()
    running = True
    pygame.mixer.music.load("music.mp3")
    pygame.mixer.music.play(-1)
    
    views = [
        (3.94, 56.00, -359.00),
        (7.94, 29.00, -353.00),
        (7.94, 60.00, -527.00),
        (7.94, 29.50, -446.00),
        (7.94, 33.50, -295.00),
        (4.94, 52.50, -353.50),
        (16.94, 25.50, -350.50),
    ]
    current_view_index = 0

    lerp_speed = 0.04  # Controls how fast to interpolate

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    view_info = f"Zoom: {target_distance:.2f}, rot_x: {target_rot_x:.2f}, rot_y: {target_rot_y:.2f}"
                    print(view_info)  # Print to terminal

                    with open("view_log.txt", "a") as log:
                        log.write(view_info + "\n")
                    print("Saved to view_log.txt")
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    current_view_index = (current_view_index + 1) % len(views)
                    target_distance, target_rot_x, target_rot_y = views[current_view_index]
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    current_view_index = (current_view_index - 1) % len(views)
                    target_distance, target_rot_x, target_rot_y = views[current_view_index]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    target_distance -= 0.5
                    target_distance = max(1.0, target_distance)
                elif event.button == 5:
                    target_distance += 0.5
                elif event.button == 1:
                    mouse_down = True
                    last_mouse_pos = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_down = False
            elif event.type == pygame.MOUSEMOTION and mouse_down:
                x, y = pygame.mouse.get_pos()
                dx = x - last_mouse_pos[0]
                dy = y - last_mouse_pos[1]
                # Directly rotate current rotation by mouse drag
                current_rot_y += dx * 0.5
                current_rot_x += dy * 0.5
                last_mouse_pos = (x, y)

        # Smoothly interpolate current values toward targets
        current_distance = lerp(current_distance, target_distance, lerp_speed)
        current_rot_x = lerp(current_rot_x, target_rot_x, lerp_speed)
        current_rot_y = lerp(current_rot_y, target_rot_y, lerp_speed)

        # Calculate camera position from current zoom distance
        camera_pos = glm.vec3(0, 0, current_distance)
        view = glm.lookAt(camera_pos, config.CAMERA_TARGET, config.CAMERA_UP)
        glUniformMatrix4fv(view_loc, 1, GL_FALSE, glm.value_ptr(view))

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        time_elapsed = time.time() - start_time
        glow_strength = 0.5 + 0.5 * glm.sin(time_elapsed * 1.0)
        glow_strength1 = 0.5 + 0.5 * glm.sin(time_elapsed * 2.0)

        for obj in objects:
            model_matrix = glm.mat4(1.0)

            # Apply smooth rotations to scene
            model_matrix = glm.rotate(model_matrix, glm.radians(current_rot_x), glm.vec3(1, 0, 0))
            model_matrix = glm.rotate(model_matrix, glm.radians(current_rot_y), glm.vec3(0, 1, 0))

            # Calculate orbit translation (except world)
            if not obj.source_path.lower().endswith("world.txt"):
                radius = 0.01
                speed = 0.4
                x = radius * glm.cos(time_elapsed * speed)
                z = radius * glm.sin(time_elapsed * speed)
                y = 0.3 * glm.sin(time_elapsed * 1.5)
                model_matrix = glm.translate(model_matrix, glm.vec3(x, y, z))

            # Depth mask for outline outfit
            name = getattr(obj, 'source_path', '').lower()
            if "outline_outfit.txt" in name:
                glDepthMask(GL_FALSE)
            else:
                glDepthMask(GL_TRUE)

            # Emissive glow logic
            if "eyes.txt" in name:
                emissive = glm.vec3(0.6, 0.15, 0.8) * glow_strength * 3
            elif "outline_outfit.txt" in name:
                emissive = glm.vec3(75/255, 0/255, 130/255) * glow_strength1 * 0.2
            elif "magic.txt" in name:
                emissive = glm.vec3(0.7,0.3,0.0) * glow_strength1 * 3   
            elif "astaff.txt" in name:
                emissive = glm.vec3(0.25, 0.0, 0.4) * glow_strength1 * 3                 
            else:
                emissive = glm.vec3(0.0)

            glUniform3fv(emissive_loc, 1, glm.value_ptr(emissive))
            glUniformMatrix4fv(model_loc, 1, GL_FALSE, glm.value_ptr(model_matrix))
            obj.draw(shader_program, config.TEXTURE_UNITS)

        glDepthMask(GL_TRUE)

        pygame.display.flip()

    for obj in objects:
        glDeleteVertexArrays(1, [obj.VAO])
        glDeleteBuffers(1, [obj.VBO])
        glDeleteBuffers(1, [obj.EBO])
        for tex_id in obj.textures.values():
            glDeleteTextures(1, [tex_id])

    glDeleteProgram(shader_program)
    pygame.quit()

if __name__ == "__main__":
    main()
