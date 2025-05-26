import os
import numpy as np
from OpenGL.GL import *

class SceneObject:
    def __init__(self, name, vertices, indices, textures, source_path=None):
        self.name = name
        self.source_path = source_path  # <-- NEW: store file path
        self.vertex_count = len(indices)
        self.textures = textures

        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(1)
        self.EBO = glGenBuffers(1)

        vertex_data = np.array(vertices, dtype=np.float32)
        index_data = np.array(indices, dtype=np.uint32)

        glBindVertexArray(self.VAO)

        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, GL_STATIC_DRAW)

        # Positions
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # TexCoords
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

    def draw(self, shader_program, texture_units):
        if "BaseColor" in self.textures:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.textures["BaseColor"])
            glUniform1i(glGetUniformLocation(shader_program, "texture_diffuse"), 0)

        for tex_type, tex_id in self.textures.items():
            unit = texture_units.get(tex_type, 0)
            glActiveTexture(GL_TEXTURE0 + unit)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glUniform1i(glGetUniformLocation(shader_program, tex_type), unit)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.vertex_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)


def load_model_from_txt(folder_path, texture_loader):
    objects = []
    texture_types = ["BaseColor", "Normal", "Roughness", "Alpha", "Metallic", "Emissive"]

    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r') as f:
            lines = f.readlines()

        name = lines[0].split(":")[1].strip()
        textures = {}
        for i, ttype in enumerate(texture_types):
            tex_name = lines[i+1].split(":")[1].strip()
            if tex_name != "None":
                tex_path = os.path.join("texture", tex_name)
                textures[ttype] = texture_loader(tex_path)

        v_start = lines.index("Vertices:\n") + 1
        i_start = lines.index("Indices:\n")
        vertices = [list(map(float, l.strip().split())) for l in lines[v_start:i_start]]
        indices = [int(i) for l in lines[i_start+1:] for i in l.strip().split()]
        flat_vertices = [coord for v in vertices for coord in v]

        obj = SceneObject(name, flat_vertices, indices, textures, source_path=filename)
        objects.append(obj)

    return objects
