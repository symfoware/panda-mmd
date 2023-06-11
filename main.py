import os
from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d

import mmd.loader
import mmd.converter

class App(ShowBase):
    # コンストラクタ
    def __init__(self):
        # ShowBaseを継承する
        ShowBase.__init__(self)

        # ウインドウの設定
        self.properties = p3d.WindowProperties()
        self.properties.setTitle('Box model')
        self.properties.setSize(700, 700)
        self.win.requestProperties(self.properties)
        self.setBackgroundColor(0, 0, 0)

        # マウス操作を禁止
        #self.disableMouse()
        # カメラの設定
        #self.camera.setPos(0, -50, 10)
        #self.camera.lookAt(0, 0, 0)

        # 座標軸
        self.axis = self.loader.loadModel('models/zup-axis')
        self.axis.setPos(0, 0, 0)
        self.axis.setScale(2)
        self.axis.reparentTo(self.render)

        mmd_model = mmd.loader.load('dist/miku/Lat式ミクVer2.31_Normal.pmd')
        #mmd_model = mmd.loader.load('dist/miku2/miku.pmd')
        #mmd_model = mmd.loader.load('dist/chihaya/chihaya.pmd')
        mmd_egg = mmd.converter.convert_model(mmd_model)

        stream = p3d.StringStream()
        mf = p3d.Multifile()
        mf.openReadWrite(stream)

        # 変換した内容を登録
        egg_bytes = p3d.StringStream(mmd_egg.encode('utf-8'))
        mf.addSubfile('model.egg', egg_bytes, 1)
        # flushを実行してバッファーの内容を確定させる
        mf.flush()

        # モデルで使用している画像をメモリーに転送
        registed = set()
        for material in mmd_model.materials:
            if not material.fileName:
                continue
            
            fileNames = material.fileName.split('*')
            for fileName in fileNames:
                if fileName in registed:
                    continue
                registed.add(fileName)
                texture = os.path.join(mmd_model.metadata.base, fileName)
                texture_bytes = p3d.StringStream(open(texture, 'rb').read())
                mf.addSubfile(fileName, texture_bytes, 1)
                mf.flush()

        # 仮想ファイルに/mfでマウント
        vfs = p3d.VirtualFileSystem.getGlobalPtr()
        if not vfs.mount(mf, '/mf', p3d.VirtualFileSystem.MFReadOnly):
            print('vfs mount error')
            return

        self.model = self.loader.loadModel('/mf/model.egg')

        # 奥向になるので180度回転し、手前(yマイナス)に向ける
        self.model.setH(self.model, 180)
        self.model.reparentTo(self.render)
        


app = App()
app.run()

