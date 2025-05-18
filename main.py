import pygame
from pygame.locals import *
from OpenGL.GL import *
import glm

import config
from model_loader import load_model_from_txt
from texture_loader import load_texture
from shader import create_shader_program

def main():
    pygame.init()
    display = (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption(config.WINDOW_TITLE)

    glEnable(GL_DEPTH_TEST)

    shader_program = create_shader_program()
    glUseProgram(shader_program)

    objects = load_model_from_txt("parts", load_texture)

    projection = glm.perspective(glm.radians(config.FOV), display[0] / display[1], config.NEAR_PLANE, config.FAR_PLANE)
    view = glm.lookAt(config.CAMERA_POS, config.CAMERA_TARGET, config.CAMERA_UP)
    model = glm.mat4(1.0)

    proj_loc = glGetUniformLocation(shader_program, "projection")
    view_loc = glGetUniformLocation(shader_program, "view")
    model_loc = glGetUniformLocation(shader_program, "model")

    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, glm.value_ptr(projection))
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, glm.value_ptr(view))

    # Set the background color to black
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Black background (RGBA)

    # Camera and rotation state
    camera_pos = config.CAMERA_POS
    target_camera_distance = glm.length(camera_pos)
    rot_x, rot_y = 0, 0
    last_mouse_pos = (0, 0)
    mouse_down = False

    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            # Zoom and rotate with mouse
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up (zoom in)
                    target_camera_distance -= 0.5
                    target_camera_distance = max(1.0, target_camera_distance)
                elif event.button == 5:  # Scroll down (zoom out)
                    target_camera_distance += 0.5

                if event.button == 1:  # Left click (rotate)
                    mouse_down = True
                    last_mouse_pos = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click release
                    mouse_down = False

            if event.type == pygame.MOUSEMOTION and mouse_down:
                x, y = pygame.mouse.get_pos()
                dx = x - last_mouse_pos[0]
                dy = y - last_mouse_pos[1]
                rot_y += dx * 0.5
                rot_x += dy * 0.5
                last_mouse_pos = (x, y)

        # --- Smooth Interpolation ---
        lerp_speed = 0.1  # Speed of transition
        camera_pos = glm.vec3(0, 0, target_camera_distance)
        camera_pos.x += (config.CAMERA_POS.x - camera_pos.x) * lerp_speed
        camera_pos.y += (config.CAMERA_POS.y - camera_pos.y) * lerp_speed
        camera_pos.z += (target_camera_distance - camera_pos.z) * lerp_speed

        # Apply view and projection
        view = glm.lookAt(camera_pos, config.CAMERA_TARGET, config.CAMERA_UP)
        glUniformMatrix4fv(view_loc, 1, GL_FALSE, glm.value_ptr(view))

        # Apply model transformations for rotation
        rot_model = glm.mat4(1.0)
        rot_model = glm.rotate(rot_model, glm.radians(rot_x), glm.vec3(1, 0, 0))
        rot_model = glm.rotate(rot_model, glm.radians(rot_y), glm.vec3(0, 1, 0))
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, glm.value_ptr(rot_model))

        # Draw objects
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        for obj in objects:
            obj.draw(shader_program, config.TEXTURE_UNITS)
        
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
