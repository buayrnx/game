from math import pi, sin, cos, atan2, degrees
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, DirectionalLight, AmbientLight
from panda3d.core import TransparencyAttrib
from panda3d.core import WindowProperties
from panda3d.core import CollisionTraverser, CollisionNode, CollisionBox, CollisionRay, CollisionHandlerQueue, CollisionHandlerEvent, CollisionHandlerPusher, CollisionSphere
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton
from panda3d.core import TextNode
from panda3d.core import BitMask32
from panda3d.core import ClockObject
from panda3d.core import Vec3 , Point3, LVecBase3f, GeoMipTerrain
from direct.task import Task
from direct.task.TaskManagerGlobal import taskMgr
from direct.showbase.DirectObject import DirectObject
from direct.actor.Actor import Actor
import random

loadPrcFile("settings.prc")

def degToRad(degrees):
       return degrees * ( pi / 180.0)

class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        self.selectedBlockType = "grass"
        self.loadModels()
        self.setupLights()
        self.setupCamera()
        self.setupSkybox()
        self.captureMouse()
        self.setupControls()
        self.loadSounds()
        self.loadBackgroundMusic()
        self.sheepMusic()
        self.loadMeatModel()
     
        self.can = 9
        self.monsters = []
        self.sheep = []
        self.blocks = []
        self.trees= []
        self.heartImages = []
        self.meatList = []
    
        self.areaSize = 26
        self.removed_blocks = set()
        self.block_size = 1
        self.fall_distance= 3
        
        self.wood = 0
        self.axeModel = None
        self.axeActivated = False
        self.axeActivatedtext = None

        self.isLeftMousePressed = False
        self.leftMousePressTime = 0.0

        self.meatClickTime = None

        self.canMoveUp = False
        self.canMoveDown = False

        self.generateTerrain()
        self.createMonsters(1)
        self.createSheeps(3)
        self.createTrees(2)
        self.createChest()

        self.taskMgr.add(self.update, "update")

        for i in range(9):
            heartImage = OnscreenImage(
                image = "heart_image.png",
                pos = ( -1.4 + i * 0.1, 0, -0.95),
                scale = (0.05, 1, 0.05)
            )
            heartImage.setTransparency(TransparencyAttrib.MAlpha)
            self.heartImages.append(heartImage)


        self.woodText = OnscreenText(
            text="Wood: 0",
            pos=(1.5, 0.9),
            scale=0.1,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
        )

    def showAxeActivatedText(self):
        self.axeActivatedText = OnscreenText(
            text="Axe is activated!",
            pos=(1.6, -0.7),
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
        )
        self.accept("mouse1", self.targetMonster)
        
    def update(self, task):
        globalClock = ClockObject.getGlobalClock()
        dt =globalClock.getDt()

        playerMoveSpeed = 10
        monsterMoveSpeed = 0.5
        sheepMoveSpeed = 1

        playerPos = self.camera.getPos()

        for monster in self.monsters:
            if not self.checkFallingandStuck(monster):
                monsterPos = monster.getPos()
                direction = (playerPos - monsterPos).normalized()
                movement = direction.xy * monsterMoveSpeed * dt

                newPosX = monster.getX() + movement[0]
                newPosY = monster.getY() + movement[1]

                if abs(newPosX) <= self.areaSize and abs(newPosY) <= self.areaSize:
                    if not self.checkBlockCollision(newPosX, newPosY):
                        monster.setX(newPosX)
                        monster.setY(newPosY)

                dx = playerPos.x - monsterPos.x
                dy = playerPos.y - monsterPos.y
                angle = atan2(dy,dx)
                monster_heading = degrees(angle) - 90
                monster.setH(monster_heading)

        for sheep in self.sheep:
            if not self.checkFallingandStuck(sheep):                
                x_movement =random.uniform(-sheepMoveSpeed, sheepMoveSpeed) * dt
                y_movement =random.uniform(-sheepMoveSpeed, sheepMoveSpeed) * dt
                newPosX = sheep.getX() + x_movement
                newPosY = sheep.getY() + y_movement

                if abs(newPosX) <= self.areaSize and abs(newPosY) <= self.areaSize:
                    if not self.checkBlockCollision(newPosX, newPosY):
                        sheep.setX(newPosX)
                        sheep.setY(newPosY)

                dx = playerPos.x - sheep.getX()
                dy = playerPos.y - sheep.getY()
                angle = atan2(dy, dx)
                sheep_heading = degrees(angle) - 270
                sheep.setH(sheep_heading) 

        blocks_broken = self.countBrokenBlocks("sheep", "monster")

        self.lowerEntities("sheep", "monsters")

        for sheep in self.sheep:
            sheep.setZ(sheep.getZ() - (15 *blocks_broken))

        for monster in self.monsters:
            monster.setZ(monster.getZ()- (15 *blocks_broken))

        x_movement = 0
        y_movement = 0
        z_movement = 0

        if self.keyMap['forward']:
            x_movement -= dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
            y_movement += dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
        if self.keyMap['backward']:
            x_movement += dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
            y_movement -= dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
        if self.keyMap['left']:
            x_movement -= dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
            y_movement -= dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
        if self.keyMap['right']:
            x_movement += dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
            y_movement += dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
        if self.keyMap['up']:
            if self.canMoveUp:
                z_movement += dt * playerMoveSpeed
        if self.keyMap['down']:
            if self.canMoveDown:
                z_movement -= dt * playerMoveSpeed

        self.camera.setPos(
            self.camera.getX() + x_movement,
            self.camera.getY() + y_movement,
            self.camera.getZ() + z_movement,
        )

        if self.cameraSwingActivated:
            md =self.win.getPointer(0)
            mouseX = md.getX()
            mouseY = md.getY()
 
            mouseChangeX = mouseX - self.lastMouseX
            mouseChangeY = mouseY - self.lastMouseY

            self.cameraSwingFactor = 1
        
            currentH = self.camera.getH()
            currentP = self.camera.getP()

            self.camera.setHpr(
                currentH - mouseChangeX * dt * self.cameraSwingFactor,
                min(180, max(-180, currentP - mouseChangeY * dt * self.cameraSwingFactor)),
                0
            )

            self.lastMouseX = mouseX
            self.lastMouseY = mouseY

        for monster in self.monsters:
            if random.random() < dt:
                self.fire(monster)
                monsterSound = monster.getPythonTag("sound")
                monsterSound.play()
        if not self.monsters:
            self.monsterSound.stop() 

        for i in range(len(self.heartImages)):
            if i < self.can:
                self.heartImages[i].show()
            else:
                self.heartImages[i].hide()

        if self.isLeftMousePressed:
            self.leftMousePressTime += dt

            if self.leftMousePressTime >= 3.0:
                for tree in self.trees:
                    distance = self.camera.getDistance(tree)
                    if distance < 14:
                        tree.removeNode()
                        self.trees.remove(tree)
                        self.isLeftMousePressed = False
                        self.leftMousePressTime = 0.0
                        self.wood += 3 
                        self.woodText.setText(f"Wood: {self.wood}") 
                        break

                for sheep in self.sheep:
                    distance = self.camera.getDistance(sheep)
                    if distance < 14:
                        self.createMeat(sheep.getPos())
                        self.sheep.remove(sheep)
                        sheep.removeNode()
                        self.isLeftMousePressed = False
                        self.leftMousePressTime = 0.0
                        break

                if self.keyMap['r']:
                    self.removeAxe()

                if self.meatClickTime is not None and (globalClock.getFrameTime() - self.meatClickTime) >= 3.0:
                    self.removeMeat()
                    self.can += 1
                    print("You ate the meat! Health increased. Current health:", self.can)
                    self.isLeftMousePressed = False
                    self.leftMousePressTime = 0.0

            self.woodText.setText(f"Wood: {self.wood}")
            self.checkWoodCount()

        if not self.sheep:
            self.stopSheepMusic()
            self.canMoveDown = True
            self.canMoveUp = True
        else:
            self.canMoveDown = False
            self.canMoveUp = False

        return task.cont
    
    def checkBlockCollision(self, x, y):
        for block in self.blocks:
            blockPos = block.getPos()
            if int(blockPos.x) == int(x) and int(blockPos.y) == int(y):
                return True
        return False
    
    def getBlockPos(self, x, y, z):
        block_size = 4  
        return Point3(x * block_size, y * block_size, z * block_size)
    
    def removeBlock(self, x, y, z):
        self.removed_blocks.add(Point3(x, y, z))
    
    def checkFallingandStuck(self, entity):
        currentPos = entity.getPos()
        x, y, z = int(currentPos.x), int(currentPos.y), int(currentPos.z)
        block_positions = []

        for dz in range(1, self.fall_distance + 1):
            block_pos = Point3(x, y, z - dz * self.block_size)
            block_positions.append(block_pos)
        for block_pos in block_positions:
            if block_pos not in  self.removed_blocks:
                return False
        entity.setZ(entity.getZ() - self.fall_distance * self.block_size)

        return True

    def fire(self, monster):
        distance =self.camera.getDistance(monster)
        if distance < 6:
            self.can -=1
            print("You were bitten! Health:", self.can)
            self.hituserSound.play()
        if self.can <= 0:
                print("You are a loser hahahaha ")
                exit()

    def setupControls(self):
        self.keyMap = {
            "forward": False,
            "backward":False,
            "left":False,
            "right":False,
            "up":False,
            "down":False,
            "r": False 
        }
        self.accept("escape", self.releaseMouse)
        self.accept("mouse1", self.handleLeftClick)
        self.accept("mouse3", self.placeBlock)

        self.accept("w", self.updateKeyMap, ["forward", True])
        self.accept("w-up", self.updateKeyMap, ["forward", False])
        self.accept("a", self.updateKeyMap, ["left", True])
        self.accept("a-up", self.updateKeyMap, ["left", False])
        self.accept("s", self.updateKeyMap, ["backward", True])
        self.accept("s-up", self.updateKeyMap, ["backward", False])
        self.accept("d", self.updateKeyMap, ["right", True])
        self.accept("d-up", self.updateKeyMap, ["right", False])
        
        self.accept("space", self.updateKeyMap, ["up", True])
        self.accept("space-up", self.updateKeyMap, ["up", False])
        self.accept("lshift", self.updateKeyMap, ["down", True])
        self.accept("lshift-up", self.updateKeyMap, ["down", False])

        self.accept("1", self.setSelectedBlockType, ["grass"])
        self.accept("2", self.setSelectedBlockType, ["dirt"])
        self.accept("3", self.setSelectedBlockType, ["sand"])
        self.accept("4", self.setSelectedBlockType, ["stone"])
        
        self.accept("mouse1-up", self.handleLeftClickRelease)
        self.accept("t", self.toggleAxe)
        self.accept("x", self.handleXKey)

    def handleXKey(self):
        if self.axeActivated:
           self.targetMonster()

    def setSelectedBlockType(self, type):
        self.selectedBlockType = type

    def countBrokenBlocks(self, *owners):
        count = 0 
        for block in self.blocks:
            for owner in owners:
                if block.getPythonTag("owner") == owner:
                    if block.getZ() < self.player.getZ():
                        count += 1
        return count
    
    def blockBroken(self, block):
        self.blocks.append(block)
        self.lowerEntities()

    def lowerEntities(self, *owners):
        blocks_broken = len(self.blocks)
        for owner in owners:
            for entity in getattr(self, owner):
                if entity and not entity.isEmpty():
                    if self.checkFallingandStuck(entity):
                        entity.setZ(entity.getZ() - blocks_broken * self.block_sized)
                    else:
                        entity.setZ(entity.getZ() - blocks_broken * self.block_size)

    def handleLeftClick(self):
        self.captureMouse()
        self.removeBlock()

        for monster in self.monsters:
            distance = self.camera.getDistance(monster)
            if distance < 2 :
                self.can -= 1 
                print("Canavar tarafından ısırıldın!Canın:", self.can)
            if distance < 14:
                self.isLeftMousePressed = True
                self.leftMousePressTime = 0.0
            if self.axeActivated:
                self.targetMonster()

        for tree in self.trees:
            distance = self.camera.getDistance(tree)
            if distance < 14:
                self.isLeftMousePressed = True
                self.leftMousePressTime = 0.0
                taskMgr.add(self.destroySheep, "destroySheep")
                

    def handleLeftClickRelease(self):
        self.isLeftMousePressed = False
        self.leftMousePressTime = 0.0
        taskMgr.remove("destroySheep")
        taskMgr.remove("destroyMonster")
        self.removeAxe()

    def removeBlock(self):
        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)
            
            hitNodePath = rayHit.getIntoNodePath()
            hitObject = hitNodePath.getPythonTag("owner")
            distanceFromPlayer = hitObject.getDistance(self.camera)

            if distanceFromPlayer < 8:
                hitNodePath.clearPythonTag("owner")
                hitObject.removeNode()

                if hitNodePath.hasPythonTag("type") and hitNodePath.getPythonTag("type") == "tree":
                    self.wood += 3
                    self.woodText.setText(f"Wood: {self.wood}")

             
                for entity in self.sheep + self.monsters:
                    if entity and hitObject and not entity.isEmpty() and not hitObject.isEmpty():
                        if entity.getZ() > hitObject.getZ():
                            entity.setZ(entity.getZ() - 24 )
             
 
    def placeBlock(self):
        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)
            hitNodePath = rayHit.getIntoNodePath()
            normal = rayHit.getSurfaceNormal(hitNodePath)

            
            hitObject = hitNodePath.getPythonTag("owner")
            distanceFromPlayer = hitObject.getDistance(self.camera)

            if distanceFromPlayer < 14:
                hitBlockPos = hitObject.getPos()
                newBlockPos = hitBlockPos + normal * 2
                self.createNewBlock(newBlockPos.x, newBlockPos.y, newBlockPos.z, self.selectedBlockType)
        
    def updateKeyMap(self, key, value):
        self.keyMap[key] = value

        if key == "up":
            self.canMoveUp = value
        elif key == "down":
            self.canMoveDown = value

    def captureMouse(self):
        self.cameraSwingActivated = True
        md =self.win.getPointer(0)
        self.lastMouseX = md.getX()
        self.lastMouseY = md.getY()

        properties = WindowProperties()
        properties.setCursorHidden(True)
        properties.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(properties)
    
    def releaseMouse(self):
        self.cameraSwingActivated = False
        properties = WindowProperties()
        properties.setCursorHidden(False)
        properties.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(properties)

    def setupCamera(self):
        self.disableMouse()
        self.camera.setPos(0, 0, 3)
        self.camLens.setFov(90)
        
        crosshairs = OnscreenImage(
            image = "crosshairs.png",
            pos = (0, 0, 0),
            scale = 0.05
        )
        crosshairs.setTransparency(TransparencyAttrib.MAlpha)

        self.cTrav = CollisionTraverser()
        ray = CollisionRay()
        ray.setFromLens(self.camNode, (0, 0))
        rayNode = CollisionNode("line-of-sight")
        rayNode.addSolid(ray)
        rayNodePath = self.camera.attachNewNode(rayNode)
        self.rayQueue = CollisionHandlerQueue()
        self.cTrav.addCollider(rayNodePath, self.rayQueue)

    def setupSkybox(self):
        skybox = self.loader.loadModel("skybox/skybox.egg")
        skybox.setScale(1000)
        skybox.setBin("background", 1)
        skybox.setDepthWrite(0)
        skybox.setLightOff()
        skybox.reparentTo(self.render)


    def generateTerrain(self):
        for z in range(10):
            for y in range(20):
                for x in range(20):
                    self.createNewBlock(
                        x * 2 -20,
                        y * 2 -20,
                       -z * 2,
                       "grass" if z ==0 else "dirt"
                    )
        self.createMonsters(5)
        self.createTrees(2)

    def createTrees(self, num_trees):
        for _ in range(num_trees):
            corner = random.choice([(1, 1), (-1, -1)])
            x = corner[0] * random.randint(10, 14)
            y = corner[1] * random.randint(10, 14)
            z = -1
            self.createTree(x, y, z)

    def createTree(self, x, y, z):
        tree =self.loader.loadModel("minecraft_tree.glb")
        tree.setPos(x, y, z)
        tree.setScale(5)
        tree.reparentTo(self.render)
        self.trees.append(tree)
        tree.setPythonTag("type", "tree")

    def destroyTree(self):
        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)
            hitNodePath = rayHit.getIntoNodePath()
            hitObject = hitNodePath.getPythonTag("owner")
            distanceFromPlayer = hitObject.getDistance(self.camera)

            if distanceFromPlayer < 14:
                hitTreePos = hitObject.getPos()
                hitObject.removeNode()
                self.trees.remove(hitObject)

    def createMonsters(self, num_monsters):
        for _ in range(num_monsters):
            x =random.randint( -14, 14)
            y =random.randint( -14, 14)
            z = 1
            self.createMonster(x, y, z)

    def createMonster(self, x, y, z):
        monster = self.loader.loadModel("monster.glb")
        monster.setScale(0.7)
        monster.setPos(x, y, z)
        monster.reparentTo(self.render)
        self.monsters.append(monster)

        monster.setPythonTag("owner", "monster")

        monster.setPythonTag("sound", self.monsterSound)

    
    def showAxeActivatedText(self):
        self.axeActivatedText = OnscreenText(
            text="Axe is activated!",
            pos=(1.6, -0.7),
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
        )
     

    def targetMonster(self):
        if self.axeActivated:
            closestMonster = None
            minDistance = float('inf')
            playerPos = self.camera.getPos()

            for monster in self.monsters:
                distance = monster.getDistance(self.camera)
                if distance < minDistance:
                    closestMonster = monster
                    minDistance = distance

            if closestMonster and minDistance < 10:
                self.destroyMonster(closestMonster)
                self.axeShot.play()
                    
    def destroyMonster(self, monster):
        self.monsters.remove(monster)
        monster.removeNode()
        
    def createSheeps(self, num_sheep):
        for _ in range(num_sheep):
            x = random.randint(-11, 11)
            y = random.randint(-10, 10)
            z = 1
            self.createSheep(x, y, z)
        if not self.sheep:
            self.canMoveDown = True
            self.canMoveDown = True

    def createSheep(self, x, y, z):
        sheep = self.loader.loadModel("sheep.glb")
        sheep.setScale(0.8)
        sheep.setPos(x, y, z)
        sheep.reparentTo(self.render)
        self.sheep.append(sheep)

        sheep.setPythonTag("owner", "sheep")

        sheep.setPythonTag("sound", self.sheepMusic)

        self.canMoveDown = True
        self.canMoveUp = True

    def destroySheep(self, task):
        globalClock = ClockObject.getGlobalClock()
        if self.isLeftMousePressed:
            self.leftMousePressTime += globalClock.getDt()
            if self.leftMousePressTime >= 3.0:
                for sheep in self.sheep:
                    distance = self.camera.getDistance(sheep)
                    if distance < 14:
                        self.sheep.remove(sheep)
                        sheep.removeNode()
                self.isLeftMousePressed = False
                self.leftMousePressTime = 0.0
                self.canMoveUp = False
                self.canMoveDown = False
                return Task.done
        return Task.cont

    def createNewBlock(self, x, y, z, type):
        newBlockNode = self.render.attachNewNode("new-block-placehold")
        newBlockNode.setPos(x, y, z)

        if type == "grass":
            self.grassBlock.instanceTo(newBlockNode)
        elif type == "dirt":
            self.dirtBlock.instanceTo(newBlockNode)
        elif type == "sand":
            self.sandBlock.instanceTo(newBlockNode)
        elif type == "stone":
            self.stoneBlock.instanceTo(newBlockNode)

        blockSolid = CollisionBox((-1, -1, -1), (1, 1, 1))
        blockNode =CollisionNode("block-collision-node")
        blockNode.addSolid(blockSolid)
        collider = newBlockNode.attachNewNode(blockNode)
        collider.setPythonTag("owner", newBlockNode)
        blockNode.setPythonTag("type", type)

    def createMeat(self, pos):
        meat = self.meatModel.copyTo(self.render)
        meat.setPos(pos.getX(), pos.getY(), pos.getZ() + self.block_size)
        meat.show()
        self.meatList.append(meat)
        self.eatSound.play()
        taskMgr.doMethodLater(3.0, self.removeMeat, "removeMeat", extraArgs=[meat])
     
    def checkEatMeat(self):
        for meat in self.meatList:
            globalClock = ClockObject.getGlobalClock()
            distance = self.camera.getDistance(meat)
            if distance < 14:
                self.meatClickTime = globalClock.getFrameTime()
                meat.removeNode()
                self.meatList.remove(meat)
                self.isLeftMousePressed = False
                self.leftMousePressTime = 0.0
                self.can += 1
                print("You ate the meat! Health increased. Current health:", self.can)
                break

    def removeMeat(self, meat):
        meat.removeNode()
        self.meatList.remove(meat)
        self.can += 1
        print("Meat removed!")
    
    def createChest(self):
        self.chest = None

    def createChestModel(self):
        x = random.randint(-10, 10)
        y = random.randint(-10, 10)
        z = 1
        self.chest = self.loader.loadModel("chest.glb")
        self.chest.setScale(0.5)
        self.chest.setPos(x, y, z)
        self.chest.reparentTo(self.render)

    def createAxe(self):
        self.axe = self.loader.loadModel("axe.glb")
        self.axe.setScale(1.5)
        self.axe.setPos(self.chest.getPos())
        self.axe.reparentTo(self.render)
        self.chest.removeNode()
        self.chest = None
        self.wood -= 6
        self.woodText.setText(f"Wood: {self.wood}")
        self.axeActivated = True
        self.showAxeActivatedText()

        if self.axeActivated:
            self.axe.hide()
        else:
            self.axe.show

    def removeAxe(self):
        if self.axeModel:
            self.axeModel.removeNode()
            self.axeModel = None
            print("Axe is deactivated!")
            self.axeActivatedText.removeNode() 
    
    def removeText(self, text):
        text.destroy()

    def checkWoodCount(self):
        if self.wood >= 6 and not self.chest:
            self.createChestModel()
    
    def toggleAxe(self):
        if self.chest and self.chest.getDistance(self.camera) < 10:
            self.createAxe()

    def playEatSound(self, task):
        self.eatSound.play()
        return task.done

    def increaseHealth(self, amount, task):
        self.can += amount
        return task.done            

    def loadModels(self):
        self.grassBlock = self.loader.loadModel("grass-block.glb")

        self.dirtBlock = self.loader.loadModel("dirt-block.glb")
        
        self.stoneBlock = self.loader.loadModel("stone-block.glb")

        self.sandBlock = self.loader.loadModel("sand-block.glb")

    def loadMeatModel(self):
        self.meatModel = self.loader.loadModel("meat.glb")
        self.meatModel.setPos(0, 0, 0)
        self.meatModel.setScale(0.5)
        self.meatModel.reparentTo(self.render)
        self.meatModel.hide()

    def loadSounds(self):
        self.monsterSound = self.loader.loadSfx("zombıe.wav")
        self.hituserSound = self.loader.loadSfx("hıtuser.wav")
        self.eatSound = self.loader.loadSfx("eat.wav")
        self.axeShot = self.loader.loadSfx("axe_shot.wav")
        
    def loadBackgroundMusic(self):
        music_path =  "background.mp3"
        ShowBase.background_music = self.loader.loadSfx(music_path)
        ShowBase.background_music.setLoop(True)
        ShowBase.background_music.play()
    
    def sheepMusic(self):
        music_path ="sheepsound.mp3"
        ShowBase.background_music = self.loader.loadSfx(music_path)
        ShowBase.background_music.setLoop(True)
        ShowBase.background_music.play()
        
    def stopSheepMusic(self):
        self.background_music.stop()
    
    def setupLights(self):
        mainLİght = DirectionalLight("main light")
        mainLİghtNodePath = self.render.attachNewNode(mainLİght)
        mainLİghtNodePath.setHpr(30, -60, 0)
        self.render.setLight(mainLİghtNodePath)

        ambientLight = AmbientLight("ambient light")
        ambientLight.setColor((0.3, 0.3, 0.3, 1))
        ambientLightNodePath = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNodePath)

    
game = MyGame()
game.run()