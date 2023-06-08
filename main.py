from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from panda3d.core import NodePath
from panda3d.core import Texture
from panda3d.core import VirtualFileSystem
from panda3d.core import Multifile
from panda3d.core import Filename, StringStream

import mmd.loader as loader
import mmd.converter as converter

class App(ShowBase):
    # コンストラクタ
    def __init__(self):
        # ShowBaseを継承する
        ShowBase.__init__(self)

        # ウインドウの設定
        self.properties = WindowProperties()
        self.properties.setTitle('Box model')
        self.properties.setSize(700, 700)
        self.win.requestProperties(self.properties)
        self.setBackgroundColor(0, 0, 0)

        # マウス操作を禁止
        #self.disableMouse()
        # カメラの設定
        self.camera.setPos(0, -50, 10)
        #self.camera.lookAt(0, 0, 0)

        # 座標軸
        self.axis = self.loader.loadModel('models/zup-axis')
        self.axis.setPos(0, 0, 0)
        self.axis.setScale(1.5)
        self.axis.reparentTo(self.render)
        
        #ret = loader.load('dist/miku/Lat式ミクVer2.31_Normal.pmd')
        #ret = loader.load('dist/alicia/Alicia_solid.pmx')
        """
        for vertice in ret.vertices:
            sphere = self.loader.loadModel("models/misc/sphere")
            sphere.reparentTo(self.render)
            sphere.setScale(0.1, 0.1, 0.1)
            sphere.setPos(vertice.position[0], vertice.position[2], vertice.position[1])
        """

        self.model = self.loader.loadModel('dist/miku/test.egg')
        #self.model = self.loader.loadModel('models/cmss12.egg')
        
        #self.model.setPos(0, 0, 0)
        #self.cube1.setScale(5)
        self.model.reparentTo(self.render)


        


app = App()
app.run()

