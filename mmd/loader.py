import io
import struct

class ddict(dict): 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

class DataView(object):
    def __init__(self, data):
        self.buffer = io.BytesIO(data)

    def get_int8(self):
        v = struct.unpack_from('b', self.buffer.read(1))
        return v[0]

    def get_int8_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_int8())
        return a

    def get_uint8(self):
        v = struct.unpack_from('B', self.buffer.read(1))
        return v[0]

    def get_uint8_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_uint8())
        return a

    def get_int16(self):
        v = struct.unpack_from('h', self.buffer.read(2))
        return v[0]

    def get_int16_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_int16())
        return a

    def get_uint16(self):
        v = struct.unpack_from('H', self.buffer.read(2))
        return v[0]

    def get_uint16_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_uint16())
        return a

    def get_int32(self):
        v = struct.unpack_from('i', self.buffer.read(4))
        return v[0]

    def get_int32_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_int32())
        return a

    def get_uint32(self):
        v = struct.unpack_from('I', self.buffer.read(4))
        return v[0]

    def get_uint32_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_uint32())
        return a

    def get_float32(self):
        v = struct.unpack_from('f', self.buffer.read(4))
        return v[0]

    def get_float32_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_float32())
        return a

    def get_float64(self):
        v = struct.unpack_from('d', self.buffer.read(8))
        return v[0]

    def get_float64_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_float64())
        return a

    def get_index(self, itype, unsigned):
        if itype ==1:
            if unsigned:
                return self.get_uint8()
            return self.get_int8()
        elif itype ==2:
            if unsigned:
                return self.get_uint16()
            return self.get_int16()
        elif itype ==3:
            return self.get_int32()
        
        raise KeyError('unknown number type %d exception.!' % itype)
        
    def get_index_array(self, itype, size, unsigned):
        a = []
        for i in range(size):
            a.append(self.get_index(itype, unsigned))
        return a

    def get_chars(self, size):
        str = ''
        while (size > 0):
            value = self.get_uint8()
            size -= 1
            if not value:
                break
            str += chr(value)

        while (size > 0):
            self.get_uint8()
        
        return str

    def get_sjis_strings(self, size):
        chars = b''
        while (size > 0):
            value = self.get_uint8()
            size -= 1
            if not value:
                break
            chars += value.to_bytes(1, 'little')

        while (size > 0):
            self.get_uint8()
            size -= 1

        return chars.decode('ms932')

    def get_unicode_strings(self, size):
        chars = b''
        while (size > 0):
            value = self.get_uint16()
            size -= 2
            if not value:
                break
            chars += value.to_bytes(2, 'little')

        while (size > 0):
            self.get_uint8()
            size -= 1

        return chars.decode('utf-8')

    def get_text_buffer(self):
        size = self.get_uint32()
        return self.get_unicode_strings(size)


def load_pmd(dv):
    pmd = ddict()
    metadata = ddict()
    pmd.metadata = metadata
    pmd.metadata.format = 'pmd'
    pmd.metadata.coordinateSystem = 'left'

    def parse_header():
        metadata = pmd.metadata
        metadata.magic = dv.get_chars(3)

        if metadata.magic != 'Pmd':
            raise ValueError('PMD file magic is not Pmd, but %s' % (metadata.magic))

        metadata.version = dv.get_float32()
        metadata.modelName = dv.get_sjis_strings(20)
        metadata.comment = dv.get_sjis_strings(256)

    
    def parse_vertices():
        def parse_vertex():
            p = ddict()
            p.position = dv.get_float32_array(3)
            p.normal = dv.get_float32_array(3)
            p.uv = dv.get_float32_array(2)
            p.skinIndices = dv.get_uint16_array(2)
            p.skinWeights = [ dv.get_uint8() / 100 ]
            p.skinWeights.append( 1.0 - p.skinWeights[0] )
            p.edgeFlag = dv.get_uint8()
            return p
        
        metadata.vertexCount = dv.get_uint32()
        pmd.vertices = []
        for i in range(metadata.vertexCount):
            pmd.vertices.append( parse_vertex() )
        
    
    def parse_faces():
        def parse_face():
            p = ddict()
            p.indices = dv.get_uint16_array(3)
            return p
        
        metadata.faceCount = int(dv.get_uint32() / 3)
        pmd.faces = []
        for i in range(metadata.faceCount):
            pmd.faces.append( parse_face() )

    def parse_materials():
        def parse_material():
            p = ddict()
            p.diffuse = dv.get_float32_array(4)
            p.shininess = dv.get_float32()
            p.specular = dv.get_float32_array(3)
            p.ambient = dv.get_float32_array(3)
            p.toonIndex = dv.get_int8()
            p.edgeFlag = dv.get_uint8()
            p.faceCount = int(dv.get_uint32() / 3)
            p.fileName = dv.get_sjis_strings(20)
            return p

        metadata.materialCount = dv.get_uint32()
        pmd.materials = []
        for i in range(metadata.materialCount):
            pmd.materials.append( parse_material() )

    def parse_bones():
        def parse_bone():
            p = ddict()
            p.name = dv.get_sjis_strings(20)
            p.parentIndex = dv.get_int16()
            p.tailIndex = dv.get_int16()
            p.type = dv.get_uint8()
            p.ikIndex = dv.get_int16()
            p.position = dv.get_float32_array(3)
            return p

        metadata.boneCount = dv.get_uint16()
        pmd.bones = []
        for i in range(metadata.boneCount):
            pmd.bones.append( parse_bone() )


    def parse_iks():
        def parse_ik():
            p = ddict()
            p.target = dv.get_uint16()
            p.effector = dv.get_uint16()
            p.linkCount = dv.get_uint8()
            p.iteration = dv.get_uint16()
            p.maxAngle = dv.get_float32()

            p.links = []
            for i in range(p.linkCount):
                link = ddict()
                link.index = dv.get_uint16()
                p.links.append(link)
            return p

        metadata.ikCount = dv.get_uint16()
        pmd.iks = []
        for i in range(metadata.ikCount):
            pmd.iks.append( parse_ik() )


    def parse_morphs():
        def parse_morph():
            p = ddict()
            p.name = dv.get_sjis_strings(20)
            p.elementCount = dv.get_uint32()
            p.type = dv.get_uint8()

            p.elements = []
            for i in range(p.elementCount):
                p.elements.append( ddict({
                    'index': dv.get_uint32(),
                    'position': dv.get_float32_array(3)
                }) )

            return p

        metadata.morphCount = dv.get_uint16()
        pmd.morphs = []
        for i in range(metadata.morphCount):
            pmd.morphs.append( parse_morph() )


    def parse_morph_frames():
        def parse_morph_frame():
            p = ddict()
            p.index = dv.get_uint16()
            return p

        metadata.morphFrameCount = dv.get_uint8()
        pmd.morphFrames = []
        for i in range(metadata.morphFrameCount):
            pmd.morphFrames.append( parse_morph_frame() )


    def parse_bone_frame_names():
        def parse_bone_frame_name():
            p = ddict()
            p.name = dv.get_sjis_strings(50)
            return p
        
        metadata.boneFrameNameCount = dv.get_uint8()
        pmd.boneFrameNames = []
        for i in range(metadata.boneFrameNameCount):
            pmd.boneFrameNames.append( parse_bone_frame_name() )


    def parse_bone_frames():
        def parse_bone_frame():
            p = ddict()
            p.boneIndex = dv.get_int16()
            p.frameIndex = dv.get_uint8()
            return p

        metadata.boneFrameCount = dv.get_uint32()
        pmd.boneFrames = []
        for i in range(metadata.boneFrameCount):
            pmd.boneFrames.append( parse_bone_frame() )

    def parse_english_header():
        metadata.englishCompatibility = dv.get_uint8()
        if metadata.englishCompatibility > 0:
            metadata.englishModelName = dv.get_sjis_strings(20)
            metadata.englishComment = dv.get_sjis_strings(256)

    def parse_english_bone_names():
        def parse_english_bone_name():
            p = ddict()
            p.name = dv.get_sjis_strings(20)

        if not metadata.englishCompatibility:
            return

        pmd.englishBoneNames = []
        for i in range(metadata.boneCount):
            pmd.englishBoneNames.append( parse_english_bone_name() )

    
    def parse_english_morph_names():
        def parse_english_morph_name():
            p = ddict()
            p.name = dv.get_sjis_strings(20)
            return p

        if not metadata.englishCompatibility:
            return

        pmd.englishMorphNames = []
        for i in range(metadata.morphCount):
            pmd.englishMorphNames.append( parse_english_morph_name() )


    def parse_english_bone_frame_names():
        def parse_english_bone_frame_name():
            p = ddict()
            p.name = dv.get_sjis_strings(50)
            return p

        if not metadata.englishCompatibility:
            return

        pmd.englishBoneFrameNames = []
        for i in range(metadata.boneFrameNameCount):
            pmd.englishBoneFrameNames.append( parse_english_bone_frame_name() )


    def parse_toon_textures():
        def parse_toon_texture():
            p = ddict()
            p.fileName = dv.get_sjis_strings(100)
            return p

        pmd.toonTextures = []
        for i in range(10):
            pmd.toonTextures.append( parse_toon_texture() )


    def parse_rigid_bodies():
        def parse_rigid_body():
            p = ddict()
            p.name = dv.get_sjis_strings(20)
            p.boneIndex = dv.get_int16()
            p.groupIndex = dv.get_uint8()
            p.groupTarget = dv.get_uint16()
            p.shapeType = dv.get_uint8()
            p.width = dv.get_float32()
            p.height = dv.get_float32()
            p.depth = dv.get_float32()
            p.position = dv.get_float32_array(3)
            p.rotation = dv.get_float32_array(3)
            p.weight = dv.get_float32()
            p.positionDamping = dv.get_float32()
            p.rotationDamping = dv.get_float32()
            p.restitution = dv.get_float32()
            p.friction = dv.get_float32()
            p.type = dv.get_uint8()
            return p

        metadata.rigidBodyCount = dv.get_uint32()
        pmd.rigidBodies = []
        for i in range(metadata.rigidBodyCount):
            pmd.rigidBodies.append( parse_rigid_body() )


    def parse_constraints():
        def parse_constraint():
            p = ddict()
            p.name = dv.get_sjis_strings(20)
            p.rigidBodyIndex1 = dv.get_uint32()
            p.rigidBodyIndex2 = dv.get_uint32()
            p.position = dv.get_float32_array(3)
            p.rotation = dv.get_float32_array(3)
            p.translationLimitation1 = dv.get_float32_array(3)
            p.translationLimitation2 = dv.get_float32_array(3)
            p.rotationLimitation1 = dv.get_float32_array(3)
            p.rotationLimitation2 = dv.get_float32_array(3)
            p.springPosition = dv.get_float32_array(3)
            p.springRotation = dv.get_float32_array(3)
            return p

        metadata.constraintCount = dv.get_uint32()
        pmd.constraints = []
        for i in range(metadata.constraintCount):
            pmd.constraints.append( parse_constraint() )


    parse_header()
    parse_vertices()
    parse_faces()
    parse_materials()
    parse_bones()
    parse_iks()
    parse_morphs()
    parse_morph_frames()
    parse_bone_frame_names()
    parse_bone_frames()
    parse_english_header()
    parse_english_bone_names()
    parse_english_morph_names()
    parse_english_bone_frame_names()
    parse_toon_textures()
    parse_rigid_bodies()
    parse_constraints()

    #print(pmd.metadata)

    return pmd
    


    


def load(file):
    with open(file, 'rb') as f:
        dv = DataView(f.read())

    return load_pmd(dv)



if __name__ == '__main__':
    load('miku/Lat式ミクVer2.31_Normal.pmd')