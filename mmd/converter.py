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
    f.write('<CoordinateSystem> { Z-Up }\n')

    f.write('<VertexPool> mmd {\n')
    for i, vertex in enumerate(model.vertices):
        f.write('  <Vertex> %d {\n' % (i))
        f.write('    %.11f %.11f %.11f\n' % (vertex.position[0], vertex.position[2], vertex.position[1]))
        f.write('  }\n')
    
    f.write('}\n')

    f.write('<Group> mmd {\n')
    for face in model.faces:
        f.write('  <Polygon> {\n')
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