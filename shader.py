from OpenGL.GL import *

vertex_shader = """
#version 330 core
layout (location = 0) in vec3 position;
layout (location = 1) in vec2 texCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec2 TexCoord;

void main() {
    gl_Position = projection * view * model * vec4(position, 1.0);
    TexCoord = texCoord;
}
"""

fragment_shader = """
#version 330 core
in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D texture_diffuse;
uniform vec3 emissiveColor;

void main() {
    vec4 baseColor = texture(texture_diffuse, TexCoord);
    if (baseColor.a < 0.1)
        discard;

    vec3 finalColor = baseColor.rgb + emissiveColor;
    FragColor = vec4(finalColor, baseColor.a);
}
"""

def create_shader_program():
    vs = glCreateShader(GL_VERTEX_SHADER)
    fs = glCreateShader(GL_FRAGMENT_SHADER)

    glShaderSource(vs, vertex_shader)
    glShaderSource(fs, fragment_shader)

    glCompileShader(vs)
    glCompileShader(fs)

    for shader, name in [(vs, "VERTEX"), (fs, "FRAGMENT")]:
        success = glGetShaderiv(shader, GL_COMPILE_STATUS)
        if not success:
            info_log = glGetShaderInfoLog(shader)
            print(f"ERROR::SHADER_COMPILATION_ERROR of type: {name}\n{info_log.decode()}")

    program = glCreateProgram()
    glAttachShader(program, vs)
    glAttachShader(program, fs)
    glLinkProgram(program)

    success = glGetProgramiv(program, GL_LINK_STATUS)
    if not success:
        info_log = glGetProgramInfoLog(program)
        print(f"ERROR::PROGRAM_LINKING_ERROR\n{info_log.decode()}")

    glDeleteShader(vs)
    glDeleteShader(fs)

    return program
