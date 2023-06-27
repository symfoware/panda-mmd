import io
import os
import struct

class ddict(dict): 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

class DataView(object):
    def __init__(self, data):
        self.length = len(data)
        self.buffer = io.BytesIO(data)

    def read(self, size):
        self.length -= size
        return self.buffer.read(size)

    def get_int8(self):
        v = struct.unpack_from('b', self.read(1))
        return v[0]

    def get_int8_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_int8())
        return a

    def get_uint8(self):
        v = struct.unpack_from('B', self.read(1))
        return v[0]

    def get_uint8_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_uint8())
        return a

    def get_int16(self):
        v = struct.unpack_from('h', self.read(2))
        return v[0]

    def get_int16_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_int16())
        return a

    def get_uint16(self):
        v = struct.unpack_from('H', self.read(2))
        return v[0]

    def get_uint16_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_uint16())
        return a

    def get_int32(self):
        v = struct.unpack_from('i', self.read(4))
        return v[0]

    def get_int32_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_int32())
        return a

    def get_uint32(self):
        v = struct.unpack_from('I', self.read(4))
        return v[0]

    def get_uint32_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_uint32())
        return a

    def get_float32(self):
        v = struct.unpack_from('f', self.read(4))
        return v[0]

    def get_float32_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_float32())
        return a

    def get_float64(self):
        v = struct.unpack_from('d', self.read(8))
        return v[0]

    def get_float64_array(self, size):
        a = []
        for i in range(size):
            a.append(self.get_float64())
        return a

    def get_index(self, itype, unsigned=False):
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
        
    def get_index_array(self, itype, size, unsigned=False):
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
            size -= 1
        
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

        return chars.decode('cp932')

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

        return chars.decode('utf-16')

    def get_text_buffer(self):
        size = self.get_uint32()
        return self.get_unicode_strings(size)

    def is_empty(self):
        return self.length == 0


# parse pmd format file
def parse_pmd(dv):
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
        if dv.is_empty():
            metadata.englishCompatibility = 0
            return

        metadata.englishCompatibility = dv.get_uint8()
        if metadata.englishCompatibility > 0:
            metadata.englishModelName = dv.get_sjis_strings(20)
            metadata.englishComment = dv.get_sjis_strings(256)

    def parse_english_bone_names():
        def parse_english_bone_name():
            p = ddict()
            p.name = dv.get_sjis_strings(20)
            return p

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
        for i in range(metadata.morphCount-1):
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

        if dv.is_empty():
            return

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

        if dv.is_empty():
            return

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

        if dv.is_empty():
            return

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

    return pmd
    


# parse pmx format file
def parse_pmx(dv):

    pmx = ddict()
    metadata = ddict()
    pmx.metadata = metadata
    pmx.metadata.format = 'pmx'
    pmx.metadata.coordinateSystem = 'left'

    def parse_header():
        metadata.magic = dv.get_chars(4).strip()
        if metadata.magic != 'PMX':
            raise ValueError('PMX file magic is not PMX, but %s' % (metadata.magic))

        metadata.version = dv.get_float32()
        if metadata.version != 2.0 and metadata.version != 2.1:
            raise ValueError('PMX version %.2f is not supported.' % (metadata.version))

        metadata.headerSize = dv.get_uint8()
        metadata.encoding = dv.get_uint8()
        metadata.additionalUvNum = dv.get_uint8()
        metadata.vertexIndexSize = dv.get_uint8()
        metadata.textureIndexSize = dv.get_uint8()
        metadata.materialIndexSize = dv.get_uint8()
        metadata.boneIndexSize = dv.get_uint8()
        metadata.morphIndexSize = dv.get_uint8()
        metadata.rigidBodyIndexSize = dv.get_uint8()
        metadata.modelName = dv.get_text_buffer()
        metadata.englishModelName = dv.get_text_buffer()
        metadata.comment = dv.get_text_buffer()
        metadata.englishComment = dv.get_text_buffer()


    def parse_vertices(): # Vertex
        def parse_vertex():
            p = ddict()
            p.position = dv.get_float32_array(3)
            p.normal = dv.get_float32_array(3)
            p.uv = dv.get_float32_array(2)
            
            p.auvs = []
            for i in range(metadata.additionalUvNum):
                p.auvs.append( dv.get_float32_array(4) )

            p.type = dv.get_uint8()
            index_size = metadata.boneIndexSize
            if p.type == 0: # BDEF1
                p.skinIndices = dv.get_index_array(index_size, 1)
                p.skinWeights = [ 1.0 ]

            elif p.type == 1: # BDEF2
                p.skinIndices = dv.get_index_array(index_size, 2 )
                p.skinWeights = dv.get_float32_array(1)
                p.skinWeights.append( 1.0 - p.skinWeights[0] )

            elif p.type == 2: # BDEF4
                p.skinIndices = dv.get_index_array(index_size, 4)
                p.skinWeights = dv.get_float32_array(4)

            elif p.type == 3: # SDEF

                p.skinIndices = dv.get_index_array(index_size, 2)
                p.skinWeights = dv.get_float32_array(1)
                p.skinWeights.append( 1.0 - p.skinWeights[0] )

                p.skinC = dv.get_float32_array(3)
                p.skinR0 = dv.get_float32_array(3)
                p.skinR1 = dv.get_float32_array(3)

                # SDEF is not supported yet and is handled as BDEF2 so far.
                # TODO: SDEF support
                p.type = 1

            else:
                raise ValueError('unsupport bone type %d exception.' % (p.type))

            p.edgeRatio = dv.get_float32()
            return p

        metadata.vertexCount = dv.get_uint32()
        pmx.vertices = []
        for i in range(metadata.vertexCount):
            pmx.vertices.append( parse_vertex() )


    def parse_faces(): # Faces
        def parse_face():
            p = ddict()
            p.indices = dv.get_index_array(metadata.vertexIndexSize, 3, True)
            return p

        metadata.faceCount = int(dv.get_uint32() / 3)
        pmx.faces = []
        for i in range(metadata.faceCount):
            pmx.faces.append( parse_face() )


    def parse_textures(): # Textures
        def parse_texture():
            return dv.get_text_buffer()

        metadata.textureCount = dv.get_uint32()
        pmx.textures = []
        for i in range(metadata.textureCount):
            pmx.textures.append( parse_texture() )


    def parse_materials(): # Material
        def parse_material():
            p = ddict()
            p.name = dv.get_text_buffer()
            p.englishName = dv.get_text_buffer()
            p.diffuse = dv.get_float32_array(4)
            p.specular = dv.get_float32_array(3)
            p.shininess = dv.get_float32()
            p.ambient = dv.get_float32_array(3)
            p.flag = dv.get_uint8()
            p.edgeColor = dv.get_float32_array(4)
            p.edgeSize = dv.get_float32()
            p.textureIndex = dv.get_index(metadata.textureIndexSize)
            p.envTextureIndex = dv.get_index(metadata.textureIndexSize)
            p.envFlag = dv.get_uint8()
            p.toonFlag = dv.get_uint8()

            if p.toonFlag == 0:
                p.toonIndex = dv.get_index(metadata.textureIndexSize)

            elif p.toonFlag == 1:
                p.toonIndex = dv.get_int8()

            else:
                raise ValueError('unknown toon flag %d exception.' % (p.toonFlag))

            p.comment = dv.get_text_buffer()
            p.faceCount = int(dv.get_uint32() / 3)
            return p

        metadata.materialCount = dv.get_uint32()
        pmx.materials = []
        for i in range(metadata.materialCount):
            pmx.materials.append( parse_material() )


    def parse_bones(): # Bone
        def parse_bone():
            p = ddict()
            p.name = dv.get_text_buffer()
            p.englishName = dv.get_text_buffer()
            p.position = dv.get_float32_array(3)
            p.parentIndex = dv.get_index(pmx.metadata.boneIndexSize)
            p.transformationClass = dv.get_uint32()
            p.flag = dv.get_uint16()

            if p.flag & 0x1:
                p.connectIndex = dv.get_index(pmx.metadata.boneIndexSize)

            else:
                p.offsetPosition = dv.get_float32_array(3)


            if p.flag & 0x100 or p.flag & 0x200: # 回転、移動付与
                grant = ddict()

                grant.isLocal = True if p.flag & 0x80 else False
                grant.affectRotation = True if p.flag & 0x100 else False
                grant.affectPosition = True if p.flag & 0x2000 else False
                grant.parentIndex = dv.get_index(metadata.boneIndexSize)
                grant.ratio = dv.get_float32()

                p.grant = grant


            if p.flag & 0x400: # 軸固定
                p.fixAxis = dv.get_float32_array(3)

            if p.flag & 0x800: # ローカル軸
                p.localXVector = dv.get_float32_array(3)
                p.localZVector = dv.get_float32_array(3)

            if p.flag & 0x2000: # 外部親変形
                p.key = dv.get_uint32()

            if p.flag & 0x20: # IK
                ik = ddict()

                ik.effector = dv.get_index(metadata.boneIndexSize)
                ik.target = None
                ik.iteration = dv.get_uint32()
                ik.maxAngle = dv.get_float32()
                ik.linkCount = dv.get_uint32()
                ik.links = []
                for i in range(ik.linkCount):
                    link = ddict()
                    link.index = dv.get_index(metadata.boneIndexSize)
                    link.angleLimitation = dv.get_uint8()

                    if link.angleLimitation == 1:
                        link.lowerLimitationAngle = dv.get_float32_array(3)
                        link.upperLimitationAngle = dv.get_float32_array(3)

                    ik.links.append( link )

                p.ik = ik

            return p

        metadata.boneCount = dv.get_uint32()
        pmx.bones = []
        for i in range(metadata.boneCount):
            pmx.bones.append( parse_bone() )


    def parse_morphs(): # モーフ
        def parse_morph():
            p = ddict()
            p.name = dv.get_text_buffer()
            p.englishName = dv.get_text_buffer()
            p.panel = dv.get_uint8()
            p.type = dv.get_uint8()
            p.elementCount = dv.get_uint32()
            p.elements = []

            for i in range(p.elementCount):
                if p.type == 0: # group morph
                    m = ddict()
                    m.index = dv.get_index(metadata.morphIndexSize)
                    m.ratio = dv.get_float32()
                    p.elements.append(m)

                elif p.type == 1: # vertex morph
                    m = ddict()
                    m.index = dv.get_index(metadata.vertexIndexSize, True)
                    m.position = dv.get_float32_array(3)
                    p.elements.append(m)

                elif p.type == 2: # bone morph
                    m = ddict()
                    m.index = dv.get_index(metadata.boneIndexSize)
                    m.position = dv.get_float32_array(3)
                    m.rotation = dv.get_float32_array(4)
                    p.elements.append(m)

                elif p.type == 3: # uv morph
                    m = ddict()
                    m.index = dv.get_index(metadata.vertexIndexSize, True)
                    m.uv = dv.get_float32_array(4)
                    p.elements.append(m)

                elif p.type == 4: # additional uv1
                    # TODO: implement
                    pass

                elif p.type == 5: # additional uv2
                    # TODO: implement
                    pass

                elif p.type == 6: # additional uv3
                    # TODO: implement
                    pass

                elif p.type == 7: # additional uv4
                    # TODO: implement
                    pass

                elif p.type == 8: # material morph
                    m = ddict()
                    m.index = dv.get_index(metadata.materialIndexSize)
                    m.type = dv.get_uint8()
                    m.diffuse = dv.get_float32_array(4)
                    m.specular = dv.get_float32_array(3)
                    m.shininess = dv.get_float32()
                    m.ambient = dv.get_float32_array(3)
                    m.edgeColor = dv.get_float32_array(4)
                    m.edgeSize = dv.get_float32()
                    m.textureColor = dv.get_float32_array(4)
                    m.sphereTextureColor = dv.get_float32_array(4)
                    m.toonColor = dv.get_float32_array(4)
                    p.elements.append(m)

            return p

        metadata.morphCount = dv.get_uint32()
        pmx.morphs = []
        for i in range(metadata.morphCount):
            pmx.morphs.append( parse_morph() )


    def parse_frames(): # 表示枠
        def parse_frame():
            p = ddict()
            p.name = dv.get_text_buffer()
            p.englishName = dv.get_text_buffer()
            p.type = dv.get_uint8()
            p.elementCount = dv.get_uint32()
            p.elements = []

            for i in range(p.elementCount):
                e = ddict()
                e.target = dv.get_uint8()
                e.index = dv.get_index(metadata.boneIndexSize) if e.target == 0 else dv.get_index(metadata.morphIndexSize)
                p.elements.append(e)

            return p

        metadata.frameCount = dv.get_uint32()
        pmx.frames = []
        for i in range(metadata.frameCount):
            pmx.frames.append( parse_frame() )



    def parse_rigid_bodies(): # 剛体
        def parse_rigid_body():
            p = ddict()
            p.name = dv.get_text_buffer()
            p.englishName = dv.get_text_buffer()
            p.boneIndex = dv.get_index(metadata.boneIndexSize)
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
        pmx.rigidBodies = []
        for i in range(metadata.rigidBodyCount):
            pmx.rigidBodies.append( parse_rigid_body() )


    def parse_constraints(): # ジョイント
        def parse_constraint():
            p = ddict()
            p.name = dv.get_text_buffer()
            p.englishName = dv.get_text_buffer()
            p.type = dv.get_uint8()
            p.rigidBodyIndex1 = dv.get_index(metadata.rigidBodyIndexSize)
            p.rigidBodyIndex2 = dv.get_index(metadata.rigidBodyIndexSize)
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
        pmx.constraints = []
        for i in range(metadata.constraintCount):
            pmx.constraints.append( parse_constraint() )


    parse_header()
    parse_vertices()
    parse_faces()
    parse_textures()
    parse_materials()
    parse_bones()
    parse_morphs()
    parse_frames()
    parse_rigid_bodies()
    parse_constraints()

    return pmx


# parse vmd format file
def parse_vmd(dv):
    vmd = ddict()
    metadata = ddict()
    vmd.metadata = metadata
    vmd.metadata.coordinateSystem = 'left'

    def parse_header():
        metadata.magic = dv.get_chars(30)
        if metadata.magic != 'Vocaloid Motion Data 0002':
            raise ValueError('VMD file magic is not Vocaloid Motion Data 0002, but %s' % (metadata.magic))

        metadata.name = dv.get_sjis_strings(20)

    
    def parse_motions():
        def parse_motion():
            p = ddict()
            p.boneName = dv.get_sjis_strings(15)
            p.frameNum = dv.get_uint32()
            p.position = dv.get_float32_array(3)
            p.rotation = dv.get_float32_array(4)
            p.interpolation = dv.get_uint8_array(64)
            return p

        metadata.motionCount = dv.get_uint32()
        vmd.motions = []
        for i in range(metadata.motionCount):
            vmd.motions.append( parse_motion() )


    def parse_morphs():
        def parse_morph():
            p = ddict()
            p.morphName = dv.get_sjis_strings(15)
            p.frameNum = dv.get_uint32()
            p.weight = dv.get_float32()
            return p

        metadata.morphCount = dv.get_uint32()
        vmd.morphs = []
        for i in range(metadata.morphCount):
            vmd.morphs.append( parse_morph() )

    def parse_cameras():
        def parse_camera():
            p = ddict()
            p.frameNum = dv.get_uint32()
            p.distance = dv.get_float32()
            p.position = dv.get_float32_array(3)
            p.rotation = dv.get_float32_array(3)
            p.interpolation = dv.get_uint8_array(24)
            p.fov = dv.get_uint32()
            p.perspective = dv.get_uint8()
            return p

        metadata.cameraCount = dv.get_uint32()
        vmd.cameras = []
        for i in range(metadata.cameraCount):
            vmd.cameras.push( parse_camera() )

    parse_header()
    parse_motions()
    parse_morphs()
    parse_cameras()

    return vmd

    

def parse_vpd(dv, encode='ms932'):
    import re
    text = dv.buffer.read().decode(encode)
    text = re.sub(';.*', '', text)
    lines = re.split('\r|\n|\r\n', text)

    vpd = ddict()
    metadata = ddict()
    vpd.metadata = metadata
    vpd.bones = []

    def check_magic():
        if lines[ 0 ] != 'Vocaloid Pose Data file':
            raise ValueError('the file seems not vpd file.')

    def parse_header():
        if len(lines) < 4:
            raise ValueError('the file seems not vpd file.')

        metadata.parentFile = lines[2]
        metadata.boneCount = int(lines[3])

    def parse_bones():
        header = re.compile(r'^\s*(Bone[0-9]+)\s*\{\s*(.*)$')
        vector = re.compile(r'^\s*(-?[0-9]+\.[0-9]+)\s*,\s*(-?[0-9]+\.[0-9]+)\s*,\s*(-?[0-9]+\.[0-9]+)\s*')
        quaternion = re.compile(r'^\s*(-?[0-9]+\.[0-9]+)\s*,\s*(-?[0-9]+\.[0-9]+)\s*,\s*(-?[0-9]+\.[0-9]+)\s*,\s*(-?[0-9]+\.[0-9]+)\s*')
        footer = re.compile(r'^\s*}')

        n = None
        t = None
        q = None
        for line in lines[5:]:
            if not line:
                continue
            
            if not n:
                m = header.match(line)
                if not m:
                    raise ValueError('the file seems not vpd file.')

                n = m.groups()[1]
                continue
                
            if not t:
                m = vector.match(line)
                if not m:
                    raise ValueError('the file seems not vpd file.')
                
                t = [ float(f) for f in m.groups() ]
                continue

            if not q:
                m = quaternion.match(line)
                if not m:
                    raise ValueError('the file seems not vpd file.')
                
                q = [ float(f) for f in m.groups() ]
                continue
            
            if not footer.match(line):
                raise ValueError('the file seems not vpd file.')

            vpd.bones.append(ddict({
                'name': n,
                'translation': t,
                'quaternion': q
            }))
            n = None
            t = None
            q = None


    check_magic()
    parse_header()
    parse_bones()

    return vpd


def load(file, format=None, encode='ms932'):
    with open(file, 'rb') as f:
        dv = DataView(f.read())

    if not format:
        format = file.split('.')[-1].upper()
    
    loaded = None
    if 'PMD' == format:
        loaded = parse_pmd(dv)
    elif 'PMX' == format:
        loaded = parse_pmx(dv)
    elif 'VMD' == format:
        loaded = parse_vmd(dv)
    elif 'VPD' == format:
        loaded = parse_vpd(dv, encode)

    if not loaded:
        raise ValueError('Unknown format %s.' % (format))

    loaded.metadata.base = os.path.dirname(file)
    return loaded


