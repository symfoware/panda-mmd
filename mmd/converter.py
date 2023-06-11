import io
from . import loader

def convert(file):
    model = loader.load(file)
    return convert_model(model)

def convert_model(model):
    if not model:
        raise ValueError('ファイル変換エラー')

    if not model.metadata.format in ['pmd', 'pmx']:
        raise ValueError('ファイルがpmd、pmx形式ではありません')

    f = io.StringIO()
    f.write('<CoordinateSystem> { y-up }\n')

    materials_list = []
    for i, material in enumerate(model.materials):
        tref = -1
        if material.fileName:
            fileName = material.fileName.split('*')[0]
            f.write('<Texture> %d { "%s"' % (i, fileName))
            f.write('}\n')
            tref = i

        materials_list.append({'tref': tref, 'faceCount':material.faceCount})

    f.write('<VertexPool> mmd {\n')
    for i, vertex in enumerate(model.vertices):
        f.write('  <Vertex> %d {\n' % (i))
        f.write('    %.11f %.11f %.11f\n' % (vertex.position[0], vertex.position[1], vertex.position[2]))
        f.write('    <Normal> { %.11f %.11f %.11f }\n' % (vertex.normal[0], vertex.normal[1], vertex.normal[2]))
        f.write('    <UV> { %.11f %.11f }\n' % (vertex.uv[0], 1-vertex.uv[1]))
        f.write('  }\n')
    
    f.write('}\n')

    f.write('<Group> mmd {\n')
    current_tref = -1
    for face in model.faces:
        tref = materials_list[0]['tref']
        materials_list[0]['faceCount'] -= 1
        if not materials_list[0]['faceCount']:
            del materials_list[0]

        if tref != -1:
            current_tref = tref

        f.write('  <Polygon> {\n')
        if current_tref != -1:
            f.write('    <TRef> { %d }\n' % (current_tref))
        f.write('    <BFace> { 0 }\n')
        f.write('    <VertexRef> { %s <Ref> { mmd } }\n' % (' '.join([str(i) for i in face.indices])))
        f.write('  }\n')

    f.write('}\n')
    
    f.seek(0)
    return f.read()


'''
normal: 法線マッピング
テクスチャ画像の情報を使い、平板なモデルの表面に凹凸があるかのように見せる手法。
陰影情報が記録されたRGB画像を用いて、モデル表面の法線（normal）を変化させることで凹凸を表現する。

uv: UV座標系
3DCGモデルにテクスチャをマッピングするとき、貼り付ける位置や方向、大きさなどを指定するために使う座標系のこと。
'''