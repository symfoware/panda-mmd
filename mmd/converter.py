import io
from . import loader

def convert(file):

    ret = loader.load(file)
    if not ret:
        raise ValueError('ファイル変換エラー')

    if not ret.metadata.format in ['pmd', 'pmx']:
        raise ValueError('ファイルがpmd、pmx形式ではありません')

    f = io.StringIO()
    f.write('<CoordinateSystem> { Z-Up }\n')

    f.write('<VertexPool> mmd {\n')
    for i, vertex in enumerate(ret.vertices):
        f.write('  <Vertex> %d {\n' % (i))
        f.write('    %f %f %f\n' % (vertex.position[0], vertex.position[2], vertex.position[1]))
        f.write('  }\n')
    
    f.write('}\n')

    f.write('<Group> mmd {\n')
    for face in ret.faces:
        f.write('  <Polygon> {\n')
        f.write('    <VertexRef> { %s <Ref> { mmd } }\n' % (' '.join([str(i) for i in face.indices])))
        f.write('  }\n')

    f.write('}\n')
    
    f.seek(0)
    return f.read()

